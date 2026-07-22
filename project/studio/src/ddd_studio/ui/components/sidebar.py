import streamlit as st
from infra.inference_provider import InferenceProvider
from models.domain_analysis import DomainAnalysis
from ui.utils.storage import clear_all_data


def _get_draft_service():
    """Build or retrieve the DraftService singleton from session state."""
    if "_draft_service" not in st.session_state:
        from infra.adapters.file_draft_repository import FileDraftRepository
        from services.draft_service import DraftService

        repo = FileDraftRepository()
        st.session_state["_draft_service"] = DraftService(repository=repo)
    return st.session_state["_draft_service"]


def render_sidebar():
    """Renderiza la barra lateral con instrucciones y controles de sesión."""
    with st.sidebar:
        st.header("🧠 Domain Modeler AI")
        _maybe_show_clear_result()
        _render_ai_config()
        _render_help_tutorial()
        _render_history_section()
        st.markdown("""
        Esta herramienta utiliza **GenAI** para convertir Transcripciónes de talleres (Event Storming) en modelos de dominio DDD.

        **Pasos:**
        1. 🎤 Sube un audio o pega texto.
        2. 📝 (Opcional) Sube un PDF con reglas de negocio.
        3. 🚀 Genera el modelo.
        4. ✏️ Edita y valida los resultados.
        5. 📥 Descarga el reporte (PDF, JSON, diagramas).
        """)

        st.divider()
        if st.button("🗑️ Limpiar Todo", width="stretch"):
            st.session_state["_confirm_clear_all"] = True

        if st.session_state.get("_confirm_clear_all"):
            _render_clear_all_confirmation()

        st.caption("v2.1 - Powered by Raul A.")


def _render_help_tutorial():
    """Render the in-app help/tutorial as an expander with one sub-expander per section."""
    from ui.components.help_content import HELP_SECTIONS

    with st.expander("📚 Ayuda / Tutorial", expanded=False):
        st.caption("Cómo usar DDD Studio, paso a paso.")
        for title, body in HELP_SECTIONS:
            with st.expander(title, expanded=False):
                st.markdown(body)


def _maybe_show_clear_result():
    """Show a one-shot success toast after a full clear."""
    counts = st.session_state.pop("_clear_result", None)
    if not counts:
        return
    parts = [
        f"static: {counts.get('static', 0)}",
        f"cache: {counts.get('cache', 0)}",
        f"drafts: {counts.get('drafts', 0)}",
    ]
    if counts.get("llm_config"):
        parts.append("llm_config: 1")
    st.success("🧹 Limpieza completada — " + ", ".join(parts))


@st.dialog("Confirmar Limpieza Total")
def _render_clear_all_confirmation():
    """Confirm full wipe: session, cache, drafts, static JSON, optionally API key."""
    st.warning(
        "Esto borrará: resultado actual, caché (`.cache/`), historial de drafts "
        "(`drafts/`) y el JSON estático. La acción **no se puede deshacer**."
    )
    wipe_config = st.checkbox(
        "También borrar configuración LLM (API Key y modelo)",
        value=False,
        help="Si lo marcas, tendrás que reingresar tu Google API Key.",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sí, limpiar todo", type="primary", width="stretch"):
            counts = clear_all_data(include_llm_config=wipe_config)
            st.session_state.clear()
            st.session_state["_clear_result"] = counts
            st.rerun()
    with col2:
        if st.button("Cancelar", width="stretch"):
            st.session_state.pop("_confirm_clear_all", None)
            st.rerun()


def _render_history_section():
    """Render the Generation History expander in the sidebar."""
    draft_service = _get_draft_service()

    drafts = draft_service.list_drafts()

    with st.expander("📜 Generation History", expanded=bool(drafts)):
        if not drafts:
            st.info("No generations saved yet. Run a generation to see your history here.")
            return

        for entry in drafts:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**{entry.project_name}**\n\n{entry.created_at[:16].replace('T', ' ')} — {entry.summary.label}"
                )
                if st.button("👁️ Preview", key=f"preview_{entry.id}", width="stretch"):
                    _load_draft_into_session(draft_service, entry.id, entry.generation_id)

            with col2:
                if st.button("🗑️", key=f"delete_{entry.id}"):
                    st.session_state["_confirm_delete_draft_id"] = entry.id

    # Handle delete confirmation dialog
    confirm_id = st.session_state.get("_confirm_delete_draft_id")
    if confirm_id:
        _render_delete_confirmation(draft_service, confirm_id)


