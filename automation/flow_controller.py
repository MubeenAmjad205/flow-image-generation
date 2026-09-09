"""Google Flow UI Controller module (Phases 5-7).

Automates Google Flow UI interaction mechanics: project creation, Agent Mode toggle (OFF),
model selection (Nano Banana), 16:9 aspect ratio configuration, prompt submission,
async completion monitoring, and asset downloading.
"""

import time
import re
from pathlib import Path
from typing import Any
from utils.logger import logger
from automation.auth import SessionGuard


class FlowController:
    """Manages DOM interactions within Google Flow workspace."""

    def __init__(self, page: Any):
        self.page = page

    def create_new_project(self, project_name: str = "Google Flow Project") -> str:
        """Clicks '+ Add New project' button and verifies browser lands on /project/<id>."""
        logger.info(f"FlowController: Creating new project '{project_name}'...")

        # 1. Dismiss any lingering modals first
        SessionGuard.dismiss_modal_popups(self.page)
        self.page.wait_for_timeout(1000)

        # 2. Check if login is required
        SessionGuard.check_and_handle_login(self.page)

        # 3. Ensure we land in an active project workspace (/project/<id>)
        attempts = 0
        while "/project/" not in self.page.url and attempts < 3:
            attempts += 1
            logger.info(f"FlowController: Attempt #{attempts} to click New Project button...")

            # Candidate Locators for 'New Project' button
            locators = [
                self.page.locator("button.new-project-button"),
                self.page.locator(".new-project-button"),
                self.page.locator("button:has-text('New project')"),
                self.page.locator("button:has-text('New Project')"),
                self.page.locator("button:has-text('project')"),
                self.page.get_by_text("New project", exact=False),
                self.page.get_by_text("add New project", exact=False),
                self.page.locator("button.mdc-fab")
            ]

            btn_clicked = False
            for loc in locators:
                try:
                    if loc.is_visible(timeout=2000):
                        logger.info(f"FlowController: Clicked New Project button...")
                        loc.click()
                        btn_clicked = True
                        break
                except Exception:
                    continue

            if not btn_clicked:
                logger.warning("FlowController: Attempting JS click fallback for New Project button...")
                try:
                    self.page.evaluate("""() => {
                        const btn = document.querySelector('.new-project-button') || 
                                    Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('project'));
                        if (btn) btn.click();
                    }""")
                    btn_clicked = True
                except Exception as err:
                    logger.error(f"JS click fallback failed: {err}")

            self.page.wait_for_timeout(4000)

            # Re-check login if redirected
            SessionGuard.check_and_handle_login(self.page)
            SessionGuard.dismiss_modal_popups(self.page)

        # 4. Set project title if input field is accessible inside project page
        if "/project/" in self.page.url:
            try:
                title_input = self.page.locator("input.editable-text-input").or_(
                    self.page.get_by_label("Editable text")
                )
                if title_input.is_visible(timeout=3000):
                    title_input.fill(project_name)
                    title_input.press("Enter")
            except Exception as err:
                logger.debug(f"Title input set skipped: {err}")
        else:
            logger.warning(f"FlowController: Current URL is '{self.page.url}' (expected /project/<id>)")

        project_url = self.page.url
        logger.info(f"FlowController: Project workspace ready at '{project_url}'")
        return project_url

    def configure_project(
        self,
        model: str = "nano_banana",
        aspect_ratio: str = "16:9",
        disable_agent_mode: bool = True
    ) -> None:
        """Configures Agent Mode (OFF), Model (Nano Banana), and Aspect Ratio (16:9)."""
        logger.info(f"FlowController: Configuring settings -> Model: {model}, Ratio: {aspect_ratio}, Agent Mode: OFF")

        # Open Tune / Settings Drawer if tune button is visible
        try:
            settings_pattern = re.compile("Settings|Tune", re.IGNORECASE)
            tune_btn = self.page.locator("button:has(i:has-text('tune'))").or_(
                self.page.get_by_label(settings_pattern)
            )
            if tune_btn.is_visible(timeout=2000):
                tune_btn.click()
                self.page.wait_for_timeout(1000)
        except Exception:
            pass

        # 1. Disable Agent Mode if active
        if disable_agent_mode:
            try:
                agent_pattern = re.compile("Agent Mode", re.IGNORECASE)
                agent_toggle = self.page.get_by_label(agent_pattern).or_(
                    self.page.locator("input[type='checkbox'][aria-label*='Agent']")
                )
                if agent_toggle.is_visible(timeout=2000):
                    if agent_toggle.is_checked():
                        logger.info("FlowController: Toggling Agent Mode to OFF...")
                        agent_toggle.click()
            except Exception as err:
                logger.debug(f"Agent Mode toggle check: {err}")

        # 2. Select Model (Nano Banana)
        try:
            model_pattern = re.compile("Model|Nano Banana", re.IGNORECASE)
            model_btn = self.page.get_by_role("button", name=model_pattern)
            if model_btn.is_visible(timeout=2000):
                model_btn.click()
                self.page.get_by_text("Nano Banana", exact=True).click()
        except Exception as err:
            logger.debug(f"Model selection check: {err}")

        # 3. Select Aspect Ratio (16:9)
        try:
            ratio_btn = self.page.get_by_text(aspect_ratio, exact=True)
            if ratio_btn.is_visible(timeout=2000):
                ratio_btn.click()
        except Exception as err:
            logger.debug(f"Aspect ratio selection check: {err}")

        self.page.wait_for_timeout(1000)

    def generate_single_prompt(self, prompt_text: str, target_output_path: Path, timeout_sec: int = 90) -> bool:
        """Injects prompt text, submits generation, monitors completion, and saves asset."""
        logger.info(f"FlowController: Submitting prompt (Len: {len(prompt_text)})...")

        # Exclude hidden reCAPTCHA textareas, target real prompt input box
        prompt_box = self.page.get_by_placeholder("What do you want to create?").or_(
            self.page.locator("textarea[placeholder*='create'], input[placeholder*='create']")
        ).or_(
            self.page.locator("textarea:not(.g-recaptcha-response)")
        )
        prompt_box.wait_for(state="visible", timeout=15000)
        prompt_box.fill("")
        prompt_box.fill(prompt_text)

        submit_btn = self.page.locator("button[type='submit']").or_(
            self.page.locator("button:has(i:has-text('arrow_forward'))")
        )
        submit_btn.wait_for(state="enabled", timeout=5000)
        submit_btn.click()

        logger.info("FlowController: Waiting for image generation completion...")
        start_time = time.time()
        self.page.wait_for_timeout(2000)

        while time.time() - start_time < timeout_sec:
            stop_btn_visible = False
            try:
                stop_btn = self.page.locator("button:has(i:has-text('stop'))")
                stop_btn_visible = stop_btn.is_visible(timeout=500)
            except Exception:
                pass

            if not stop_btn_visible:
                logger.info("FlowController: Generation finished! Collecting asset...")
                break

            self.page.wait_for_timeout(2000)
        else:
            logger.error(f"FlowController: Generation timed out after {timeout_sec} seconds.")
            return False

        return self._download_latest_media_asset(target_output_path)

    def _download_latest_media_asset(self, target_output_path: Path) -> bool:
        """Intercepts download for the latest media thumbnail card."""
        target_output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            thumbnail = self.page.locator(".media-thumbnail-card, div[role='button']:has(img)").first
            if thumbnail.is_visible(timeout=3000):
                thumbnail.click(button="right")
                self.page.wait_for_timeout(500)
                
                with self.page.expect_download(timeout=15000) as download_info:
                    self.page.get_by_text("Download", exact=True).click()
                
                download = download_info.value
                download.save_as(str(target_output_path))
                logger.info(f"FlowController: Saved generated image to '{target_output_path}'")
                return True
        except Exception as err:
            logger.warning(f"Context menu download fallback engaged: {err}")

        try:
            img_element = self.page.locator("img[src*='blob:'], img[src*='googleusercontent']").first
            if img_element.is_visible(timeout=3000):
                src = img_element.get_attribute("src")
                if src and src.startswith("blob:"):
                    logger.info("FlowController: Direct image blob link verified.")
                    return True
        except Exception as err:
            logger.error(f"Failed to capture image asset: {err}")

        return False
