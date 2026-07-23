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

6ª ronda (rediseño de ingeniería de contexto — el eco de instrucciones era
causado por el propio prompt):
- El system prompt acumulaba 878 palabras de directivas; el modelo pequeño las
  RECITABA en escena ("(Here is the next step in the conversation…)"). Se
  rediseñó bajo presupuesto: 349 palabras reales (test de regresión ≤330 con
  fixture), directivas deduplicadas, y reglas+ejemplo AL FINAL (sesgo de
  recencia).
- Few-shot: nuevo bloque STYLE_EXAMPLE (un intercambio ejemplo del formato
  esperado) — mostrar > prohibir para modelos 2–4B.
- Contrato de salida: la instrucción por turno pide "ONE short line of spoken
  dialogue — nothing else"; `sanitize-reply` quita la etiqueta de hablante
  ("You:", "Sofía Torres:") si el modelo copia el formato del transcript.
- `chat-brevity`: patrón para paréntesis de planificación ("Here is the next
  step in the conversation…").
- `renderCharacterStyle` compacto (regla de inglés deduplicada a EMMA_BASE).

7ª ronda (opener repetido + fallback técnico rompiendo la inmersión):
- Nuevo `repetition-guard.ts` (dominio): si la respuesta abre con las mismas
  4 palabras normalizadas que un turno anterior de la persona ("Great, so far
  so good!…"), el opener se extirpa de forma determinista.
- `run-chat-turn-use-case.ts`: cuando el modelo generó algo pero la limpieza
  lo vació por completo, se responde con la línea de recuperación EN PERSONAJE
  ("Sorry, I lost my train of thought…") — el fallback técnico "EMMA is having
  trouble responding" queda SOLO para timeout sin tokens o respuesta vacía del
  motor (Sofía nunca vuelve a hablar como sistema).
- Instrucción por turno: "never repeat … an opener you already used".

8ª ronda (la recuperación se repetía y se volvió el nuevo bucle):
- Loop de validación en `runChatTurn`: generar → limpiar → si quedó vacío o
  idéntico al último turno de la persona, UN reintento con nudge correctivo
  ("Your previous reply was rejected… reply again with different wording") →
  si también falla, recuperación en personaje VARIADA (`pickRecovery`: nunca
  la misma línea dos turnos seguidos).
- `cleanReply` ya no inyecta la recuperación (devuelve "" y el caller decide);
  una respuesta idéntica al turno anterior de la persona cuenta como inválida.
- FALLBACK técnico queda solo para: timeout sin tokens o motor que devuelve
  cadena vacía.

9ª ronda (pipeline agéntico por turno — checklist con estado + capas de contexto):
- Nuevo `scene-state.ts` (dominio): el razonamiento del agente es código
  determinista, no el modelo. Checklist por escenario (standup: yesterday /
  today / blockers; interview; vacation). Observe: cada mensaje sustantivo del
  aprendiz cubre el ítem pendiente y CAPTURA el hecho literal; el relleno
  ("yeah") no avanza. Decide: la directiva del turno dice qué ya se sabe
  (prohibido re-preguntar, con los hechos) y qué preguntar AHORA. Verify:
  `isReaskingCovered` veta respuestas que re-preguntan un ítem cubierto →
  dispara el reintento del loop. Reemplaza a scene-script.ts (avanzaba por
  conteo de turnos: "yeah" lo avanzaba y lo respondido temprano no se marcaba).
- Nuevo `history-layers.ts` (dominio): capas de contexto — últimos 4 turnos
  verbatim; turnos viejos solo si sustantivos; smalltalk viejo colapsado a
  "(Earlier: greetings and small talk were exchanged.)" (los hechos ya viajan
  en el checklist).
- `runChatTurn` acepta `validateReply` (Verify inyectable) y aplica las capas
  al plegar el historial. `use-chat-session` mantiene el `SceneState` (replay
  al restaurar) y cablea Observe→Decide→Verify.

10ª ronda (contrato de escena como prerequisito e inyección):
- DEFECTO: la narrativa inmersiva de la antesala solo se MOSTRABA al aprendiz;
  nunca entraba al system prompt — la persona jugaba una escena que no conocía
  (dos mundos desconectados) y el prompt le decía "inventa tus detalles".
- Nuevo `create-scene-contract-use-case.ts`: única fuente de verdad. Genera
  (1) hechos EN fijos (3 líneas, validadas en el borde) y (2) la narrativa ES
  derivada DE ESOS hechos. Los hechos se inyectan al system como
  "SCENE FACTS (fixed — never contradict them)" (guardrail), reemplazando al
  bloque genérico. Fallback determinista: el framing del catálogo.
- Prerequisito de inicio: `use-chat-session` genera el contrato al montar la
  antesala (timeout 25s → fallback) y `begin()` lo exige; el botón muestra
  "Creando tu escena…" (spinner) hasta que está listo — esto también explica
  el "cambio de texto" reportado: antes el estático se reemplazaba en vivo.
- `scene-intro.tsx` ya no llama al LLM: recibe narrativa/sceneReady por props;
  `sceneBriefing` del runtime se reemplaza por `sceneContract`.

11ª ronda (el agente decide terminar → feedback de Emma automático):
- `isSceneComplete` (scene-state): checklist sin pendientes ⇒ la escena debe
  cerrar. En `use-chat-session`, cuando el checklist se completa la respuesta
  siguiente es el CIERRE de la persona; tras entregarlo (o al agotar el
  presupuesto `maxTurnsFor`) se marca `sceneComplete`, se bloquean nuevos
  turnos y `EndSession` dispara `finish()` automáticamente (autoFinish, con
  pausa de 2.5s para leer la despedida).
- El flujo de cierre ya existente entrega TODO lo pedido: reporte/lección de
  Emma (errores del búfer silencioso revelados), `evaluateProgression`
  (promoción de nivel o aspectos a mejorar), `markPassed` y recomendación del
  siguiente escenario. Antes era solo manual (botón Terminar, que se conserva
  para salir antes).

12ª ronda (lección real de Emma + resumen rediseñado + transición suave):
- Nuevo `build-lesson-use-case.ts`: Emma (LLM) escribe la lección en ESPAÑOL —
  por qué está mal cada error, la regla y ejemplos correctos en inglés, con
  mini-reto — validada en el borde; null ⇒ respaldo determinista (LESSON_TIPS).
- Nuevo `session-summary.ts` (dominio): markdown por secciones en español, sin
  tablas (se renderizaban rotas): 🏁 cabecera con métricas, ✏️ correcciones
  numeradas (dijiste → mejor), 📚 lección, 🎯 siguiente paso con práctica
  recomendada. `finishSession` lo usa; `buildFeedbackReport` (paridad Python)
  se conserva exportado con sus pruebas.
- Transición: al completar la escena el composer se reemplaza por el banner
  "Escena completada — Emma está preparando tu lección…" (ya no es un modal
  que aparece de golpe) y el dialog pasa a "🎓 Tu lección con Emma" con
  descripción.

13ª ronda (markdown plano y corrección basura en la lección):
- CAUSA del "mal diseño": `@tailwindcss/typography` NUNCA estuvo instalado —
  todas las clases `prose` del app eran letra muerta (headings/listas sin
  estilo en la lección, Teach me y traducciones). Instalado y registrado en
  `tailwind.config.ts`.
- Nuevo `isActionableCorrection` (domain/chat/silent-error): filtra las
  meta-respuestas del checker ("(No correction needed for this input.)",
  "no change", "already correct", paréntesis puro) que entraban al búfer,
  inflaban la métrica y contaminaban la lección con reglas inventadas.
  Filtrado en la FUENTE (bufferGrammar) + defensa en finishSession/buildLesson.
- Correcciones a una línea: “original” → **“mejor”** _(tipo)_ (el salto suave
  de markdown se renderizaba como espacio).
