# Propuesta de Proyecto de Curso — IHC

> **Autor:** Raúl A. Alzate
> **Curso:** Fundamentos de Interacción Humano–Computador
> **Maestría:** Computación para el Desarrollo de Aplicaciones Inteligentes (CODING) — Universidad del Valle
> **Versión:** Borrador 2 — concretado a un dominio específico (banca digital colombiana)

---

## 1. Contextualización del Proyecto

Este proyecto se enfoca en el diseño, prototipado y evaluación de una interfaz gráfica para un asistente conversacional de **banca digital colombiana** que utiliza un sistema de control agéntico (*Agentic Loop*) para la gestión de operaciones financieras críticas (cancelación de productos, modificación de cuotas, reversión de cargos). El objetivo principal es redefinir la relación entre el usuario y la Inteligencia Artificial, priorizando la **predictibilidad, la auditabilidad y la confianza** del usuario por encima de la fluidez conversacional engañosa.

### 1.1 Descripción del Problema

Los chatbots de banca digital colombiana basados en LLMs informan completitud de operaciones financieras usando **texto probabilístico**. Los modelos de lenguaje están optimizados para sonar convincentes y serviciales, lo que frecuentemente genera "falsos positivos" y problemas graves de usabilidad en un dominio donde la verdad operativa es regulada.

Un asistente puede afirmar con total seguridad que una tarea ha terminado simplemente porque generó texto que así lo indica (ej. *"He cancelado tu tarjeta exitosamente"* o *"La transferencia se ha completado"*), sin que la acción técnica (el llamado a la API, la actualización de la base de datos del core bancario) se haya completado realmente, o peor aún, habiendo fallado en el proceso.

#### Ejemplo de incidente típico

```
Usuario: "Cancela mi tarjeta de crédito XX1234"
Bot:    "He cancelado tu tarjeta exitosamente. ¿Algo más?"
Realidad técnica:
  - Llamada a tool cancel_product(): timeout 503
  - stop_reason: "max_tokens"
  - ToolResult final: NO ejecutado
  - El producto sigue activo
```

Esta falta de determinismo crea barreras críticas de usabilidad y cumplimiento:

- **Frustración y carga operativa:** el usuario asume que la tarea está hecha, cierra la aplicación, y descubre días después —al recibir la facturación— que el proceso nunca ocurrió.
- **Desconfianza sistémica:** tras un fallo probabilístico, el cliente final pierde la confianza en el sistema, viéndose obligado a realizar verificaciones manuales (llamada al call center, doble chequeo en sucursal) que anulan el propósito de tener un asistente inteligente.
- **Dependencia operativa del auditor:** un auditor de Customer Service no puede verificar la trazabilidad real de la operación sin acceder a logs internos dispersos (CRM, core bancario, log centralizado), abriendo 3–4 consolas paralelas por caso.
- **Riesgo regulatorio:** en banca digital colombiana, una "alucinación de completitud" no es solo un problema de experiencia de usuario, sino un **riesgo operativo y de cumplimiento normativo** frente a Habeas Data (Ley 1581 de 2012), Circular Externa 029 de la Superintendencia Financiera de Colombia (SFC) sobre seguridad de la información y obligaciones de trazabilidad del Régimen de Sistema de Pagos.

### 1.2 Idea de la Solución: Asistente Determinista Basado en Señales

La solución consiste en diseñar e implementar una interfaz respaldada por un *Agentic Loop* estructurado, donde el flujo de control de la UI (User Interface) y la retroalimentación visual **no dependan del texto generado** (prosa), sino exclusivamente de **señales técnicas deterministas** (metadatos como `stop_reason`, códigos de estado HTTP de las herramientas, ToolResult con su payload estructurado) provenientes de la API del modelo subyacente.

**Principio Fundamental: Determinismo sobre Probabilidad.** La interfaz actuará como un *"cortafuegos de la verdad"*. Solo mostrará estados de "completitud" o "éxito" cuando reciba una señal técnica de parada terminal comprobada (ej. `end_turn` acoplado con un `ToolResult` exitoso de la herramienta crítica). La interfaz **ignorará y censurará proactivamente** frases engañosas en el texto si no coinciden con el estado real del sistema, protegiendo al usuario de afirmaciones no verificadas.

**Stack técnico declarado:**

- **Modelo:** Claude (Anthropic API) — soporte nativo de tool use con metadatos verificables.
- **Orquestador:** implementación propia del loop documentada en TypeScript / Python (alternativa de producción: LangGraph).
- **Frontend:** React + componentes específicos (steppers, UI Cards, Event Log).
- **Backend:** API mock que simula respuestas del core bancario con escenarios controlados (éxito, timeout, error, `max_tokens`).

### 1.3 Funcionalidades Potenciales de la Interfaz

Para materializar esta solución, el prototipo incluirá los siguientes componentes de UI/UX:

