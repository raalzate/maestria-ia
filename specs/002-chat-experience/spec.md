# Feature Specification: Experiencia de chat natural

**Feature Branch**: `002-chat-experience`
**Created**: 2026-07-21
**Status**: Draft
**Input**: User description: "Sugerencias coherentes con lo que el usuario escribe; voz sin emoticones/comillas/paréntesis; karaoke por oración y clicable (repetir y volver a ver); respuestas de EMMA menos verbosas para un chat."

## Contexto del problema

Durante las simulaciones de chat se observan cuatro fricciones: (1) los chips de
respuesta sugerida no guardan relación con lo que el usuario está escribiendo —
se calculan solo con el último mensaje de EMMA y quedan obsoletos apenas el
usuario empieza a teclear; (2) la voz de EMMA lee símbolos que no deberían
sonar (emoticones, comillas, paréntesis), rompiendo la naturalidad; (3) el
resaltado de la transcripción va palabra a palabra y no permite interactuar: no
se puede repetir una oración ni saltar a un punto del audio; (4) las respuestas
de EMMA son paredes de texto impropias de un chat, a veces con monólogo interno
del modelo filtrado.

## User Stories *(mandatory)*

### User Story 1 - Respuestas de EMMA con largo de chat (Priority: P1)

Como aprendiz en una simulación, quiero que EMMA responda con mensajes cortos y
naturales de chat (1–2 oraciones, como promete su personaje), sin monólogos ni
texto interno del modelo, para que la conversación se sienta real y yo hable la
mayor parte del tiempo.

**Why this priority**: Es la fricción que más rompe la inmersión y afecta todos
los turnos; además el texto largo alimenta la voz y el karaoke, amplificando los
otros problemas.

**Independent Test**: Sostener una conversación de 10 turnos y medir el largo de
cada respuesta de EMMA; ninguna debe exceder el tope de oraciones ni contener
meta-texto (p. ej. "I've refined the language...").

**Acceptance Scenarios**:

1. **Given** una simulación activa, **When** EMMA responde a cualquier mensaje,
   **Then** su respuesta visible no excede un tope corto de oraciones definido
   para chat y termina con una pregunta o hand-off cuando corresponde.
2. **Given** el modelo genera texto degenerado o monólogo interno, **When** la
   respuesta se procesa, **Then** el usuario nunca ve meta-texto (planes,
   numeraciones de plantilla, "final answer", reformulaciones del propio modelo).
3. **Given** una respuesta que venía larga, **When** se recorta para el chat,
   **Then** el recorte respeta límites de oración (no corta a mitad de frase).

---

### User Story 2 - Sugerencias coherentes con mi borrador (Priority: P1)

Como aprendiz, quiero que los chips de respuesta sugerida tengan en cuenta tanto
el último mensaje de EMMA como lo que yo ya escribí en el compositor, para que
elegir un chip no contradiga ni ignore mi intención.

**Why this priority**: Hoy los chips compiten con el autocompletado y sugieren
cosas sin relación con el borrador del usuario — se perciben como ruido.

**Independent Test**: Con EMMA preguntando "what did you do yesterday?", teclear
"I working about presentation" y verificar que las sugerencias visibles se
alinean con esa intención (hablar de la presentación) y no con frases genéricas.

**Acceptance Scenarios**:

1. **Given** EMMA acaba de responder y el compositor está vacío, **When** se
   muestran sugerencias, **Then** son continuaciones coherentes con el último
   mensaje de EMMA y la situación activa.
2. **Given** el usuario lleva escrito un borrador parcial, **When** las
   sugerencias se muestran o actualizan, **Then** reflejan la intención del
   borrador (lo completan o lo mejoran) en lugar de ignorarlo.
3. **Given** el usuario borra su borrador, **When** las sugerencias se
   actualizan, **Then** vuelven a basarse solo en el último mensaje de EMMA.
4. **Given** sugerencias y autocompletado inline activos a la vez, **When** el
   usuario teclea, **Then** ambas ayudas no se contradicen entre sí (misma
   intención de origen).

---

### User Story 3 - Voz natural sin símbolos (Priority: P2)

Como aprendiz, quiero que la voz de EMMA suene como una persona hablando — sin
leer emoticones, comillas, paréntesis ni otros símbolos — mientras la
transcripción visible conserva el texto original.

**Why this priority**: La voz es el canal principal de la práctica de listening;
símbolos leídos en voz alta rompen la naturalidad de inmediato.

