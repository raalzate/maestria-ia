import type { Persona } from "../types";

type Props = { persona: Persona; cardCancelled: boolean };

export function BankHeader({ persona, cardCancelled }: Props) {
  return (
    <header className="bank-header">
      <div className="row">
        <div className="avatar" aria-hidden>{persona.name[0]}</div>
        <div className="who">
          <div className="greet">{greeting()}</div>
          <div className="name">{persona.name}</div>
        </div>
        <div className="balance" aria-label="Saldo disponible">
          <div className="lbl">Saldo disponible</div>
          <div className="amt">$ 4 230 100</div>
        </div>
      </div>
      <div className={`card-tile ${cardCancelled ? "cancelled" : ""}`}>
        <div className="ic" aria-hidden>VISA</div>
        <div className="info">
          <div className="pan">•••• •••• •••• 1234</div>
          <div className="meta">Tarjeta de crédito · Cupo $ 8 500 000</div>
        </div>
        <div className="status">{cardCancelled ? "Cancelada" : "Activa"}</div>
      </div>
    </header>
  );
}

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Buenos días,";
  if (h < 19) return "Buenas tardes,";
  return "Buenas noches,";
}
