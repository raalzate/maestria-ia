import uuid

import streamlit as st
from config.settings import LLM_MODEL
from prompts import registry
from ui.components.context import render_context_fields


def _get_draft_service():
    """Build or retrieve the DraftService singleton from session state."""
    if "_draft_service" not in st.session_state:
        from infra.adapters.file_draft_repository import FileDraftRepository
        from services.draft_service import DraftService

        repo = FileDraftRepository()
        st.session_state["_draft_service"] = DraftService(repository=repo)
    return st.session_state["_draft_service"]


def _pdf_to_markdown(uploaded_pdf, inference=None):
    """Extract PDF content and convert to structured Markdown (AI-powered when available)."""
    from ui.utils.pdf import pdf_to_markdown

    return pdf_to_markdown(uploaded_pdf, inference=inference)


def process_input(source_type, source_data, source_name, ctx_pdf, ctx_text):
    """Process input using the new refactored pipeline with injected adapters."""
    from application.pipeline import AnalysisRequest, run_analysis
    from domain.events import ErrorEvent, ProgressEvent

    inference = st.session_state.get("_inference_port")
    transcription = st.session_state.get("_transcription_port")
    cache = st.session_state.get("_cache_port")

    if inference is None:
        st.error("Motor de inferencia no disponible. Reinicia la aplicación.")
        return

    focus_directive = (st.session_state.get("_focus_directive") or "").strip() or None
    if focus_directive:
        st.info(f"🎯 Aplicando directiva de foco: «{focus_directive}»")

    with st.status(f"🤖 Procesando {source_name}...", expanded=True) as status:
        try:
            # Prepare context
            final_context = ctx_text or ""
            if ctx_pdf:
                ctx_pdf_name = getattr(ctx_pdf, "name", "PDF")
                status.write(f"📄 Procesando documento «{ctx_pdf_name}» (etapa: Contexto Adicional)...")
                pdf_md = _pdf_to_markdown(ctx_pdf, inference=inference)
                final_context = f"{final_context}\n\n--- DOCUMENTACIÓN PDF ---\n{pdf_md}"

            # Build event handler for real-time UI updates.
            # LangGraph runs parallel branches in worker threads that lack a
            # Streamlit ScriptRunContext; swallow those writes instead of
            # crashing the pipeline. Events are still captured by the
            # collector in pipeline.run_analysis.
            from streamlit.errors import NoSessionContext

            def on_event(event):
                try:
                    if isinstance(event, ProgressEvent):
                        status.write(f"⚙️ [{event.node_name}] {event.message}")
                    elif isinstance(event, ErrorEvent):
                        status.write(f"⚠️ [{event.node_name}] {event.message}")
                except NoSessionContext:
                    pass

            # Build request
            if source_type == "audio":
                # Build the transcription adapter lazily (downloads the Whisper
                # model on first run) — only when audio is actually submitted.
                if transcription is None:
                    from ui.streamlit_app import _build_transcription_adapter

                    status.write("🎧 Preparando el motor de transcripción (la primera vez descarga el modelo)...")
                    transcription = _build_transcription_adapter()
                    st.session_state["_transcription_port"] = transcription
                status.write(f"🎧 Transcribiendo audio «{source_name}» (etapa: Fuente de Información)...")
                audio_bytes = source_data.getvalue() if hasattr(source_data, "getvalue") else source_data
                request = AnalysisRequest(
                    audio_bytes=audio_bytes,
                    audio_name=source_name,
                    context=final_context if final_context.strip() else None,
                    focus_directive=focus_directive,
                    language="es",
                )
            else:
                status.write(f"🧠 Analizando documento «{source_name}» (etapa: Fuente de Información)...")
                request = AnalysisRequest(
                    transcript=source_data,
                    context=final_context if final_context.strip() else None,
                    focus_directive=focus_directive,
                    language="es",
                )

            # Run the pipeline
            result = run_analysis(
                request=request,
                inference=inference,
                transcription=transcription,
                cache=cache,
                emitter=on_event,
            )

            # Store result in session state
            st.session_state.analysis_result = {
                "analysis": result.analysis,
                "transcript": result.transcript,
                "context": final_context if final_context.strip() else None,
                "logs": f"Events: {len(result.events)}, Errors: {len(result.errors)}",
            }

            # Persist the full analysis (including ddd_specs) to disk
            from ui.utils.storage import save_static_json as _save_json

            to_save = result.analysis.model_dump()
            to_save["transcript"] = result.transcript
            _save_json(to_save)

            if result.errors:
                for err in result.errors:
                    st.warning(f"⚠️ [{err.node_name}] {err.message}")

            # Create draft snapshot of the successful generation
            generation_id = str(uuid.uuid4())
            st.session_state.current_generation_id = generation_id
            try:
                draft_service = _get_draft_service()
                draft_service.create_draft(result.analysis, generation_id)
            except Exception:
                pass  # Draft creation failure must not block the pipeline

            # Signal the refinement agent to auto-trigger post-generation analysis.
            st.session_state.refinement_pending = True

            status.update(label="✅ ¡Análisis Completado!", state="complete", expanded=False)
            st.rerun()

        except Exception as e:
            status.update(label="❌ Error Crítico", state="error")
            st.error(f"Ocurrió un error inesperado: {e}")


