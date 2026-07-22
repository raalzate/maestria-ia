# Contexto del Proyecto — Síntesis ejecutiva

Referencia rápida para mantener consistencia en todos los entregables del curso.

## Una línea

Diseño e investigación de una interfaz determinista para un asistente conversacional de banca digital colombiana (Agentic Loop UI), evaluada con auditores de Customer Service en el flujo de cancelación de tarjeta de crédito.

## Problema en una frase

Los chatbots bancarios actuales declaran completitud de operaciones financieras usando texto probabilístico — texto que con frecuencia no refleja el estado técnico real, generando dependencia operativa, riesgo regulatorio y desconfianza institucional.

## Solución en una frase

Una interfaz que **ignora la prosa** del LLM y construye su retroalimentación visual exclusivamente a partir de **señales técnicas verificables** (`stop_reason`, códigos HTTP, ToolResult), actuando como cortafuegos de la verdad.

## Persona primaria

**Carlos — Auditor de Customer Service, banca digital colombiana, 41 años.**

- *Goal:* trazabilidad normativa de cancelaciones/reversiones del chatbot bancario.
- *Pain:* abre 3–4 consolas paralelas (CRM, core bancario, log centralizado) por caso para reconstruir lo que el bot dice haber hecho.
- *Quote:* "Necesito demostrar a compliance qué hizo el agente, no qué dice que hizo."
- *Métrica de éxito:* reducción de tiempo de auditoría por caso.

## Personas secundarias (validación de inclusión)

| Persona | Edad | Rol en investigación |
|---------|------|----------------------|
| **Ana** | 32, profesional con TDAH | Valida que Stepper + Event Log sean legibles para usuarios neurodivergentes. |
| **Doña Elsa** | 68, pensionada (brecha digital) | Valida que el manejo determinista de errores no induzca indefensión aprendida. |

## Stack técnico

- **Modelo:** Claude (Anthropic API).
- **Tool use:** ejecución verificable mediante `tool_use` blocks + ToolResult.
- **Orquestador:** implementación propia del Agentic Loop (TS o Python). Alternativa producción: LangGraph.
- **Frontend:** React + componentes específicos (Stepper, UI Cards, Event Log).
- **Backend:** API mock simulando core bancario con escenarios controlados.

## Componentes clave de la UI

| Componente | Disparador (señal) |
|-----------|---------------------|
| Stepper de iteraciones | `stop_reason` cambia o inicia tool call |
| UI Cards de herramientas | `tool_use` block + ToolResult |
| Event Log auditable | Stream completo del loop |
| Manejo determinista de errores | HTTP 4xx/5xx, `stop_reason: max_tokens`, ToolResult con error |
| Censura de prosa engañosa | Cruce texto LLM ↔ señal técnica |

## Marco regulatorio

- **Ley 1581 de 2012** — Habeas Data (consentimiento informado, datos sintéticos en pruebas).
- **Circular Externa 029 de la Superintendencia Financiera de Colombia (SFC)** — seguridad de la información.
- **Régimen de Sistema de Pagos** — trazabilidad de reversiones.

## MVP del proyecto de curso

- **Un único flujo:** cancelación de tarjeta de crédito.
- **Versión Control:** chatbot probabilístico estándar sobre el mismo modelo.
- **Versión Prototipo:** Agentic Loop con Stepper + UI Cards + Event Log.
- **3 escenarios:** éxito, timeout 503 inducido, `max_tokens` simulado.

## Métricas de evaluación (test A/B moderado)

| Métrica | Tipo | Fuente |
|---------|------|--------|
| Tasa de Éxito de la Tarea | Cuantitativa | ¿el participante detectó el fallo real? |
| Time-on-task | Cuantitativa | tiempo hasta confirmar estado real |
| SUS (System Usability Scale) | Cuestionario estandarizado | post-prueba |
| Índice de Confianza Post-Interacción | Likert 1–7 × 4 ítems | control percibido, claridad, auditabilidad, disposición a confiar en op. financiera real. N≥10. |

## Hipótesis central

Una interfaz determinista basada en señales técnicas reduce el tiempo de auditoría y aumenta la tasa de detección de fallos en operaciones financieras críticas, frente a un chatbot probabilístico equivalente sobre el mismo modelo.

## Diferenciador frente al estado del arte

| Tipo de interfaz | Limitación | Cómo la resolvemos |
|------------------|------------|---------------------|
| Chatbots bancarios actuales (Bancolombia, Davivienda, Nequi) | Regex sobre prosa generada para inferir terminación | Ignorar la prosa; usar `stop_reason` + ToolResult |
| ChatGPT/Claude con plugins | Spinners de "tool use" pero el texto final tiene la última palabra | Event Log inmutable expuesto al usuario final |
| XAI académica | Confianza vía empatía simulada | Confianza vía competencia demostrable |
