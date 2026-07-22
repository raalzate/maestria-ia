import logging
import warnings

import streamlit as st

from ddd_studio.models.domain_analysis import DomainAnalysis
from ddd_studio.ui.components.input import render_input_tabs
from ddd_studio.ui.components.results import render_results_tabs
from ddd_studio.ui.components.sidebar import render_sidebar
from ddd_studio.ui.utils.storage import STATIC_JSON_PATH, load_static_json

# --- Configuración ---
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Silence Streamlit's "missing ScriptRunContext" warnings emitted by the
# LangGraph worker threads running the parallel extraction DAG. These are
# benign — we handle them explicitly via try/except in on_event.
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)


@st.cache_resource(show_spinner="Conectando con el proveedor de IA…")
def _get_inference_port(config_hash: int):
    """Retrieve the inference port, cached by configuration hash."""
    from ddd_studio.infra.inference_provider import InferenceProvider

    return InferenceProvider.get_inference_port()


@st.cache_resource(
    show_spinner="Preparando el motor de transcripción (la primera vez descarga el modelo, puede tardar unos minutos)…"
)
def _build_transcription_adapter():
    """Construct the FasterWhisperTranscriptionAdapter once."""
    from ddd_studio.config.settings import TRANSCRIPTION_MAX_BYTES, WHISPER_MODEL
    from ddd_studio.infra.adapters.faster_whisper_transcription import (
        FasterWhisperTranscriptionAdapter,
    )

    return FasterWhisperTranscriptionAdapter(
        model_name=WHISPER_MODEL or "small",
        max_bytes=TRANSCRIPTION_MAX_BYTES,
    )


@st.cache_resource(show_spinner=False)
def _build_cache_adapter():
    """Construct the FileCacheAdapter once."""
    from ddd_studio.infra.adapters.file_cache import FileCacheAdapter

    return FileCacheAdapter()


@st.cache_resource(show_spinner="Inicializando el asistente de IA…")
def _get_chat_agent_port(config_hash: int):
    """Retrieve the chat agent port, cached by configuration hash."""
    from ddd_studio.infra.inference_provider import InferenceProvider

    return InferenceProvider.get_chat_agent_port()


def setup_app():
    """Configura la página y carga el estado inicial."""
    st.set_page_config(
        layout="wide",
        page_title="Domain Modeler AI",
        page_icon="🧠",
        initial_sidebar_state="expanded",
    )

    # Construct and store infrastructure adapters in session state
    from ddd_studio.infra.inference_provider import InferenceProvider

    config = InferenceProvider.get_config()
    config_hash = hash(frozenset(config.items()))

    # Always get the port (it will be cached based on settings)
    st.session_state["_inference_port"] = _get_inference_port(config_hash)
    st.session_state["_chat_agent_port"] = _get_chat_agent_port(config_hash)

    if "_cache_port" not in st.session_state:
        st.session_state["_cache_port"] = _build_cache_adapter()
    # The transcription adapter downloads the Whisper model on first run, which
    # can take minutes. Build it lazily on the first audio upload (see
    # components/input.process_input) instead of blocking app startup here.

    # Carga de estado
    if "analysis_result" not in st.session_state:
        loaded = load_static_json()
        if loaded:
            try:
                analysis_obj = DomainAnalysis.model_validate(loaded)
                st.session_state.analysis_result = {
                    "analysis": analysis_obj,
                    "transcript": loaded.get("transcript", ""),
                    "logs": f"Cargado desde {STATIC_JSON_PATH}",
                }
                st.info("📂 Análisis previo cargado automáticamente.")
            except Exception as e:
                st.session_state.analysis_result = {"error": f"Error cargando JSON: {e}"}
        else:
            st.session_state.analysis_result = None
        st.session_state.logs = ""


def run_streamlit_app():
    setup_app()
    render_sidebar()

    # Header Principal
    st.title("Análisis de Dominio Aumentado")

    render_input_tabs()

    if st.session_state.analysis_result:
        render_results_tabs(st.session_state.analysis_result)


if __name__ == "__main__":
    run_streamlit_app()
