# Workspace Coding & Modular Standards Rule

## Rule Enforcements for Google Flow Automation Project

1. **Package Management: ALWAYS Use `uv`**:
   - **Mandatory Policy**: Always use `uv` for environment management, package installation, and Python script execution (`uv venv`, `uv pip install`, `uv run`). NEVER use standard `pip` directly.

2. **Modular Architecture**:
   - Keep code strictly modularized under `extractor/`, `validator/`, `automation/`, `state/`, `config/`, and `utils/`.
   - No single file should exceed 300 lines of code.

3. **Clean Logging Policy (No Loose Log Files)**:
   - Do NOT create loose `.log`, `.txt`, or `.tmp` files in the root folder or workspace directories.
   - All logging must use Python's standard `logging` module configured via `utils/logger.py`.
   - Logs must be written exclusively to `logs/execution.log` (which is git-ignored) and standard console output.

4. **Strict Type Annotations & Clean Code**:
   - Annotate all function parameters and return values with Python type hints (`str`, `int`, `List[dict]`, `Optional[Path]`).
   - Use `dataclasses` or Pydantic models for structured data objects.

5. **Resumable State Management**:
   - Always update and persist `state.json` inside the designated job directory (`jobs/job_<id>/state.json`).
   - Never lose prompt execution state during crashes or retries.

6. **Stealth & Anti-Detection Compliance**:
   - Browser automation components must use `undetected-chromedriver` or `playwright-stealth` with persistent profiles (`profiles/google-session`).
   - Never bypass Google reCAPTCHAs or security mechanisms; pause and request human-in-the-loop auth if session expires.