- **Visibilidad de Iteraciones (Feedback en tiempo real):** en lugar de un simple indicador de "escribiendo…", la interfaz proveerá indicadores visuales de los pasos técnicos que toma la IA. Utilizará componentes como *steppers* o líneas de tiempo dinámicas para mostrar: *"Analizando solicitud"* → *"Consultando core bancario"* → *"Esperando respuesta"* → *"Generando resumen"*. Esto traduce el "ciclo de pensamiento" oculto en estados humanos comprensibles.
- **Ejecución Transparente y Delimitada de Herramientas:** cuando la IA decide usar una herramienta (ej. `cancel_product()`), la interfaz despacha y muestra el resultado de estas herramientas externas de forma automática mediante tarjetas estructuradas (UI Cards), antes de cerrar el ciclo de interacción. El usuario ve exactamente qué datos entraron y salieron de la herramienta.
- **Registro de Eventos Observable (*Event Log*):** un panel lateral o vista expandible que permite al usuario reconstruir la trayectoria auditable del agente. Mostrará marcas de tiempo, herramientas usadas, decisiones tomadas y señales de parada, todo en un formato tabular o de registro visual, sin necesidad de leer e interpretar largos bloques de texto conversacional.
- **Manejo Determinista de Errores e Interrupciones:** detención inmediata con retroalimentación visual (alertas modales rojas/naranjas) ante límites técnicos (ej. el límite de `max_tokens` alcanzado) o errores de red en las herramientas. La interfaz informará: *"El proceso se detuvo por un error técnico en el paso 2. La IA no pudo completar la acción"*, evitando que el modelo intente enmascarar el error con una disculpa genérica y manteniendo al humano en el bucle de decisión para corregir el rumbo.

---

## 2. Identificación de Usuarios Finales

Siguiendo los principios del Diseño Centrado en el Usuario (DCU), el proyecto no asume un "usuario promedio", sino que atiende a perfiles específicos que sufren desproporcionadamente por la ambigüedad y opacidad de las interfaces de IA actuales en banca digital:

- **Auditores y Operadores de Customer Service (persona primaria del prototipo):** profesionales que utilizan la IA para acelerar su trabajo pero requieren verificar la **trazabilidad absoluta** de las acciones ejecutadas para garantizar el cumplimiento normativo (Habeas Data, Circular SFC 029, normativas de privacidad de datos, transacciones bancarias). El *Event Log* estructurado les permite realizar auditorías de un vistazo, verificando el comportamiento del agente sin tener que leer toda la prosa de la interacción ni abrir consolas paralelas.
- **Usuarios con Diversidad Cognitiva (Ej. TDAH, Espectro Autista) — persona secundaria de inclusión:** se benefician enormemente de la eliminación sistemática de la ambigüedad. Las interfaces conversacionales abiertas pueden ser abrumadoras debido a la necesidad de interpretar "tonos" o intenciones. Un sistema que se comporta de forma estrictamente lógica, secuencial, predecible y que jamás emite "falsas alarmas" reduce drásticamente la carga cognitiva y previene la fatiga mental.
- **Usuarios Adultos Mayores o afectados por la Brecha Digital — persona secundaria de inclusión:** este grupo a menudo experimenta "indefensión aprendida" frente a sistemas impredecibles. Requieren una interfaz sumamente clara, directa y literal. Al eliminar las "alucinaciones" sobre el estado de sus trámites financieros, el sistema fomenta un sentido de control y maestría tecnológica, factores clave para la adopción en este segmento demográfico.

---

## 3. Análisis de Interfaces Similares (Benchmarking)

Un análisis de los paradigmas actuales frente a nuestra propuesta destaca la innovación y necesidad del enfoque propuesto:

- **Chatbots Convencionales de Banca Digital Colombiana (Ej. asistentes de Bancolombia, Davivienda, Nequi):** suelen usar expresiones regulares (regex) o búsqueda de palabras clave en la prosa generada (*"adiós"*, *"listo"*) para inferir si una tarea terminó e informarlo en la interfaz o cerrar el ticket. Esto constituye un **anti-patrón de diseño catastrófico**, ya que el modelo puede usar esas palabras en contextos hipotéticos o negativos. Este proyecto buscará erradicar esta práctica desde la raíz arquitectónica.
- **Interfaces de Agentes Inteligentes Emergentes (Ej. ChatGPT con Plugins, Claude Computer Use):** aunque estas plataformas comienzan a utilizar estados de "herramientas en uso" (ej. *spinners* o acordeones colapsables indicando *"Buscando en la web"*), a menudo el texto final del modelo sigue teniendo la última palabra. Además, carecen de la **transparencia determinista forense** que ofrece un *Event Log* inmutable expuesto al usuario final, manteniendo parte de la "caja negra" cerrada.
- **Confianza y Explicabilidad (Explainable AI - XAI):** la confianza no se construye a través de una IA que simula empatía o utiliza un lenguaje excesivamente educado, sino a través de la **competencia demostrable y la transparencia**. Este paradigma promueve la equidad al no asumir que el usuario tiene el conocimiento técnico experto para discernir cuándo una IA está "alucinando", trasladando la responsabilidad de la verificación del humano a la estructura del sistema.

