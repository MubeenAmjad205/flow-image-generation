"""Deterministic DOCX Extractor module (Phase 1).

Parses Microsoft Word (.docx) XML documents using pure Python zipfile and
ElementTree XML parsing to extract image generation prompts, sequence numbers,
script cues, and key-value metadata with 0ms API overhead.
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from utils.logger import logger
from extractor.confidence import ConfidenceEvaluator

# OpenXML Namespace map
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class DeterministicParser:
    """Parses DOCX files deterministically using XML structure and pattern invariants."""

    BEAT_HEADER_REGEX = re.compile(
        r"^BEAT\s+(\d+)\s*[—\-–·]\s*(.*)$", re.IGNORECASE
    )
    SCRIPT_CUE_REGEX = re.compile(
        r"^Script:\s*[\“\"']?(.*?)[\”\"']?$", re.IGNORECASE
    )
    METADATA_KEY_REGEX = re.compile(
        r"^(Camera|Lighting|Mood|Action|Palette):\s*(.*)$", re.IGNORECASE
    )

    def parse(self, docx_path: str) -> Tuple[Dict[str, Any], float]:
        """Parses a DOCX file and returns the extracted payload and confidence score."""
        path = Path(docx_path)
        if not path.exists():
            raise FileNotFoundError(f"DOCX production package not found: {docx_path}")

        logger.info(f"DeterministicParser: Ingesting '{path.name}'...")
        paragraphs = self._read_docx_paragraphs(path)
        
        # 1. Isolate prompt section paragraphs
        prompt_paragraphs = self._isolate_image_prompts_section(paragraphs)
        
        # 2. Extract Project Title
        project_name = self._extract_project_title(paragraphs)
        
        # 3. Extract Beats & Prompts
        extracted_images, expected_count = self._extract_beat_items(prompt_paragraphs)
        
        # 4. Calculate Confidence Score
        confidence = ConfidenceEvaluator.evaluate(extracted_images, expected_count)
        
        payload = {
            "project_name": project_name,
            "source_file": path.name,
            "total_prompts": len(extracted_images),
            "default_aspect_ratio": "16:9",
            "default_model": "nano_banana",
            "images": extracted_images
        }
        
        logger.info(f"DeterministicParser: Extracted {len(extracted_images)} prompt items. Confidence: {confidence:.2f}")
        return payload, confidence

    def _read_docx_paragraphs(self, path: Path) -> List[str]:
        """Extracts text lines from word/document.xml inside docx zip container."""
        paragraphs = []
        with zipfile.ZipFile(path) as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("Corrupted DOCX package: missing word/document.xml")
            xml_content = z.read("word/document.xml")

        root = ET.fromstring(xml_content)
        for p in root.iter(f"{{{WORD_NS['w']}}}p"):
            texts = [
                t.text for t in p.iter(f"{{{WORD_NS['w']}}}t") if t.text
            ]
            if texts:
                paragraphs.append("".join(texts).strip())
        return paragraphs

    def _isolate_image_prompts_section(self, paragraphs: List[str]) -> List[str]:
        """Locates the true Section 5 Image Prompts body, bypassing TOC and notes."""
        start_idx = 0
        end_idx = len(paragraphs)

        # 1. Find section start: Look for "5 · Image Prompts" header or first "BEAT 1 —" after line 50
        for idx in range(50, len(paragraphs)):
            p = paragraphs[idx]
            if re.match(r"^5\s*[\·\-\—]\s*Image\s+Prompts", p, re.IGNORECASE) or p.startswith("BEAT 1 —"):
                start_idx = idx
                break

        # 2. Find section end: Look for "6 · Motion Specifications" or "Section 6" after start_idx
        for idx in range(start_idx + 1, len(paragraphs)):
            p = paragraphs[idx]
            if re.match(r"^6\s*[\·\-\—]\s*Motion", p, re.IGNORECASE) or p.startswith("6 · Motion") or p.startswith("Section 6"):
                end_idx = idx
                break

        isolated = paragraphs[start_idx:end_idx]
        logger.debug(f"Isolated prompt section: lines {start_idx} to {end_idx} ({len(isolated)} paragraphs).")
        return isolated

    def _extract_project_title(self, paragraphs: List[str]) -> str:
        """Extracts project title from top document paragraphs."""
        for p in paragraphs[:10]:
            if "Production Package" in p or "Series" in p or len(p) < 60:
                clean_title = p.replace("Production Package", "").strip()
                if clean_title:
                    return clean_title
        return "Google Flow Image Generation Job"

    def _extract_beat_items(self, paragraphs: List[str]) -> Tuple[List[Dict[str, Any]], int]:
        """Parses paragraph list into structured beat prompt specifications."""
        items: List[Dict[str, Any]] = []
        current_beat: Optional[Dict[str, Any]] = None
        expected_count = 120

        for p in paragraphs:
            beat_match = self.BEAT_HEADER_REGEX.match(p)
            if beat_match:
                if current_beat:
                    self._finalize_beat(current_beat)
                    items.append(current_beat)

                seq_num = int(beat_match.group(1))
                time_code = beat_match.group(2).strip()
                current_beat = {
                    "sequence": seq_num,
                    "time_code": time_code,
                    "script_cue": "",
                    "prompt": "",
                    "aspect_ratio": "16:9",
                    "model": "nano_banana",
                    "count": 1,
                    "metadata": {
                        "camera": "",
                        "lighting": "",
                        "mood": "",
                        "action": "",
                        "palette": ""
                    },
                    "_prompt_lines": []
                }
                continue

            if not current_beat:
                continue

            script_match = self.SCRIPT_CUE_REGEX.match(p)
            if script_match:
                current_beat["script_cue"] = script_match.group(1).strip()
                continue

            meta_match = self.METADATA_KEY_REGEX.match(p)
            if meta_match:
                key = meta_match.group(1).lower()
                val = meta_match.group(2).strip()
                current_beat["metadata"][key] = val
                continue

            if not p.startswith("Section ") and not p.startswith("BEAT "):
                current_beat["_prompt_lines"].append(p)

        if current_beat:
            self._finalize_beat(current_beat)
            items.append(current_beat)

        return items, expected_count

    def _finalize_beat(self, beat: Dict[str, Any]) -> None:
        lines = beat.pop("_prompt_lines", [])
        raw_prompt = " ".join(lines).strip()
        clean_prompt = re.sub(r"\s+", " ", raw_prompt)
        beat["prompt"] = clean_prompt
