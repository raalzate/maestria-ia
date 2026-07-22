# Prototipo — Agentic Loop UI · cancelación de tarjeta

App de banca digital ficticia (**UniBanca**) que materializa la solución del proyecto. La vista principal es el **chat de banca cliente** — la misma conversación que verá un usuario final cancelando su tarjeta de crédito. Todos los servicios están **mockeados**: no llama a Anthropic, ni a un core bancario real, ni a un backend HTTP.

React 18 + Vite 5 + TypeScript. Sin más dependencias.

## Cómo se ve

- **Tabs arriba** — un tab por participante del A/B test (Carlos · auditor / Ana · TDAH / Doña Elsa · pensionada). Cambiar de tab cambia el "lente" con el que se ve la misma conversación.
- **Marco de banca** — header rojo Univalle con avatar, saludo, saldo, tarjeta VISA **••••1234**.
- **Chat** — conversación en burbujas (usuario derecha, bot UB izquierda) que reproduce el `LoopState` como mensajes progresivos: pills de iteración, mini-cards de cuenta/tarjeta, badges HTTP, prosa censurada cuando aplica, verdict final.
- **Composer** — input de mensaje al pie, deshabilitado pero visualmente presente para verisimilitud.
- **Demo Pane lateral** — controla persona-rationale, A/B (Control vs Prototipo), escenario (Éxito / Timeout 503 / max_tokens), botón "Iniciar conversación".
- **Audit Drawer** — bajo el chat, *solo para Carlos*. Event Log con filtros + tabla de "Señales deterministas" (stop_reason, ToolResult, conteos, verdict).

## Cómo cada persona la ve

| Persona | Densidad | Qué ve | Qué se oculta |
|---|---|---|---|
| **Carlos** (auditor) | full | Stepper técnico, badges `HTTP 200/503`, JSON colapsable de input/tool_result, drawer auditor con Event Log + tabla de señales, copy técnico. | nada. |
| **Ana** (TDAH) | compact | Burbujas con texto humano ("Encontré tu tarjeta. Está activa."), mini-account cards visuales, step pills sin jerga, verdict claro. | JSON, `tool_use_id`, drawer auditor, terminología técnica. |
| **Doña Elsa** (pensionada) | plain | Mensaje del usuario en *usted*, tipografía 1.18×, verdict como gran tarjeta llana ("Su tarjeta sigue activa, no se preocupe…"), botón "Volver a intentar" grande. | Stepper, tool cards, mini-account, prosa, drawer, jerga. |

## Versión Control vs Prototipo

Toggle en el panel lateral. La vista *Control* renderiza un BankBot azul de chatbot probabilístico que afirma siempre "He cancelado tu tarjeta exitosamente", y muestra:

- Burbuja roja `lying` cuando el escenario forzó un fallo y aun así el bot dijo "exitosamente".
- Aviso "⚠ Realidad técnica oculta al usuario" explicando por qué mintió (HTTP 503 / max_tokens).
- Card explicativa "Por qué este patrón es peligroso".

Es el **anti-patrón** que el Prototipo está diseñado para reemplazar.

## Cómo se decide el verdict (sin tocar la prosa)

`decideVerdict()` en `src/lib/agenticLoop.ts`:

1. `final_stop_reason === "max_tokens"` → ⚠ inconcluso.
2. Sin `tool_use` con `name: "cancel_product"` → ⚠ no realizado.
3. Sin `tool_result` para ese `tool_use_id` → ✕ indeterminado.
4. `tool_result.is_error === true` → ✕ falló (HTTP visible).
5. `final_stop_reason !== "end_turn"` → ⚠ no terminal.
6. Todo OK → ✓ con `ticket_id`.

La prosa del LLM puede afirmar lo contrario; cuando lo hace, se renderiza como burbuja **`bloqueado`** con el texto tachado.

## Mapeo a las recomendaciones del taller

| Recomendación de `deliverables/taller_resuelto.html` | Encarnación |
|---|---|
| Persona PRIMARIA — Carlos | Tab activo por defecto, drawer auditor expandido, JSON visible. |
| Personas SECUNDARIAS — Ana / Elsa | Tabs alternativos, mismo chat con copy y densidad ajustadas. |
| Heurística #1 visibilidad | Step pills + mini-account cards + verdict prominente. |
| Heurística #5 prevención de errores | Verdict basado en señales, prosa engañosa censurada antes de mostrarse. |
| Sweller carga cognitiva | Modo Ana oculta JSON e `id`s; modo Elsa oculta el flujo intermedio. |
| XAI confianza por competencia | Drawer auditor: tabla de señales deterministas + Event Log inmutable + export `.json`. |
| Test A/B Control vs Prototipo | Toggle persistente, ambas vistas en la misma app. |
| Caminos Tristes | Hero verdict rojo/amarillo con CTA *Reintentar*; bubble `bloqueado` rayada. |
| Trazabilidad regulatoria (Habeas Data, SFC 029) | Chips en topbar, badge live en drawer, payload `regulatory_notice` en éxito. |

## Estructura

```
prototype/
├── index.html
├── vite.config.ts · package.json · tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx                     orquesta tabs/persona/A/B/escenario
    ├── styles.css                  Inter + paleta Univalle + 3 variantes density
    ├── types.ts                    StreamEvent, ToolUseBlock, Persona, ViewMode
    ├── lib/
    │   ├── agenticLoop.ts          reducer + decideVerdict()
    │   └── personas.ts             configuración de las 3 personas
    ├── mocks/
    │   ├── claudeStream.ts         AsyncGenerator del loop
    │   ├── bankingCore.ts          cancel_product / account_status
    │   └── scenarios.ts            success | timeout_503 | max_tokens
    └── components/
        ├── PersonaTabs.tsx         tabs persona (top)
        ├── BankHeader.tsx          header rojo, avatar, saldo, tarjeta VISA
        ├── DemoPane.tsx            panel lateral con A/B + escenario + run
        ├── ChatView.tsx            burbujas progresivas (LoopState → chat)
        ├── AuditDrawer.tsx         drawer Carlos: Event Log + señales
        └── ControlChat.tsx         BankBot azul anti-patrón
```

## Ejecutar

Requiere Node ≥ 18. Desde `prototype/`:

```bash
pnpm install
pnpm dev          # → http://127.0.0.1:5173
pnpm typecheck    # estricto
pnpm build        # ≈ 55 kB gzip
```

## Reemplazar mocks por servicios reales

1. Sustituir `runAgenticLoop()` en `src/mocks/claudeStream.ts` por un consumer SSE/fetch del backend (que use Claude Agent SDK — ver `notebooks/`) manteniendo el shape de `StreamEvent`.
2. Eliminar `bankingCore.ts` — el core real lo invoca el orquestador, no el cliente.
3. Reutilizar `agenticLoop.ts`, `personas.ts` y todos los componentes sin cambios.

Los tipos en `src/types.ts` son intencionalmente isomorfos al shape de la API de Claude (`tool_use`, `tool_result`, `stop_reason`).
