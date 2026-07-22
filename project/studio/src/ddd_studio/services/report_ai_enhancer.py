"""AI-generated executive summary + insights for the analysis PDF report.

Takes a DomainAnalysis and produces a structured enhancement that the PDF
builder weaves into the report. Routing (Claude Code CLI vs API) is handled
by `InferencePort` — the caller picks the right adapter, this module is
backend-agnostic.
"""

from __future__ import annotations

import logging

from domain.ports import InferencePort
from models.domain_analysis import DomainAnalysis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiagramExplanation(BaseModel):
    """AI-generated narrative for one diagram in the report."""

    diagram_name: str = Field(
        ...,
        description=(
            "Exact diagram title as it appears in the report. MUST match one of the titles "
            "listed in the prompt verbatim."
        ),
    )
    explanation: str = Field(
        ...,
        description=(
            "3-5 sentences in Spanish describing what the diagram shows, the key elements "
            "to notice, and the business meaning. No generic boilerplate."
        ),
    )


class ReportAIEnhancement(BaseModel):
    """Structured AI synthesis injected into the PDF report."""

    executive_summary: str = Field(
        ..., description="2-3 paragraphs in Spanish summarising the business domain and main flow."
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="5-8 short bullet points capturing the most important model observations.",
    )
    risk_areas: list[str] = Field(
        default_factory=list,
        description="Risks and hotspots: integrations, unclear rules, manual workarounds, technical debt.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Concrete next steps the team should take (architecture, validations, missing context).",
    )
    diagram_explanations: list[DiagramExplanation] = Field(
        default_factory=list,
        description="One entry per diagram listed in the prompt, explaining what it shows.",
    )

    def explanation_for(self, diagram_name: str) -> str | None:
        """Return the AI-written explanation for a given diagram title, if available."""
        for e in self.diagram_explanations:
            if e.diagram_name.strip().lower() == diagram_name.strip().lower():
                return e.explanation
        return None


_SYSTEM = (
    "You are a Senior Domain-Driven Design analyst. Given the JSON of an Event Storming "
    "analysis, produce an executive synthesis in SPANISH for stakeholders who will read "
    "this as the opening pages of a PDF report. "
    "Be specific to THIS model — quote actor names, aggregate names, hotspot names, and "
    "integration points. Never invent details that are not present in the JSON. "
    "Tone: professional, concise, actionable. "
    "VOCABULARY (use business-friendly Spanish in the narrative, NOT technical DDD jargon): "
    "say 'acción' instead of 'comando', and say 'consecuencia' instead of 'evento'. "
    "Both for singular and plural. Treat 'agregado', 'política', 'regla de negocio', "
    "'actor', 'sistema externo', 'read model' as already business-friendly enough — keep "
    "them as they are. "
    "OUTPUT CONSTRAINT: use only standard ASCII characters in narrative text. "
    "Use '->' instead of arrows (→ ⇒ ⟶). Use plain hyphens '-' instead of em-dashes (— –). "
    "Do not use bullets, smart quotes, or other Unicode punctuation; the renderer's font "
    "lacks those glyphs and they will display as '?' in the final PDF."
)


def list_diagram_titles(analysis: DomainAnalysis) -> list[str]:
    """Return the exact titles of every diagram the PDF builder will include.

    The AI must explain each by name; titles MUST match what `report_pdf.py`
    uses, otherwise lookup fails.
    """
    titles: list[str] = [
        "Event Storming - Mapa Completo",
        "Big Picture",
        "Process Level - Todos los Agregados",
    ]
    for agg in analysis.agregados:
        titles.append(f"Process Level - {agg.nombre_agregado}")
    if analysis.read_models:
        titles.append("Modelos de Lectura")
    if analysis.ddd_specs:
        if analysis.ddd_specs.get("context_map"):
            titles.append("Context Map (Diseño Estratégico)")
        if analysis.ddd_specs.get("domain_models"):
            titles.append("Modelo de Dominio (Diseño Táctico)")
    return titles


def generate_enhancement(analysis: DomainAnalysis, inference: InferencePort) -> ReportAIEnhancement:
    """Call the InferencePort to produce a structured AI enhancement."""
    snapshot = analysis.model_dump_json(indent=2)
    diagrams = list_diagram_titles(analysis)
    diagrams_block = "\n".join(f"  - {t}" for t in diagrams)
    prompt = (
        f"{_SYSTEM}\n\n"
        "INSTRUCTIONS:\n"
        "- executive_summary: 2-3 paragraphs (max ~180 words) describing the domain, the main\n"
        "  end-to-end flow, and what differentiates the model (legacy vs new core, hotspots).\n"
        "- key_insights: 5-8 bullets, each ≤140 characters. Mention concrete elements.\n"
        "- risk_areas: 3-6 bullets — focus on Hotspots, External Systems, ambiguous policies.\n"
        "- recommendations: 3-6 bullets — actionable next steps (validations, missing read models,\n"
        "  decoupling integrations, etc.). Each ≤180 characters.\n"
        "- diagram_explanations: ONE entry per diagram listed below. Use the diagram_name\n"
        "  VERBATIM (exact spelling, punctuation, accents). Each explanation: 3-5 sentences\n"
        "  describing what it shows, the most relevant elements (named explicitly), and what\n"
        "  the reader should learn from it. Speak about THIS model, not generic Event Storming.\n\n"
        "DIAGRAMS IN THE REPORT (use these exact names):\n"
        f"{diagrams_block}\n\n"
        "Return ONLY the JSON object matching the schema. No preamble.\n\n"
        f"DOMAIN ANALYSIS JSON:\n{snapshot}"
    )
    return inference.invoke(prompt, ReportAIEnhancement)
