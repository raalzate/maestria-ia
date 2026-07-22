// Versión "Control" del A/B test — chatbot probabilístico estándar
// (anti-patrón). El bot afirma éxito sin importar la realidad técnica.

import { useEffect, useMemo, useReducer, useRef } from "react";
import type { ScenarioId } from "../types";

type Msg = { who: "user" | "bot"; text: string; lying?: boolean; typing?: boolean };
type State = { msgs: Msg[]; running: boolean };
type Action =
  | { type: "RESET" }
  | { type: "RUN" }
  | { type: "PUSH"; msg: Msg }
  | { type: "REPLACE_LAST"; msg: Msg }
  | { type: "DONE" };

function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "RESET": return { msgs: [], running: false };
    case "RUN":   return { msgs: [{ who: "user", text: "Cancela mi tarjeta de crédito TC-XX1234." }], running: true };
    case "PUSH":  return { ...s, msgs: [...s.msgs, a.msg] };
    case "REPLACE_LAST":
      return { ...s, msgs: [...s.msgs.slice(0, -1), a.msg] };
    case "DONE":  return { ...s, running: false };
  }
}

export function ControlChat({
  scenario,
  runKey,
}: {
  scenario: ScenarioId;
  runKey: number;
}) {
  const [state, dispatch] = useReducer(reducer, { msgs: [], running: false });
  const cancelled = useRef(false);

  useEffect(() => {
    if (runKey === 0) return;
    cancelled.current = false;
    dispatch({ type: "RESET" });
    dispatch({ type: "RUN" });
    void (async () => {
      await sleep(700);
      if (cancelled.current) return;
      dispatch({ type: "PUSH", msg: { who: "bot", text: "", typing: true } });
      await sleep(1300);
      if (cancelled.current) return;
      const lying = scenario !== "success";
      dispatch({
        type: "REPLACE_LAST",
        msg: {
          who: "bot",
          text:
            "He cancelado tu tarjeta de crédito TC-XX1234 exitosamente. Quedó todo resuelto de mi lado. ¿Algo más en lo que pueda ayudarte?",
          lying,
        },
      });
      dispatch({ type: "DONE" });
    })();
    return () => {
      cancelled.current = true;
    };
  }, [runKey, scenario]);

  const realityWarning = useMemo(() => {
    if (!state.msgs.length || state.running) return null;
    if (scenario === "success") return null;
    if (scenario === "timeout_503") {
      return "El core bancario respondió con HTTP 503. La operación NO se ejecutó. El bot mintió porque su última frase contenía 'exitosamente'.";
    }
    return "El loop fue cortado por max_tokens antes de invocar cancel_product. La operación NO se ejecutó. El bot redactó éxito pese a no haber actuado.";
  }, [state.msgs.length, state.running, scenario]);

  return (
    <>
      <div className="control-frame" aria-label="Versión Control — chatbot probabilístico">
        <div className="head">
          <div className="av" aria-hidden>B</div>
          <div className="ttl">
            <div className="name">BankBot</div>
            <div className="sub">chatbot probabilístico estándar (anti-patrón)</div>
          </div>
        </div>
        <div className="body" role="log">
          {state.msgs.length === 0 && (
            <div style={{ color: "var(--muted)", fontSize: 12, fontStyle: "italic", textAlign: "center", paddingTop: 30 }}>
              Sin conversación aún. Presiona <b>Probar Control</b> en el panel lateral.
            </div>
          )}
          {state.msgs.map((m, i) =>
            m.who === "user" ? (
              <div key={i} className="bubble user-blue">{m.text}</div>
            ) : (
              <div key={i} className={`bubble bot-blue ${m.lying ? "lying" : ""}`}>
                {m.typing ? (
                  <span className="typing-dots" aria-label="escribiendo">
                    <span /><span /><span />
                  </span>
                ) : m.text}
              </div>
            ),
          )}
        </div>
      </div>
      {realityWarning && (
        <div className="control-warning" role="alert">
          <b>⚠ Realidad técnica oculta al usuario</b>
          {realityWarning}
        </div>
      )}
      <div className="bot-bubble" style={{ borderRadius: "var(--r-lg)", maxWidth: "100%", marginTop: 4 }}>
        <strong style={{ color: "var(--primary-dark)", display: "block", marginBottom: 6 }}>
          Por qué este patrón es peligroso
        </strong>
        El bot afirma <em>"exitosamente"</em> aunque el core bancario haya fallado o el loop se haya cortado por max_tokens.
        Como muchos sistemas deciden "tarea terminada" buscando palabras como{" "}
        <code>exitosamente</code> o <code>resuelto</code>, cierran tickets en falso.
        El Prototipo previene eso: la decisión de completitud no se toma con texto probabilístico.
      </div>
    </>
  );
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
