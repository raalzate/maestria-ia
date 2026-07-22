import json

import streamlit as st
from models.domain_analysis import DomainAnalysis
from ui.analyze import analyze_domain_data
from ui.components.chat import render_chat_tab
from ui.components.specs import render_specs_tab
from ui.reconstruct_utils import reconstruct_domain_analysis
from ui.utils.storage import save_static_json
from ui.visualization.graph import render_graph_tab
from ui.visualization.stats import render_stats_tab


def _render_downloads_section(analysis_obj: DomainAnalysis, data: dict):
    """Render the consolidated downloads block at the bottom of the results page."""
    from services.report_pdf import build_analysis_pdf

    cached_key = "_pdf_report_bytes"
    cached_for = "_pdf_report_for"
    cached_ai_key = "_pdf_report_ai_bytes"
    cached_ai_payload = "_pdf_report_ai_payload"
    cached_html_key = "_html_report_bytes"
    cached_html_for = "_html_report_for"
    cached_html_ai_key = "_html_report_ai_bytes"
    cached_html_ai_for = "_html_report_ai_for"
    project_key = (analysis_obj.nombre_proyecto, analysis_obj.version, analysis_obj.fecha_analisis)
    slug = "".join(c if c.isalnum() else "_" for c in analysis_obj.nombre_proyecto).strip("_") or "reporte"

    st.divider()
    st.markdown("### ⬇️ 4. Descargas")
    st.caption("Genera y descarga el reporte ejecutivo y los artefactos derivados del análisis.")

    # ── Subsección: Reporte PDF ──────────────────────────────────────
    st.markdown("**Reporte PDF**")
    cols = st.columns(4)
    with cols[0]:
        if st.button("📄 Generar Reporte PDF", width="stretch", key="btn_build_report_pdf"):
            with st.spinner("Construyendo PDF (incluye renderizado de diagramas)..."):
                try:
                    st.session_state[cached_key] = build_analysis_pdf(analysis_obj)
                    st.session_state[cached_for] = project_key
                    st.session_state.pop(cached_ai_key, None)
                    st.session_state.pop(cached_ai_payload, None)
                except Exception as e:
                    st.error(f"No se pudo generar el PDF: {e}")
                    st.session_state.pop(cached_key, None)

    pdf_bytes = st.session_state.get(cached_key)
    base_ready = bool(pdf_bytes) and st.session_state.get(cached_for) == project_key

    with cols[1]:
        if base_ready:
            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"{slug}-reporte.pdf",
                mime="application/pdf",
                width="stretch",
                key="dl_report_pdf",
            )
        else:
            st.button("⬇️ Descargar PDF", width="stretch", disabled=True, key="dl_report_pdf_off")
    with cols[2]:
        if st.button(
            "🤖 Mejorar con IA",
            width="stretch",
            key="btn_enhance_report_pdf",
            disabled=not base_ready,
            help="Genera síntesis ejecutiva, insights y explicaciones por diagrama con IA.",
        ):
            _generate_ai_enhanced_pdf(analysis_obj, cached_ai_key, cached_ai_payload, project_key)

    ai_bytes = st.session_state.get(cached_ai_key)
    ai_ready = bool(ai_bytes) and st.session_state.get(cached_ai_payload, {}).get("project_key") == project_key
    with cols[3]:
        if ai_ready:
            st.download_button(
                "⬇️ Descargar PDF + IA",
                data=ai_bytes,
                file_name=f"{slug}-reporte-ia.pdf",
                mime="application/pdf",
                width="stretch",
                key="dl_report_pdf_ai",
            )
        else:
            st.button("⬇️ Descargar PDF + IA", width="stretch", disabled=True, key="dl_report_pdf_ai_off")

    # ── Subsección: Reporte HTML interactivo ─────────────────────────
    st.markdown("**Reporte HTML interactivo** — single-file, vector, CDN-friendly")
    cols = st.columns(4)
    with cols[0]:
        if st.button("📊 Generar HTML", width="stretch", key="btn_build_html_report"):
            from services.report_html import build_analysis_html

            with st.spinner("Construyendo HTML (diagramas vector SVG inline)..."):
                try:
                    st.session_state[cached_html_key] = build_analysis_html(analysis_obj)
                    st.session_state[cached_html_for] = project_key
                    st.session_state.pop(cached_html_ai_key, None)
                    st.session_state.pop(cached_html_ai_for, None)
                except Exception as e:
                    st.error(f"No se pudo generar el HTML: {e}")
                    st.session_state.pop(cached_html_key, None)

    html_bytes = st.session_state.get(cached_html_key)
    html_ready = bool(html_bytes) and st.session_state.get(cached_html_for) == project_key

    with cols[1]:
        if html_ready:
            st.download_button(
                "⬇️ Descargar HTML",
                data=html_bytes,
                file_name=f"{slug}-reporte.html",
                mime="text/html",
                width="stretch",
                key="dl_report_html",
            )
        else:
            st.button("⬇️ Descargar HTML", width="stretch", disabled=True, key="dl_report_html_off")

    enhancement_cached = ai_ready  # the PDF flow already produced an enhancement
    with cols[2]:
        if st.button(
            "🤖 HTML + IA",
            width="stretch",
            key="btn_build_html_with_ai",
            disabled=not html_ready,
            help=("Reutiliza la síntesis IA del flow PDF si existe; de lo contrario la genera ahora."),
        ):
            _generate_ai_enhanced_html(
                analysis_obj,
                cached_html_ai_key,
                cached_html_ai_for,
                project_key,
                pdf_ai_cache_key=cached_ai_key,
                pdf_ai_payload_key=cached_ai_payload,
                pdf_ai_ready=enhancement_cached,
            )

    html_ai_bytes = st.session_state.get(cached_html_ai_key)
    html_ai_ready = bool(html_ai_bytes) and st.session_state.get(cached_html_ai_for) == project_key
    with cols[3]:
        if html_ai_ready:
            st.download_button(
                "⬇️ Descargar HTML + IA",
                data=html_ai_bytes,
                file_name=f"{slug}-reporte-ia.html",
                mime="text/html",
                width="stretch",
                key="dl_report_html_ai",
            )
        else:
            st.button("⬇️ Descargar HTML + IA", width="stretch", disabled=True, key="dl_report_html_ai_off")

    # ── Subsección: Datos y Diagramas ────────────────────────────────
    st.markdown("**Datos y Diagramas**")
    specs = analysis_obj.ddd_specs or {}
    context_map = specs.get("context_map")
    domain_models = specs.get("domain_models")

    cols = st.columns(3)
    with cols[0]:
        st.download_button(
            "⬇️ JSON del análisis",
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name=f"{slug}-analysis.json",
            mime="application/json",
            width="stretch",
            key="dl_analysis_json",
        )
    with cols[1]:
        if context_map:
            st.download_button(
                "⬇️ Context Map (.puml)",
                data=context_map,
                file_name=f"{slug}-context_map.puml",
                mime="text/plain",
                width="stretch",
                key="dl_context_map_puml",
            )
        else:
            st.button(
                "⬇️ Context Map (.puml)",
                width="stretch",
                disabled=True,
                key="dl_context_map_puml_off",
                help="Genera el Context Map desde la pestaña DDD primero.",
            )
    with cols[2]:
        if domain_models:
            st.download_button(
                "⬇️ Modelo Táctico (.puml)",
                data=domain_models,
                file_name=f"{slug}-tactical_domain_model.puml",
                mime="text/plain",
                width="stretch",
                key="dl_domain_model_puml",
            )
        else:
            st.button(
                "⬇️ Modelo Táctico (.puml)",
                width="stretch",
                disabled=True,
                key="dl_domain_model_puml_off",
                help="Genera el Modelo Táctico desde la pestaña DDD primero.",
            )


