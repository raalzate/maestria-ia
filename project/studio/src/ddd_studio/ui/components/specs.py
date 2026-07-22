import streamlit as st
from models.domain_analysis import DomainAnalysis
from services.spec_generator import SpecGenerator
from ui.utils.puml import render_plantuml
from ui.utils.storage import save_static_json


def _clean_puml(raw: str) -> str:
    """Strip markdown fences so only PlantUML syntax remains."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # If LLM added prose before @startuml, skip to it
    if not text.startswith("@startuml") and "@startuml" in text:
        text = text[text.index("@startuml") :]
    return text.strip()


def render_specs_tab(analysis_obj: DomainAnalysis, specs: dict | None = None):
    """
    Renders the Domain-Driven Design tab with strategic and tactical models.
    """
    st.markdown("### 🛠️ Domain-Driven Design (DDD)")
    st.info("Genera mapas estratégicos (Context Map) y modelos tácticos (Diagramas de Clases) basados en tu análisis.")

    # Aseguramos que el objeto tenga el diccionario listo
    if analysis_obj.ddd_specs is None:
        analysis_obj.ddd_specs = {}

    # Use the dynamic inference port from session state
    inference = st.session_state.get("_inference_port")
    generator = SpecGenerator(analysis_obj, inference)

    tab1, tab2 = st.tabs(["🗺️ Context Map", "🏗️ Modelo de Dominio (Táctico)"])

    # === CONTEXT MAP ===
    with tab1:
        _render_spec_section(
            analysis_obj,
            key="context_map",
            heading="#### Strategic Design — Mapa Estratégico",
            caption="Subdominios (Core / Supporting / Generic), Bounded Contexts y sus relaciones de mapa de contexto.",
            generate_button_label="Generar Context Map",
            generator_fn=generator.generate_context_map,
            empty_msg="*No se ha generado el Context Map aún.*",
            editor_key="puml_editor_cmap",
            rerender_key="btn_rerender_cmap",
            generate_btn_key="btn_gen_cmap",
            preview_key="_pending_context_map",
            spinner="Generando diagrama de diseño estratégico con IA...",
        )

    # === DDD DOMAIN MODELS (Tactical) ===
    with tab2:
        _render_spec_section(
            analysis_obj,
            key="domain_models",
            heading="#### Tactical Design — Diagrama de Clases",
            caption="Entidades, Value Objects, Aggregates y su comportamiento interno.",
            generate_button_label="Generar Modelo de Dominio (Táctico)",
            generator_fn=generator.generate_domain_models,
            empty_msg="*No se ha generado el modelo de dominio táctico aún.*",
            editor_key="puml_editor_dmodel",
            rerender_key="btn_rerender_dmodel",
            generate_btn_key="btn_gen_ddd",
            preview_key="_pending_domain_models",
            spinner="Generando diagrama de dominio táctico con IA...",
        )


def _render_spec_section(
    analysis_obj: DomainAnalysis,
    *,
    key: str,
    heading: str,
    caption: str,
    generate_button_label: str,
    generator_fn,
    empty_msg: str,
    editor_key: str,
    rerender_key: str,
    generate_btn_key: str,
    preview_key: str,
    spinner: str,
) -> None:
    """Generate → preview → save flow for a DDD spec block.

    The generated PlantUML stays in `session_state[preview_key]` so the user
    can review it before committing. Saving writes to `analysis_obj.ddd_specs`
    and persists to disk; discarding drops the preview.
    """
    st.markdown(heading)
    st.caption(caption)

    saved_code = analysis_obj.ddd_specs.get(key)
    pending_code = st.session_state.get(preview_key)
    has_pending = bool(pending_code)
    code_to_show = pending_code if has_pending else saved_code

    if code_to_show:
        if has_pending:
            st.info("📝 Diagrama generado pero sin guardar. Revisa el preview y decide.")
        puml_code = _clean_puml(code_to_show)
        render_plantuml(puml_code, height=650)

        with st.expander("Ver / editar código PlantUML", expanded=False):
            edited = st.text_area(
                "Código PlantUML (puedes corregir errores de sintaxis aquí)",
                value=puml_code,
                height=300,
                key=editor_key,
            )
            if edited.strip() != puml_code.strip():
                if st.button("Re-renderizar con cambios", key=rerender_key):
                    # Treat the edit as a new pending preview.
                    st.session_state[preview_key] = edited
                    st.rerun()

        if has_pending:
            cols = st.columns([1, 1, 4])
            with cols[0]:
                if st.button("💾 Guardar", type="primary", key=f"btn_save_{key}", width="stretch"):
                    analysis_obj.ddd_specs[key] = pending_code
                    save_static_json(analysis_obj.model_dump())
                    st.session_state.pop(preview_key, None)
                    st.success("Guardado.")
                    st.rerun()
            with cols[1]:
                if st.button("🗑️ Descartar", key=f"btn_discard_{key}", width="stretch"):
                    st.session_state.pop(preview_key, None)
                    st.rerun()
        else:
            st.caption("Descarga el `.puml` desde el bloque ⬇️ Descargas al final de la página.")
    else:
        st.markdown(empty_msg)

    if st.button(generate_button_label, key=generate_btn_key):
        with st.spinner(spinner):
            result = generator_fn()
            st.session_state[preview_key] = result
            st.rerun()
