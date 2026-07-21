# Feature Specification: Onboarding conversacional natural

**Feature Branch**: `001-onboarding-natural`
**Created**: 2026-07-21
**Status**: Draft
**Input**: User description: "Rediseño del onboarding conversacional de EMMA: hacerlo natural (no cuestionario), rápido al inicio y con asimilación real de las respuestas."

## Contexto del problema

El onboarding actual se percibe como un cuestionario: EMMA hace una pregunta por
turno, en orden fijo de campos, sin reaccionar de verdad a lo que el usuario
cuenta. El arranque es lento (el usuario espera mirando un indicador de "pensando"
antes del primer saludo) y cada turno tarda cada vez más. Además, el sistema
guarda las respuestas de forma literal: no interpreta, no normaliza y no
sintetiza lo que el usuario dijo, por lo que el perfil resultante no refleja una
comprensión real ("no asimila").

## User Stories *(mandatory)*

### User Story 1 - Conversación natural, no cuestionario (Priority: P1)

Como usuario nuevo, quiero que la charla inicial con EMMA se sienta como una
conversación con una tutora real: que reaccione a lo que digo, haga preguntas de
seguimiento cuando aporte contexto interesante, y aproveche todo lo que cuento en
una sola respuesta (si digo mi nombre, rol y stack en una frase, no debe volver a
preguntar ninguno de esos datos).

**Why this priority**: Es la queja principal — la experiencia actual rompe la
promesa central del producto (tutora conversacional). Sin esto, el resto de
mejoras no cambia la percepción.

**Independent Test**: Conversar con EMMA respondiendo varios datos en un solo
mensaje y verificar que no re-pregunta lo ya dicho, que sus mensajes reaccionan
al contenido del usuario y que el orden de la charla varía según las respuestas.

**Acceptance Scenarios**:

1. **Given** el onboarding inicia, **When** el usuario responde con un mensaje
   que contiene varios datos (p. ej. nombre, rol y tecnologías), **Then** EMMA
   registra todos los datos presentes y su siguiente mensaje NO pregunta por
   ninguno de ellos.
2. **Given** EMMA acaba de recibir una respuesta, **When** genera su siguiente
   mensaje, **Then** este incluye una reacción específica al contenido de la
   respuesta (no una fórmula genérica) antes de pedir más información.
3. **Given** faltan varios datos por capturar, **When** EMMA decide qué
   preguntar, **Then** la pregunta se formula de manera conversacional y puede
   conectar con lo que el usuario ya contó (no una lista fija en orden
   invariable).
4. **Given** el usuario responde algo ambiguo o incompleto, **When** EMMA lo
   procesa, **Then** hace una pregunta de seguimiento natural en lugar de
   repetir la misma pregunta literal.

---

### User Story 2 - Arranque inmediato y ritmo fluido (Priority: P2)

Como usuario nuevo, quiero ver el saludo de EMMA de inmediato al entrar al
onboarding y que cada respuesta suya llegue sin esperas crecientes, para no
sentir que la aplicación está congelada o es lenta.

**Why this priority**: La primera impresión ocurre en los primeros segundos; hoy
el usuario mira un indicador de espera antes de la primera palabra de EMMA.

**Independent Test**: Cronometrar desde que se abre la pantalla de onboarding
hasta que aparece el primer mensaje de EMMA, y medir la latencia de los turnos
sucesivos en una conversación de 6+ turnos.

**Acceptance Scenarios**:

1. **Given** el usuario abre la pantalla de onboarding, **When** la pantalla
   carga, **Then** el saludo inicial de EMMA aparece de forma casi inmediata
   (sin depender de la preparación del motor de IA).
2. **Given** el motor de IA aún se está preparando, **When** el usuario envía su
   primera respuesta, **Then** la preparación ya inició en segundo plano y la
   espera percibida es menor que hoy.
3. **Given** una conversación avanzada (6+ turnos), **When** EMMA responde,
   **Then** la latencia por turno se mantiene estable (no crece con el largo de
   la conversación).

---

### User Story 3 - Asimilación real del perfil (Priority: P1)

Como usuario, quiero que EMMA entienda y procese lo que le conté — no que guarde
mis frases literales — de modo que mi perfil quede con datos limpios y
normalizados, y que al cerrar el onboarding EMMA demuestre que me entendió con un
resumen interpretado de quién soy y qué quiero practicar.

**Why this priority**: Es la segunda queja central ("guarda literal, no asimila").
El perfil alimenta todas las simulaciones posteriores; datos crudos degradan toda
la experiencia aguas abajo.

