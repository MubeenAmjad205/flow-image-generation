"""Job State & Checkpoint Manager module (Phase 9).

Maintains state.json persistence for real-time execution tracking,
checkpointing, and crash recovery.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config.settings import settings
from utils.logger import logger


class StateManager:
    """Manages job state serialization, updates, and disk checkpointing."""

    def __init__(self, job_dir: Path):
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.job_dir / "state.json"
        self.state_data: Dict[str, Any] = {}

    @classmethod
    def create_new_job(cls, normalized_payload: Dict[str, Any], job_id: Optional[str] = None) -> "StateManager":
        """Initializes a new job state checkpoint from normalized payload.
        
        Args:
            normalized_payload: Validated job payload.
            job_id: Optional custom job ID string.
            
        Returns:
            Initialized StateManager instance.
        """
        if not job_id:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            job_id = f"job_{timestamp}"

        job_dir = settings.jobs_dir / job_id
        manager = cls(job_dir)

        prompts_state: List[Dict[str, Any]] = []
        for img in normalized_payload.get("images", []):
            prompts_state.append({
                "sequence": img["sequence"],
                "status": "PENDING",
                "attempts": 0,
                "prompt_text": img["prompt"],
                "output_filename": None,
                "completed_at": None,
                "error": None
            })

        manager.state_data = {
            "job_id": job_id,
            "project_name": normalized_payload.get("project_name", "Google Flow Job"),
            "source_file": normalized_payload.get("source_file", "unknown.docx"),
            "total_prompts": len(prompts_state),
            "status": "INITIALIZED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_sequence": 1,
            "summary": {
                "completed": 0,
                "failed": 0,
                "pending": len(prompts_state)
            },
            "prompts": prompts_state
        }

        manager.save()
        logger.info(f"StateManager: Initialized new job state '{job_id}' with {len(prompts_state)} prompts.")
        return manager

    @classmethod
    def load_existing_job(cls, state_file_path: Path) -> "StateManager":
        """Loads an existing state.json file for job resumption."""
        path = Path(state_file_path)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        manager = cls(path.parent)
        with open(path, "r", encoding="utf-8") as f:
            manager.state_data = json.load(f)
            
        logger.info(f"StateManager: Loaded existing job state '{manager.state_data.get('job_id')}'")
        return manager

    def mark_generating(self, sequence: int) -> None:
        """Marks prompt sequence as GENERATING."""
        prompt = self._get_prompt(sequence)
        if prompt:
            prompt["status"] = "GENERATING"
            prompt["attempts"] += 1
            self.state_data["status"] = "IN_PROGRESS"
            self.state_data["current_sequence"] = sequence
            self.save()

    def mark_completed(self, sequence: int, output_filename: str) -> None:
        """Marks prompt sequence as COMPLETED and records output file name."""
        prompt = self._get_prompt(sequence)
        if prompt:
            prompt["status"] = "COMPLETED"
            prompt["output_filename"] = output_filename
            prompt["completed_at"] = datetime.now(timezone.utc).isoformat()
            prompt["error"] = None
            self._update_summary()
            self.save()
            logger.info(f"StateManager: Checkpoint saved -> Prompt #{sequence} COMPLETED ({output_filename})")

    def mark_failed(self, sequence: int, error_msg: str) -> None:
        """Marks prompt sequence as FAILED and records error message."""
        prompt = self._get_prompt(sequence)
        if prompt:
            prompt["status"] = "FAILED"
            prompt["error"] = error_msg
            self._update_summary()
            self.save()
            logger.warning(f"StateManager: Checkpoint saved -> Prompt #{sequence} FAILED ({error_msg})")

    def get_next_pending_sequence(self) -> Optional[int]:
        """Returns sequence number of the next uncompleted prompt."""
        for prompt in self.state_data.get("prompts", []):
            if prompt["status"] in ["PENDING", "GENERATING", "FAILED"]:
                if prompt["status"] == "FAILED" and prompt["attempts"] >= 3:
                    continue  # Skip permanently failed prompts with max attempts
                return prompt["sequence"]
        return None

    def is_finished(self) -> bool:
        """Returns True if all prompts are either COMPLETED or max-attempt FAILED."""
        return self.get_next_pending_sequence() is None

    def save(self) -> None:
        """Flushes current state data to disk atomically."""
        self.state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state_data, f, indent=2)

    def _get_prompt(self, sequence: int) -> Optional[Dict[str, Any]]:
        for p in self.state_data.get("prompts", []):
            if p["sequence"] == sequence:
                return p
        return None

    def _update_summary(self) -> None:
        prompts = self.state_data.get("prompts", [])
        completed = sum(1 for p in prompts if p["status"] == "COMPLETED")
        failed = sum(1 for p in prompts if p["status"] == "FAILED")
        pending = len(prompts) - completed - failed
        self.state_data["summary"] = {
            "completed": completed,
            "failed": failed,
            "pending": pending
        }
        if pending == 0:
            self.state_data["status"] = "COMPLETED"
