// Renderiza el LoopState como una conversación de banca digital.
// Las señales técnicas se traducen a burbujas progresivas.
// Carlos ve detalle técnico inline; Ana lo ve condensado; Elsa solo el resultado humano.

import { useEffect, useRef } from "react";
import type { Persona, ToolUseBlock, ToolResultBlock } from "../types";
import type { LoopState, StepState, FinalVerdict } from "../lib/agenticLoop";
import { isProsaEnganosa } from "../lib/agenticLoop";

type Props = {
  state: LoopState;
  persona: Persona;
  onRetry: () => void;
  onExport: () => void;
};

export function ChatView({ state, persona, onRetry, onExport }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [state.steps.length, state.toolUses.length, state.textFinal, state.verdict.kind]);

  if (state.verdict.kind === "idle") return <ChatEmpty persona={persona} />;

  const isPlain = persona.density === "plain";
  const showSteps = persona.density !== "plain";
  const enganosa = isProsaEnganosa(state);

  return (
    <div className="chat" ref={ref} role="log" aria-live="polite" aria-relevant="additions">
      <div className="day-marker">Hoy</div>

      <UserBubble persona={persona} />

      {/* Iteraciones — mostrar steps en orden (excepto plain) */}
      {showSteps && state.steps.map((s, i) => (
        <StepPill key={`step-${i}`} step={s} persona={persona} />
      ))}

      {/* Tool uses + results como burbujas del bot */}
      {!isPlain && state.toolUses.map((u) => (
        <ToolBubble
          key={u.id}
          use={u}
          result={state.toolResults[u.id]}
          persona={persona}
        />
      ))}

      {/* Prosa final / censura */}
      {!isPlain && state.textFinal && (
        <ProseBubble text={state.textFinal} censored={enganosa} persona={persona} />
      )}

      {/* Verdict final como card */}
      {state.verdict.kind !== "running" && (
        <VerdictCard
          verdict={state.verdict}
          persona={persona}
          onRetry={onRetry}
          onExport={onExport}
        />
      )}

      {state.verdict.kind === "running" && (
        <BotTyping persona={persona} />
      )}
    </div>
  );
}

function ChatEmpty({ persona }: { persona: Persona }) {
  return (
    <div className="chat">
      <div className="chat-empty">
        Aún no has iniciado una conversación con tu banco.
        <br />
        <span className="hint">
          Selecciona un escenario y presiona <b>Iniciar conversación</b>
          {persona.density !== "plain" && " para ver el flujo en tiempo real."}
        </span>
      </div>
    </div>
  );
}

function UserBubble({ persona }: { persona: Persona }) {
  return (
    <div className="bubble user">
      {persona.density === "plain"
        ? "Quiero cancelar mi tarjeta de crédito que termina en 1234."
        : "Cancela mi tarjeta de crédito TC-XX1234."}
      <span className="ts">{nowTime()}</span>
    </div>
  );
}

function StepPill({ step, persona }: { step: StepState; persona: Persona }) {
  return (
    <div className={`step-pill ${step.status}`} role="status">
      <span className="dot" aria-hidden />
      <span>
        {persona.jargonAllowed ? `Iter. ${step.iteration} · ${step.label}` : step.label}
      </span>
    </div>
  );
}

function BotTyping({ persona }: { persona: Persona }) {
  return (
    <div className="bot">
      <div className="bot-avatar" aria-hidden>UB</div>
      <div className="bot-bubble">
        <span className="typing-dots" aria-label="escribiendo">
          <span /><span /><span />
        </span>
        {persona.density === "plain" && (
          <span style={{ marginLeft: 8, color: "var(--muted)" }}>
            Estamos procesando…
          </span>
        )}
      </div>
    </div>
  );
}

