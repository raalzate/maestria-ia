"""Unit tests for the BusinessFlowExtractor service."""

from __future__ import annotations

import pytest
from services.business_flow_extractor import (
    BusinessFlowExtraction,
    extract_business_flow,
)


class _FakeInference:
    def __init__(self, payload: BusinessFlowExtraction) -> None:
        self.payload = payload
        self.calls: list[tuple[str, type]] = []

    def invoke(self, prompt, schema):
        self.calls.append((prompt, schema))
        return self.payload

    def invoke_text(self, prompt):  # pragma: no cover — unused
        return ""


_FIXTURE = BusinessFlowExtraction(
    flow_narrative="Apertura, asignación, dictamen, pago.",
    detected_topics=["Apertura de trámite", "Pago"],
    excluded_topics=["Política de RRHH"],
    confidence="high",
    summary="Flujo de vencimientos y siniestros.",
)


def test_extract_business_flow_sends_corpus_and_returns_model():
    fake = _FakeInference(_FIXTURE)
    docs = [
        ("manual.pdf", "Sección sobre trámite y pago."),
        ("rrhh.pdf", "Política de vacaciones — irrelevante."),
    ]

    result = extract_business_flow(docs, fake)

    assert isinstance(result, BusinessFlowExtraction)
    assert result.confidence == "high"
    assert result.detected_topics == ["Apertura de trámite", "Pago"]
    assert len(fake.calls) == 1
    prompt, schema = fake.calls[0]
    assert schema is BusinessFlowExtraction
    # Each document must be tagged with its filename so the model knows the source.
    assert "=== DOCUMENTO: manual.pdf ===" in prompt
    assert "=== DOCUMENTO: rrhh.pdf ===" in prompt
    assert "Política de vacaciones" in prompt
    # The system prompt must instruct the model to filter noise.
    assert "EXCLUDE content unrelated" in prompt


def test_extract_business_flow_skips_empty_documents():
    fake = _FakeInference(_FIXTURE)
    docs = [
        ("blanco.txt", "   "),
        ("manual.pdf", "Flujo real."),
    ]

    extract_business_flow(docs, fake)

    prompt, _ = fake.calls[0]
    assert "blanco.txt" not in prompt
    assert "manual.pdf" in prompt


def test_extract_business_flow_raises_when_all_documents_empty():
    fake = _FakeInference(_FIXTURE)
    with pytest.raises(ValueError, match="empty"):
        extract_business_flow([("a.txt", ""), ("b.txt", "  ")], fake)


def test_extract_business_flow_raises_when_no_documents_provided():
    fake = _FakeInference(_FIXTURE)
    with pytest.raises(ValueError, match="at least one document"):
        extract_business_flow([], fake)


def test_extract_business_flow_passes_user_overrides_to_prompt():
    fake = _FakeInference(_FIXTURE)
    docs = [("manual.pdf", "Flujo real con muchos detalles.")]

    extract_business_flow(
        docs,
        fake,
        force_include=["Política de retención de datos", "  "],  # blank entry ignored
        force_exclude=["Tipos de trámite"],
    )

    prompt, _ = fake.calls[0]
    assert "USER-DRIVEN OVERRIDES" in prompt
    assert "FORCE INCLUDE these topics" in prompt
    assert "Política de retención de datos" in prompt
    assert "FORCE EXCLUDE these topics" in prompt
    assert "Tipos de trámite" in prompt


def test_extract_business_flow_omits_override_block_when_lists_are_empty_or_blank():
    fake = _FakeInference(_FIXTURE)
    docs = [("manual.pdf", "x")]

    extract_business_flow(docs, fake, force_include=["", "   "], force_exclude=None)

    prompt, _ = fake.calls[0]
    assert "USER-DRIVEN OVERRIDES" not in prompt


def test_extract_business_flow_injects_focus_directive_with_priority_wording():
    fake = _FakeInference(_FIXTURE)
    docs = [("manual.pdf", "x")]

    extract_business_flow(
        docs,
        fake,
        focus_directive="Enfócate solo en el bloque de Liquidación",
    )

    prompt, _ = fake.calls[0]
    assert "USER FOCUS DIRECTIVE" in prompt
    assert "Enfócate solo en el bloque de Liquidación" in prompt
    assert "HIGHEST PRIORITY" in prompt


def test_extract_business_flow_omits_focus_directive_when_blank():
    fake = _FakeInference(_FIXTURE)
    docs = [("manual.pdf", "x")]
    extract_business_flow(docs, fake, focus_directive="   ")
    prompt, _ = fake.calls[0]
    assert "USER FOCUS DIRECTIVE" not in prompt
