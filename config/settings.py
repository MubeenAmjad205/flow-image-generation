"""Centralized configuration settings for Google Flow Image Generation Automation."""

import os
from pathlib import Path
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class SystemSettings:
    """System configuration values and default parameters."""
    
    # Directory Paths
    base_dir: Path = BASE_DIR
    input_dir: Path = BASE_DIR / "input"
    output_dir: Path = BASE_DIR / "output"
    jobs_dir: Path = BASE_DIR / "jobs"
    logs_dir: Path = BASE_DIR / "logs"
    profiles_dir: Path = BASE_DIR / "profiles" / "google-session"
    schemas_dir: Path = BASE_DIR / "schemas"
    
    # Canonical Schema File
    canonical_schema_path: Path = BASE_DIR / "schemas" / "canonical_job.schema.json"

    # Default Automation Parameters
    default_aspect_ratio: str = "16:9"
    default_model: str = "nano_banana"
    default_count_per_prompt: int = 1

    # Confidence Thresholds
    extraction_confidence_threshold: float = 0.90

    # API Keys & Endpoints
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    def __post_init__(self):
        """Ensure all required runtime directories exist."""
        for path_attr in [self.input_dir, self.output_dir, self.jobs_dir, self.logs_dir]:
            path_attr.mkdir(parents=True, exist_ok=True)


settings = SystemSettings()
