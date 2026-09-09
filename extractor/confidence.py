"""Extraction Confidence Evaluator module.

Calculates a normalized confidence score S in [0.0, 1.0] for extracted document data.
"""

from typing import List, Dict, Any
from utils.logger import logger


class ConfidenceEvaluator:
    """Evaluates extraction completeness and structural integrity."""

    @staticmethod
    def evaluate(extracted_items: List[Dict[str, Any]], expected_count: int = 0) -> float:
        """Calculates confidence score S in [0.0, 1.0].
        
        S = 0.40 * C_seq + 0.30 * C_complete + 0.20 * C_non_empty + 0.10 * C_metadata
        """
        if not extracted_items:
            logger.warning("Confidence evaluation: 0 items extracted.")
            return 0.0

        total_extracted = len(extracted_items)

        # 1. Sequence Continuity (40%)
        sequences = [item.get("sequence", 0) for item in extracted_items]
        expected_seq = list(range(1, total_extracted + 1))
        c_seq = 1.0 if sequences == expected_seq else 0.5 if len(set(sequences)) == total_extracted else 0.0

        # 2. Completeness vs Expected (30%)
        if expected_count > 0:
            c_complete = min(1.0, total_extracted / float(expected_count))
        else:
            c_complete = 1.0 if total_extracted >= 1 else 0.0

        # 3. Non-Empty Prompt Quality (20%)
        valid_prompts = sum(1 for item in extracted_items if len(item.get("prompt", "").strip()) >= 15)
        c_non_empty = valid_prompts / float(total_extracted)

        # 4. Metadata Richness (10%)
        with_metadata = sum(1 for item in extracted_items if item.get("metadata") and any(item["metadata"].values()))
        c_metadata = with_metadata / float(total_extracted)

        # Composite Score Calculation
        score = (0.40 * c_seq) + (0.30 * c_complete) + (0.20 * c_non_empty) + (0.10 * c_metadata)
        logger.info(
            f"Extraction Confidence Score: {score:.2f} "
            f"(Extracted: {total_extracted}, Continuous: {c_seq == 1.0}, Quality: {c_non_empty:.2f})"
        )
        return round(score, 2)
