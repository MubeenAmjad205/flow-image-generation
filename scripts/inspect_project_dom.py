"""Diagnostic script to inspect DOM elements inside an active Google Flow project workspace."""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from config.settings import settings

def inspect_project_ui():
    print("=== INSPECTING GOOGLE FLOW PROJECT WORKSPACE DOM ===")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(settings.profiles_dir),
            channel="chrome",
            headless=False,
            viewport={"width": 1440, "height": 900}
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://flow.google.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Click New project or existing project
        print("Clicking New Project...")
        page.locator(".new-project-button, button:has-text('project')").first.click()
        page.wait_for_timeout(5000)

        print(f"Current URL: {page.url}")

        # Extract all textareas, inputs, contenteditables, and custom elements
        elements_info = page.evaluate("""() => {
            const nodes = Array.from(document.querySelectorAll('textarea, input, [contenteditable="true"], flow-prompt-input, [placeholder]'));
            return nodes.map((el, idx) => ({
                idx: idx + 1,
                tagName: el.tagName,
                type: el.type || null,
                placeholder: el.getAttribute('placeholder') || null,
                ariaLabel: el.getAttribute('aria-label') || null,
                classList: Array.from(el.classList).join(' '),
                id: el.id || null,
                name: el.name || null,
                isVisible: el.offsetWidth > 0 && el.offsetHeight > 0,
                outerHTML: el.outerHTML.slice(0, 300)
            }));
        }""")

        print(f"\nFound {len(elements_info)} candidate input elements:")
        for el in elements_info:
            print(json.dumps(el, indent=2))

        context.close()

if __name__ == "__main__":
    inspect_project_ui()