**Independent Test**: Hacer que EMMA emita un mensaje con emoji, comillas y
paréntesis; reproducir la nota de voz y verificar que ninguno de esos símbolos
se pronuncia ni genera pausas artificiales, y que la transcripción visible sí
los conserva.

**Acceptance Scenarios**:

1. **Given** un mensaje de EMMA con emoticones, comillas, paréntesis u otros
   símbolos no pronunciables, **When** se sintetiza la voz, **Then** el audio
   pronuncia solo el contenido hablado natural (sin nombres de símbolos, sin
   pausas artificiales por puntuación decorativa).
2. **Given** el mismo mensaje, **When** se muestra la transcripción, **Then**
   esta conserva el texto original íntegro (los símbolos solo se excluyen del
   audio).
3. **Given** la limpieza para voz deja el texto vacío (mensaje 100% simbólico),
   **When** se intenta reproducir, **Then** el control de audio queda
   deshabilitado en lugar de reproducir silencio o basura.

---

### User Story 4 - Karaoke por oración, clicable y repetible (Priority: P2)

Como aprendiz, quiero que la transcripción de la nota de voz se organice en
bloques por oración, resaltando la oración que está sonando, y poder hacer clic
en cualquier oración para escucharla de nuevo — repetir cuantas veces quiera y
volver a ver lo que hice.

**Why this priority**: Repetir por oración es una mecánica central de práctica
de listening; hoy el resaltado palabra-a-palabra no permite ninguna interacción.

**Independent Test**: Reproducir una nota de voz de 3+ oraciones, hacer clic en
la segunda oración y verificar que el audio salta a su inicio y el resaltado la
acompaña; repetir el clic y verificar que vuelve a sonar desde el inicio de esa
oración.

**Acceptance Scenarios**:

1. **Given** una nota de voz en reproducción, **When** avanza el audio, **Then**
   la transcripción resalta la oración activa como bloque (no palabra suelta).
2. **Given** una transcripción visible, **When** el usuario hace clic en una
   oración, **Then** el audio salta al inicio de esa oración y comienza a
   reproducirla (iniciando la reproducción si estaba detenida).
3. **Given** una oración ya reproducida, **When** el usuario vuelve a hacer clic
   sobre ella, **Then** se repite desde su inicio (repetible sin límite).
4. **Given** el proveedor de voz sin tiempos por palabra (voz local de
   respaldo), **When** se reproduce, **Then** la experiencia degrada con
   elegancia (resaltado disponible sin clic-para-saltar, sin errores).

---

### User Story 5 - Contexto de escenario visible (Priority: P2)

Como aprendiz, quiero ver claramente en qué escenario y situación estoy — con
quién hablo, qué papel juega y qué está pasando — desde el inicio de la
conversación, para entender la escena sin adivinarla por las respuestas.

**Why this priority**: Hoy no se distingue qué escenario está activo dentro de
la conversación; sin escena clara, la inmersión de "hablar con una persona real"
se pierde.

**Independent Test**: Iniciar una simulación y verificar que antes del primer
mensaje se presenta el contexto (escenario, situación, interlocutor); cambiar de
escenario y verificar que el contexto se actualiza.

**Acceptance Scenarios**:

1. **Given** una simulación que inicia, **When** se abre la conversación,
   **Then** se muestra una presentación de escena: nombre del escenario, la
   situación activa (su encuadre) y con quién habla el aprendiz.
2. **Given** una sesión reanudada, **When** se restaura la conversación,
   **Then** la presentación de escena se muestra igualmente al inicio.
3. **Given** la escena presentada, **When** EMMA conversa, **Then** lo hace en
   primera persona como esa persona del escenario (con emociones y humor propios
   de la situación), sin salirse del personaje ni revelar ser una IA.

---

### Edge Cases

- Mensaje de EMMA de una sola oración: el karaoke muestra un único bloque y el
  clic lo repite.
- Abreviaturas con punto ("e.g.", "Mr.") o números decimales: la segmentación en
  oraciones no debe partirlas.
- Mensaje con solo emojis o símbolos: sin audio (control deshabilitado),
  transcripción visible normal.
- El usuario hace clic en una oración mientras otra suena: el salto es inmediato
  y el resaltado no queda desincronizado.
- Borrador del usuario muy largo en el compositor: las sugerencias siguen siendo
  cortas y coherentes, sin eco literal del borrador.