def _load_draft_into_session(draft_service, draft_id: str, generation_id: str):
    """Load a draft snapshot into session state as the active model."""
    draft = draft_service.get_draft(draft_id)
    if not draft:
        st.error("Draft not found.")
        return

    try:
        analysis_obj = DomainAnalysis.model_validate(draft.snapshot)
    except Exception as e:
        st.error(f"Failed to load draft: {e}")
        return

    st.session_state.analysis_result = {
        "analysis": analysis_obj,
        "transcript": draft.snapshot.get("transcript", ""),
        "logs": f"Loaded from draft {draft_id[:8]}…",
    }
    st.session_state.current_generation_id = generation_id
    st.session_state.pop("_preview_draft_id", None)
    st.rerun()


@st.dialog("Confirm Deletion")
def _render_delete_confirmation(draft_service, draft_id):
    """Show a confirmation dialog before deleting a draft."""
    st.warning("Are you sure you want to permanently delete this draft?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", type="primary", width="stretch"):
            draft_service.delete_draft(draft_id)
            # Clear preview if the deleted draft was being previewed
            if st.session_state.get("_preview_draft_id") == draft_id:
                st.session_state.pop("_preview_draft_id", None)
            st.session_state.pop("_confirm_delete_draft_id", None)
            st.rerun()
    with col2:
        if st.button("Cancel", width="stretch"):
            st.session_state.pop("_confirm_delete_draft_id", None)
            st.rerun()


_CLAUDE_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5",
]

_GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def _apply_cli_toggle():
    """Persist the CLI flag the moment the checkbox flips, and invalidate caches.

    Writes to st.session_state.llm_config + disk so the next script run (triggered
    automatically by the checkbox change) rebuilds _inference_port via the new
    `use_claude_code_cli` value.
    """
    new_value = bool(st.session_state.get("cfg_use_cli_checkbox", False))
    cfg = dict(st.session_state.get("llm_config", {}))
    cfg["use_claude_code_cli"] = new_value
    st.session_state["llm_config"] = cfg

    from ui.utils.storage import save_llm_config

    try:
        save_llm_config(cfg)
    except Exception:
        pass

    # Drop the cached inference/chat ports so setup_app rebuilds with the new flag.
    try:
        from ddd_studio.ui.streamlit_app import _get_chat_agent_port, _get_inference_port

        _get_inference_port.clear()
        _get_chat_agent_port.clear()
    except Exception:
        pass
    st.session_state.pop("_inference_port", None)
    st.session_state.pop("_chat_agent_port", None)


