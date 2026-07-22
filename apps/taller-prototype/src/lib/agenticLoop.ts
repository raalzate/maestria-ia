// Hook que consume el stream del orquestador y mantiene el estado de la UI.
// Es deliberadamente "tonto" sobre el texto del LLM: el estado final se
// computa SIEMPRE a partir de stop_reason + ToolResult, nunca de la prosa.

import { useCallback, useReducer, useRef } from "react";
import type {
  ContentBlock,
  ScenarioId,
  StopReason,
  StreamEvent,
  ToolResultBlock,
  ToolUseBlock,
} from "../types";
import { runAgenticLoop } from "../mocks/claudeStream";

export type StepState = {
  iteration: number;
  label: string;
  status: "active" | "done" | "error";
};

export type LogRow = {
  ts: string;
  kind: "info" | "tool" | "stop" | "error" | "text";
  msg: string;
};

export type FinalVerdict =
  | { kind: "idle" }
  | { kind: "running" }
  | { kind: "ok"; ticketId: string }
  | { kind: "warn"; reason: string } // truncado, sin completitud verificada
  | { kind: "err"; httpStatus: number; reason: string };

export type LoopState = {
  scenario: ScenarioId;
  steps: StepState[];
  toolUses: ToolUseBlock[];
  toolResults: Record<string, ToolResultBlock>;
  textFinal: string; // prosa final del LLM (puede ser engañosa)
  log: LogRow[];
  stopReason: StopReason | null;
  verdict: FinalVerdict;
};

const initialState = (scenario: ScenarioId): LoopState => ({
  scenario,
  steps: [],
  toolUses: [],
  toolResults: {},
  textFinal: "",
  log: [],
  stopReason: null,
  verdict: { kind: "idle" },
});

type Action =
  | { type: "RESET"; scenario: ScenarioId }
  | { type: "START" }
  | { type: "EVENT"; event: StreamEvent };

function timestamp(): string {
  const d = new Date();
  return d.toLocaleTimeString("es-CO", { hour12: false }) + "." +
    String(d.getMilliseconds()).padStart(3, "0").slice(0, 3);
}

function reducer(state: LoopState, action: Action): LoopState {
  switch (action.type) {
    case "RESET":
      return initialState(action.scenario);

    case "START":
      return { ...state, verdict: { kind: "running" } };

    case "EVENT": {
      const ev = action.event;
      const log = [...state.log];
      let steps = [...state.steps];
      let toolUses = state.toolUses;
      let toolResults = state.toolResults;
      let textFinal = state.textFinal;
      let stopReason = state.stopReason;
      let verdict = state.verdict;

      switch (ev.type) {
        case "loop_start":
          log.push({
            ts: timestamp(),
            kind: "info",
            msg: `loop_start iteration=${ev.iteration}`,
          });
          break;

        case "step":
          steps = markPriorStepsDone(steps);
          steps.push({
            iteration: ev.iteration,
            label: ev.label,
            status: "active",
          });
          log.push({
            ts: timestamp(),
            kind: "info",
            msg: `step "${ev.label}"`,
          });
          break;

        case "text_delta":
          textFinal = textFinal + ev.text;
          break;

        case "tool_use":
          toolUses = [...toolUses, ev.block];
          log.push({
            ts: timestamp(),
            kind: "tool",
            msg: `tool_use ${ev.block.name}(${JSON.stringify(ev.block.input)})`,
          });
          break;

        case "tool_result":
          toolResults = { ...toolResults, [ev.block.tool_use_id]: ev.block };
          log.push({
            ts: timestamp(),
            kind: ev.block.is_error ? "error" : "tool",
            msg: `tool_result http=${ev.block.http_status} is_error=${ev.block.is_error}`,
          });
          if (ev.block.is_error) {
            steps = markCurrentStepError(steps);
          }
          break;

        case "stop":
          stopReason = ev.stop_reason;
          log.push({
            ts: timestamp(),
            kind: "stop",
            msg: `stop_reason=${ev.stop_reason}`,
          });
          break;

        case "loop_end":
          steps = markPriorStepsDone(steps);
          stopReason = ev.final_stop_reason;
          verdict = decideVerdict(toolUses, toolResults, ev.final_stop_reason);
          log.push({
            ts: timestamp(),
            kind: "stop",
            msg: `loop_end final=${ev.final_stop_reason} verdict=${verdict.kind}`,
          });
          break;
      }

      return {
        ...state,
        steps,
        toolUses,
        toolResults,
        textFinal,
        stopReason,
        verdict,
        log,
      };
    }
  }
}

