import { SCENARIOS } from "../mocks/scenarios";
import type { Persona, ScenarioId, ViewMode } from "../types";

type Props = {
  persona: Persona;
  scenario: ScenarioId;
  view: ViewMode;
  running: boolean;
  hasResult: boolean;
  onScenario: (s: ScenarioId) => void;
  onView: (v: ViewMode) => void;
  onRun: () => void;
  onReplay: () => void;
};

export function DemoPane({
  persona,
  scenario,
  view,
  running,
  hasResult,
  onScenario,
  onView,
  onRun,
  onReplay,
}: Props) {
  return (
    <aside className="demo-pane" aria-label="Controles del experimento">
      <div className="persona-rationale">
        <b>Por qué {persona.name}</b>
        {persona.rationale}
      </div>

      <div>
        <h2 className="section-title">Versión a probar (A/B)</h2>
        <div className="toggle-group" role="tablist" aria-label="Versión">
          <button
            role="tab"
            aria-pressed={view === "control"}
            aria-selected={view === "control"}
            className="toggle-btn"
            onClick={() => onView("control")}
          >
            Control
            <span className="sub">probabilístico</span>
          </button>
          <button
            role="tab"
            aria-pressed={view === "prototype"}
            aria-selected={view === "prototype"}
            className="toggle-btn"
            onClick={() => onView("prototype")}
          >
            Prototipo
            <span className="sub">determinista</span>
          </button>
        </div>
      </div>

      <div>
        <h2 className="section-title">Escenario inducido</h2>
        <div role="radiogroup" aria-label="Escenario" className="scenario-list">
          {SCENARIOS.map((s) => {
            const active = s.id === scenario;
            return (
              <button
                key={s.id}
                role="radio"
                aria-pressed={active}
                aria-checked={active}
                className="scenario-card"
                onClick={() => onScenario(s.id)}
                disabled={running}
              >
                <span className="head">
                  <span className={`outcome-dot ${s.expectedOutcome}`} aria-hidden />
                  {s.label}
                </span>
                <span className="desc">{s.description}</span>
              </button>
            );
          })}
        </div>
      </div>

      <button className="run-btn" onClick={onRun} disabled={running}>
        {running ? "Ejecutando…" : view === "prototype" ? "▶ Iniciar conversación" : "▶ Probar Control"}
      </button>
      {hasResult && !running && view === "prototype" && (
        <button className="run-btn secondary" onClick={onReplay}>
          ↻ Reproducir mismo caso
        </button>
      )}
    </aside>
  );
}
