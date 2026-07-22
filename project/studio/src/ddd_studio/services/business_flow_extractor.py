"""Extract a business flow narrative from heterogeneous source documents.

Use case: the user uploads multiple PDFs/MD files that describe their business
but include unrelated noise (HR policies, marketing copy, irrelevant sections).
We delegate to the InferencePort to filter out the noise and emit a clean
narrative ready for `analyze_semantics`.

Routing (Claude Code CLI vs API) is the caller's responsibility — pick the
right adapter via `InferenceProvider.get_inference_port()` so the same
subscription/API flag governs this flow too.
"""

from __future__ import annotations

import logging

from domain.ports import InferencePort
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BusinessFlowExtraction(BaseModel):
    """AI-extracted business flow ready to be fed into the Event Storming pipeline."""

    flow_narrative: str = Field(
        ...,
        description=(
            "Coherent narrative in SPANISH describing the business flow, actors, commands, "
            "events, policies, aggregates, integrations, and read models the system handles. "
            "Must read like a workshop transcript suitable for Event Storming extraction."
        ),
    )
    detected_topics: list[str] = Field(
        default_factory=list,
        description="Topics found in the documents that ARE part of the business flow.",
    )
    excluded_topics: list[str] = Field(
        default_factory=list,
        description="Topics found in the documents that were excluded as noise (HR, marketing, off-topic).",
    )
    confidence: str = Field(
        "medium",
        description="Confidence in the extracted flow: 'high', 'medium' or 'low'.",
    )
    summary: str = Field(
        "",
        description="2-3 sentence summary of the extracted business flow.",
    )


_SYSTEM = (
    "You are a Senior Domain-Driven Design analyst. Multiple documents will be given to you. "
    "They MAY contain text about the target business process AND unrelated noise (HR policies, "
    "general company history, generic IT standards, marketing material, philosophical notes, "
    "page headers/footers, table of contents). "
    "Your job is to:\n"
    "1. Identify the SUBJECT BUSINESS FLOW these documents are about.\n"
    "2. AGGRESSIVELY EXCLUDE content unrelated to that flow.\n"
    "3. Produce a coherent SPANISH narrative — written as a workshop facilitator would describe "
    "the flow — that an Event Storming pipeline can consume to extract Actors, Commands, "
    "Domain Events, Policies, Aggregates, Read Models, External Systems and Hotspots.\n\n"
    "RULES:\n"
    "- The narrative MUST be derived strictly from the documents. Do NOT invent new entities, "
    "actors, events, integrations or rules that are not present in the source text.\n"
    "- Use the exact terminology found in the documents (lenguaje ubicuo).\n"
    "- Mention named integrations (REST APIs, legacy systems, third parties), business rules, "
    "and any pain points / contradictions explicitly described.\n"
    "- Preserve chronological order of the flow when the documents make it clear.\n"
    "- If the documents are too ambiguous to identify a flow, set confidence='low' and write "
    "the most coherent narrative you can with what is available.\n"
    "- Return ONLY the JSON object matching the schema. No preamble."
)


def extract_business_flow(
    documents: list[tuple[str, str]],
    inference: InferencePort,
    *,
    force_include: list[str] | None = None,
    force_exclude: list[str] | None = None,
    focus_directive: str | None = None,
) -> BusinessFlowExtraction:
    """Run the LLM extraction over a list of (filename, markdown_content) pairs.

    Optional overrides:
        force_include: topics the user marked as relevant (must appear in the narrative
            even if the model would have excluded them).
        force_exclude: topics the user marked as noise (drop from the narrative even
            if the model would have included them).
    """
    if not documents:
        raise ValueError("extract_business_flow requires at least one document.")

    blocks: list[str] = []
    for name, content in documents:
        cleaned = (content or "").strip()
        if not cleaned:
            continue
        blocks.append(f"=== DOCUMENTO: {name} ===\n{cleaned}")
    if not blocks:
        raise ValueError("All provided documents were empty.")

    corpus = "\n\n".join(blocks)
    overrides = _format_overrides(force_include, force_exclude)
    directive_block = _format_focus_directive(focus_directive)
    prompt = (
        f"{_SYSTEM}\n\n"
        f"{directive_block}"
        f"{overrides}"
        "DOCUMENT CORPUS (you must filter noise from these):\n"
        "==========================================================\n"
        f"{corpus}\n"
        "==========================================================\n\n"
        "Now produce the JSON. Remember: only include topics that belong to the business flow."
    )
    return inference.invoke(prompt, BusinessFlowExtraction)


def _format_focus_directive(directive: str | None) -> str:
    """Render the user-provided focus directive at the top of the prompt, with
    the strongest priority wording. The model MUST honour this as a rule.
    """
    text = (directive or "").strip()
    if not text:
        return ""
    return (
        "USER FOCUS DIRECTIVE (HIGHEST PRIORITY - this is a rule, not a hint):\n"
        f"  {text}\n"
        "Apply this directive as the primary lens for what counts as 'the\n"
        "business flow' BEFORE filtering noise. If a topic contradicts the\n"
        "directive, exclude it. If the directive narrows scope (e.g. 'focus\n"
        "only on block X'), drop everything outside that scope.\n\n"
    )


def _format_overrides(
    force_include: list[str] | None,
    force_exclude: list[str] | None,
) -> str:
    """Render the optional override block above the document corpus."""
    inc = [t.strip() for t in (force_include or []) if t and t.strip()]
    exc = [t.strip() for t in (force_exclude or []) if t and t.strip()]
    if not inc and not exc:
        return ""
    lines = [
        "USER-DRIVEN OVERRIDES (HIGHEST PRIORITY — they outrank your own filtering):",
    ]
    if inc:
        lines.append(
            "- FORCE INCLUDE these topics in flow_narrative and detected_topics, "
            "weaving them into the business narrative using the same wording the user provided. "
            "If a topic is unrelated to the flow but the user insists, integrate it as a side aspect:"
        )
        for t in inc:
            lines.append(f"  * {t}")
    if exc:
        lines.append(
            "- FORCE EXCLUDE these topics. Do NOT mention them in flow_narrative or "
            "detected_topics, even if you think they are relevant. Move them to excluded_topics:"
        )
        for t in exc:
            lines.append(f"  * {t}")
    lines.append("")
    return "\n".join(lines) + "\n"
