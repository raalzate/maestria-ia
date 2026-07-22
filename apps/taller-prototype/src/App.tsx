import { useCallback, useState } from "react";
import { PersonaTabs } from "./components/PersonaTabs";
import { BankHeader } from "./components/BankHeader";
import { DemoPane } from "./components/DemoPane";
import { ChatView } from "./components/ChatView";
import { AuditDrawer } from "./components/AuditDrawer";
import { ControlChat } from "./components/ControlChat";
import { useAgenticLoop } from "./lib/agenticLoop";
import { PERSONAS } from "./lib/personas";
import type { PersonaId, ScenarioId, ViewMode } from "./types";

export function App() {
  const [personaId, setPersonaId] = useState<PersonaId>("carlos");
  const [view, setView] = useState<ViewMode>("prototype");
  const [scenario, setScenario] = useState<ScenarioId>("success");
  const [controlRunKey, setControlRunKey] = useState(0);
  const { state, start } = useAgenticLoop(scenario);

  const persona = PERSONAS[personaId];
  const running = state.verdict.kind === "running";
  const hasResult = state.verdict.kind !== "idle";
  const cardCancelled = state.verdict.kind === "ok";

  const run = useCallback(() => {
    if (view === "prototype") start(scenario);
    else setControlRunKey((k) => k + 1);
  }, [view, scenario, start]);

  const replay = useCallback(() => start(scenario), [start, scenario]);

  const onExport = useCallback(() => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evidencia-${scenario}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [state, scenario]);

  const onCopy = useCallback(() => {
    const text = state.log.map((r) => `${r.ts}\t${r.kind.toUpperCase()}\t${r.msg}`).join("\n");
    void navigator.clipboard.writeText(text);
  }, [state.log]);

  return (
    <div
      className={`app density-${persona.density}`}
      style={{ fontSize: `${persona.fontScale * 14}px` }}
    >
      <header className="appbar">
        <div className="row1">
          <div className="brand">
            <div className="brand-mark" aria-hidden>UB</div>
            <div className="brand-meta">
              <div className="name">UniBanca</div>
              <div className="sub">App de banca digital · Cancelación de tarjeta</div>
            </div>
          </div>
          <div className="appbar-spacer" />
          <div className="compliance" aria-label="Marco regulatorio">
            <span className="chip">Ley 1581</span>
            <span className="chip">SFC 029</span>
            <span className="chip muted">Univalle · CODING</span>
          </div>
        </div>
        <PersonaTabs value={personaId} onChange={setPersonaId} />
      </header>

      <div className="body">
        <DemoPane
          persona={persona}
          scenario={scenario}
          view={view}
          running={running}
          hasResult={hasResult}
          onScenario={setScenario}
          onView={setView}
          onRun={run}
          onReplay={replay}
        />

        <main
          className="stage"
          role="tabpanel"
          id={`panel-${persona.id}`}
          aria-labelledby={`tab-${persona.id}`}
        >
          {view === "prototype" ? (
            <>
              <div className="bank-frame">
                <BankHeader persona={persona} cardCancelled={cardCancelled} />
                <ChatView
                  state={state}
                  persona={persona}
                  onRetry={replay}
                  onExport={onExport}
                />
                <Composer running={running} />
              </div>
              {persona.showEventLog && (
                <AuditDrawer
                  state={state}
                  running={running}
                  onCopy={onCopy}
                  onExport={onExport}
                />
              )}
            </>
          ) : (
            <ControlChat scenario={scenario} runKey={controlRunKey} />
          )}
        </main>
      </div>
    </div>
  );
}

function Composer({ running }: { running: boolean }) {
  return (
    <div className="composer" aria-hidden>
      <input
        type="text"
        placeholder={running ? "Procesando…" : "Escribe un mensaje a UniBanca"}
        disabled
        readOnly
      />
      <button className="send" disabled aria-label="Enviar">↑</button>
    </div>
  );
}
