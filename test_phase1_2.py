"""Test script for Phase 1 & Phase 2 pipeline.

Parses 'Day13_Production_Package - Copy.docx', normalizes data, and validates schema.
"""

import sys
import json
from pathlib import Path

from extractor.deterministic import DeterministicParser
from validator.normalizer import DataNormalizer
from validator.schema_validator import SchemaValidator
from utils.logger import logger

def main():
    docx_file = "Day13_Production_Package - Copy.docx"
    logger.info(f"=== TESTING PHASE 1 & 2 PIPELINE ON '{docx_file}' ===")

    # 1. Deterministic Extraction (Phase 1)
    parser = DeterministicParser()
    raw_payload, confidence = parser.parse(docx_file)

    logger.info(f"Phase 1 Complete. Confidence: {confidence:.2f}")
    logger.info(f"Project Title: {raw_payload['project_name']}")
    logger.info(f"Total Extracted Prompts: {raw_payload['total_prompts']}")

    # 2. Data Normalization & Validation (Phase 2)
    normalized_payload = DataNormalizer.normalize(raw_payload)

    validator = SchemaValidator()
    is_valid, error_msg = validator.validate(normalized_payload)

    if not is_valid:
        logger.error(f"Validation FAILED: {error_msg}")
        sys.exit(1)

    logger.info("Validation PASSED successfully!")
    logger.info("=== SAMPLE EXTRACTED BEAT (BEAT #4) ===")
    sample_beat = normalized_payload["images"][3] if len(normalized_payload["images"]) >= 4 else normalized_payload["images"][0]
    print(json.dumps(sample_beat, indent=2))

if __name__ == "__main__":
    main()
