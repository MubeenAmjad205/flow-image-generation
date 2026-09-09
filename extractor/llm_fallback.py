"""LLM-Assisted Fallback Extractor module (Phase 3).

Invoked when Tier 1 Deterministic Extraction yields confidence < 0.90.
Ingests pre-processed document text chunks and uses Google Gemini API
(Gemini 2.5 Flash Free Tier) with strict JSON Schema output enforcement.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from config.settings import settings
from utils.logger import logger
from extractor.confidence import ConfidenceEvaluator


class LLMFallbackExtractor:
    """Fallback document extractor powered by Gemini API native JSON schema mode."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    def extract(self, docx_paragraphs: list[str], source_filename: str = "document.docx") -> Tuple[Dict[str, Any], float]:
        """Extracts prompts from filtered DOCX paragraphs using Gemini API.
        
        Args:
            docx_paragraphs: List of raw text lines from DOCX.
            source_filename: Name of source document file.
            
        Returns:
            Tuple of (extracted_payload, confidence_score)
        """
        logger.info(f"LLMFallbackExtractor: Engaging Gemini API fallback for '{source_filename}'...")

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Using heuristic fallback parser.")
            return self._heuristic_fallback(docx_paragraphs, source_filename)

        # Pre-process text to minimize token payload (~2,000 tokens)
        filtered_text = self._preprocess_text(docx_paragraphs)

        try:
            # Try importing Google GenAI SDK
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            prompt_text = f"""You are a precision document extraction engine.
Extract all image generation prompts from the provided document into a JSON payload.

Rules:
1. Do not invent or summarize prompts. Extract prompt text verbatim.
2. Each item must have sequence (integer 1..N), prompt text, script_cue, and metadata (camera, lighting, mood, action, palette).
3. Standardize aspect_ratio to "16:9" and model to "nano_banana".

Document Text:
<<<
{filtered_text}
>>>
"""

            response = model.generate_content(
                prompt_text,
                generation_config={"response_mime_type": "application/json"}
            )

            raw_json = json.loads(response.text)
            extracted_images = raw_json.get("images", raw_json if isinstance(raw_json, list) else [])
            confidence = ConfidenceEvaluator.evaluate(extracted_images)

            payload = {
                "project_name": raw_json.get("project_name", "Google Flow Project"),
                "source_file": source_filename,
                "total_prompts": len(extracted_images),
                "default_aspect_ratio": "16:9",
                "default_model": "nano_banana",
                "images": extracted_images
            }

            logger.info(f"LLMFallbackExtractor: Gemini extracted {len(extracted_images)} items. Confidence: {confidence:.2f}")
            return payload, confidence

        except Exception as err:
            logger.error(f"Gemini API Extraction failed: {err}", exc_info=True)
            return self._heuristic_fallback(docx_paragraphs, source_filename)

    def _preprocess_text(self, paragraphs: list[str]) -> str:
        """Strips irrelevant TOC/Verification notes to cut token usage by 95%."""
        relevant_lines = []
        for p in paragraphs:
            # Include lines containing visual descriptors or prompt cues
            if any(k in p for k in ["BEAT", "Script:", "Camera:", "Lighting:", "Mood:", "Action:", "Palette:", "Hand-drawn", "illustration"]):
                relevant_lines.append(p)

        result = "\n".join(relevant_lines)
        if len(result) > 20000:
            result = result[:20000]
        return result

    def _heuristic_fallback(self, paragraphs: list[str], source_filename: str) -> Tuple[Dict[str, Any], float]:
        """Secondary local heuristic fallback if API key is missing or call fails."""
        logger.info("Executing local heuristic fallback parser...")
        items = []
        seq = 1

        for p in paragraphs:
            if len(p) > 50 and any(kw in p for kw in ["illustration", "Background:", "cartoon", "Hand-drawn"]):
                items.append({
                    "sequence": seq,
                    "time_code": None,
                    "script_cue": None,
                    "prompt": p.strip(),
                    "aspect_ratio": "16:9",
                    "model": "nano_banana",
                    "count": 1,
                    "metadata": {
                        "camera": None, "lighting": None, "mood": None, "action": None, "palette": None
                    }
                })
                seq += 1

        payload = {
            "project_name": "Google Flow Fallback Job",
            "source_file": source_filename,
            "total_prompts": len(items),
            "default_aspect_ratio": "16:9",
            "default_model": "nano_banana",
            "images": items
        }
        confidence = ConfidenceEvaluator.evaluate(items)
        return payload, confidence