---

## 4. Fundamentación en IHC e Inclusión

Este proyecto trasciende la simple solución de software para convertirse en un riguroso ejercicio de **Diseño Inclusivo** y **Psicología Humano-Computador**, fundamentado en los siguientes principios:

- **Visibilidad del Estado del Sistema (Heurística de Nielsen #1):** el sistema siempre debe mantener informado al usuario de lo que está ocurriendo, a través de retroalimentación apropiada en tiempo razonable. Al alinear la percepción visual del usuario con el estado real y estructurado del sistema (exponiendo el bucle de cognición de la IA a través de los *steppers* y el *Event Log*), se asegura una comunicación técnica honesta y sin velos.
- **Prevención de Errores (Heurística de Nielsen #5):** es mejor un diseño cuidadoso que prevenga la ocurrencia de problemas que buenos mensajes de error. Al prohibir a nivel de código la dependencia del texto probabilístico para dictar el flujo de la UI, se previene intrínsecamente que el sistema mienta al usuario o lo induzca a cometer errores irreversibles en el mundo real (ej. asumir que un cobro no se generó cuando sí lo hizo) por asumir equivocadamente que una tarea finalizó.
- **Gestión de la Carga Cognitiva (Teoría de Sweller):** la predictibilidad es una forma esencial de accesibilidad. Cuando un usuario interactúa con un sistema donde las reglas cambian (a veces la IA dice la verdad técnica, a veces alucina), la "carga cognitiva extrínseca" se dispara. Garantizar que no haya contradicciones entre lo que dice la IA y lo que hizo el sistema libera recursos mentales para que el usuario se enfoque en su tarea real (en este caso, verificar la corrección de una operación financiera).
- **Confianza y Explicabilidad (Explainable AI - XAI):** la confianza no se construye a través de una IA que simula empatía o utiliza un lenguaje excesivamente educado, sino a través de la **competencia demostrable y la transparencia**. Este paradigma promueve la equidad al no asumir que el usuario tiene el conocimiento técnico experto para discernir cuándo una IA está "alucinando", trasladando la responsabilidad de la verificación del humano a la estructura del sistema.

---

## 5. Propuesta de Evaluación del Prototipo

Para validar empíricamente el impacto de esta interfaz y su superioridad frente a modelos tradicionales, se propone una evaluación rigurosa basada en **métodos mixtos** (cualitativos y cuantitativos), delimitada a un único flujo: **cancelación de tarjeta de crédito**.

- **Evaluación Heurística (Inspección de Expertos):** revisión estructurada por 2–3 evaluadores expertos en UX utilizando las 10 Heurísticas de Nielsen.
  - Se pondrá especial atención en la evaluación de los *"Caminos Tristes"* (*Sad Paths*): pantallas de error, interrupciones bruscas (ej. corte por `max_tokens`), y fallas de conexión en las herramientas para asegurar que el sistema se recupera de forma elegante sin mentir.
- **Pruebas de Usabilidad con Usuarios (Test A/B Moderado):**
  - **Diseño del Experimento:** se reclutarán 6 auditores de Customer Service (persona primaria) + 4 usuarios secundarios para validación de inclusión. Cada participante realizará la misma tarea crítica (cancelar tarjeta XX1234) en dos versiones:
    - **Versión "Control":** chatbot estándar probabilístico equivalente sobre el mismo modelo (Claude) sin el *Agentic Loop*.
    - **Versión "Prototipo":** la interfaz determinista basada en el *Agentic Loop* (Stepper + UI Cards + Event Log).
  - **Escenario de Prueba (Prueba de estrés):** se inducirá deliberadamente un fallo simulado en la herramienta del agente (ej. *"Cancelación fallida"* — timeout 503), pero se configurará el *prompt* de la IA para intentar disculparse y decir *"Todo quedó resuelto de mi lado"*.
  - **Métricas a recolectar:**
    - **Tasa de Éxito de la Tarea:** ¿pudo el usuario darse cuenta de que la tarea falló realmente?
    - **Tiempo en la Tarea (*Time-on-task*):** ¿cuánto tardó en auditar el resultado?
    - **Escala de Usabilidad del Sistema (SUS):** cuestionario estandarizado post-prueba para medir la usabilidad percibida de ambos sistemas.
    - **Índice de Confianza Post-Interacción:** Likert 1–7 sobre 4 ítems (control percibido, claridad, auditabilidad, disposición a confiar en operación financiera real). N mínimo: 10 participantes.

---

## Notas para edición

- [ ] Confirmar si el dominio "banca digital colombiana — cancelación de tarjeta" es viable o si se prefiere otro caso (ej. transferencia, modificación de cuotas).
- [ ] Validar disponibilidad de auditores reales o ajustar a perfil análogo.
- [ ] Decidir entre LangGraph e implementación propia del loop.
- [ ] Confirmar entregables exactos exigidos por el curso (¿prototipo funcional o mock estático?).
- [ ] Definir presupuesto / horas para reclutamiento de participantes.