def _render_docs_extraction_tab() -> str:
    """Multi-document tab: extract a clean business-flow narrative via the LLM.

    Routes through `_inference_port` so the active backend (Claude Code CLI when the
    subscription flag is on, otherwise the API adapter) does the extraction.
    Returns the narrative chosen by the user (empty string if none ready).
    """
    st.info(
        "Sube uno o varios documentos (PDF, MD, TXT). La IA filtrará secciones que NO pertenezcan "
        "al flujo de negocio (recursos humanos, marketing, contenido genérico, etc.) y producirá "
        "una narrativa lista para el pipeline de Event Storming."
    )
    uploaded = st.file_uploader(
        "📂 Documentos del proceso a analizar",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        key="docs_multi_uploader",
    )

    if not uploaded:
        return ""

    # ── Step 1: extract markdown from each file (cached by filename+size) ──
    inference = st.session_state.get("_inference_port")
    docs: list[tuple[str, str]] = []
    with st.spinner("📄 Procesando documentos..."):
        for f in uploaded:
            cache_key = f"_docs_extract_{f.name}_{f.size}"
            if cache_key not in st.session_state:
                if f.type == "application/pdf":
                    st.session_state[cache_key] = _pdf_to_markdown(f, inference=inference)
                else:
                    try:
                        st.session_state[cache_key] = f.getvalue().decode("utf-8")
                    except Exception:
                        st.session_state[cache_key] = str(f.getvalue())
            docs.append((f.name, st.session_state[cache_key]))

    total_chars = sum(len(c) for _, c in docs)
    st.caption(f"{len(docs)} documento(s) listos · {total_chars:,} caracteres en total.")

    backend = type(inference).__name__ if inference is not None else "—"
    is_cli = backend == "ClaudeCodeCliInferenceAdapter"
    badge = "🖥️ CLI suscripción" if is_cli else f"💠 API ({backend})"
    st.caption(f"Backend de extracción: {badge}")

    extraction_key = "_docs_flow_extraction"
    extraction_sig = (
        tuple((n, len(c)) for n, c in docs),
        backend,
    )

    if st.button(
        "🧠 Extraer flujo de negocio con IA",
        type="secondary",
        key="btn_extract_business_flow",
        disabled=inference is None,
    ):
        from services.business_flow_extractor import extract_business_flow

        focus = (st.session_state.get("_focus_directive") or "").strip() or None
        with st.spinner(f"Filtrando ruido y extrayendo el flujo de negocio vía {backend}..."):
            try:
                result = extract_business_flow(docs, inference, focus_directive=focus)
                st.session_state[extraction_key] = {"result": result, "sig": extraction_sig}
                # Default checkbox state: included == True, excluded == False.
                _reset_topic_overrides(result)
                st.success(f"✅ Extracción completada (confianza: {result.confidence}).")
            except Exception as e:
                st.error(f"La IA no pudo extraer el flujo: {e}")
                st.session_state.pop(extraction_key, None)

    cached = st.session_state.get(extraction_key)
    if not cached or cached.get("sig") != extraction_sig:
        return ""

    result = cached["result"]
    if result.summary:
        st.markdown(f"**Resumen:** {result.summary}")

    st.markdown(
        "Marca / desmarca temas según corresponda. Cuando quede algún cambio, pulsa "
        "**Re-extraer** para que la IA reescriba la narrativa incluyendo los temas que "
        "movieron al flujo y descartando los que sacaste."
    )
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**✅ Temas incluidos en el flujo** (desmarca para EXCLUIR)")
        for i, topic in enumerate(result.detected_topics):
            st.checkbox(
                topic,
                value=st.session_state.get(_topic_state_key("inc", i), True),
                key=_topic_state_key("inc", i),
            )
    with cols[1]:
        st.markdown("**🚫 Temas excluidos como ruido** (marca para INCLUIR)")
        for i, topic in enumerate(result.excluded_topics):
            st.checkbox(
                topic,
                value=st.session_state.get(_topic_state_key("exc", i), False),
                key=_topic_state_key("exc", i),
            )

    force_include, force_exclude = _collect_topic_overrides(result)
    overrides_pending = bool(force_include or force_exclude)

    if st.button(
        "🔄 Re-extraer con cambios",
        key="btn_reextract_business_flow",
        disabled=not overrides_pending or inference is None,
        help=(
            "Re-ejecuta la extracción de IA forzando los temas marcados / desmarcados. "
            "Sin cambios marcados queda deshabilitado."
        ),
    ):
        from services.business_flow_extractor import extract_business_flow

        focus = (st.session_state.get("_focus_directive") or "").strip() or None
        with st.spinner(f"Re-extrayendo con overrides del usuario vía {backend}..."):
            try:
                new_result = extract_business_flow(
                    docs,
                    inference,
                    force_include=force_include,
                    force_exclude=force_exclude,
                    focus_directive=focus,
                )
                st.session_state[extraction_key] = {"result": new_result, "sig": extraction_sig}
                _reset_topic_overrides(new_result)
                st.success(f"✅ Re-extracción lista (confianza: {new_result.confidence}).")
                st.rerun()
            except Exception as e:
                st.error(f"La IA no pudo re-extraer: {e}")

    edited = st.text_area(
        "Narrativa extraída (editable antes de analizar)",
        value=result.flow_narrative,
        height=320,
        key="docs_extracted_narrative_editor",
    )
    use_it = st.checkbox(
        "Usar esta narrativa para el análisis",
        value=True,
        key="use_extracted_business_flow",
    )
    return edited if use_it else ""


