# Notebooks PoC — Claude Agent SDK · cancelación de tarjeta

Tres notebooks que validan, en orden creciente de complejidad, la viabilidad técnica del **Agentic Loop** propuesto, usando la herramienta oficial: **Claude Agent SDK** (Python).

Documentación canónica: <https://code.claude.com/docs/en/agent-sdk/overview>

## Índice

| # | Archivo                              | Pregunta que responde                                                          |
|---|--------------------------------------|--------------------------------------------------------------------------------|
| 1 | `01_intro_agent_sdk.ipynb`           | ¿Cómo se instala, autentica y se ejecuta un primer `query()` con el SDK?       |
| 2 | `02_tools_banca.ipynb`               | ¿Cómo se declaran tools `cancel_product` y `account_status` y se invocan?     |
| 3 | `03_senales_deterministas.ipynb`     | ¿Cómo se extraen `stop_reason`, `tool_use`, `ToolResult`, tokens — y se decide el verdict sin leer prosa? |

## Setup

Requiere **Python ≥ 3.10**. Desde `notebooks/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # api key real
python -m ipykernel install --user --name=taller-agent-sdk
jupyter lab        # o usa el kernel desde VS Code
```

## Convenciones

- Cada notebook es **idempotente**: puede correrse de cero.
- Uso de `nest_asyncio` para ejecutar coroutines en celdas Jupyter.
- Las llamadas reales a la API consumen tokens. Los notebooks 1 y 2 pueden correrse sin red usando los stubs marcados con `# OFFLINE`.

## Relación con el prototipo

Los `StreamEvent` que consume la UI en `prototype/src/types.ts` son intencionalmente isomorfos a los mensajes que devuelve `query()` del Agent SDK (`AssistantMessage`, `ToolUseBlock`, `ResultMessage`). Al reemplazar el mock por un backend real, basta con traducir los mensajes del SDK a `StreamEvent` y reutilizar todo el frontend.
