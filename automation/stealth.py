"""Stealth Browser Manager module (Phase 4).

Configures undetected Chrome contexts to bypass bot detection,
`navigator.webdriver` flags, and Google reCAPTCHA challenges.
"""

from pathlib import Path
from typing import Optional, Any
from config.settings import settings
from utils.logger import logger


class StealthBrowserManager:
    """Manages stealth browser initialization with persistent user profiles."""

    @staticmethod
    def launch_playwright_stealth(
        user_data_dir: Optional[Path] = None,
        headless: bool = False
    ) -> Any:
        """Launches a Playwright Chromium persistent context configured with stealth arguments.
        
        Args:
            user_data_dir: Path to persistent profile directory.
            headless: Whether to run headlessly.
            
        Returns:
            Playwright BrowserContext instance.
        """
        profile_path = Path(user_data_dir or settings.profiles_dir)
        profile_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StealthBrowserManager: Launching Playwright Stealth context with profile '{profile_path}'...")
        
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            channel="chrome",
            headless=headless,
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage"
            ]
        )
        return context

    @staticmethod
    def launch_undetected_chrome(
        user_data_dir: Optional[Path] = None,
        headless: bool = False
    ) -> Any:
        """Launches undetected-chromedriver (UC) instance with patched Chrome V8 binary.
        
        Args:
            user_data_dir: Path to persistent profile directory.
            headless: Whether to run headlessly.
            
        Returns:
            undetected_chromedriver.Chrome driver instance.
        """
        profile_path = Path(user_data_dir or settings.profiles_dir)
        profile_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"StealthBrowserManager: Launching Undetected ChromeDriver with profile '{profile_path}'...")
        
        import undetected_chromedriver as uc
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-first-run")
        options.add_argument("--window-size=1440,900")
        if headless:
            options.add_argument("--headless=new")

        driver = uc.Chrome(options=options, use_subprocess=True)
        return driver
