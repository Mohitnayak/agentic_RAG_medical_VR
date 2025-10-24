## VR Dental Planning Scene Reference

Purpose: authoritative reference of scene components, controls, values, and example utterances to ground domain-only Q&A and control actions.

### Scene description

The VR planning workspace centers around the anatomical `skull_model` on the left. Above the skull sits the `xray_display`, which provides radiographic context. The `menu_bar` in the center offers UI navigation, while the `control_panel` on the far-left exposes imaging adjustments like `brightness` and `contrast`. On the right, the `dental_tray` and `implants` area provide instruments and implant selection. Several overlays and aids can be toggled on demand: `handles` for on-screen manipulation, the `xray_flashlight` to spotlight regions with X‑ray appearance, `show_nerve` to visualize the nerve canal overlay, `show_sinus` to visualize sinus anatomy, and `align_implants` to display guidance for implant alignment. Brightness and contrast are numeric controls (0–100) that shape visualization; overlays are switches you can turn on or off.

Component usage overview:
- `skull_model` (model): Main 3D anatomy for planning. Refer to it in questions (e.g., “where is the skull?”). Not a switch.
- `xray_display` (display): Radiographic view above the skull. Not a switch. Use `xray_flashlight` overlay for focused X‑ray effect.
- `menu_bar` (UI): Navigation/menu context. Not voice-controlled in this version.
- `control_panel` (UI): Home for value controls. Use voice to set numeric values (e.g., “set brightness to 50”).
- `dental_tray` (tray): Holds instruments; contextual reference. Not a switch.
- `implants` (object): Implant tray and placement context. Ask definitions or sizing. For sizing: height_y_mm (3.0–4.8), length_z_mm (6–17).
- `handles` (switch): Show/hide manipulation handles. “turn on handles”, “hide handles”, or “toggle handles”.
- `xray_flashlight` (switch): Enable an X‑ray style spotlight. “switch on x‑ray flashlight”, “turn off flashlight”.
- `show_nerve` (switch): Toggle nerve overlay. “show nerve”, “turn off nerve overlay”.
- `show_sinus` (switch): Toggle sinus overlay. “show sinuses”, “hide sinus overlay”.
- `align_implants` (switch): Toggle alignment guide. “enable alignment”, “disable alignment”.
- `brightness` (value 0–100): “set brightness to 50”, “brightness 70%”. If value omitted, the system asks for a number.
- `contrast` (value 0–100): “set contrast to 40”, “contrast 75%”. If value omitted, the system asks for a number.

### Scene elements overview

| Element | Type | Location | Purpose | Synonyms |
|---|---|---|---|---|
| skull_model | model | left | Main anatomical model for planning | skull, skull model, dental model |
| implants | object | right | Implant tray and placement context | implant, dental implants, implant tray |
| menu_bar | UI | center | Navigation/menu actions | menu, menu bar |
| xray_display | display | above the skull | Shows X‑ray imagery | x-ray, x ray, xray, xray display |
| control_panel | UI | far-left | Adjust brightness/contrast | control panel, contrast panel, brightness panel |
| dental_tray | tray | right | Instruments and related items | dental tray |
| handles | switch | n/a | Toggle on-screen manipulation handles | handle, handles |
| xray_flashlight | switch | n/a | Focused X‑ray overlay “flashlight” | xray flashlight, x‑ray flashlight, x ray flashlight, flashlight, flash light |
| show_nerve | switch | n/a | Toggle nerve overlay | nerve, nerve overlay, show nerve |
| show_sinus | switch | n/a | Toggle sinus overlay | sinus, sinuses, sinus overlay, show sinus, show sinuses |
| align_implants | switch | n/a | Toggle implant alignment guide | align implants, alignment |
| contrast | value | control panel | Adjust imaging contrast | contrast |
| brightness | value | control panel | Adjust scene brightness | brightness |

### Switch controls

