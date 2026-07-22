// Simula la respuesta streaming del orquestador (Agentic Loop).
// Emite la misma secuencia de StreamEvents que produciría un backend real:
//   loop_start → step → text_delta → tool_use → tool_result → stop → loop_end
//
// El LLM, en el escenario de fallo, intenta cerrar con prosa engañosa
// ("He cancelado tu tarjeta exitosamente"). La UI verá esa prosa pero
// no la utilizará: el estado se decide por ToolResult + stop_reason.

import type { ScenarioId, StreamEvent, ToolUseBlock } from "../types";
import { callBankingCore } from "./bankingCore";

const TARGET_CARD = "TC-XX1234";
const ACCOUNT_ID = "ACC-9911";

export async function* runAgenticLoop(
  scenario: ScenarioId,
): AsyncGenerator<StreamEvent> {
  // -------- Iteración 1: lectura del estado de la cuenta --------
  yield { type: "loop_start", iteration: 1 };
  yield { type: "step", iteration: 1, label: "Analizando solicitud" };
  await sleep(400);

  yield {
    type: "step",
    iteration: 1,
    label: "Consultando estado de la cuenta",
  };
  await sleep(250);

  const statusUse: ToolUseBlock = {
    type: "tool_use",
    id: "tu_001",
    name: "account_status",
    input: { account_id: ACCOUNT_ID },
  };
  yield { type: "tool_use", iteration: 1, block: statusUse };
  const statusResult = await callBankingCore({
    name: "account_status",
    input: statusUse.input,
    scenario,
    toolUseId: statusUse.id,
  });
  yield { type: "tool_result", iteration: 1, block: statusResult };
  yield { type: "stop", iteration: 1, stop_reason: "tool_use" };

  // -------- Iteración 2: ejecutar la cancelación --------
  yield { type: "loop_start", iteration: 2 };
  yield {
    type: "step",
    iteration: 2,
    label: "Solicitando cancelación al core bancario",
  };
  await sleep(300);

  // Caso max_tokens: el LLM corta antes de invocar la tool.
  if (scenario === "max_tokens") {
    yield {
      type: "text_delta",
      iteration: 2,
      text: "Procediendo con la cancelación de la tarjeta TC-XX1234, voy a invocar",
    };
    await sleep(900);
    yield { type: "stop", iteration: 2, stop_reason: "max_tokens" };
    yield { type: "loop_end", final_stop_reason: "max_tokens" };
    return;
  }

  const cancelUse: ToolUseBlock = {
    type: "tool_use",
    id: "tu_002",
    name: "cancel_product",
    input: {
      account_id: ACCOUNT_ID,
      product_id: TARGET_CARD,
      product_type: "credit_card",
      regulatory: ["ley_1581_2012", "sfc_029"],
    },
  };
  yield { type: "tool_use", iteration: 2, block: cancelUse };
  const cancelResult = await callBankingCore({
    name: "cancel_product",
    input: cancelUse.input,
    scenario,
    toolUseId: cancelUse.id,
  });
  yield { type: "tool_result", iteration: 2, block: cancelResult };
  yield { type: "stop", iteration: 2, stop_reason: "tool_use" };

  // -------- Iteración 3: redacción final (potencialmente engañosa) --------
  yield { type: "loop_start", iteration: 3 };
  yield { type: "step", iteration: 3, label: "Generando resumen" };
  await sleep(350);

  // El LLM SIEMPRE redacta como si todo hubiera salido bien.
  // La UI debe censurar este texto si ToolResult fue error.
  const prosaEnganosa =
    "He cancelado tu tarjeta de crédito TC-XX1234 exitosamente. Quedó todo resuelto de mi lado.";
  for (const chunk of chunkText(prosaEnganosa, 14)) {
    yield { type: "text_delta", iteration: 3, text: chunk };
    await sleep(60);
  }
  yield { type: "stop", iteration: 3, stop_reason: "end_turn" };
  yield { type: "loop_end", final_stop_reason: "end_turn" };
}

function chunkText(text: string, size: number): string[] {
  const out: string[] = [];
  for (let i = 0; i < text.length; i += size) out.push(text.slice(i, i + size));
  return out;
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
