"""Schema Validator module (Phase 2).

Validates normalized job payloads against the formal canonical JSON Schema.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import jsonschema

from config.settings import settings
from utils.logger import logger


class SchemaValidator:
    """Validates payload against draft-07 canonical_job.schema.json."""

    def __init__(self, schema_path: Path = settings.canonical_schema_path):
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Canonical schema file not found at: {self.schema_path}")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates payload against canonical schema.
        
        Args:
            payload: Dict to validate.
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=payload, schema=self.schema)
            logger.info("SchemaValidator: Payload successfully passed schema validation!")
            return True, ""
        except jsonschema.ValidationError as err:
            error_msg = f"Schema validation error at path '{'.'.join(str(p) for p in err.path)}': {err.message}"
            logger.error(f"SchemaValidator failed: {error_msg}")
            return False, error_msg
        except Exception as err:
            error_msg = f"Unexpected schema validation exception: {err}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