function markPriorStepsDone(steps: StepState[]): StepState[] {
  return steps.map((s) =>
    s.status === "active" ? { ...s, status: "done" } : s,
  );
}

function markCurrentStepError(steps: StepState[]): StepState[] {
  return steps.map((s, i, arr) =>
    i === arr.length - 1 && s.status === "active"
      ? { ...s, status: "error" }
      : s,
  );
}

// Decide el verdict final SOLO con señales técnicas — nunca con el texto.
function decideVerdict(
  toolUses: ToolUseBlock[],
  toolResults: Record<string, ToolResultBlock>,
  finalStopReason: StopReason,
): FinalVerdict {
  if (finalStopReason === "max_tokens") {
    return {
      kind: "warn",
      reason:
        "El loop se detuvo por max_tokens antes de completar la cancelación. Estado real desconocido — reintentar.",
    };
  }

  const cancelUse = toolUses.find((t) => t.name === "cancel_product");
  if (!cancelUse) {
    return {
      kind: "warn",
      reason: "Nunca se invocó cancel_product. Operación no realizada.",
    };
  }

  const cancelResult = toolResults[cancelUse.id];
  if (!cancelResult) {
    return {
      kind: "err",
      httpStatus: 0,
      reason: "Sin ToolResult para cancel_product. Estado indeterminado.",
    };
  }

  if (cancelResult.is_error) {
    const payload = cancelResult.payload as { message?: string; error?: string };
    return {
      kind: "err",
      httpStatus: cancelResult.http_status,
      reason:
        payload.message ?? payload.error ?? "Error en core bancario.",
    };
  }

  if (finalStopReason !== "end_turn") {
    return {
      kind: "warn",
      reason: `stop_reason=${finalStopReason} no es terminal verificado.`,
    };
  }

  const ticketId =
    (cancelResult.payload as { ticket_id?: string }).ticket_id ?? "—";
  return { kind: "ok", ticketId };
}

export function isProsaEnganosa(state: LoopState): boolean {
  // La prosa habla de "exitosamente" / "resuelto" pero la verdad técnica
  // dice lo contrario. Esa contradicción es la que se censura visualmente.
  if (!state.textFinal) return false;
  const claimsSuccess = /exitosamente|resuelto|completado|listo/i.test(
    state.textFinal,
  );
  const technicallyOk = state.verdict.kind === "ok";
  return claimsSuccess && !technicallyOk;
}

export function useAgenticLoop(initialScenario: ScenarioId) {
  const [state, dispatch] = useReducer(reducer, initialScenario, initialState);
  const cancelledRef = useRef(false);

  const start = useCallback((scenario: ScenarioId) => {
    cancelledRef.current = false;
    dispatch({ type: "RESET", scenario });
    dispatch({ type: "START" });
    void (async () => {
      for await (const ev of runAgenticLoop(scenario)) {
        if (cancelledRef.current) return;
        dispatch({ type: "EVENT", event: ev });
      }
    })();
  }, []);

  const cancel = useCallback(() => {
    cancelledRef.current = true;
  }, []);

  const blocksOrdered: ContentBlock[] = state.toolUses.flatMap((u) => {
    const result = state.toolResults[u.id];
    return result ? [u, result] : [u];
  });

  return { state, start, cancel, blocksOrdered };
}