def _generate_ai_enhanced_html(
    analysis_obj: DomainAnalysis,
    cached_html_ai_key: str,
    cached_html_ai_for: str,
    project_key,
    *,
    pdf_ai_cache_key: str,
    pdf_ai_payload_key: str,
    pdf_ai_ready: bool,
) -> None:
    """Build the HTML report using an existing AI enhancement when possible.

    If the user already produced the PDF+IA, we reuse the cached enhancement.
    Otherwise we generate one on the fly via the active InferencePort.
    """
    from infra.inference_provider import InferenceProvider
    from services.report_ai_enhancer import generate_enhancement
    from services.report_html import build_analysis_html

    enhancement = st.session_state.get("_pdf_ai_enhancement_obj")
    if enhancement is None or not pdf_ai_ready:
        inference = InferenceProvider.get_inference_port()
        backend = type(inference).__name__
        with st.spinner(f"Generando síntesis con IA via {backend}..."):
            try:
                enhancement = generate_enhancement(analysis_obj, inference)
                st.session_state["_pdf_ai_enhancement_obj"] = enhancement
            except Exception as e:
                st.error(f"La IA no pudo generar la síntesis: {e}")
                return
    with st.spinner("Reconstruyendo HTML con la síntesis..."):
        try:
            st.session_state[cached_html_ai_key] = build_analysis_html(analysis_obj, ai_enhancement=enhancement)
            st.session_state[cached_html_ai_for] = project_key
            st.success("HTML + IA listo para descargar.")
        except Exception as e:
            st.error(f"No se pudo reconstruir el HTML: {e}")
            st.session_state.pop(cached_html_ai_key, None)