def _render_ai_config():
    """Render the AI engine configuration in the sidebar."""
    config = InferenceProvider.get_config()
    active_cli = bool(config.get("use_claude_code_cli"))
    model_name = config.get("model_name", "?")
    if active_cli:
        st.success(f"🖥️ Análisis: **Claude Code CLI** · modelo `{model_name}`")
    else:
        st.caption(f"💠 Análisis: API · modelo `{model_name}`")

    with st.expander("⚙️ Configuración IA", expanded=False):
        st.info("Configura el motor de IA para esta sesión.")

        use_cli = st.checkbox(
            "🖥️ Análisis vía Claude Code CLI (suscripción)",
            value=bool(config.get("use_claude_code_cli", False)),
            key="cfg_use_cli_checkbox",
            on_change=_apply_cli_toggle,
            help=(
                "Cuando está activo, la extracción del `DomainAnalysis` (JSON) usa "
                "`claude -p --output-format json` y consume tu cuenta de suscripción "
                "en lugar de la API metered. El chat agéntico sigue por API para "
                "preservar tool-calls. Requiere `claude` en el PATH y `claude login`. "
                "Se aplica automáticamente (no necesita Guardar)."
            ),
        )

        available_models = _CLAUDE_MODELS + _GEMINI_MODELS
        current_model = config.get("model_name", "claude-sonnet-4-6")
        default_index = available_models.index(current_model) if current_model in available_models else 0
        model_name = st.selectbox(
            "Modelo LLM",
            options=available_models,
            index=default_index,
            help="Claude (Anthropic) o Gemini (Google). El provider se infiere del prefijo del modelo.",
        )

        is_claude = model_name.lower().startswith("claude")
        api_key_label = "Anthropic API Key" if is_claude else "Google API Key"
        if use_cli:
            api_key_help = (
                "Requerida para el chat agéntico (mantiene tool-calls). "
                "El análisis JSON usa la suscripción del CLI y no consume esta key."
            )
        else:
            api_key_help = (
                "Tu clave de API de console.anthropic.com" if is_claude else "Tu clave de API de Google AI Studio"
            )
        api_key = st.text_input(
            api_key_label,
            value=config.get("api_key", ""),
            type="password",
            help=api_key_help,
        )
        if use_cli:
            st.caption("🖥️ Análisis → CLI suscripción · 💬 Chat → API (usa esta key)")

        if st.button("💾 Guardar Configuración", width="stretch"):
            cfg = {
                "model_name": model_name,
                "api_key": api_key,
                "use_claude_code_cli": use_cli,
            }
            st.session_state.llm_config = cfg
            from ui.utils.storage import save_llm_config

            save_llm_config(cfg)
            st.success("Configuración guardada y persistida.")

        if st.button("🔌 Probar Conexión", width="stretch"):
            if use_cli:
                _test_claude_cli_connection(model_name)
                if not api_key:
                    st.warning("⚠️ El chat agéntico necesita una API Key para funcionar.")
                else:
                    _test_api_key_connection(model_name, api_key)
            elif not api_key:
                st.error("Por favor, ingresa una API Key.")
            else:
                _test_api_key_connection(model_name, api_key)


def _test_api_key_connection(model_name: str, api_key: str) -> None:
    """Validate the API key by issuing a small smoke prompt via the API adapter."""
    is_claude = model_name.lower().startswith("claude")
    try:
        with st.spinner("Validando API Key..."):
            if is_claude:
                from infra.adapters.claude_inference import ClaudeInferenceAdapter

                adapter = ClaudeInferenceAdapter(model=model_name, api_key=api_key)
            else:
                from infra.adapters.gemini_inference import GeminiInferenceAdapter

                adapter = GeminiInferenceAdapter(model=model_name, api_key=api_key)
            result = adapter.invoke_text("Dí 'Conexión Exitosa' en 2 palabras.")
            st.success(f"API Key OK — {result.strip()}")
    except Exception as e:
        st.error(f"Error con API Key: {e}")


def _test_claude_cli_connection(model_name: str) -> None:
    """Validate that the `claude` CLI is on PATH and a smoke prompt succeeds."""
    import shutil

    from infra.adapters.claude_code_cli_inference import (
        CLAUDE_CLI_BINARY,
        ClaudeCodeCliInferenceAdapter,
    )

    if shutil.which(CLAUDE_CLI_BINARY) is None:
        st.error(f"No se encontró `{CLAUDE_CLI_BINARY}` en el PATH. Instala Claude Code y ejecuta `claude login`.")
        return
    try:
        with st.spinner("Validando CLI..."):
            adapter = ClaudeCodeCliInferenceAdapter(model=model_name, timeout_seconds=60)
            result = adapter.invoke_text("Responde EXACTAMENTE: Conexión CLI Exitosa")
            st.success(f"¡Listo! {result.strip()}")
    except Exception as e:
        st.error(f"Error usando Claude Code CLI: {e}")