def _render_video_tab() -> str:
    """Video tab: record a specific monitor in real time or upload a video,
    then analyze it with the vision model to produce a business-flow narrative.

    Returns the narrative chosen by the user (empty string if none ready).
    """
    mode = st.radio(
        "Selecciona fuente de video:",
        ["🖥️ Grabar Pantalla", "📂 Subir Video"],
        horizontal=True,
        label_visibility="collapsed",
        key="video_input_mode",
    )

    if mode == "🖥️ Grabar Pantalla":
        _render_screen_recording_controls()
    else:
        uploaded_video = st.file_uploader(
            "Sube tu video (mp4, mov, webm, avi)",
            type=["mp4", "mov", "webm", "avi"],
            key="video_uploader",
        )
        if uploaded_video is not None:
            import tempfile
            from pathlib import Path

            cache_key = f"_video_upload_{uploaded_video.name}_{uploaded_video.size}"
            if st.session_state.get("_video_upload_key") != cache_key:
                suffix = Path(uploaded_video.name).suffix or ".mp4"
                tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                tmp.write(uploaded_video.getvalue())
                tmp.close()
                st.session_state["_video_path"] = tmp.name
                st.session_state["_video_upload_key"] = cache_key
                st.session_state.pop("_video_narrative", None)

    video_path = st.session_state.get("_video_path")
    if not video_path:
        return ""

    st.video(video_path)

    with_audio = st.checkbox(
        "🎧 Transcribir narración de audio del video (si existe)",
        value=mode == "📂 Subir Video",
        key="video_transcribe_audio",
        help="La grabación de pantalla no captura audio; aplica sobre todo a videos subidos.",
    )

    if st.button("🧠 Analizar Video con IA", type="secondary", key="btn_analyze_video"):
        inference = st.session_state.get("_inference_port")
        if inference is None:
            st.error("Motor de inferencia no disponible. Reinicia la aplicación.")
        else:
            from domain.exceptions import VisionNotSupportedError
            from services.video_analysis import analyze_video

            transcription = None
            if with_audio:
                transcription = st.session_state.get("_transcription_port")
                if transcription is None:
                    from ui.streamlit_app import _build_transcription_adapter

                    transcription = _build_transcription_adapter()
                    st.session_state["_transcription_port"] = transcription

            focus = (st.session_state.get("_focus_directive") or "").strip() or None
            with st.status("🎬 Analizando el video...", expanded=True) as status:
                try:
                    narrative = analyze_video(
                        video_path,
                        inference=inference,
                        transcription=transcription,
                        focus_directive=focus,
                        emit=status.write,
                    )
                    st.session_state["_video_narrative"] = narrative
                    status.update(label="✅ Video analizado", state="complete", expanded=False)
                except VisionNotSupportedError as e:
                    status.update(label="❌ Visión no soportada", state="error")
                    st.error(str(e))
                except Exception as e:
                    status.update(label="❌ Error analizando el video", state="error")
                    st.error(f"No se pudo analizar el video: {e}")

    narrative = st.session_state.get("_video_narrative")
    if not narrative:
        return ""

    edited = st.text_area(
        "Narrativa del flujo observado (editable antes de analizar)",
        value=narrative,
        height=300,
        key="video_narrative_editor",
    )
    use_it = st.checkbox(
        "Usar esta narrativa para el análisis",
        value=True,
        key="use_video_narrative",
    )
    return edited if use_it else ""