**Independent Test**: Responder con frases coloquiales y verbosas (p. ej. "pues
trabajo con python y esas cosas, también algo de aws") y verificar que el perfil
persistido contiene valores limpios y canónicos (p. ej. "Python, AWS") y que el
cierre incluye un resumen sintetizado, no un eco de las respuestas.

**Acceptance Scenarios**:

1. **Given** el usuario responde con lenguaje coloquial, **When** el sistema
   captura un dato, **Then** el valor persistido está normalizado (sin muletillas,
   con capitalización y formato canónicos), no el texto literal.
2. **Given** el proceso de interpretación falla en un turno, **When** el sistema
   decide qué persistir, **Then** NO persiste texto crudo; reintenta la
   comprensión o pide aclaración, y el perfil nunca queda con basura literal.
3. **Given** todos los datos requeridos fueron capturados, **When** el onboarding
   cierra, **Then** EMMA presenta un resumen sintetizado del perfil (interpretación
   propia, no repetición de las frases del usuario) y lo persistido coincide con
   ese resumen.
4. **Given** una respuesta larga con datos ya capturados y datos nuevos, **When**
   el sistema procesa el turno, **Then** los datos ya capturados no se
   sobrescriben con valores vacíos ni degradados.

---

### User Story 4 - Indicador de avance honesto (Priority: P3)

Como usuario, quiero que cualquier indicador de avance del onboarding refleje el
progreso real y no delate una estructura de formulario, para que la experiencia
se mantenga conversacional.

**Why this priority**: Menor impacto, pero hoy el indicador muestra una escala
incorrecta (cuenta pasos que no existen en el flujo actual) y refuerza la
sensación de cuestionario.

**Independent Test**: Completar el onboarding y verificar que el indicador parte
de la escala correcta, avanza monotónicamente y llega al 100% exactamente al
cierre.

**Acceptance Scenarios**:

1. **Given** el onboarding inicia, **When** se muestra el indicador de avance,
   **Then** su escala coincide con el número real de datos requeridos por el
   flujo vigente.
2. **Given** una respuesta captura varios datos a la vez, **When** el indicador
   se actualiza, **Then** refleja todos los datos capturados en ese turno.

---

### Edge Cases

- Usuario escribe en español o mezcla idiomas: los datos deben capturarse igual
  y EMMA mantiene su rol de tutora (responde en inglés según su personalidad).
- Usuario da una respuesta totalmente fuera de tema: EMMA redirige con
  naturalidad sin perder lo ya capturado.
- Usuario se niega a dar un dato no crítico: el flujo continúa sin ese dato y el
  cierre no lo inventa.
- El motor de IA no está disponible (ni local ni remoto): el usuario recibe un
  mensaje claro y el onboarding puede retomarse después sin perder lo capturado.
- Cierre inesperado de la app a mitad del onboarding: al volver, EMMA retoma
  saludando por el nombre (si ya lo tiene) y no re-pregunta lo persistido.
- Respuesta del usuario extremadamente larga: la captura no se trunca ni corrompe
  los datos ya guardados.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST mostrar el saludo inicial de EMMA de inmediato al
  entrar al onboarding, sin bloquearse en la preparación del motor de IA.
- **FR-002**: El sistema MUST iniciar la preparación del motor de IA en segundo
  plano desde que el onboarding se abre.
- **FR-003**: EMMA MUST reaccionar al contenido de cada respuesta del usuario
  antes de pedir información adicional (nada de fórmulas fijas por turno).
- **FR-004**: El sistema MUST capturar todos los datos presentes en una misma
  respuesta del usuario, sin re-preguntar datos ya capturados.
- **FR-005**: El sistema MUST permitir preguntas de seguimiento cuando la
  respuesta sea ambigua, en lugar de repetir la pregunta literal.
- **FR-006**: El sistema MUST resolver cada turno de conversación con una única
  interacción con el motor de IA (la comprensión no puede duplicar la latencia
  del turno).
- **FR-007**: El sistema MUST procesar la comprensión de forma incremental sobre
  el último intercambio, de modo que la latencia por turno no crezca con el
  largo de la conversación.
- **FR-008**: El sistema MUST normalizar cada dato capturado (limpieza de
  muletillas, formato canónico) antes de persistirlo; NUNCA persiste el texto
  literal del usuario como valor del perfil.
- **FR-009**: Ante fallo de comprensión en un turno, el sistema MUST conservar el
  perfil íntegro (sin escribir valores crudos ni vacíos) y reintentar o pedir
  aclaración.
- **FR-010**: Al completar la captura, EMMA MUST presentar un resumen sintetizado
  del perfil que demuestre interpretación (no eco de las frases del usuario), y
  ese resumen MUST ser consistente con lo persistido.
- **FR-011**: El indicador de avance MUST usar como escala el número real de
  datos requeridos del flujo vigente y avanzar de forma monótona hasta el cierre.
- **FR-012**: El sistema MUST retomar un onboarding interrumpido sin re-preguntar
  datos ya persistidos, saludando de forma personalizada si ya conoce el nombre.
- **FR-013**: Los datos requeridos del perfil se mantienen: nombre, rol,
  tecnologías y habilidades a practicar; años de experiencia sigue siendo
  opcional. El nombre sigue siendo el único dato crítico no omitible.
- **FR-014**: Toda salida del motor de IA usada para poblar el perfil MUST ser
  validada en el borde antes de entrar al dominio.

### Key Entities

- **Contexto de onboarding**: datos capturados durante la charla (nombre, rol,
  años de experiencia, tecnologías, habilidades a practicar), con distinción
  entre capturado, pendiente y omitido.
- **Perfil de usuario**: resultado persistido del onboarding; valores
  normalizados y resumen sintetizado del cierre.
- **Turno de conversación**: intercambio mensaje-de-EMMA / respuesta-de-usuario;
  unidad sobre la que se hace la comprensión incremental.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El primer mensaje de EMMA aparece en menos de 1 segundo desde que
  se abre la pantalla de onboarding, en frío.
- **SC-002**: La latencia por turno de EMMA se reduce al menos 40% respecto al
  flujo actual (mismo hardware, mismo modelo local) y se mantiene estable (±20%)
  entre el turno 2 y el turno 10.
- **SC-003**: En una conversación donde el usuario aporta 3 datos en un solo
  mensaje, el onboarding completo requiere como máximo 4 turnos del usuario.
- **SC-004**: 0 valores literales sin normalizar persistidos en el perfil en un
  set de 10 conversaciones de prueba con respuestas coloquiales.
- **SC-005**: El 100% de los onboardings completados termina con un resumen
  sintetizado consistente con los datos persistidos.
- **SC-006**: El indicador de avance nunca muestra una escala distinta al número
  de datos requeridos ni retrocede durante la conversación.
