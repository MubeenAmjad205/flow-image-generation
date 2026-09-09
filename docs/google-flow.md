# Google Flow UI Automation & Selector Specification

## 1. Overview

This document specifies the exact reverse-engineered DOM structures, Angular Material component classes, ARIA locators, popup dismissal rules, and image management mechanics for **Google Flow** (`https://flow.google.com`), updated with empirical screenshots of image context menus and project download features.

---

## 2. Real-World UI Layout & Navigation Architecture

```text
+---------------------------------------------------------------------------------------------------+
|  [Home]  [Project Name Input: editable-text-input]  [Search] [Filter] [Add Media] [Help] [:] [Avatar]
+---------------------------------------------------------------------------------------------------+
|  LEFT SIDEBAR      |  MAIN MEDIA WORKSPACE CANVAS            |  RIGHT SESSION SIDEBAR              |
|                    |                                         |                                     |
|  [*] All media     |  +-----------------------------------+  |  [Untitled session]             [X] |
|  [ ] Images        |  | Media Card [Menu: ...]            |  |                                     |
|  [ ] Characters    |  | +-------------------------------+ |  |  Hi Vernell                         |
|  [ ] Scenes        |  | | Context Menu:                 | |  |  What would you like to create?     |
|  [ ] Tools         |  | | - Favourite                   | |  |                                     |
|                    |  | | - Reuse prompt                | |  |  +-------------------------------+  |
|  [Bin]             |  | | - Download ->                 | |  |  | Beat #1 Prompt History        |  |
|  [Collapse]        |  | | - Rename                      | |  |  +-------------------------------+  |
|                    |  | +-------------------------------+ |  |                                     |
|                    |  +-----------------------------------+  |  [What do you want to create?    ]  |
|                    |                                         |  [+]          [Tune/Settings]  [^]  |
+--------------------+-----------------------------------------+-------------------------------------+
```

---

## 3. Top Header Menu & "Download Project" Feature

In the top workspace header, clicking the **More Options** button (three vertical dots `...`) opens the project menu:

```text
+----------------------------+
| Download project           |  <--- Bulk downloads all generated media assets
| Product Help               |
| Flow Help Centre           |
| View all changelogs        |
| Flow Music / Flow TV       |
+----------------------------+
```

### Selector Protocol:
- **Header Menu Button**: `page.get_by_role("button", name="More options for the project")`
- **Download Project Action**: `page.get_by_role("menuitem", name="Download project")` or `page.get_by_text("Download project")`

---

## 4. Image Context Menu & Renaming Protocol

Right-clicking or clicking the overflow menu on any generated media thumbnail opens the image options dropdown:

### Context Menu Items:
- `Favourite`
- `Reuse prompt`
- `Animate`
- `Add to prompt`
- **`Download`** (Submenu)
- `Copy`
- **`Rename`** (Triggers inline title editor)
- `Set project cover`
- `Flag output`
- `Move to bin`

### Inline Rename Protocol:
1. Click `Rename` in image context menu.
2. An inline popover appears containing an input box pre-filled with the current title (e.g., `Wolf and dog with puppy`).
3. Fill new sequence title (e.g., `01-wolf-and-dog-with-puppy`).
4. Click the checkmark `✓` button to confirm rename.

---

## 5. Stealth Driver Integration (`undetected-chromedriver`)

To ensure Google reCAPTCHA challenges never disrupt automated sessions, the automation uses **`undetected-chromedriver`**:

```python
import undetected_chromedriver as uc

def init_flow_session(profile_path: str):
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--disable-popup-blocking")
    
    driver = uc.Chrome(options=options)
    driver.get("https://flow.google.com")
    return driver
```

---

## 6. Popup & Modal Auto-Dismissal Protocol

Upon landing on `https://flow.google.com`, the automation clears any visible modal overlays:
1. **Opt-in / Terms Modal**: Click `"Next"` (`button.flow-button-primary`).
2. **Privacy Notice Modal**: Click `"Continue"`.
3. **Changelog Modal**: Click `"Get started"`.

---

## 7. Reverse-Engineered DOM Element Dictionary

### 7.1 Active Project Workspace (`https://flow.google.com/project/<id>`)

| UI Action / Element | DOM Tag & Classes | Primary ARIA / Selector | Playwright / UC Locator |
| :--- | :--- | :--- | :--- |
| **Home Button** | `BUTTON.back-button` | ARIA Label: `"Home"` | `get_by_role("button", name="Home")` |
| **Project Title Input**| `INPUT.editable-text-input` | ARIA Label: `"Editable text"` | `locator("input.editable-text-input")` |
| **Header More Options**| `BUTTON.more-options-button`| ARIA Label: `"More options for the project"` | `get_by_role("button", name="More options for the project")` |
| **Download Project** | `BUTTON` / `MENUITEM` | Text: `"Download project"` | `get_by_text("Download project")` |
| **Prompt Input Box** | `TEXTAREA` / `INPUT` | Placeholder: `"What do you want to create?"` | `get_by_placeholder("What do you want to create?")` |
| **Submit / Generate** | `BUTTON` (Arrow icon) | Submit button | `locator("button[type='submit']")` |
| **Stop Generation** | `BUTTON` (Square icon) | Active gen stop button | `locator("button:has(i:has-text('stop'))")` |