def _render_recording_status(recorder) -> None:
    """Live recording indicator: monitor, elapsed time, frames and a preview
    of the latest captured frame (FR-010)."""
    if recorder is None or not recorder.is_recording:
        return
    mins, secs = divmod(int(recorder.elapsed_seconds), 60)
    st.markdown(f"#### 🔴 GRABANDO — {recorder.monitor_label}")
    st.caption(f"⏱️ {mins:02d}:{secs:02d} · {recorder.frames_captured} fotogramas · {recorder.fps:.0f} fps")
    if recorder.latest_frame_jpeg:
        st.image(
            recorder.latest_frame_jpeg,
            caption="Vista previa en vivo de lo que se está grabando",
            width=640,
        )


def _render_screen_recording_controls() -> None:
    """Start/stop real-time recording of a specific monitor (state in session)."""
    recorder = st.session_state.get("_screen_recorder")

    if recorder is not None and recorder.is_recording:
        # Fragment reruns every second so the timer, frame counter and live
        # preview refresh without user interaction.
        @st.fragment(run_every=1.0)
        def _live_status() -> None:
            _render_recording_status(st.session_state.get("_screen_recorder"))

        _live_status()
        if st.button("⏹️ Detener Grabación", type="primary", key="btn_stop_recording"):
            try:
                path = recorder.stop()
                st.session_state["_video_path"] = str(path)
                st.session_state.pop("_video_narrative", None)
            except Exception as e:
                st.error(
                    f"La grabación falló: {e}. En macOS, otorga permiso de Grabación de "
                    "Pantalla a tu terminal en Ajustes → Privacidad y Seguridad."
                )
            finally:
                st.session_state["_screen_recorder"] = None
            st.rerun()
        return

    try:
        from services.screen_recorder import list_monitors

        monitors = list_monitors()
    except Exception as e:
        st.error(f"No se pudieron detectar las pantallas: {e}")
        return

    if not monitors:
        st.error("No se detectó ninguna pantalla.")
        return

    selected = st.selectbox(
        "Pantalla a capturar:",
        monitors,
        format_func=lambda m: m.label,
        key="video_monitor_select",
    )
    fps = st.slider(
        "Fotogramas por segundo",
        min_value=1,
        max_value=10,
        value=2,
        key="video_fps",
        help="Para flujos de negocio en pantalla, 1-2 fps suele ser suficiente.",
    )

    if st.button("🔴 Iniciar Grabación", type="primary", key="btn_start_recording"):
        from services.screen_recorder import ScreenRecorder

        rec = ScreenRecorder(monitor_index=selected.index, fps=float(fps), monitor_label=selected.label)
        try:
            rec.start()
            st.session_state["_screen_recorder"] = rec
        except Exception as e:
            st.error(f"No se pudo iniciar la grabación: {e}")
        st.rerun()


