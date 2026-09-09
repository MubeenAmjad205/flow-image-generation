"""Google Flow UI Controller module (Phases 5-7).

Automates Google Flow UI interaction mechanics: project creation, Agent Mode toggle (OFF),
model selection (Nano Banana), 16:9 aspect ratio configuration, prompt submission,
async completion monitoring, and asset downloading.
"""

import time
import re
import base64
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

    def _get_media_image_sources(self) -> List[str]:
        """Extracts valid generated image asset URLs across img tags, SVG images, and CSS background-images."""
        try:
            return self.page.evaluate(r"""() => {
                const urls = new Set();
                // 1. Standard img tags
                document.querySelectorAll('img').forEach(e => {
                    if (e.src) urls.add(e.src);
                });
                // 2. SVG image elements
                document.querySelectorAll('image').forEach(e => {
                    const href = e.getAttribute('href') || e.getAttribute('xlink:href');
                    if (href) urls.add(href);
                });
                // 3. Background image styles
                document.querySelectorAll('*').forEach(e => {
                    try {
                        const bg = window.getComputedStyle(e).backgroundImage;
                        if (bg && bg.includes('url(')) {
                            const match = bg.match(/url\(["']?(.*?)["']?\)/);
                            if (match && match[1]) urls.add(match[1]);
                        }
                    } catch (err) {}
                });

                return [...urls].filter(src => {
                    if (!src) return false;
                    if (src.includes('/ogw/') || src.includes('avatar') || src.includes('favicon')) return false;
                    return src.startsWith('blob:') || (src.includes('googleusercontent') && !src.includes('/ogw/'));
                });
            }""")
        except Exception as err:
            logger.debug(f"Media extraction error: {err}")
            return []

    def generate_single_prompt(self, prompt_text: str, target_output_path: Path, timeout_sec: int = 90) -> bool:
        """Injects prompt text into ProseMirror contenteditable editor, submits generation, and saves asset."""
        logger.info(f"FlowController: Submitting prompt (Len: {len(prompt_text)})...")

        # Snapshot existing image URLs on page before submitting
        initial_sources = set()
        try:
            initial_sources = set(self._get_media_image_sources())
        except Exception:
            pass

        # 1. Locate ProseMirror contenteditable editor
        prompt_box = self.page.locator(".ProseMirror, [contenteditable='true']").first
        prompt_box.wait_for(state="visible", timeout=15000)
        prompt_box.click()

        # Fill text via Playwright or JS evaluate to trigger ProseMirror input events cleanly
        try:
            prompt_box.fill(prompt_text)
        except Exception:
            self.page.evaluate("""(text) => {
                const el = document.querySelector('.ProseMirror') || document.querySelector('[contenteditable="true"]');
                if (el) {
                    el.innerText = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""", prompt_text)

        self.page.wait_for_timeout(500)

        # 2. Click Submit / Generate button or fallback to pressing Enter
        submitted = False
        submit_selectors = [
            "button:has(i:has-text('arrow_forward')):visible",
            "button:has(i:has-text('arrow_upward')):visible",
            "button:has(i:has-text('send')):visible",
            "button[aria-label*='Submit']:visible",
            "button[aria-label*='Generate']:visible",
            "button.flow-button-primary:visible:not(.settings-trigger-button)",
            "button[type='submit']:visible",
        ]
        
        for selector in submit_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    submitted = True
                    logger.info(f"FlowController: Clicked submit button matching '{selector}'.")
                    break
            except Exception:
                continue

        if not submitted:
            logger.info("FlowController: No explicit visible submit button found; pressing Enter on prompt box...")
            prompt_box.press("Enter")

        logger.info("FlowController: Waiting for image generation completion...")
        self.page.wait_for_timeout(5000)

        start_time = time.time()
        target_img_src = None

        while time.time() - start_time < (timeout_sec - 10):
            # Check for explicit failure card in Google Flow DOM
            try:
                fail_card = self.page.locator(
                    "text='Sorry, this image failed to generate.'"
                ).or_(
                    self.page.locator("text='Failed'").filter(has_text="not been charged")
                )
                if fail_card.is_visible(timeout=500):
                    logger.error("FlowController: Google Flow reported generation failure: 'Sorry, this image failed to generate.'")
                    try:
                        trash_btn = self.page.locator("button:has(i:has-text('delete')), button:has(mat-icon:has-text('delete'))").first
                        if trash_btn.is_visible(timeout=500):
                            trash_btn.click()
                    except Exception:
                        pass
                    return False
            except Exception:
                pass

            try:
                current_sources = self._get_media_image_sources()
                new_imgs = [s for s in current_sources if s not in initial_sources]

                is_loading = False
                try:
                    loader = self.page.locator("button:has(i:has-text('stop')), .mat-mdc-progress-spinner, [role='progressbar']")
                    is_loading = loader.is_visible(timeout=300)
                except Exception:
                    pass

                if new_imgs and not is_loading:
                    target_img_src = new_imgs[-1]
                    logger.info(f"FlowController: Generation finished! Captured asset src: {target_img_src[:60]}...")
                    break
                elif not initial_sources and current_sources and not is_loading:
                    target_img_src = current_sources[-1]
                    logger.info(f"FlowController: Generation finished! Captured asset src: {target_img_src[:60]}...")
                    break
            except Exception:
                pass

            self.page.wait_for_timeout(2000)

        if not target_img_src:
            logger.error(f"FlowController: Generation timed out after {timeout_sec} seconds.")
            return False

        return self._save_image_src_to_path(target_img_src, target_output_path)

    def _save_image_src_to_path(self, img_src: str, target_output_path: Path) -> bool:
        """Downloads or extracts image data from URL or blob and writes cleanly to file."""
        target_output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if img_src.startswith("blob:"):
                logger.info("FlowController: Fetching image data from blob URL...")
                b64_data = self.page.evaluate("""async (url) => {
                    const resp = await fetch(url);
                    const blob = await resp.blob();
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                }""", img_src)

                if b64_data and "," in b64_data:
                    header, encoded = b64_data.split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                    target_output_path.write_bytes(image_bytes)
                    logger.info(f"FlowController: Successfully saved generated image ({len(image_bytes)} bytes) to '{target_output_path}'")
                    return True
            elif img_src.startswith("http"):
                logger.info("FlowController: Downloading image from HTTP URL...")
                response = self.page.request.get(img_src)
                if response.ok:
                    target_output_path.write_bytes(response.body())
                    logger.info(f"FlowController: Successfully saved generated image ({len(response.body())} bytes) to '{target_output_path}'")
                    return True
        except Exception as err:
            logger.error(f"FlowController: Direct image save failed for '{img_src[:60]}': {err}")

        # Fallback context menu download attempt
        return self._download_latest_media_asset(target_output_path)

    def _download_latest_media_asset(self, target_output_path: Path) -> bool:
        """Fallback method: Intercepts download for the latest media thumbnail card."""
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

        return False

    def generate_batch_prompts(
        self,
        prompts: List[str],
        target_output_paths: List[Path],
        timeout_sec: int = 300
    ) -> List[bool]:
        """Submits multiple quoted prompts in a single batch to trigger parallel generation."""
        logger.info(f"FlowController: Submitting batch of {len(prompts)} prompts...")

        combined_text = "\n\n".join([f'"{p.strip()}"' for p in prompts])

        initial_sources = set()
        try:
            initial_sources = set(self._get_media_image_sources())
        except Exception:
            pass

        prompt_box = self.page.locator(".ProseMirror, [contenteditable='true']").first
        prompt_box.wait_for(state="visible", timeout=15000)
        prompt_box.click()
        prompt_box.focus()

        try:
            self.page.keyboard.press("Meta+A")
            self.page.keyboard.press("Backspace")
        except Exception:
            pass

        try:
            # keyboard.insert_text simulates direct paste/input in contenteditable, preserving newlines
            self.page.keyboard.insert_text(combined_text)
        except Exception:
            try:
                prompt_box.fill(combined_text)
            except Exception:
                self.page.evaluate("""(text) => {
                    const el = document.querySelector('.ProseMirror') || document.querySelector('[contenteditable="true"]');
                    if (el) {
                        el.innerText = text;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", combined_text)

        self.page.wait_for_timeout(1000)

        submitted = False
        submit_selectors = [
            "button:has(i:has-text('arrow_forward')):visible",
            "button:has(i:has-text('arrow_upward')):visible",
            "button:has(i:has-text('send')):visible",
            "button[aria-label*='Submit']:visible",
            "button[aria-label*='Generate']:visible",
            "button.flow-button-primary:visible:not(.settings-trigger-button)",
            "button[type='submit']:visible",
        ]

        for selector in submit_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    submitted = True
                    logger.info(f"FlowController: Clicked submit button matching '{selector}'.")
                    break
            except Exception:
                continue

        if not submitted:
            logger.info("FlowController: Pressing Enter on prompt box for batch...")
            prompt_box.press("Enter")

        logger.info(f"FlowController: Waiting for batch generation of {len(prompts)} assets...")
        self.page.wait_for_timeout(5000)

        start_time = time.time()
        results = [False] * len(prompts)

        while time.time() - start_time < timeout_sec:
            try:
                current_sources = self._get_media_image_sources()
                new_imgs = [s for s in current_sources if s not in initial_sources]

                is_loading = False
                try:
                    loader = self.page.locator("button:has(i:has-text('stop')), .mat-mdc-progress-spinner, [role='progressbar']")
                    is_loading = loader.is_visible(timeout=300)
                except Exception:
                    pass

                is_idle = False
                try:
                    submit_btn = self.page.locator("button:has(i:has-text('arrow_forward')):visible, button:has(i:has-text('send')):visible, button[type='submit']:visible").first
                    is_idle = submit_btn.is_visible(timeout=300)
                except Exception:
                    pass

                if new_imgs:
                    logger.info(f"FlowController: Batch progress -> {len(new_imgs)}/{len(prompts)} assets detected (IsLoading={is_loading}, IsIdle={is_idle})")

                if (len(new_imgs) >= len(prompts)) or (new_imgs and not is_loading and is_idle):
                    logger.info(f"FlowController: Batch generation completed early! Saving {len(new_imgs)} assets after {int(time.time() - start_time)}s...")
                    for idx, target_path in enumerate(target_output_paths):
                        if idx < len(new_imgs):
                            results[idx] = self._save_image_src_to_path(new_imgs[idx], target_path)
                    break
            except Exception:
                pass

            self.page.wait_for_timeout(2000)

        if not any(results):
            try:
                current_sources = self._get_media_image_sources()
                new_imgs = [s for s in current_sources if s not in initial_sources]
                if new_imgs:
                    logger.info(f"FlowController: Fallback saving {len(new_imgs)} batch assets...")
                    for idx, target_path in enumerate(target_output_paths):
                        if idx < len(new_imgs):
                            results[idx] = self._save_image_src_to_path(new_imgs[idx], target_path)
            except Exception:
                pass

        # Fallback for any uncompleted prompt items in batch: execute single prompt generation sequentially
        for idx, (p, target_path) in enumerate(zip(prompts, target_output_paths)):
            if not results[idx] or not target_path.exists() or target_path.stat().st_size <= 5000:
                logger.info(f"FlowController: Batch item #{idx+1} missing or invalid. Falling back to single prompt generation...")
                results[idx] = self.generate_single_prompt(p, target_path)

        return results
