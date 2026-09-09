# AGENTS.md — Coding Standards & Development Guidelines

This document defines the architectural rules, coding standards, directory conventions, package management policies, and logging rules for the **Google Flow Image Generation Automation** codebase. All agents and developers modifying this repository must strictly adhere to these guidelines.

---

## 1. Core Architectural Principles

1. **Modular & Functional Design (Single Responsibility Principle)**
   - Every module, class, and function must have **one clearly defined responsibility**.
   - Avoid bloated monolithic files. Split logic into focused, decoupled packages (`extractor/`, `validator/`, `automation/`, `state/`, `utils/`).
   - Keep functions concise (< 50 lines) and pure wherever possible.

2. **Package Management: ALWAYS Use `uv` (Never `pip`)**
   - **Mandatory Policy**: Always use `uv` for environment setup, package installation, and execution (`uv venv`, `uv add`, `uv run`, `uv sync`). Never use standard `pip` directly.
   - Example commands:
     - `uv venv`  
     - `uv add jsonschema python-docx pydantic pyyaml playwright undetected-chromedriver`
     - `uv run main.py`
     - `uv sync`

3. **Strict Typing & Data Validation**
   - Use explicit Python type hints (`typing` module) for all function arguments and return types.
   - Use `dataclasses` or `pydantic` for internal data transfer objects (DTOs) and configuration structs.
   - Never pass untyped raw dictionaries across module boundaries.

4. **No Workspace Log Pollution**
   - **Never write loose `.log` or `.tmp` files to the workspace root or output directories.**
   - All runtime logs must be handled via Python's standard `logging` module and routed exclusively to:
     - Standard Console Output (`stdout` / `stderr`) with clean formatting.
     - Dedicated, git-ignored log file inside `logs/execution.log`.
   - Temporary data must be written to isolated `tmp/` or `jobs/` subdirectories and cleaned up automatically.

5. **Zero-Trust Error Handling & Defensive Programming**
   - Catch specific exceptions (`FileNotFoundError`, `jsonschema.ValidationError`, `PlaywrightTimeoutError`) instead of bare `except Exception:`.
   - Always log meaningful context before raising or handling errors.
   - Never swallow exceptions silently.

6. **Config-Driven Architecture**
   - No hardcoded magic strings, URLs, aspect ratios, or timeouts inside core logic.
   - Load all system configurations from centralized settings (`config/settings.py` or `config/settings.yaml`).
   - Load credentials and sensitive paths from environment variables (`.env`).

---

## 2. Directory & Package Structure Rules

```text
flow-image-generation/
├── AGENTS.md                  # Development rules & architectural standards
├── .gitignore                 # Git isolation (logs/, profiles/, output/, .env)
├── config/                    # System configuration & default settings
│   ├── __init__.py
│   └── settings.py
├── schemas/                   # JSON schemas for prompt jobs & state
│   └── canonical_job.schema.json
├── extractor/                 # Document parsing module (Phase 1 & 3)
│   ├── __init__.py
│   ├── deterministic.py       # Python XML / docx deterministic parser
│   ├── llm_fallback.py        # Gemini API fallback parser
│   └── confidence.py          # Extraction confidence evaluator
├── validator/                 # Schema validation & data normalization (Phase 2)
│   ├── __init__.py
│   ├── normalizer.py          # Aspect ratio & prompt text normalizer
│   └── schema_validator.py    # Draft-07 JSON schema validator
├── state/                     # Job state & checkpoint manager (Phase 9)
│   ├── __init__.py
│   └── manager.py             # Real-time state.json persistence
├── automation/                # Browser automation & Google Flow controller (Phases 4-7)
│   ├── __init__.py
│   ├── stealth.py             # Undetected-chromedriver / stealth setup
│   ├── auth.py                # Pre-flight session & login guard
│   └── flow_controller.py     # Google Flow UI interaction & completion monitor
├── utils/                     # Shared helper utilities
│   ├── __init__.py
│   ├── logger.py              # Centralized logging setup
│   └── file_utils.py          # Safe directory & ZIP archiving helpers
├── docs/                      # Technical documentation suite
├── input/                     # Incoming DOCX production packages
├── logs/                      # Isolated execution log files (git-ignored)
└── output/                    # Final packaged image assets (git-ignored)
```

---

## 3. Code Style & Conventions

### 3.1 Python Formatting & Naming
- Follow **PEP 8** naming conventions:
  - Modules & files: `snake_case.py`
  - Classes: `PascalCase`
  - Functions & variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- Include clear docstrings (Google style) for all public classes and functions.

### 3.2 Standardized Logging Policy
All modules must import a centralized logger from `utils/logger.py`:

```python
from utils.logger import get_logger

logger = get_logger(__name__)

def parse_docx(file_path: str) -> dict:
    logger.info(f"Parsing production package: {file_path}")
    try:
        # extraction logic
        logger.debug("Extracted 120 beat elements successfully.")
        return result
    except Exception as err:
        logger.error(f"Failed to parse DOCX package '{file_path}': {err}", exc_info=True)
        raise
```

---

## 4. Git & Security Guardrails

1. **Environment Variables**: Store sensitive API keys (`GEMINI_API_KEY`) and paths in `.env`. Never commit secrets.
2. **Git Ignore Enforcements**:
   - `logs/`
   - `output/`
   - `profiles/`
   - `.env`
   - `__pycache__/`
3. **Immutability & Resumability**:
   - State mutations must flush cleanly to `state.json`.
   - Code changes must never overwrite existing completed outputs without explicit `--force` flags.
