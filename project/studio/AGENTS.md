# Agent Rules <!-- tessl-managed -->

@.tessl/RULES.md follow the [instructions](.tessl/RULES.md)

## Project Overview

This is a Python project using Streamlit for the UI, focused on Domain-Driven Design (DDD) analysis.

## Development Environment

*   **Python Version:** 3.10.9+
*   **Dependency Management:** `uv`
    *   Install dependencies: `uv sync`
*   **Environment Variables:** Create a `.env` file in the project root with `ANTHROPIC_API_KEY="sk-ant-..."` (default provider is Claude). For Gemini legacy, set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY=...` instead.

## Running the Application

*   Start Streamlit application: `uv run streamlit run src/ddd_studio/app.py` (or `uv run ddd-studio`)

## Code Quality

*   **Linting/Formatting Tool:** `ruff`
    *   Check code style: `uv run ruff check .`
    *   Check code formatting: `uv run ruff format --check .`

## Testing

*   **Test Runner:** `pytest`
*   **Run Unit Tests:** `uv run pytest tests/unit/`
*   **Run Unit Tests with Coverage:** `uv run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-fail-under=80`

## Architecture Notes

*   **Structure:** Vertical Slice Architecture.
*   **Key Directories:** (all code lives under `src/ddd_studio/`)
    *   `src/ddd_studio/app.py`: Main Streamlit entry point.
    *   `src/ddd_studio/cli.py`: `ddd-studio` CLI launcher.
    *   `src/ddd_studio/application/`: Use case orchestration and LangGraph.
    *   `src/ddd_studio/domain/`: Business models (Pydantic), exceptions, and events.
    *   `src/ddd_studio/infra/`: Adapters for external services (Claude, Gemini, Whisper, etc.).
    *   `src/ddd_studio/services/`: Support logic (NLP, completeness analyzers).
    *   `src/ddd_studio/ui/`: Streamlit components and visualization.
    *   `tests/`: Unit and integration tests.
