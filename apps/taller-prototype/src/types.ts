// Tipos canónicos del Agentic Loop UI.
// Replican el shape mínimo de la API de Claude (tool use + stop_reason)
// para que el prototipo hable el mismo lenguaje que el backend real.

export type StopReason = "end_turn" | "tool_use" | "max_tokens" | "error";

export type ToolName = "account_status" | "cancel_product";

export type ToolUseBlock = {
  type: "tool_use";
  id: string;
  name: ToolName;
  input: Record<string, unknown>;
};

export type ToolResultBlock = {
  type: "tool_result";
  tool_use_id: string;
  is_error: boolean;
  http_status: number;
  payload: Record<string, unknown> | { error: string };
};

export type TextBlock = { type: "text"; text: string };

export type ContentBlock = ToolUseBlock | ToolResultBlock | TextBlock;

// Eventos que el orquestador emite al frontend (stream).
export type StreamEvent =
  | { type: "loop_start"; iteration: number }
  | { type: "step"; iteration: number; label: string }
  | { type: "text_delta"; iteration: number; text: string }
  | { type: "tool_use"; iteration: number; block: ToolUseBlock }
  | { type: "tool_result"; iteration: number; block: ToolResultBlock }
  | { type: "stop"; iteration: number; stop_reason: StopReason }
  | { type: "loop_end"; final_stop_reason: StopReason };

export type ScenarioId = "success" | "timeout_503" | "max_tokens";

export type Scenario = {
  id: ScenarioId;
  label: string;
  description: string;
  expectedOutcome: "ok" | "warn" | "err";
};

// Persona-aware UX.
// La UI es la misma pero ajusta densidad / vocabulario.
export type PersonaId = "carlos" | "ana" | "elsa";

export type Persona = {
  id: PersonaId;
  name: string;
  role: string;
  age: number;
  density: "full" | "compact" | "plain";
  jargonAllowed: boolean;
  showEventLog: boolean;
  showRawJson: boolean;
  fontScale: number;
  rationale: string; // qué heurística IHC valida este modo
};

// Versión que ve el usuario:
//   prototype = Agentic Loop determinista (señales)
//   control   = chatbot probabilístico equivalente (anti-patrón)
export type ViewMode = "prototype" | "control";
