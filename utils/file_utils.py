"""File & Archiving Utilities module (Phase 8).

Manages sequential asset renaming, slug generation, summary JSON generation,
and output ZIP package archiving.
"""

import json
import re
import zipfile
from pathlib import Path
from typing import Dict, Any, List
from utils.logger import logger


class FileUtils:
    """Helper utilities for asset renaming and ZIP packaging."""

    @staticmethod
    def slugify(text: str, max_length: int = 30) -> str:
        """Converts text string into safe filename slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text[:max_length].strip("-") or "image"

    @staticmethod
    def format_sequence_filename(sequence: int, prompt_text: str, extension: str = "png") -> str:
        """Formats sequential image filename e.g. 01-hand-drawn-2d-cartoon.png."""
        seq_str = f"{sequence:02d}"
        slug = FileUtils.slugify(prompt_text)
        return f"{seq_str}-{slug}.{extension}"

    @classmethod
    def package_job_output(
        cls,
        job_dir: Path,
        images_dir: Path,
        summary_payload: Dict[str, Any],
        output_zip_path: Path
    ) -> Path:
        """Bundles output image files and summary.json into a ZIP package.
        
        Args:
            job_dir: Job directory path.
            images_dir: Directory containing generated PNG image assets.
            summary_payload: Summary stats dict.
            output_zip_path: Path for generated ZIP archive.
            
        Returns:
            Path to created ZIP archive.
        """
        output_zip_path.parent.mkdir(parents=True, exist_ok=True)
        summary_file = job_dir / "summary.json"

        # 1. Save summary.json
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)

        # 2. Build ZIP package
        logger.info(f"FileUtils: Packaging job output to '{output_zip_path.name}'...")
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            # Add summary.json
            z.write(summary_file, arcname="summary.json")

            # Add all image files in images_dir
            if images_dir.exists():
                for img_file in sorted(images_dir.glob("*.png")):
                    z.write(img_file, arcname=f"images/{img_file.name}")

        logger.info(f"FileUtils: ZIP package created successfully ({output_zip_path.stat().st_size / 1024:.1f} KB)")
        return output_zip_path
