"""Main Entrypoint Orchestrator for Google Flow Image Generation Automation.

Usage:
    uv run python3 main.py --input "Day13_Production_Package - Copy.docx"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

from config.settings import settings
from utils.logger import logger
from extractor.deterministic import DeterministicParser
from extractor.llm_fallback import LLMFallbackExtractor
from validator.normalizer import DataNormalizer
from validator.schema_validator import SchemaValidator
from state.manager import StateManager
from automation.stealth import StealthBrowserManager
from automation.auth import SessionGuard
from automation.flow_controller import FlowController
from automation.cookie_manager import CookieManager
from utils.file_utils import FileUtils


from typing import Optional

def run_pipeline(docx_path: str, headless: bool = False, resume: bool = True, use_cookies: bool = False, batch_size: int = 1, limit: Optional[int] = None) -> None:
    """Executes the complete Google Flow image generation pipeline.
    
    Args:
        docx_path: Path to DOCX production package file.
        headless: Whether to run browser headlessly.
        resume: Whether to resume existing job checkpoint if present.
        use_cookies: Whether to force injection of cookies.json into context.
        batch_size: Number of prompts to submit per batch.
        limit: Optional maximum number of prompts to process (useful for testing).
    """
    logger.info(f"=== STARTING GOOGLE FLOW IMAGE AUTOMATION PIPELINE ===")
    docx_file = Path(docx_path)
    if not docx_file.exists():
        logger.error(f"Input file not found: {docx_file}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 1 & 3: Document Extraction (Deterministic Primary -> LLM Fallback)
    # -------------------------------------------------------------------------
    det_parser = DeterministicParser()
    raw_payload, confidence = det_parser.parse(str(docx_file))

    if confidence < settings.extraction_confidence_threshold:
        logger.warning(f"Confidence score {confidence:.2f} < {settings.extraction_confidence_threshold}. Triggering LLM Fallback...")
        llm_parser = LLMFallbackExtractor()
        with open(docx_file, "rb") as f:
            raw_lines = [line.decode("utf-8", errors="ignore") for line in f.readlines()]
        raw_payload, confidence = llm_parser.extract(raw_lines, docx_file.name)

    # -------------------------------------------------------------------------
    # PHASE 2: Data Normalization & Schema Validation
    # -------------------------------------------------------------------------
    normalized_payload = DataNormalizer.normalize(raw_payload)
    validator = SchemaValidator()
    is_valid, error_msg = validator.validate(normalized_payload)

    if not is_valid:
        logger.error(f"Pipeline halted due to schema validation failure: {error_msg}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 9: State Management & Resumable Checkpoint Setup
    # -------------------------------------------------------------------------
    import json
    existing_jobs = []
    for d in settings.jobs_dir.glob(f"job_{docx_file.stem}_*"):
        st_file = d / "state.json"
        if st_file.exists():
            try:
                with open(st_file, "r") as f:
                    data = json.load(f)
                    completed = data.get("summary", {}).get("completed", 0)
                    existing_jobs.append((completed, d.stat().st_mtime, d))
            except Exception:
                pass

    if resume and existing_jobs:
        existing_jobs.sort(key=lambda x: (x[0], x[1]), reverse=True)
        job_dir = existing_jobs[0][2]
        job_id = job_dir.name
        state_file = job_dir / "state.json"
        state_mgr = StateManager.load_existing_job(state_file)
        logger.info(f"Resuming existing job checkpoint: '{job_id}' ({state_mgr.state_data.get('summary', {})})")
    else:
        job_id = f"job_{docx_file.stem}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        job_dir = settings.jobs_dir / job_id
        state_mgr = StateManager.create_new_job(normalized_payload, job_id=job_id)

    images_output_dir = settings.output_dir / job_id / "images"
    images_output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # PHASE 4: Stealth Browser & Manual Session Audit
    # -------------------------------------------------------------------------
    browser_context = StealthBrowserManager.launch_playwright_stealth(
        user_data_dir=settings.profiles_dir,
        headless=headless
    )

    # Inject raw cookies ONLY if explicitly requested via --use-cookies flag
    if use_cookies:
        CookieManager.load_cookies_into_context(browser_context)

    page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

    if not SessionGuard.audit_and_clear_popups(page):
        logger.error("Session authentication failed. Exiting pipeline.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 5: Google Flow UI Initialization & Project Setup
    # -------------------------------------------------------------------------
    flow = FlowController(page)
    flow.create_new_project(project_name=normalized_payload["project_name"])
    flow.configure_project(
        model=normalized_payload["default_model"],
        aspect_ratio=normalized_payload["default_aspect_ratio"],
        disable_agent_mode=True
    )

    # -------------------------------------------------------------------------
    # PHASES 6 & 7: Batch Prompt Execution Loop
    # -------------------------------------------------------------------------
    prompts_list = normalized_payload["images"]
    if limit and limit > 0:
        logger.info(f"Limiting execution to first {limit} prompts for testing.")
        prompts_list = prompts_list[:limit]
    total_prompts = len(prompts_list)

    if batch_size > 1:
        logger.info(f"FlowController: Operating in BATCH MODE (Batch size: {batch_size})")
        pending_items = []
        for item in prompts_list:
            seq = item["sequence"]
            prompt_text = item["prompt"]
            fn = FileUtils.format_sequence_filename(seq, prompt_text)
            target_path = images_output_dir / fn

            p_state = state_mgr._get_prompt(seq)
            if p_state and p_state["status"] == "COMPLETED" and target_path.exists() and target_path.stat().st_size > 5000:
                logger.info(f"Prompt #{seq}/{total_prompts} already COMPLETED ({target_path.stat().st_size} bytes). Skipping.")
                continue
            pending_items.append(item)

        for i in range(0, len(pending_items), batch_size):
            chunk = pending_items[i:i + batch_size]
            chunk_prompts = [item["prompt"] for item in chunk]
            chunk_targets = []
            for item in chunk:
                seq = item["sequence"]
                fn = FileUtils.format_sequence_filename(seq, item["prompt"])
                chunk_targets.append(images_output_dir / fn)
                state_mgr.mark_generating(seq)

            results = flow.generate_batch_prompts(chunk_prompts, chunk_targets)
            for idx, item in enumerate(chunk):
                seq = item["sequence"]
                fn = FileUtils.format_sequence_filename(seq, item["prompt"])
                if idx < len(results) and results[idx]:
                    state_mgr.mark_completed(seq, output_filename=fn)
                else:
                    state_mgr.mark_failed(seq, error_msg="Batch generation or download failed")
    else:
        for item in prompts_list:
            seq = item["sequence"]
            prompt_text = item["prompt"]

            filename = FileUtils.format_sequence_filename(seq, prompt_text)
            target_path = images_output_dir / filename

            p_state = state_mgr._get_prompt(seq)
            if p_state and p_state["status"] == "COMPLETED" and target_path.exists() and target_path.stat().st_size > 5000:
                logger.info(f"Prompt #{seq}/{total_prompts} already COMPLETED ({target_path.stat().st_size} bytes). Skipping.")
                continue

            state_mgr.mark_generating(seq)
            success = flow.generate_single_prompt(prompt_text, target_output_path=target_path)

            if success:
                state_mgr.mark_completed(seq, output_filename=filename)
            else:
                state_mgr.mark_failed(seq, error_msg="Generation or download timed out")

    # Save active session storage state to disk natively
    CookieManager.save_storage_state(browser_context)

    # -------------------------------------------------------------------------
    # PHASE 8: Summary Generation & Output ZIP Packaging
    # -------------------------------------------------------------------------
    summary_payload = {
        "job_id": job_id,
        "project_name": normalized_payload["project_name"],
        "total_prompts": total_prompts,
        "summary": state_mgr.state_data.get("summary", {}),
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    
    zip_path = settings.output_dir / f"{job_id}.zip"
    FileUtils.package_job_output(
        job_dir=job_dir,
        images_dir=images_output_dir,
        summary_payload=summary_payload,
        output_zip_path=zip_path
    )

    logger.info(f"=== GOOGLE FLOW AUTOMATION PIPELINE COMPLETED SUCCESSFULLY ===")
    logger.info(f"Output ZIP Package: {zip_path}")


def main():
    parser = argparse.ArgumentParser(description="Google Flow Image Generation Automation Pipeline")
    parser.add_argument(
        "--input", "-i",
        default="Day13_Production_Package - Copy.docx",
        help="Path to DOCX production package"
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Do not resume existing checkpoint")
    parser.add_argument("--use-cookies", action="store_true", help="Force raw JSON cookie injection from cookies.json")
    parser.add_argument("--batch-size", "-b", type=int, default=1, help="Number of prompts to submit per batch (default: 1)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limit execution to first N prompts for testing")

    args = parser.parse_args()
    run_pipeline(
        docx_path=args.input,
        headless=args.headless,
        resume=args.resume,
        use_cookies=args.use_cookies,
        batch_size=args.batch_size,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
