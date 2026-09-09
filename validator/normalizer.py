"""Data Normalizer module (Phase 2).

Standardizes aspect ratios, model enums, prompt text formatting, and ISO timestamps.
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, List
from utils.logger import logger


class DataNormalizer:
    """Normalizes raw extracted dictionaries into canonical JSON representations."""

    VALID_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}
    ASPECT_RATIO_MAP = {
        "16x9": "16:9",
        "16 BY 9": "16:9",
        "WIDE": "16:9",
        "WIDESCREEN": "16:9",
        "9x16": "9:16",
        "VERTICAL": "9:16",
        "PORTRAIT": "9:16",
        "SQUARE": "1:1",
        "1x1": "1:1",
        "4x3": "4:3",
        "3x4": "3:4",
    }

    @classmethod
    def normalize(cls, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Applies normalization rules to raw extracted payload.
        
        Args:
            raw_payload: Extracted dictionary from parser.
            
        Returns:
            Normalized dictionary ready for schema validation.
        """
        logger.info("DataNormalizer: Normalizing job payload...")

        # 1. Project metadata
        project_name = raw_payload.get("project_name", "Google Flow Project").strip()
        source_file = raw_payload.get("source_file", "unknown.docx").strip()
        default_aspect_ratio = cls._normalize_aspect_ratio(
            raw_payload.get("default_aspect_ratio", "16:9")
        )
        default_model = cls._normalize_model(raw_payload.get("default_model", "nano_banana"))

        images: List[Dict[str, Any]] = []
        raw_images = raw_payload.get("images", [])

        for idx, item in enumerate(raw_images, start=1):
            normalized_item = {
                "sequence": item.get("sequence", idx),
                "time_code": item.get("time_code") or None,
                "script_cue": item.get("script_cue") or None,
                "prompt": cls._clean_text(item.get("prompt", "")),
                "aspect_ratio": cls._normalize_aspect_ratio(
                    item.get("aspect_ratio") or default_aspect_ratio
                ),
                "model": cls._normalize_model(item.get("model") or default_model),
                "count": 1,
                "metadata": cls._normalize_metadata(item.get("metadata", {}))
            }
            images.append(normalized_item)

        normalized_payload = {
            "project_name": project_name,
            "source_file": source_file,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_prompts": len(images),
            "default_aspect_ratio": default_aspect_ratio,
            "default_model": default_model,
            "images": images
        }

        logger.info(f"DataNormalizer: Successfully normalized {len(images)} prompts.")
        return normalized_payload

    @classmethod
    def _normalize_aspect_ratio(cls, val: str) -> str:
        if not val:
            return "16:9"
        clean_val = val.strip().upper()
        if clean_val in cls.VALID_ASPECT_RATIOS:
            return clean_val
        return cls.ASPECT_RATIO_MAP.get(clean_val, "16:9")

    @classmethod
    def _normalize_model(cls, val: str) -> str:
        if not val:
            return "nano_banana"
        clean_val = val.strip().lower()
        if "pro" in clean_val:
            return "nano_banana_pro"
        return "nano_banana"

    @classmethod
    def _normalize_metadata(cls, meta: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for k in ["camera", "lighting", "mood", "action", "palette"]:
            val = meta.get(k)
            cleaned[k] = val.strip() if isinstance(val, str) and val.strip() else None
        return cleaned

    @classmethod
    def _clean_text(cls, text: str) -> str:
        if not text:
            return ""
        # Strip excessive whitespace
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned
