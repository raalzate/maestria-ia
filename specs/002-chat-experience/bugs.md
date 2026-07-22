# Bug Reports: 002-chat-experience

## BUG-001 — La protopersona rompe personaje y el escenario no es comportamental

- **Reported**: 2026-07-22
- **Severity**: high
- **Status**: fixed
- **GitHub Issue**: [#1](https://github.com/raalzate/maestria-ia/issues/1)

### Description

La simulación no sostiene la identidad de la protopersona (p.ej. Sofía Torres,
Scrum Master) y el contexto del escenario no es comportamental — no evidencia un
caso hipotético de uso. En una sesión de Daily Standup la persona respondió
"As a large language model, I need a bit more information…", rompiendo la
inmersión, y antes condujo la reunión con meta-pasos genéricos ("let's start
with the first step") en vez del guion de standup (ayer / hoy / bloqueos).

Causas raíz identificadas:
1. `sanitize-reply.ts` no filtra fugas de identidad de IA ("as a large language
   model", "as an AI", …): la frase llega intacta a la burbuja.
2. `runLocalSessionTurn` (llm-adapter) prefija el system prompt UNA sola vez en
   el KV-cache; los turnos siguientes envían solo el texto crudo del usuario y
   la persona se diluye con el modelo local pequeño.
3. `sceneGoalBlock` inyecta la descripción genérica del escenario sin hechos
   concretos del caso, y los `framingDescription` (misión del aprendiz, escritos
   en segunda persona) se inyectan en el system prompt de la IA invirtiendo los
   roles ("you" pasa a significar la persona).
4. Modelo default `gemma-e2b` con `temperature 0.8` degrada la adherencia a las
   instrucciones.

### Reproduction Steps

1. Abrir EMMA Desktop con IA local (modelo default gemma-e2b).
2. Iniciar el escenario "Daily Standup" (persona: Sofía Torres, Scrum Master).
3. Responder el kickoff ("Yes, I am ready.") y luego repetir la pregunta de la
   persona ("What is the next step?").
4. Observar: la persona no sigue el guion de standup y responde
   "As a large language model…" rompiendo el personaje.

### Root Cause

Ver causas 1–4 en Description: falta de guardia anti-fuga en el saneado, falta
de re-anclaje de persona por turno en sesiones locales, briefing de escena no
comportamental con roles invertidos, y configuración de modelo/temperatura
default débil.

### Fix Reference

- `src/domain/chat/identity-guard.ts` (nuevo): detección y limpieza de fugas de
  identidad de IA + línea de recuperación en personaje.
- `src/application/chat/run-chat-turn-use-case.ts`: aplica la guardia tras el
  saneado y antepone `characterAnchor` al turno en sesiones locales.
- `src/domain/chat/simulation-prompt.ts` + `simulation-prompt-text.ts`: bloque
  de situación con roles separados (LEARNER'S MISSION / YOUR PART), bloque
  SCENE FACTS y export `personaAnchor()`.
- `src/components/chat/use-chat-session.ts` + `src/interface/emma-runtime.ts`:
  cablean el ancla de personaje en cada turno.
- `src/lib/litert-models.ts`: default `gemma-e4b`; `src/lib/ai/litert-engine.ts`:
  `LITERT_SAMPLER_PARAMS` con temperature 0.6.
- Pruebas: `identity-guard.test.ts`, `litert-config.test.ts` (nuevas) y casos
  BUG-001 en `simulation-prompt.test.ts` y `run-chat-turn-use-case.test.ts`.

Refuerzo (2ª ronda, tras reproducirse con el bundle viejo):
- `sanitize-reply.ts`: cobertura de escrituras no latinas ampliada (tailandés,
  árabe, hebreo, cirílico, devanagari) + limpieza de puntuación huérfana +
  export `hasNonLatinScript`.
- `run-chat-turn-use-case.ts`: compuerta de streaming — retiene la apertura
  hasta la primera frontera de oración y suprime el stream si trae fuga de
  identidad o escritura no latina (la burbuja recibe solo la respuesta final
  limpia).
- `simulation-prompt-text.ts`: regla "Reply in ENGLISH ONLY" en EMMA_BASE.
- Pruebas nuevas: `sanitize-reply.test.ts` y compuerta de streaming en
  `run-chat-turn-use-case.test.ts`.

Solución de fondo (3ª ronda, tras resaludo/amnesia en turno 2):
- Se eliminó la memoria incremental del motor local (KV-cache de LiteRT perdía
  los turnos previos: la persona resaludaba e ignoraba lo dicho). Ahora cada
  turno reconstruye el contexto COMPLETO desde el historial de la app:
  `buildPrompt` emite transcripción etiquetada (You:/Learner:) + NEW MESSAGE +
  instrucción de continuidad con el ancla de personaje al final.
- `llm-adapter.ts`: adiós `runLocalSessionTurn`/mapa de conversaciones; todo
  turno local es system + prompt completo en conversación fresca.
- Nuevo `greeting-guard.ts` (dominio): elimina de forma determinista el
  resaludo cuando la escena ya empezó; si la respuesta era puro saludo se
  responde con la línea de recuperación en personaje.
- `EMMA_BASE`: regla explícita "saluda solo una vez".

4ª ronda (circularidad a los ~5 turnos + sugerencias que repiten al agente):
- Nuevo `scene-script.ts` (dominio): guion por fases con beats por turno del
  aprendiz (daily_standup: hoy → bloqueos → tema faltante/resumen → cierre;
  también tech_interview y vacation_request). El beat se inyecta como
  "SCENE SCRIPT — …" en la instrucción final del prompt de cada turno; obliga a
  avanzar en vez de repetir "tell me more about the next steps".
- Sugerencias: apéndice `SUGGEST_REPLIES_ANSWER_RULES` (los chips son el lado
  del APRENDIZ, primera persona, nunca las preguntas del agente) + filtro
  determinista `isEchoOfAgent` (solape de palabras de contenido; umbral 0.5
  para preguntas, 0.8 para afirmaciones).
- `sanitize-reply.ts`: elimina paréntesis vacíos/solo-puntuación ("( .)").

5ª ronda (vietnamita, run-ons, colapso progresivo del motor):
- `litert-engine.ts`: FUGA DE MEMORIA GPU — cada turno creaba una conversación
  LiteRT nueva y nunca la liberaba; el KV-cache acumulado degradaba el motor
  hasta el colapso a los pocos turnos. Ahora `litertGenerate` cierra la
  conversación en `finally` (`conversation.delete()`), causa probable del
  deterioro progresivo.
- `sanitize-reply.ts`: el vietnamita es escritura LATINA con diacríticos y
  evadía el filtro de runas. Nuevo `dropForeignSentences`: elimina ORACIONES
  completas con marcadores extranjeros (Latin Ext. Additional + đơưă, y las
  runas ya cubiertas), conservando las oraciones EN/ES vecinas; + limpieza de
  comillas huérfanas iniciales.
- `chat-brevity.ts`: tope duro de 60 palabras (los run-ons sin puntuación
  burlaban el tope de oraciones); elimina andamiaje de etiquetas ("What I
  need to know:", "Goal:", "(now)") y muñones de lista numerada ("1. What 2.").
