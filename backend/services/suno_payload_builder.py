# backend/services/suno_payload_builder.py

"""
Builds the minimal, correct Suno (AceData) payload.

S1 ARCHITECTURE — IMPORTANT:
    • OpenAI JSON templates NO LONGER contain any Suno fields.
    • Suno UI / Streamlit passes a clean suno_json dict into this builder.
    • This module outputs ONLY the fields AceData accepts.

AceData /suno/audios accepts the following fields:

    action:         always "generate"
    model:          Suno model string
    prompt:         short style prompt string
    lyric:          full lyrics text
    custom:         bool
    instrumental:   bool
    title:          song title text
    style:          additional style descriptors
    vocal_gender:   "f" or "m"

Any other fields are ignored or rejected by AceData.
"""

from typing import Dict


def build_suno_payload(suno_json: Dict, lyrics_text: str) -> Dict:
    """
    Construct the exact payload used for AceData /suno/audios.

    suno_json (S1 structure) must contain:
        "model"
        "prompt"
        "custom"
        "instrumental"
        "title"
        "style"
        "vocal_gender"

    All additional UI metadata (genre, tags, seed, etc.)
    is NOT sent to AceData unless they officially support it.
    """

    # Normalize vocal gender just to be safe
    vg = suno_json.get("vocal_gender", "f")
    vg = ("m" if vg.lower().startswith("m") else "f")

    payload = {
        "action": "generate",
        "model": suno_json.get("model", "chirp-v5"),  # final fallback, should not be used
        "prompt": suno_json.get("prompt", ""),
        "lyric": lyrics_text,
        "custom": bool(suno_json.get("custom", True)),
        "instrumental": bool(suno_json.get("instrumental", False)),
        "title": suno_json.get("title", "Untitled"),
        "style": suno_json.get("style", ""),
        "vocal_gender": vg,
    }

    return payload