def _generate_ai_enhanced_pdf(
    analysis_obj: DomainAnalysis, cached_ai_key: str, cached_ai_payload: str, project_key
) -> None:
    """Run the AI enhancer using the currently configured InferencePort and rebuild the PDF."""
    from infra.inference_provider import InferenceProvider
    from services.report_ai_enhancer import generate_enhancement
    from services.report_pdf import build_analysis_pdf

    inference = InferenceProvider.get_inference_port()
    backend = type(inference).__name__
    with st.spinner(f"Generando síntesis con IA via {backend}..."):
        try:
            enhancement = generate_enhancement(analysis_obj, inference)
            st.session_state["_pdf_ai_enhancement_obj"] = enhancement
        except Exception as e:
            st.error(f"La IA no pudo generar la síntesis: {e}")
            return
    with st.spinner("Reconstruyendo el PDF con la síntesis..."):
        try:
            st.session_state[cached_ai_key] = build_analysis_pdf(analysis_obj, ai_enhancement=enhancement)
            st.session_state[cached_ai_payload] = {
                "project_key": project_key,
                "backend": backend,
            }
            st.success(f"PDF mejorado generado vía {backend}. Descárgalo abajo.")
        except Exception as e:
            st.error(f"No se pudo reconstruir el PDF: {e}")
            st.session_state.pop(cached_ai_key, None)
            st.session_state.pop(cached_ai_payload, None)


def _render_summary_metrics(analysis_obj: DomainAnalysis):
    """UX: Muestra métricas clave antes de las tablas detalladas."""
    bp = analysis_obj.big_picture
    # Módulos = cantidad de subdominos GrafoPorAgregado (≠ nodos de tipo "Agregado")
    total_modules = len(analysis_obj.agregados)
    total_rms = len(analysis_obj.read_models)
    # Políticas = aristas inter-agregado (politicas_inter_agregados), no nodos
    total_policies = len(analysis_obj.politicas_inter_agregados)

    st.markdown("### 📊 3. Resumen del Modelo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Módulos de Dominio", total_modules, help="Subdominos modelados a nivel de proceso (GrafoPorAgregado)")
    c2.metric("Read Models", total_rms, help="Vistas o reportes identificados")
    c3.metric("Nodos Big Picture", len(bp.nodos), help="Total de elementos en la vista global")
    c4.metric("Políticas Inter-Agregado", total_policies, help="Flujos de política que conectan distintos módulos")
    st.divider()


