# Google Flow UI Automation & Selector Specification

## 1. Overview

This document specifies the exact reverse-engineered DOM structures, Angular Material component classes, ProseMirror text editors, ARIA locators, popup dismissal rules, and image management mechanics for **Google Flow** (`https://flow.google.com`), updated with empirical DOM dumps and screenshots from active sessions.

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
|                    |  +-----------------------------------+  |  [div.ProseMirror Editor         ]  |
|                    |                                         |  [+]          [Tune/Settings]  [^]  |
+--------------------+-----------------------------------------+-------------------------------------+
```

---

## 3. Right Session Panel & ProseMirror Prompt Input Box

Google Flow uses a **ProseMirror** rich text WYSIWYG editor component for the prompt input bar:

```html
<div contenteditable="true" translate="no" class="ProseMirror">
    <p>
        <span class="prosemirror-placeholder ProseMirror-widget" contenteditable="false">
            What do you want to create?
        </span>
        <img class="ProseMirror-separator" alt="">
        <br class="ProseMirror-trailingBreak">
    </p>
</div>
```

### Exact Locator Protocol:
- **Primary Locator**: `page.locator(".ProseMirror, [contenteditable='true']")`
- **Text Injection**: `prompt_box.fill(text)` or dispatch JS `input` event on `div.ProseMirror`.

---

## 4. Top Header Menu & "Download Project" Feature

In the top workspace header, clicking the **More Options** button (three vertical dots `...`) opens the project menu:

- **Header Menu Button**: `page.get_by_role("button", name="More options for the project")`
- **Download Project Action**: `page.get_by_role("menuitem", name="Download project")` or `page.get_by_text("Download project")`

---

## 5. Image Context Menu & Renaming Protocol

Right-clicking or clicking the overflow menu on any generated media thumbnail opens the image options dropdown:
- `Download` (Submenu)
- `Rename` (Triggers inline title editor: `Wolf and dog with puppy` $\rightarrow$ `01-wolf-and-dog-with-puppy`)

---

## 6. Reverse-Engineered DOM Element Dictionary

### Active Project Workspace (`https://flow.google.com/project/<id>`)

| UI Action / Element | DOM Tag & Classes | Primary ARIA / Selector | Playwright Locator |
| :--- | :--- | :--- | :--- |
| **Home Button** | `BUTTON.back-button` | ARIA Label: `"Home"` | `get_by_role("button", name="Home")` |
| **Project Title Input**| `INPUT.editable-text-input` | ARIA Label: `"Editable text"` | `locator("input.editable-text-input")` |
| **Header More Options**| `BUTTON.more-options-button`| ARIA Label: `"More options for the project"` | `get_by_role("button", name="More options for the project")` |
| **Prompt Input Box** | `DIV.ProseMirror` | `contenteditable="true"` | `locator(".ProseMirror, [contenteditable='true']")` |
| **Submit / Generate** | `BUTTON` (Arrow icon) | Submit button | `locator("button[type='submit']")` |
| **Stop Generation** | `BUTTON` (Square icon) | Active gen stop button | `locator("button:has(i:has-text('stop'))")` |
