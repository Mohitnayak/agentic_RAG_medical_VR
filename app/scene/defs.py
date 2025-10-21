from __future__ import annotations

from typing import Optional

# Canonical term -> concise definition suitable for UI/voice
TERM_DEFINITIONS = {
    "handles": "Handles are grabbable UI affordances used to adjust or manipulate scene elements precisely.",
    "xray_flashlight": "X‑ray flashlight is a spotlight overlay that reveals X‑ray detail where aimed.",
    "show_nerve": "Nerve overlay visualizes the mandibular canal to avoid nerve injury during planning.",
    "show_sinus": "Sinus overlay outlines the maxillary sinus boundary for safe implant planning.",
    "sinuses": "Sinus overlay outlines the maxillary sinus boundary for safe implant planning.",
    "align_implants": "Align implants realigns selected implants to a planned axis/prosthetic reference.",
    "contrast": "Contrast controls the intensity difference in the X‑ray visualization (0–100).",
    "brightness": "Brightness controls overall luminance of the X‑ray visualization (0–100).",
    "implants": "Dental implants are virtual fixtures selectable by height (y) and length (z) for planning.",
}

# Simple synonyms -> canonical term
SYNONYM_TO_TERM = {
    "handles": "handles",
    "handle": "handles",
    "x-ray flashlight": "xray_flashlight",
    "x ray flashlight": "xray_flashlight",
    "xray flashlight": "xray_flashlight",
    "nerve": "show_nerve",
    "nerve overlay": "show_nerve",
    "sinus": "show_sinus",
    "sinuses": "show_sinus",
    "sinus overlay": "show_sinus",
    "align implants": "align_implants",
    "alignment": "align_implants",
    "contrast": "contrast",
    "brightness": "brightness",
    "implants": "implants",
    "dental implants": "implants",
}


def resolve_definition(question: str) -> Optional[str]:
    q = question.strip().lower()
    # Only trigger on definition intents to avoid overfiring
    if not any(x in q for x in ["what is", "what are", "explain", "definition of", "tell me about"]):
        return None
    for syn in sorted(SYNONYM_TO_TERM.keys(), key=len, reverse=True):
        if syn in q:
            term = SYNONYM_TO_TERM[syn]
            desc = TERM_DEFINITIONS.get(term)
            if desc:
                # Friendly name
                name = {
                    "xray_flashlight": "X‑ray flashlight",
                    "show_nerve": "nerve overlay",
                    "show_sinus": "sinus overlay",
                    "align_implants": "align implants",
                }.get(term, syn)
                return f"{name}: {desc}"
    return None


