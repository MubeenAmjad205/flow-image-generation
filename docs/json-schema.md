# Canonical JSON Schema Specification

## 1. Purpose

The Canonical JSON Schema establishes a rigid contract between the **Document Extraction Engine** and the **Browser Automation Engine**. regardless of the source document's format, the data passed to Google Flow automation is normalized into this single, validated structure.

---

## 2. Formal JSON Schema (`draft-07`)

Below is the complete `json-schema.json` specification:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GoogleFlowImageJob",
  "type": "object",
  "description": "Normalized job specification for Google Flow automated image generation",
  "required": [
    "project_name",
    "total_prompts",
    "default_aspect_ratio",
    "default_model",
    "images"
  ],
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Name of the production series or project",
      "minLength": 1
    },
    "source_file": {
      "type": "string",
      "description": "Filename of the source DOCX package"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of extraction"
    },
    "total_prompts": {
      "type": "integer",
      "minimum": 1,
      "description": "Total count of image prompts in the job"
    },
    "default_aspect_ratio": {
      "type": "string",
      "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
      "default": "16:9",
      "description": "Global default aspect ratio for images in this job"
    },
    "default_model": {
      "type": "string",
      "enum": ["nano_banana", "nano_banana_pro"],
      "default": "nano_banana",
      "description": "Target Google Flow image generation model"
    },
    "images": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/definitions/ImagePromptSpec"
      }
    }
  },
  "definitions": {
    "ImagePromptSpec": {
      "type": "object",
      "required": [
        "sequence",
        "prompt",
        "aspect_ratio",
        "model",
        "count"
      ],
      "properties": {
        "sequence": {
          "type": "integer",
          "minimum": 1,
          "description": "Sequential index of the beat/image prompt (1-based)"
        },
        "time_code": {
          "type": "string",
          "description": "Time code interval in script (e.g., '0:12–0:16')"
        },
        "script_cue": {
          "type": "string",
          "description": "Associated voiceover script line"
        },
        "prompt": {
          "type": "string",
          "minLength": 10,
          "description": "Complete visual prompt text sent to Google Flow"
        },
        "aspect_ratio": {
          "type": "string",
          "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
          "description": "Specific aspect ratio for this image prompt"
        },
        "model": {
          "type": "string",
          "enum": ["nano_banana", "nano_banana_pro"],
          "description": "Target image generation model"
        },
        "count": {
          "type": "integer",
          "const": 1,
          "description": "Number of images to generate per prompt (strictly 1)"
        },
        "metadata": {
          "type": "object",
          "properties": {
            "camera": { "type": "string" },
            "lighting": { "type": "string" },
            "mood": { "type": "string" },
            "action": { "type": "string" },
            "palette": { "type": "string" }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 3. Concrete Example JSON (Derived from `Day13_Production_Package.docx`)

```json
{
  "project_name": "Wild Minds - Day 13 Reset",
  "source_file": "Day13_Production_Package.docx",
  "generated_at": "2026-09-09T14:35:00Z",
  "total_prompts": 120,
  "default_aspect_ratio": "16:9",
  "default_model": "nano_banana",
  "images": [
    {
      "sequence": 4,
      "time_code": "0:12–0:16",
      "script_cue": "Which is nothing at all. A blink. Not remotely enough time for that to be an accident.",
      "prompt": "Hand-drawn 2D cartoon illustration in a simple flat storybook style, confident bold black outlines of even weight, flat saturated colour fills with no texture. The same timeline runs across the lower third of frame with the wolf, campfire and dog standing on it. One flat pale green landmass shape (#8FCB77) with bold black outline is drawn very large behind the whole timeline as a backdrop, and against its full width the entire timeline occupies only one very short stretch at the far right, marked by one bold black bracket beneath it. Background: one flat saturated sky-blue field (#4FA8DC) filling the upper 50% of frame with two simple white cloud outlines, and one flat grass-green field (#4FA83C) filling the lower 50%, divided by one clean slightly uneven black horizon line. Every shape carries a bold uniform black outline (#1A1A1A). Flat saturated fills throughout with no gradients, no shading, no glossy highlights and no cast shadows. Side-on staging, camera at the subject's eye level, no vanishing point and no convergence. Generous negative space. 16:9, 1920×1080. Warm, plain, gently funny, never slick.",
      "aspect_ratio": "16:9",
      "model": "nano_banana",
      "count": 1,
      "metadata": {
        "camera": "Fixed eye-level orthographic mid-shot",
        "lighting": "None — flat fill only, zero shadows",
        "mood": "Scale, deflating",
        "action": "Large landmass backdrop fills in behind, bracket draws beneath.",
        "palette": "Sky blue #4FA8DC · Map land #8FCB77 · Wolf grey #9A9A9A · Dog tan #D9A055 · Outline #1A1A1A"
      }
    },
    {
      "sequence": 5,
      "time_code": "0:16–0:20",
      "script_cue": "So somebody did this. Somebody turned that into that.",
      "prompt": "Hand-drawn 2D cartoon illustration in a simple flat storybook style, confident bold black outlines of even weight, flat saturated colour fills with no texture. One cartoon grey wolf stands at the left of frame and one cartoon tan domestic dog stands at the right. Between them, one thick black arrow points from the wolf to the dog. Above the arrow, one large black hand-lettered question mark sits alone. Background: one flat saturated sky-blue field (#4FA8DC) filling the upper 50% of frame with two simple white cloud outlines, and one flat grass-green field (#4FA83C) filling the lower 50%, divided by one clean slightly uneven black horizon line. Every shape carries a bold uniform black outline (#1A1A1A). Flat saturated fills throughout with no gradients, no shading, no glossy highlights and no cast shadows. Side-on staging, camera at the subject's eye level, no vanishing point and no convergence. Generous negative space. 16:9, 1920×1080. Warm, plain, gently funny, never slick.",
      "aspect_ratio": "16:9",
      "model": "nano_banana",
      "count": 1,
      "metadata": {
        "camera": "Fixed eye-level orthographic mid-shot",
        "lighting": "None — flat fill only, zero shadows",
        "mood": "Set-up, direct",
        "action": "Arrow draws left to right, question mark pops in above it.",
        "palette": "Sky blue #4FA8DC · Grass green #4FA83C · Wolf grey #9A9A9A · Dog tan #D9A055 · Outline #1A1A1A"
      }
    }
  ]
}
```

---

## 4. Validation Rules & Field Specifications

1. **`project_name`**: Non-empty string. Derived from DOCX title or header.
2. **`total_prompts`**: Must equal `images.length`.
3. **`sequence`**: Strictly positive integer ($1, 2, \dots, N$). Sequence numbers must be strictly increasing without gaps.
4. **`prompt`**: Plain text visual prompt. Stripped of control characters, HTML tags, and trailing whitespace. Min length: 10 characters.
5. **`count`**: Strictly enforced to `1`. Multi-image generation per prompt is prohibited in this pipeline to maintain 1:1 image-to-prompt mapping integrity.
6. **`aspect_ratio`**: Must be one of the enum values (`16:9`, `9:16`, `1:1`, `4:3`, `3:4`).
