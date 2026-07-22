import type { Persona, PersonaId } from "../types";

export const PERSONAS: Record<PersonaId, Persona> = {
  carlos: {
    id: "carlos",
    name: "Carlos",
    role: "Auditor de Customer Service · banca digital",
    age: 41,
    density: "full",
    jargonAllowed: true,
    showEventLog: true,
    showRawJson: true,
    fontScale: 1,
    rationale:
      "Persona PRIMARIA. Necesita trazabilidad normativa (Habeas Data, SFC 029). Ve todas las señales técnicas, JSON y Event Log auditable.",
  },
  ana: {
    id: "ana",
    name: "Ana",
    role: "Profesional con TDAH · validación de inclusión",
    age: 32,
    density: "compact",
    jargonAllowed: false,
    showEventLog: false,
    showRawJson: false,
    fontScale: 1.05,
    rationale:
      "Persona SECUNDARIA — diversidad cognitiva. Valida heurística de Sweller: bajar carga cognitiva extrínseca. JSON oculto, Stepper grande, sin texto innecesario.",
  },
  elsa: {
    id: "elsa",
    name: "Doña Elsa",
    role: "Pensionada · validación de brecha digital",
    age: 68,
    density: "plain",
    jargonAllowed: false,
    showEventLog: false,
    showRawJson: false,
    fontScale: 1.18,
    rationale:
      "Persona SECUNDARIA — adulto mayor. Valida no inducir indefensión aprendida. Lenguaje llano: 'Estamos pidiendo cancelar su tarjeta', sin terminología técnica.",
  },
};

export const PERSONA_ORDER: PersonaId[] = ["carlos", "ana", "elsa"];