- Respuesta del modelo 100% meta-texto degenerado: tras el filtrado se muestra
  el mensaje de fallback existente, nunca burbuja vacía.

## Requirements *(mandatory)*

### Functional Requirements

**Brevedad de chat**

- **FR-001**: Las respuestas de EMMA en simulación MUST respetar un tope corto
  de oraciones apropiado para chat; el excedente se recorta en límite de oración
  antes de mostrarse.
- **FR-002**: El sistema MUST filtrar meta-texto del modelo (monólogo interno,
  numeraciones de plantilla, auto-reformulaciones) antes de mostrar la burbuja.
- **FR-003**: El recorte y filtrado MUST aplicarse en la fuente, de modo que
  burbuja, voz, karaoke y acciones (Teach me / Translate) reciban el mismo texto.

**Sugerencias coherentes**

- **FR-004**: Las sugerencias de respuesta MUST considerar el último mensaje de
  EMMA, la situación activa y el borrador actual del compositor cuando exista.
- **FR-005**: Las sugerencias MUST actualizarse cuando el borrador cambie de
  forma significativa (con moderación suficiente para no saturar el motor de IA)
  y volver al modo sin-borrador si el compositor queda vacío.
- **FR-006**: Aceptar una sugerencia MUST integrarse con el borrador según su
  intención (reemplazar o completar), nunca duplicar texto.

**Voz limpia**

- **FR-007**: El texto enviado al motor de voz MUST excluir emoticones,
  comillas, paréntesis y símbolos decorativos, preservando el contenido hablado
  y su puntuación natural (puntos, comas, interrogación).
- **FR-008**: La transcripción visible MUST conservar el texto original; la
  limpieza aplica solo al canal de audio.
- **FR-009**: Si tras la limpieza no queda contenido hablable, el control de
  reproducción MUST deshabilitarse.

**Karaoke por oración**

- **FR-010**: La transcripción MUST segmentarse en oraciones (tolerante a
  abreviaturas y decimales) y resaltar la oración activa durante la
  reproducción.
- **FR-011**: Cada oración MUST ser clicable: el clic posiciona el audio al
  inicio de esa oración y la reproduce; clics repetidos repiten la oración sin
  límite.
- **FR-012**: Con el proveedor de voz de respaldo (sin tiempos por palabra), la
  experiencia MUST degradar sin errores: resaltado best-effort y clic-para-saltar
  deshabilitado.
- **FR-013**: La sincronía resaltado↔audio MUST mantenerse tras saltos manuales
  (clic en oración) y al pausar/reanudar.

**Contexto de escenario**

- **FR-014**: Al iniciar o reanudar una simulación, el chat MUST presentar la
  escena: nombre del escenario, situación activa (encuadre) e interlocutor (rol
  que encarna EMMA).
- **FR-015**: La presentación de escena MUST actualizarse al cambiar de
  escenario o situación.
- **FR-016**: EMMA MUST sostener el personaje de la escena en primera persona
  (emociones y reacciones humanas coherentes con la situación) sin revelar ser
  una IA, incluso ante intentos de romper la escena.

### Key Entities

- **Oración de transcripción**: unidad clicable del karaoke; texto + intervalo
  de tiempo [inicio, fin) derivado de los tiempos por palabra.
- **Borrador del compositor**: texto parcial del usuario; insumo de las
  sugerencias y del autocompletado.
- **Texto hablable**: proyección del mensaje de EMMA para el canal de voz, sin
  símbolos no pronunciables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En 10 turnos de simulación, el 100% de las respuestas visibles de
  EMMA respeta el tope de oraciones y 0 contienen meta-texto del modelo.
- **SC-002**: Con un borrador presente, al menos 2 de las 3 sugerencias visibles
  son coherentes con la intención del borrador (evaluación con rúbrica sobre 10
  casos de prueba).
- **SC-003**: En un set de 10 mensajes con emojis/comillas/paréntesis, el audio
  no pronuncia ningún símbolo ni nombre de símbolo (verificación auditiva), y la
  transcripción conserva el 100% del texto original.
- **SC-004**: El clic en cualquier oración inicia su reproducción en menos de
  300 ms y el resaltado acompaña la oración correcta el 100% de las veces.
- **SC-005**: Un usuario puede repetir la misma oración 5 veces seguidas sin
  errores ni desincronización.