def _render_data_tab(analysis_obj: DomainAnalysis, data: dict):
    """Tab de Edición con mejor jerarquía visual."""
    dfs = analyze_domain_data(analysis_obj)

    st.info(
        "💡 **Tip:** Puedes editar las celdas directamente. Los cambios se guardarán al presionar el botón al final."
    )

    with st.expander("1. Big Picture (Contexto Global)", expanded=True):
        c1, c2 = st.columns(2)
        c1.markdown("#### 🔵 Nodos")
        edited_nodes_bp = c1.data_editor(dfs["nodes_bp_df"], key="edit_nodes_bp", num_rows="dynamic", width="stretch")
        c2.markdown("#### 🔗 Aristas")
        edited_edges_bp = c2.data_editor(dfs["edges_bp_df"], key="edit_edges_bp", num_rows="dynamic", width="stretch")

    with st.expander("2. Detalle por Agregados", expanded=False):
        c1, c2 = st.columns(2)
        c1.markdown("#### 📦 Nodos Internos")
        edited_nodes_agg = c1.data_editor(
            dfs["nodes_agg_df"], key="edit_nodes_agg", num_rows="dynamic", width="stretch"
        )
        c2.markdown("#### 🔗 Flujos Internos")
        edited_edges_agg = c2.data_editor(
            dfs["edges_agg_df"], key="edit_edges_agg", num_rows="dynamic", width="stretch"
        )

    with st.expander("3. Políticas y Read Models", expanded=False):
        st.markdown("#### 📜 Políticas de Negocio")
        edited_policies = st.data_editor(dfs["policies_df"], key="edit_policies", num_rows="dynamic", width="stretch")
        st.markdown("#### 👁️ Read Models (Vistas)")
        edited_rms = st.data_editor(dfs["read_models_df"], key="edit_rms", num_rows="dynamic", width="stretch")

    st.write("")
    if st.button("💾 Guardar y Aplicar Cambios", type="primary", width="content"):
        try:
            modified = reconstruct_domain_analysis(
                data,
                edited_nodes_bp,
                edited_edges_bp,
                edited_nodes_agg,
                edited_edges_agg,
                edited_policies,
                edited_rms,
            )
            validated = DomainAnalysis.model_validate(modified)
            st.session_state.analysis_result["analysis"] = validated

            # Persist the validated version (includes transcript)
            to_save = validated.model_dump()
            to_save["transcript"] = st.session_state.analysis_result.get("transcript", "")
            save_static_json(to_save)

            st.session_state.modified_json = json.dumps(to_save, indent=2, ensure_ascii=False)

            # Clear data_editor cached keys so they re-init from updated model
            for key in [
                "edit_nodes_bp",
                "edit_edges_bp",
                "edit_nodes_agg",
                "edit_edges_agg",
                "edit_policies",
                "edit_rms",
            ]:
                st.session_state.pop(key, None)

            st.toast("✅ Modelo actualizado correctamente", icon="💾")
            st.rerun()
        except Exception as e:
            st.error(f"Error al reconstruir datos: {e}")


def render_results_tabs(result: dict):
    """Muestra resultados con métricas iniciales y tabs ordenados."""
    if not isinstance(result, dict) or result.get("error") or "analysis" not in result:
        st.error(result.get("error", "Error interno."))
        return

    analysis_obj: DomainAnalysis = result["analysis"]
    data = analysis_obj.model_dump()
    data["transcript"] = result.get("transcript", "")

    st.divider()
    _render_summary_metrics(analysis_obj)

    t_chat, t_graph, t_data, t_stats, t_specs, t_raw = st.tabs(
        [
            "Chat IA",
            "🕸️ Visualización",
            "✏️ Datos y Edición",
            "📊 Estadísticas",
            "🚀 DDD",
            " Raw & Logs",
        ]
    )

    with t_chat:
        render_chat_tab(analysis_obj)
    with t_graph:
        render_graph_tab(analysis_obj)
    with t_data:
        _render_data_tab(analysis_obj, data)
    with t_stats:
        render_stats_tab(analysis_obj)
    with t_specs:
        render_specs_tab(analysis_obj, result.get("specs"))
    with t_raw:
        c1, c2 = st.columns(2)
        with c1:
            st.write("JSON Generado")
            st.json(data, expanded=False)
        with c2:
            st.write("Logs del Proceso")
            st.code(st.session_state.logs, language="log")

    _render_downloads_section(analysis_obj, data)
