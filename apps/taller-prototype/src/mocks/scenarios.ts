import type { Scenario } from "../types";

export const SCENARIOS: Scenario[] = [
  {
    id: "success",
    label: "Éxito",
    description:
      "Cancelación efectiva. ToolResult HTTP 200 + stop_reason=end_turn. La UI puede afirmar terminación con evidencia.",
    expectedOutcome: "ok",
  },
  {
    id: "timeout_503",
    label: "Timeout 503",
    description:
      "Camino triste. Core bancario timeout (HTTP 503). El LLM intenta disculparse y declarar éxito en prosa: la UI lo censura y muestra fallo real.",
    expectedOutcome: "err",
  },
  {
    id: "max_tokens",
    label: "max_tokens",
    description:
      "Camino triste. El loop se corta por límite de tokens antes de invocar cancel_product. stop_reason=max_tokens → estado indeterminado, no éxito.",
    expectedOutcome: "warn",
  },
];
