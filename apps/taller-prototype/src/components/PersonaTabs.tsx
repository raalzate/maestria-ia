import { PERSONAS, PERSONA_ORDER } from "../lib/personas";
import type { PersonaId } from "../types";

type Props = {
  value: PersonaId;
  onChange: (id: PersonaId) => void;
};

export function PersonaTabs({ value, onChange }: Props) {
  return (
    <div role="tablist" aria-label="Participantes del A/B test" className="tabs">
      {PERSONA_ORDER.map((id) => {
        const p = PERSONAS[id];
        const selected = p.id === value;
        return (
          <button
            key={p.id}
            role="tab"
            aria-selected={selected}
            aria-controls={`panel-${p.id}`}
            id={`tab-${p.id}`}
            className="tab"
            onClick={() => onChange(p.id)}
          >
            <span className="av" aria-hidden>
              {p.name[0]}
            </span>
            <span className="meta">
              <span>{p.name}</span>
              <span className="role">{shortRole(p.id)}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

function shortRole(id: PersonaId): string {
  if (id === "carlos") return "Auditor CS · 41";
  if (id === "ana") return "TDAH · 32";
  return "Pensionada · 68";
}
