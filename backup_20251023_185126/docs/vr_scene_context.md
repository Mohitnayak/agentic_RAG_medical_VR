# VR Scene Context — Dental Surgical Planning

- **Title**: VR Scene Context
- **Domain**: dental
- **Version**: 1.0
- **Last updated**: 2025-10-20

## Scene layout
- **skull_model**: left
- **menu_bar**: center
- **dental_tray**: right
- **xray_display**: above skull_model (read-only, non-interactive)
- **control_panel**: far-left (contrast, brightness)

## Controller constraints
- **left hand**: interacts only with `skull_model`
- **right hand**: interacts with `menu_bar`, `dental_tray`, `implants`, `control_panel`, `xray_flashlight`

## Controlled vocabulary
- **Tools (switch)**: `undo`, `redo`, `xray_flashlight`, `handles`, `align_implants`, `show_nerve`, `show_sinus`
- **Controls (numeric)**: `contrast` (0–100), `brightness` (0–100)
- **Entities**: `skull_model`, `dental_tray`, `xray_display`, `implants`
- **Hands**: `left`, `right`, `none`

## Tools — switches
| target | values |
|---|---|
| undo | on/off |
| redo | on/off |
| xray_flashlight | on/off |
| handles | on/off |
| align_implants | on/off |
| show_nerve | on/off |
| show_sinus | on/off |

## Controls — numeric
| target | range |
|---|---|
| contrast | 0–100 |
| brightness | 0–100 |

## Implants
- **visibility**: on/off
- **sizes**:
  - `height_y_mm`: 3.0–4.8 (supported increments only)
  - `length_z_mm`: 6–17 (supported discrete values: 6, 8, 10, 11.5, 13, 15, 17)
- **matrix layout**: rows by `height_y_mm`, columns by `length_z_mm` (indexing provided by the tray grid)

## Interaction rules
- Enforce hand constraints strictly: the **left hand** cannot operate tools/implants/controls.
- Refuse control requests that violate constraints or unknown targets.

## Refusal policy
- The assistant must answer only within this context; if a question is out-of-domain (e.g., geography), it should refuse and ask for relevant dental-planning material.

## Examples (expected actions)
- Turn off dental implants → `{ "tool": "control", "arguments": { "hand": "right", "target": "implants", "operation": "set", "value": "off" } }`
- Set brightness to 70 → `{ "tool": "control", "arguments": { "hand": "right", "target": "brightness", "operation": "set", "value": 70 } }`
- Show nerve → `{ "tool": "control", "arguments": { "hand": "right", "target": "show_nerve", "operation": "set", "value": "on" } }`
- Resize implant (4.0 x 11.5) → `{ "tool": "control", "arguments": { "hand": "right", "target": "implants", "operation": "set", "value": { "height_y_mm": 4.0, "length_z_mm": 11.5 } } }`

## Glossary (synonyms → canonical entity)
| synonyms | entity | location |
|---|---|---|
| skull, skull model, dental model | skull_model | left |
| implants, implant, implant tray, dental implants | implants | right |
| menu, menu bar | menu_bar | center |
| x-ray, x ray, xray, xray display | xray_display | above the skull |
| control panel, contrast panel, brightness panel | control_panel | far-left |
| dental tray | dental_tray | right |
