"""Session Guard & Popup Dismissal module (Phase 4).

Verifies active Google Flow session, auto-dismisses onboarding modals,
and manages human-in-the-loop auth pause loops if session expires.
"""

import sys
import re
from typing import Any
from utils.logger import logger


class SessionGuard:
    """Audits session state and clears onboarding modal popups on Google Flow."""

    FLOW_URL = "https://flow.google.com"

    @classmethod
    def audit_and_clear_popups(cls, page: Any) -> bool:
        """Navigates to Google Flow, verifies auth, and dismisses modal overlays.
        
        Args:
            page: Playwright Page instance.
            
        Returns:
            True if session is valid and popups cleared.
        """
        logger.info(f"SessionGuard: Navigating to '{cls.FLOW_URL}'...")
        page.goto(cls.FLOW_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)

        # 1. Check for Cookie Mismatch or Login Redirect
        if cls.is_login_page(page):
            return cls._handle_expired_session(page)

        # 2. Clear Modal Popups (Terms, Privacy, Feature Changelog)
        cls.dismiss_modal_popups(page)

        logger.info("SessionGuard: Dashboard loaded successfully.")
        return True

    @classmethod
    def is_login_page(cls, page: Any) -> bool:
        """Returns True if browser is on sign-in, login, or cookie mismatch page."""
        url = page.url.lower()
        return any(k in url for k in ["accounts.google.com", "signin", "servicelogin", "cookiemismatch"])

    @classmethod
    def check_and_handle_login(cls, page: Any) -> bool:
        """Checks if browser landed on login page and prompts operator if needed."""
        page.wait_for_timeout(1000)
        if cls.is_login_page(page):
            logger.warning("SessionGuard: Redirected to Google Sign-In or CookieMismatch page. Operator login required.")
            return cls._handle_expired_session(page)
        return True

    @classmethod
    def dismiss_modal_popups(cls, page: Any) -> None:
        """Detects and clicks dismiss/continue buttons on modal overlays."""
        for pass_num in range(3):
            clicked = False
            
            # Modal Button 1: "Next"
            try:
                btn_next = page.get_by_role("button", name="Next").or_(page.locator("button:has-text('Next')"))
                if btn_next.is_visible(timeout=1500):
                    logger.info("SessionGuard: Dismissing modal -> Clicked 'Next'")
                    btn_next.click()
                    page.wait_for_timeout(1000)
                    clicked = True
            except Exception:
                pass

            # Modal Button 2: "Continue"
            try:
                btn_continue = page.get_by_role("button", name="Continue").or_(page.locator("button:has-text('Continue')"))
                if btn_continue.is_visible(timeout=1500):
                    logger.info("SessionGuard: Dismissing modal -> Clicked 'Continue'")
                    btn_continue.click()
                    page.wait_for_timeout(1000)
                    clicked = True
            except Exception:
                pass

            # Modal Button 3: "Get started"
            try:
                btn_get_started = page.get_by_role("button", name="Get started").or_(page.locator("button:has-text('Get started')"))
                if btn_get_started.is_visible(timeout=1500):
                    logger.info("SessionGuard: Dismissing modal -> Clicked 'Get started'")
                    btn_get_started.click()
                    page.wait_for_timeout(1000)
                    clicked = True
            except Exception:
                pass

            if not clicked:
                break

    @classmethod
    def _handle_expired_session(cls, page: Any) -> bool:
        """Pauses automation execution and alerts operator to complete login."""
        # If on CookieMismatch page, navigate to clean Google Sign-In
        if "cookiemismatch" in page.url.lower():
            logger.warning("SessionGuard: Clearing cookie mismatch screen -> Opening Google Sign-In...")
            page.goto("https://accounts.google.com/ServiceLogin?continue=https://flow.google.com", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

        alert_msg = (
            "\n" + "=" * 70 + "\n"
            "[ACTION REQUIRED] Google session login is required.\n"
            "The browser is currently open to the Google Sign-In page.\n\n"
            "1. Please log into your Google Account in the opened browser window.\n"
            "2. Complete any MFA / Security prompts.\n"
            "3. Once logged in and on the Google Flow dashboard, press ENTER here to resume.\n"
             + "=" * 70 + "\n"
        )
        sys.stdout.write(alert_msg)
        sys.stdout.flush()

        input("Press ENTER after completing Google login in the browser window...")
        
        page.goto(cls.FLOW_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)
        cls.dismiss_modal_popups(page)
        
        return not cls.is_login_page(page)
