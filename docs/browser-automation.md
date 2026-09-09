# Browser Automation & Anti-Detection Architecture

## 1. Stealth & Anti-Detection Requirements

Google enforces sophisticated anti-bot detection algorithms (such as Cloudflare/reCAPTCHA enterprise challenges, `navigator.webdriver` audits, V8 CDC variable checks, and Chrome automation flags).

Standard Playwright or Selenium instances that emit `--enable-automation` flags are instantly flagged by Google, resulting in intrusive reCAPTCHA prompts or session rejection.

To guarantee zero reCAPTCHA interruptions, the automation engine incorporates **Undetected Chrome Automation** (`undetected-chromedriver` / `playwright-stealth`).

---

## 2. Stealth Implementation Strategies

### Approach A: `undetected-chromedriver` (Primary Stealth Driver)
`undetected-chromedriver` (UC) automatically patches Chrome binary executable files, removes V8 `cdc_` DOM properties, overrides the `navigator.webdriver` flag, and passes Google's bot detection checks without triggering reCAPTCHAs.

```python
import undetected_chromedriver as uc

def launch_stealth_browser(user_data_dir: str):
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    
    # Launch patched Chrome driver
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver
```

### Approach B: Playwright with Stealth Plugin & Evasion Flags
If using Playwright, the browser context is initialized with explicit Chrome channel flags to strip automation fingerprints:

```python
from playwright.sync_api import sync_playwright

def launch_playwright_stealth(user_data_dir: str):
    p = sync_playwright().start()
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        channel="chrome",  # Use real installed Google Chrome binary
        headless=False,
        ignore_default_args=["--enable-automation"],
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars"
        ]
    )
    return context
```

---

## 3. Comparison Matrix: Stealth Execution Options

| Feature | Standard Playwright | Standard Selenium | `undetected-chromedriver` | Playwright + Stealth Flags |
| :--- | :--- | :--- | :--- | :--- |
| **`navigator.webdriver`** | `true` (Flagged) | `true` (Flagged) | **`undefined` (Clean)** | **`undefined` (Clean)** |
| **Google reCAPTCHA Risk** | High | Extreme | **Zero / Clean** | **Near Zero** |
| **Chrome CDC Variables** | Present | Present | **Patched & Removed** | **Patched & Removed** |
| **Persistent User Profile**| Supported | Supported | **Native Support** | **Native Support** |
| **Async Execution Speed** | High | Moderate | **High** | **High** |