def _topic_state_key(kind: str, idx: int) -> str:
    return f"_docs_topic_{kind}_{idx}"


def _reset_topic_overrides(result) -> None:
    """Reset the checkbox session_state to match the new extraction defaults."""
    # Clear any stale entries from a previous extraction.
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("_docs_topic_"):
            del st.session_state[key]
    for i, _ in enumerate(result.detected_topics):
        st.session_state[_topic_state_key("inc", i)] = True
    for i, _ in enumerate(result.excluded_topics):
        st.session_state[_topic_state_key("exc", i)] = False


def _collect_topic_overrides(result) -> tuple[list[str], list[str]]:
    """Return (force_include, force_exclude) based on user checkbox state.

    - Originally-excluded topics that the user CHECKED  → force_include.
    - Originally-included topics that the user UNCHECKED → force_exclude.
    """
    force_include: list[str] = []
    force_exclude: list[str] = []
    for i, topic in enumerate(result.detected_topics):
        if not st.session_state.get(_topic_state_key("inc", i), True):
            force_exclude.append(topic)
    for i, topic in enumerate(result.excluded_topics):
        if st.session_state.get(_topic_state_key("exc", i), False):
            force_include.append(topic)
    return force_include, force_exclude


def render_input_tabs():
    """Renderiza las fases de entrada como acordeones colapsables."""

    has_result = bool(st.session_state.get("analysis_result"))

    # ── Phase 1: Fuente de Información ──────────────────────────
    audio_source = None
    audio_name = None
    final_transcript_to_process = ""

    with st.expander("📥 1. Fuente de Información", expanded=not has_result):
        st.markdown("**🎯 Directiva de foco para la IA** (opcional)")
        st.caption(
            "Instrucciones de alta prioridad que la IA tomará como regla. "
            "Ej: «Enfócate solo en el bloque de Liquidación», "
            "«Considera solo procesos relacionados con vencimientos», "
            "«Ignora todo lo referente a reportes internos». "
            "Aplica a la extracción de flujos (Documentos PDF) y al análisis semántico DDD."
        )
        # Stored in session_state via key="_focus_directive"; read elsewhere from
        # there, so the return value is intentionally not bound to a variable.
        st.text_area(
            "Foco / regla obligatoria",
            value=st.session_state.get("_focus_directive", ""),
            height=80,
            key="_focus_directive",
            label_visibility="collapsed",
            placeholder="Ej: Enfócate solo en el flujo de Vencimientos Bloque 2; ignora reportes financieros.",
        )
        st.divider()

        tab_audio, tab_video, tab_text, tab_docs = st.tabs(
            [
                "🎙️ Audio / Grabación",
                "🎥 Video / Pantalla",
                "📝 Transcripción / Texto",
                "📚 Documentos PDF (extracción IA)",
            ]
        )

        # === AUDIO ===
        with tab_audio:
            input_mode = st.radio(
                "Selecciona fuente de audio:",
                ["🎙️ Grabar Voz", "📂 Subir Archivo"],
                horizontal=True,
                label_visibility="collapsed",
            )

            if input_mode == "🎙️ Grabar Voz":
                audio_bytes = st.audio_input("Haz click para grabar")
                if audio_bytes:
                    audio_source = audio_bytes
                    audio_name = "audio_grabado.wav"
            else:
                uploaded_file = st.file_uploader(
                    "Sube tu archivo (mp3, wav, m4a, opus)", type=["mp3", "wav", "m4a", "opus"]
                )
                if uploaded_file:
                    audio_source = uploaded_file
                    audio_name = uploaded_file.name

        # === VIDEO / PANTALLA ===
        with tab_video:
            video_narrative = _render_video_tab()

        # === TEXTO / DOCUMENTO ===
        with tab_text:
            st.info("Sube un documento o pega texto para analizar.")

            doc_file = st.file_uploader("📂 Cargar Documento Base (PDF, TXT, MD)", type=["pdf", "txt", "md"])

            initial_text = ""
            if doc_file:
                cached_key = f"_doc_cache_{doc_file.name}_{doc_file.size}"
                if cached_key not in st.session_state:
                    inference = st.session_state.get("_inference_port")
                    with st.spinner(f"📄 Procesando documento «{doc_file.name}» (etapa: Fuente de Información)..."):
                        if doc_file.type == "application/pdf":
                            st.session_state[cached_key] = _pdf_to_markdown(doc_file, inference=inference)
                        else:
                            try:
                                st.session_state[cached_key] = doc_file.getvalue().decode("utf-8")
                            except Exception:
                                st.session_state[cached_key] = str(doc_file.getvalue())
                initial_text = st.session_state[cached_key]

            transcript = st.text_area("Contenido / Transcripción", value=initial_text, height=300)

            # Simulation options
            st.markdown("**Modo de simulación:**")
            sim_mode = st.radio(
                "Modo de simulación:",
                [
                    "Sin simulación",
                    "✨ Narrativa (un agente reescribe)",
                    "🤖 Taller Multi-Agente (dos agentes conversan)",
                ],
                horizontal=True,
                label_visibility="collapsed",
            )
            final_transcript_to_process = transcript

            # ── Opción 1: Narrativa (un agente) ──────────────────────
            if sim_mode == "✨ Narrativa (un agente reescribe)" and transcript.strip():
                if st.button("🎭 Generar Simulación Narrativa", type="secondary"):
                    inference = st.session_state.get("_inference_port")
                    if inference:
                        with st.spinner(f"🤖 Generando simulación de taller ({LLM_MODEL})..."):
                            prompt = registry.get("narrative_transform_ui").render(transcript=transcript).to_string()
                            simulated_text = inference.invoke_text(prompt)
                            st.session_state["simulated_narrative"] = simulated_text
                            st.session_state.pop("multi_agent_simulation", None)
                            st.success("¡Narrativa generada!")

                if "simulated_narrative" in st.session_state:
                    with st.expander("Ver Narrativa Simulada", expanded=True):
                        st.markdown(st.session_state["simulated_narrative"])
                        if st.checkbox("Usar esta narrativa para el análisis", value=True):
                            final_transcript_to_process = st.session_state["simulated_narrative"]

            # ── Opción 2: Taller Multi-Agente ────────────────────────
            elif sim_mode == "🤖 Taller Multi-Agente (dos agentes conversan)":
                st.info(
                    "Dos agentes conversan entre sí: un **Facilitador** de Event Storming "
                    "y un **Experto de Dominio**. La conversación genera un transcript listo para análisis.\n\n"
                    "Usa el texto del área de arriba como descripción del dominio (fuente de conocimiento del experto). "
                    "El Contexto Adicional (fase 2) también será considerado."
                )
                num_turns = st.slider("Número de turnos de conversación", min_value=4, max_value=16, value=8, step=2)

                domain_description = transcript.strip()
                if not domain_description:
                    st.warning(
                        "Escribe una descripción del dominio en el área de texto para que el Experto tenga conocimiento base."
                    )
                else:
                    if st.button("🎭 Iniciar Taller Multi-Agente", type="secondary"):
                        inference = st.session_state.get("_inference_port")
                        if inference:
                            from services.workshop_simulation import WorkshopSimulator

                            st.session_state.pop("multi_agent_simulation", None)
                            st.session_state.pop("simulated_narrative", None)
                            simulation_turns_display = []
                            sim_container = st.container()

                            def on_turn(turn):
                                simulation_turns_display.append(turn)
                                with sim_container:
                                    with st.chat_message("assistant", avatar="🧑‍💼"):
                                        st.markdown(f"**Facilitador (turno {turn.turn_number}):** {turn.facilitator}")
                                    with st.chat_message("user", avatar="👤"):
                                        st.markdown(f"**Experto (turno {turn.turn_number}):** {turn.expert}")

                            with st.spinner(f"🤖 Simulando taller ({num_turns} turnos)..."):
                                simulator = WorkshopSimulator(inference)
                                simulation = simulator.simulate(
                                    context=domain_description,
                                    num_turns=num_turns,
                                    on_turn=on_turn,
                                )
                            st.session_state["multi_agent_simulation"] = simulation
                            st.success(f"✅ Taller completado — {len(simulation.turns)} turnos generados.")

                if "multi_agent_simulation" in st.session_state:
                    sim = st.session_state["multi_agent_simulation"]
                    with st.expander("📜 Ver Transcript Completo del Taller", expanded=False):
                        st.text_area("Transcript generado", value=sim.transcript, height=300, disabled=True)
                    if st.checkbox(
                        "Usar esta conversación para el análisis",
                        value=True,
                        key="use_multi_agent_sim",
                    ):
                        final_transcript_to_process = sim.transcript

        # === DOCUMENTOS HETEROGÉNEOS (extracción IA) ===
        with tab_docs:
            extracted_narrative = _render_docs_extraction_tab()
            if extracted_narrative and extracted_narrative.strip():
                # If this tab produced a usable narrative, route it through the
                # standard text-analysis flow.
                final_transcript_to_process = extracted_narrative

    # A ready video narrative routes through the standard text-analysis flow
    # (same path as audio transcripts). Applied last: the text tab assigns
    # final_transcript_to_process unconditionally and would clobber it.
    if video_narrative and video_narrative.strip():
        final_transcript_to_process = video_narrative

    # ── Phase 2: Contexto Adicional ─────────────────────────────
    with st.expander("📚 2. Contexto Adicional (Reglas, Diccionario, PDFs)", expanded=not has_result):
        context_pdf, context_text = render_context_fields()

    # ── Actions: Botones de análisis ────────────────────────────
    if audio_source:
        st.success(f"🎧 Audio listo: **{audio_name}**")
        if st.button("🚀 Analizar Audio", type="primary", width="stretch"):
            process_input(
                source_type="audio",
                source_data=audio_source,
                source_name=audio_name,
                ctx_pdf=context_pdf,
                ctx_text=context_text,
            )

    if final_transcript_to_process.strip():
        if st.button("🚀 Analizar Contenido", type="primary", width="stretch"):
            process_input(
                source_type="text",
                source_data=final_transcript_to_process,
                source_name="Texto/Narrativa",
                ctx_pdf=context_pdf,
                ctx_text=context_text,
            )