| Control | What it does | Typical utterances | Notes |
|---|---|---|---|
| handles | Show/hide manipulation handles | "turn on handles", "hide handles", "toggle handles" | on/off/toggle |
| xray_flashlight | Enable/disable X‑ray flashlight | "switch on x‑ray flashlight" | on/off/toggle |
| show_nerve | Show/hide nerve overlay | "show nerve", "turn off nerve overlay" | on/off/toggle |
| show_sinus | Show/hide sinus overlay | "show sinuses", "hide sinus overlay" | on/off/toggle |
| align_implants | Toggle alignment guide | "enable alignment", "disable alignment" | on/off/toggle |

- "show …" for overlays maps to turning that switch on.
- Spelling variants and synonyms are accepted (LLM normalization).

### Value controls

| Parameter | Range | Example utterances | Notes |
|---|---|---|---|
| brightness | 0–100 | "set brightness to 50", "increase brightness to 70%" | Numeric; percent or absolute |
| contrast | 0–100 | "set contrast to 40", "contrast 75%" | Numeric; percent or absolute |

- If you say "set brightness …" without a value, the system asks for a specific number within the valid range.

### Information queries (domain-only)

| Topic | Example questions | Expected answer |
|---|---|---|
| Definitions | "what are sinuses?", "tell me about implants" | Short description; uses ingested context |
| Locations | "where is the skull?", "which side is the control panel?" | Location or side in the scene |

- If insufficient context is found, the system refuses and asks to ingest relevant docs.

### Implant sizing requests

| Intent | Example utterances | Behavior |
|---|---|---|
| size_request (no size provided) | "give me dental implants", "I need implants" | Asks for size (height_y_mm 3.0–4.8; length_z_mm 6–17) |
| control_value (size present) | "give me implant size 4 x 11.5" | Applies with specified dimensions |

### Notes functions

| Action | Example utterances | System behavior |
|---|---|---|
| Start notes | "start recording", "start taking notes", "begin notes" | Returns note_action function=start_notes |
| Add note | "note this: …", "take notes of …" | Returns note_action function=add_note with text |
| End notes | "stop recording", "end notes", "finalize notes" | Returns note_action function=end_notes |

- Recommended UX: play a short beep after start_notes; subsequent "note this:" lines get appended.

### Disambiguation and clarification

- If intent/entity/value confidence is low, the system asks targeted questions:
  - Missing entity for a switch: "Which element should I turn on? (e.g., handles, show_sinus…)"
  - Value mentioned but target unclear: "I detected value 50. Which control should I apply it to? (brightness 0–100, contrast 0–100)"
  - Missing numeric value: "What value should I set for brightness (0–100)?"

### Guardrails (domain-only QA)

- Answers require sufficient retrieved context; otherwise the system refuses with guidance to ingest or rephrase.
- Random/out-of-domain questions are not answered.

### Quick command-to-intent mapping

| Command (examples) | Interpreted as | Notes |
|---|---|---|
| "show sinuses" | control_on → target=show_sinus | Switch on overlay |
| "hide sinuses" | control_off → target=show_sinus | Switch off overlay |
| "set brightness to 50" | control_value → brightness=50 | Value in 0–100 |
| "what are sinuses?" | info_definition(sinuses) | Uses RAG context |
| "where is the skull?" | info_location(skull_model) | Uses scene metadata |
| "start recording" | note_action(start_notes) | Starts note session |
| "note this: patient prefers 4 x 11.5" | note_action(add_note) | Adds text to notes |
| "stop recording" | note_action(end_notes) | Finalizes notes |

### Ranges and constraints (summary)

- brightness: 0–100
- contrast: 0–100
- implants: height_y_mm 3.0–4.8; length_z_mm 6–17

### Ingestion tip

- Title suggestion: "VR Dental Planning Scene Reference"
- Domain: dental
- Ingest this file to ground definition/location answers and improve clarification prompts.


