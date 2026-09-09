"""Cookie & Storage State Management module.

Allows importing, loading, and saving Google authentication cookies/storage state
(e.g., from EditThisCookie, storage_state.json, or browser exports) to bypass
repeated login prompts.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings
from utils.logger import logger


class CookieManager:
    """Manages Google auth cookie import and Playwright storageState binding."""

    DEFAULT_COOKIE_FILE = settings.base_dir / "cookies.json"
    STORAGE_STATE_FILE = settings.base_dir / "profiles" / "storage_state.json"

    @classmethod
    def load_cookies_into_context(cls, context: Any, cookie_file: Optional[Path] = None) -> bool:
        """Injects JSON cookies into Playwright browser context.
        
        Args:
            context: Playwright BrowserContext instance.
            cookie_file: Path to cookies.json or storage_state.json.
            
        Returns:
            True if cookies were loaded successfully.
        """
        target_file = Path(cookie_file or cls.DEFAULT_COOKIE_FILE)
        
        if not target_file.exists():
            # Check storage_state.json backup
            if cls.STORAGE_STATE_FILE.exists():
                target_file = cls.STORAGE_STATE_FILE
            else:
                logger.debug(f"CookieManager: No cookie file found at '{target_file}'")
                return False

        logger.info(f"CookieManager: Loading cookies from '{target_file.name}'...")
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Case 1: Playwright storage_state format {"cookies": [...], "origins": [...]}
            if isinstance(data, dict) and "cookies" in data:
                cookies = data["cookies"]
            # Case 2: Raw cookie array [{"name": "...", "value": "...", ...}]
            elif isinstance(data, list):
                cookies = data
            else:
                logger.error(f"CookieManager: Unrecognized cookie format in '{target_file}'")
                return False

            normalized_cookies = cls._normalize_cookies(cookies)
            context.add_cookies(normalized_cookies)
            logger.info(f"CookieManager: Injected {len(normalized_cookies)} cookies into browser context!")
            return True

        except Exception as err:
            logger.error(f"CookieManager failed to load cookies from '{target_file}': {err}", exc_info=True)
            return False

    @classmethod
    def save_storage_state(cls, context: Any) -> Path:
        """Saves current browser context storage state (cookies + localStorage) to disk."""
        cls.STORAGE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(cls.STORAGE_STATE_FILE))
        logger.info(f"CookieManager: Saved active session state to '{cls.STORAGE_STATE_FILE}'")
        return cls.STORAGE_STATE_FILE

    @classmethod
    def _normalize_cookies(cls, cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardizes cookie fields to match Playwright context.add_cookies schema."""
        normalized = []
        for c in cookies:
            name = c.get("name") or c.get("key")
            value = c.get("value")
            if not name or value is None:
                continue

            domain = c.get("domain", ".google.com")
            if not domain.startswith("."):
                domain = f".{domain}"

            cookie_dict = {
                "name": str(name),
                "value": str(value),
                "domain": domain,
                "path": c.get("path", "/"),
            }

            # Optional attributes
            if "secure" in c:
                cookie_dict["secure"] = bool(c["secure"])
            if "httpOnly" in c:
                cookie_dict["httpOnly"] = bool(c["httpOnly"])
            if "sameSite" in c:
                same_site = str(c["sameSite"]).capitalize()
                if same_site in ["Strict", "Lax", "None"]:
                    cookie_dict["sameSite"] = same_site

            normalized.append(cookie_dict)
        return normalized