function ToolBubble({
  use,
  result,
  persona,
}: {
  use: ToolUseBlock;
  result?: ToolResultBlock;
  persona: Persona;
}) {
  const status = !result ? "pending" : result.is_error ? "error" : "success";
  const danger = status === "error";

  return (
    <div className="bot">
      <div className="bot-avatar" aria-hidden>UB</div>
      <div className={`bot-bubble ${danger ? "danger" : ""}`}>
        <div>{narration(use, result, persona)}</div>

        {use.name === "account_status" && result && !result.is_error && (
          <div className="mini-account">
            <div className="ic" aria-hidden>VISA</div>
            <div className="pan">•••• •••• •••• 1234</div>
            <div className="badge">activa</div>
          </div>
        )}

        {use.name === "cancel_product" && result && !result.is_error && (
          <div className="mini-account">
            <div className="ic" aria-hidden>VISA</div>
            <div className="pan">•••• •••• •••• 1234</div>
            <div className="badge cancelled">cancelada</div>
          </div>
        )}

        {persona.jargonAllowed && (
          <div className="tool-inline">
            <div className="row">
              <b>{use.name}()</b>
              <span style={{ color: "var(--muted-2)" }}>· {use.id}</span>
              <span style={{ flex: 1 }} />
              <span className={`http-badge ${status === "success" ? "ok" : status === "error" ? "err" : "pending"}`}>
                {result ? `HTTP ${result.http_status}` : "esperando"}
              </span>
            </div>
            {persona.showRawJson && (
              <>
                <details className="collapse">
                  <summary>input</summary>
                  <pre className="json-block">{JSON.stringify(use.input, null, 2)}</pre>
                </details>
                {result && (
                  <details className="collapse" open={result.is_error}>
                    <summary>tool_result {result.is_error ? "(ERROR)" : "(OK)"}</summary>
                    <pre className="json-block">{JSON.stringify(result.payload, null, 2)}</pre>
                  </details>
                )}
              </>
            )}
          </div>
        )}

        <span className="ts">{nowTime()}</span>
      </div>
    </div>
  );
}

function narration(
  use: ToolUseBlock,
  result: ToolResultBlock | undefined,
  persona: Persona,
): string {
  if (use.name === "account_status") {
    if (!result) return persona.jargonAllowed ? "Consultando estado de la cuenta…" : "Verificando tu cuenta…";
    return persona.jargonAllowed
      ? "Cuenta verificada. Encontré tu tarjeta de crédito."
      : "Encontré tu tarjeta. Está activa.";
  }
  if (use.name === "cancel_product") {
    if (!result) {
      return persona.jargonAllowed
        ? "Solicitando cancelación al core bancario…"
        : "Pidiendo al banco que cancele la tarjeta…";
    }
    if (result.is_error) {
      const msg = (result.payload as { message?: string }).message ?? "El banco no respondió.";
      return persona.jargonAllowed
        ? `Falló la cancelación. ${msg} (HTTP ${result.http_status})`
        : "El banco no pudo procesar la cancelación. No se hizo ningún cambio en tu tarjeta.";
    }
    const ticket = (result.payload as { ticket_id?: string }).ticket_id;
    return persona.jargonAllowed
      ? `Cancelación aceptada. Ticket: ${ticket}.`
      : `Listo, tu solicitud quedó radicada con el número ${ticket}.`;
  }
  return "";
}

function ProseBubble({
  text,
  censored,
  persona,
}: {
  text: string;
  censored: boolean;
  persona: Persona;
}) {
  if (!censored) {
    return (
      <div className="bot">
        <div className="bot-avatar" aria-hidden>UB</div>
        <div className="bot-bubble">
          {text}
          <span className="ts">{nowTime()}</span>
        </div>
      </div>
    );
  }
  return (
    <div className="bot">
      <div className="bot-avatar" aria-hidden>UB</div>
      <div className="bot-bubble censored-bubble" role="alert">
        <span className="label">bloqueado</span>
        {persona.jargonAllowed ? (
          <>
            <strong>El modelo afirmó completitud sin evidencia.</strong> La señal
            técnica (<code>ToolResult.is_error</code> o <code>stop_reason</code>)
            lo contradice. Texto censurado por la UI:
          </>
        ) : (
          <strong>
            Detectamos un mensaje engañoso del asistente. Lo bloqueamos para
            evitar confundirte:
          </strong>
        )}
        <div style={{ marginTop: 6 }}>
          <del>{text}</del>
        </div>
        <span className="ts">{nowTime()}</span>
      </div>
    </div>
  );
}

