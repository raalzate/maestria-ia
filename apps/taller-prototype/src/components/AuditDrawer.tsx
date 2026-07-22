// Drawer auditor — solo Carlos. Compacta el Event Log + tabla de señales
// deterministas debajo del chat principal.

import { useMemo, useState } from "react";
import type { LoopState, LogRow } from "../lib/agenticLoop";

type Filter = "all" | "tool" | "stop" | "error" | "info";
const FILTERS: Filter[] = ["all", "tool", "stop", "error", "info"];

type Props = {
  state: LoopState;
  running: boolean;
  onCopy: () => void;
  onExport: () => void;
};

export function AuditDrawer({ state, running, onCopy, onExport }: Props) {
  const [open, setOpen] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");

  const rows = useMemo(() => {
    if (filter === "all") return state.log;
    return state.log.filter((r) => r.kind === filter);
  }, [state.log, filter]);

  return (
    <section className="audit-drawer" aria-label="Panel de auditoría — Carlos">
      <button
        className="audit-drawer-head"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <h3>Panel del auditor</h3>
        {running && <span className="badge-live">en vivo</span>}
        <span className="sub">
          {state.log.length} evento{state.log.length !== 1 ? "s" : ""} · trazabilidad inmutable
        </span>
        <span className="toggle">{open ? "▾ contraer" : "▸ expandir"}</span>
      </button>

      {open && (
        <div className="audit-drawer-body">
          <div className="col">
            <h4>Event Log auditable</h4>
            <div className="filters" role="toolbar" aria-label="Filtros">
              {FILTERS.map((f) => (
                <button
                  key={f}
                  className="filter-chip"
                  aria-pressed={filter === f}
                  onClick={() => setFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
            <div className="event-list" role="log" aria-live="polite">
              {rows.length === 0 ? (
                <p className="event-empty">
                  {state.log.length === 0
                    ? "Sin eventos. Inicia un escenario."
                    : "Ningún evento coincide con el filtro."}
                </p>
              ) : (
                rows.map((r, i) => <Row key={i} row={r} />)
              )}
            </div>
            <div className="audit-actions">
              <button onClick={onCopy} title="Copiar al portapapeles">⧉ Copiar</button>
              <button onClick={onExport} title="Exportar evidencia .json">⤓ Exportar evidencia</button>
            </div>
          </div>

          <div className="col">
            <h4>Señales deterministas</h4>
            <SignalsBoard state={state} />
          </div>
        </div>
      )}
    </section>
  );
}

function Row({ row }: { row: LogRow }) {
  return (
    <div className="event-row">
      <span className="ts">{row.ts}</span>
      <span className={`kind ${row.kind}`}>{row.kind}</span>
      <span className="msg">{row.msg}</span>
    </div>
  );
}

function SignalsBoard({ state }: { state: LoopState }) {
  const cancelUse = state.toolUses.find((u) => u.name === "cancel_product");
  const cancelResult = cancelUse ? state.toolResults[cancelUse.id] : undefined;

  const stopTone =
    state.stopReason === "end_turn" ? "ok"
    : state.stopReason === "max_tokens" ? "warn"
    : state.stopReason === "error" ? "err"
    : "";
  const toolTone =
    cancelResult === undefined ? "warn"
    : cancelResult.is_error ? "err" : "ok";
  const verdictTone =
    state.verdict.kind === "ok" ? "ok"
    : state.verdict.kind === "err" ? "err"
    : state.verdict.kind === "warn" ? "warn" : "";

  return (
    <div className="signals">
      <div className={`signal-row ${stopTone}`}>
        <span className="label">stop_reason final</span>
        <span className="value">{state.stopReason ?? "—"}</span>
      </div>
      <div className={`signal-row ${toolTone}`}>
        <span className="label">cancel_product · ToolResult</span>
        <span className="value">
          {!cancelUse ? "no invocada"
            : !cancelResult ? "pendiente"
            : `HTTP ${cancelResult.http_status} ${cancelResult.is_error ? "ERR" : "OK"}`}
        </span>
      </div>
      <div className="signal-row">
        <span className="label">tool_uses totales</span>
        <span className="value">{state.toolUses.length}</span>
      </div>
      <div className="signal-row">
        <span className="label">tool_results recibidos</span>
        <span className="value">{Object.keys(state.toolResults).length}</span>
      </div>
      <div className="signal-row">
        <span className="label">eventos en log</span>
        <span className="value">{state.log.length}</span>
      </div>
      <div className={`signal-row ${verdictTone}`}>
        <span className="label">verdict computado</span>
        <span className="value">{state.verdict.kind}</span>
      </div>
    </div>
  );
}
