// Mock del core bancario. Cada tool retorna un payload estructurado +
// HTTP status para que la UI pueda decidir éxito/fallo de forma determinista.

import type { ScenarioId, ToolName, ToolResultBlock } from "../types";

type CoreCall = {
  name: ToolName;
  input: Record<string, unknown>;
  scenario: ScenarioId;
  toolUseId: string;
};

export async function callBankingCore({
  name,
  input,
  scenario,
  toolUseId,
}: CoreCall): Promise<ToolResultBlock> {
  await sleep(jitter(450, 250));

  if (name === "account_status") {
    // Lectura siempre OK (no modificada por escenarios).
    return {
      type: "tool_result",
      tool_use_id: toolUseId,
      is_error: false,
      http_status: 200,
      payload: {
        account_id: input.account_id ?? "ACC-9911",
        holder: "Carlos Auditor",
        products: [
          {
            id: "TC-XX1234",
            type: "credit_card",
            status: "ACTIVE",
            balance_cop: 2_350_000,
          },
        ],
      },
    };
  }

  if (name === "cancel_product") {
    if (scenario === "timeout_503") {
      await sleep(1200);
      return {
        type: "tool_result",
        tool_use_id: toolUseId,
        is_error: true,
        http_status: 503,
        payload: {
          error: "core_bancario_timeout",
          message: "Upstream core bancario no respondió en 1200ms.",
        },
      };
    }

    if (scenario === "max_tokens") {
      // Aquí el core sí responde, pero el orquestador cortará por max_tokens
      // antes de que el ToolResult sea consumido en el flujo final.
      return {
        type: "tool_result",
        tool_use_id: toolUseId,
        is_error: false,
        http_status: 200,
        payload: {
          ticket_id: "CCL-2026-0073",
          product_id: input.product_id ?? "TC-XX1234",
          state: "PENDING_VERIFICATION",
          notice: "Email Habeas Data en cola.",
        },
      };
    }

    // success
    return {
      type: "tool_result",
      tool_use_id: toolUseId,
      is_error: false,
      http_status: 200,
      payload: {
        ticket_id: "CCL-2026-0073",
        product_id: input.product_id ?? "TC-XX1234",
        state: "CANCELLED",
        cancelled_at: new Date().toISOString(),
        regulatory_notice: {
          ley_1581_2012: "consentimiento registrado",
          sfc_circular_029: "log de operación generado",
        },
      },
    };
  }

  throw new Error(`Tool desconocida: ${name}`);
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function jitter(base: number, variance: number) {
  return base + Math.random() * variance;
}