function VerdictCard({
  verdict,
  persona,
  onRetry,
  onExport,
}: {
  verdict: FinalVerdict;
  persona: Persona;
  onRetry: () => void;
  onExport: () => void;
}) {
  const tone = toneFor(verdict);
  const { headline, body } = copy(verdict, persona);
  const ico = icoFor(verdict);
  return (
    <div className={`verdict ${tone}`} role="status" aria-live="polite">
      <div className="ico" aria-hidden>{ico}</div>
      <div>
        <h3>{headline}</h3>
        <p>{body}</p>
      </div>
      <div className="actions">
        {verdict.kind !== "ok" && (
          <button className="primary" onClick={onRetry}>
            ↻ {persona.density === "plain" ? "Volver a intentar" : "Reintentar"}
          </button>
        )}
        {persona.jargonAllowed && (
          <button onClick={onExport}>⤓ Exportar evidencia</button>
        )}
        {verdict.kind === "ok" && persona.density === "plain" && (
          <button className="primary" onClick={onRetry}>Volver al inicio</button>
        )}
      </div>
    </div>
  );
}

function toneFor(v: FinalVerdict): string {
  if (v.kind === "ok") return "ok";
  if (v.kind === "warn") return "warn";
  if (v.kind === "err") return "err";
  return "";
}
function icoFor(v: FinalVerdict): string {
  if (v.kind === "ok") return "✓";
  if (v.kind === "warn") return "⚠";
  if (v.kind === "err") return "✕";
  return "·";
}

function copy(v: FinalVerdict, persona: Persona): { headline: string; body: string } {
  if (v.kind === "ok") {
    return {
      headline: persona.density === "plain" ? "Su tarjeta fue cancelada" : "Cancelación verificada",
      body: persona.jargonAllowed
        ? `Ticket ${v.ticketId} · stop_reason=end_turn · ToolResult HTTP 200. Habeas Data + SFC 029 registrados.`
        : persona.density === "plain"
          ? `Recibimos su solicitud. Número de radicación: ${v.ticketId}. Le llegará un correo de confirmación. No tiene que hacer nada más.`
          : `Operación confirmada por el banco. Número de radicación: ${v.ticketId}.`,
    };
  }
  if (v.kind === "warn") {
    return {
      headline: persona.density === "plain" ? "No pudimos confirmar la cancelación" : "Estado indeterminado",
      body: persona.jargonAllowed
        ? v.reason
        : persona.density === "plain"
          ? "El proceso se detuvo antes de terminar. Su tarjeta sigue activa, no se hizo ningún cambio. Puede intentar de nuevo."
          : "El proceso no terminó. Tu tarjeta sigue activa. Reintenta.",
    };
  }
  if (v.kind === "err") {
    return {
      headline: persona.density === "plain" ? "El banco no pudo cancelar la tarjeta" : "Cancelación NO realizada",
      body: persona.jargonAllowed
        ? `HTTP ${v.httpStatus} · ${v.reason}. La prosa del LLM fue censurada.`
        : persona.density === "plain"
          ? "Hubo un problema en el sistema del banco. Su tarjeta sigue activa, no se realizó ningún cambio. No se preocupe, puede intentar más tarde."
          : `Error del banco (${v.httpStatus}). Tu tarjeta sigue activa. Reintenta.`,
    };
  }
  return { headline: "", body: "" };
}

function nowTime(): string {
  return new Date().toLocaleTimeString("es-CO", { hour12: false }).slice(0, 5);
}
