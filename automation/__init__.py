"""Automation package initialization."""
from automation.stealth import StealthBrowserManager
from automation.auth import SessionGuard
from automation.flow_controller import FlowController
from automation.cookie_manager import CookieManager

__all__ = ["StealthBrowserManager", "SessionGuard", "FlowController", "CookieManager"]
