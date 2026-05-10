# backend/services/lyrics_service.py

import json
import re
import random
import logging
from typing import Tuple

from backend.services.openai_service import (
    resolve_openai_key,
    load_mode_prompt_and_json,
    call_openai_generate_lyrics,
    call_openai_pick_emoji,
    call_openai_generate_title,
    get_mode_emoji_list,
)
from backend.models.lyrics import create_lyrics
from backend.models.users import get_api_keys


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------
def _parse_list_field(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,\n;]", raw)
    return [p.strip() for p in parts if p.strip()]


def flatten_lyrics_json_if_needed(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return text

    try:
        data = json.loads(stripped)
    except Exception:
        return text

    if isinstance(data, dict) and "lyrics" in data and isinstance(data["lyrics"], dict):
        sections = data["lyrics"]
    elif isinstance(data, dict):
        sections = data
    else:
        return text

    lines: list[str] = []
    for key, section in sections.items():
        if not isinstance(section, dict):
            continue
        caption = section.get("caption") or f"[{key.upper()}]"
        content = section.get("content") or ""
        lines.append(caption.strip())
        if content:
            lines.append(content.strip())
        lines.append("")

    return "\n".join(lines).strip() or text


def _extract_fallback_title(lyrics_text: str) -> str:
    for line in lyrics_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        return line[:80]
    return "Untitled"


# ---------------------------------------------------------
# Caption Variation Engine (B1 — section-aware, mild, stable)
# ---------------------------------------------------------

_SECTION_VARIANTS = {
    "intro": [
        "dreamy synth haze",
        "soft shimmering pads",
        "warm airy textures",
        "fluttering summer breeze",
        "gentle ambient glow",
    ],
    "verse": [
        "steady rhythmic pulse",
        "soft groove movement",
        "light melodic flow",
        "warm storytelling texture",
        "gentle harmonic lift",
    ],
    "bridge": [
        "emotional buildup",
        "floating harmonic tension",
        "soft rising shimmer",
        "cinematic breath",
        "warm transitional glow",
    ],
    "hook": [
        "bright energetic shine",
        "large melodic lift",
        "chorus-style sparkle",
        "anthemic pop-burst",
        "wide emotional resonance",
    ],
    "cpart": [
        "dramatic tonal shift",
        "plot-twist harmonic surge",
        "unexpected emotional turn",
        "spotlight moment texture",
        "distinct narrative pivot",
    ],
    "outro": [
        "fading soft textures",
        "gentle dissolve",
        "warm drifting ambience",
        "calm settling glow",
        "slow quiet fade-out",
    ],
}


def _detect_section_type(caption: str) -> str:
    c = caption.lower()
    if "intro" in c:
        return "intro"
    if "verse" in c:
        return "verse"
    if "chorus" in c:
        # treat chorus as hook
        return "hook"
    if "pre-chorus" in c or "prechorus" in c:
        # treat pre-chorus as bridge-type lift
        return "bridge"
    if "bridge" in c:
        return "bridge"
    if "hook" in c:
        return "hook"
    if "c-part" in c or "cpart" in c:
        return "cpart"
    if "outro" in c:
        return "outro"
    return "verse"



def _apply_caption_variation(caption: str) -> str:
    section_key = _detect_section_type(caption)
    variants = _SECTION_VARIANTS.get(section_key, [])
    if not variants:
        return caption

    extra = random.choice(variants)

    if "]" in caption:
        idx = caption.rfind("]")
        before = caption[:idx]
        after = caption[idx:]
        return before + ", " + extra + after

    return caption + " — " + extra


# ---------------------------------------------------------
# Apply user inputs + style injection + caption variation
# ---------------------------------------------------------
def merge_lyrics_template_inputs(
    template: dict,
    *,
    language: str,
    artist: str,
    genre: str,
    topics_text: str,
    semantic: str,
    subgenre: str,
    forbidden_words_text: str,
    formatting_text: str,
    finalsteps_text: str,
    onomatopoeia_text: str,
) -> dict:

    # Make a shallow copy
    tpl = dict(template)

    # Core fields
    tpl["language"] = (language or "").strip() or tpl.get("language", "english")
    tpl["alphabet"] = "latin"

    if artist.strip():
        tpl["artist"] = artist.strip()
    if genre.strip():
        tpl["genre"] = genre.strip()
    if subgenre.strip():
        tpl["subgenre"] = subgenre.strip()

    # List-like fields
    if (topics := _parse_list_field(topics_text)):
        tpl["topics"] = topics

    if semantic.strip():
        tpl["semantic"] = semantic.strip()

    if (fw := _parse_list_field(forbidden_words_text)):
        tpl["forbidden-words"] = fw

    if (fmt := _parse_list_field(formatting_text)):
        tpl["formatting"] = fmt

    if (fs := _parse_list_field(finalsteps_text)):
        tpl["finalsteps"] = fs

    if (ono := _parse_list_field(onomatopoeia_text)):
        tpl["onomatopoeia"] = ono

    # Build style string
    style_parts = []
    if tpl.get("genre"):
        style_parts.append(tpl["genre"])
    if tpl.get("subgenre"):
        style_parts.append(tpl["subgenre"])
    if tpl.get("artist"):
        style_parts.append(f"in the style of {tpl['artist']}")

    style_str = ", ".join(style_parts)

    # Inject styles + caption variations
    struct = tpl.get("structure") or {}
    for section in struct.values():
        if not isinstance(section, dict):
            continue

        caption = section.get("caption", "")

        if "{style}" in caption:
            caption = caption.replace("{style}", style_str)

        caption = _apply_caption_variation(caption)

        section["caption"] = caption

    return tpl


# ---------------------------------------------------------
# Forbidden-word post-filter
# ---------------------------------------------------------
def _remove_forbidden_words(text: str, forbidden: list[str]) -> str:
    if not forbidden:
        return text

    out = text
    for word in forbidden:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        out = pattern.sub("[redacted]", out)

    return out


# ---------------------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------------------
def generate_lyrics(
    user: dict,
    mode: str,
    language: str,
    artist: str,
    genre: str,
    auto_title: bool = True,
    manual_title: str | None = None,
    topics_text: str = "",
    semantic: str = "",
    subgenre: str = "",
    forbidden_words_text: str = "",
    formatting_text: str = "",
    finalsteps_text: str = "",
    onomatopoeia_text: str = "",
) -> Tuple[int, str, str, str]:

    # Resolve OpenAI key
    api_keys = get_api_keys(user["id"])
    key = resolve_openai_key(api_keys)
    if not key:
        raise RuntimeError("Missing OpenAI API key. Add in Settings.")

    # Load prompt + JSON template (from new openai_base.json etc.)
    md_prompt_raw, template_raw = load_mode_prompt_and_json(mode)

    # Inject user fields
    template = merge_lyrics_template_inputs(
        template_raw,
        language=language,
        artist=artist,
        genre=genre,
        topics_text=topics_text,
        semantic=semantic,
        subgenre=subgenre,
        forbidden_words_text=forbidden_words_text,
        formatting_text=formatting_text,
        finalsteps_text=finalsteps_text,
        onomatopoeia_text=onomatopoeia_text,
    )

    # Replace placeholder
    md_prompt = md_prompt_raw.replace("__LANGUAGE__", template.get("language", "english"))

    # Convert JSON
    user_json = json.dumps(template, ensure_ascii=False, indent=2)

    logging.info("=== LYRICS GENERATION REQUEST ===")
    logging.info(md_prompt)
    logging.info(user_json)

    # Call OpenAI
    raw_text, tokens, cost = call_openai_generate_lyrics(key, md_prompt, user_json)

    # Flatten JSON output if needed
    text = flatten_lyrics_json_if_needed(raw_text)

    # Forbidden-word removal
    text = _remove_forbidden_words(text, template.get("forbidden-words", []))

    # Title
    fallback_title = _extract_fallback_title(text)

    if auto_title:
        try:
            title = call_openai_generate_title(key, text)
        except Exception:
            title = fallback_title
    else:
        title = (manual_title or "").strip() or fallback_title

    # Emoji
    emoji = call_openai_pick_emoji(key, get_mode_emoji_list(mode))

    # Save to DB
    lyrics_id = create_lyrics(
        user_id=user["id"],
        title=title,
        emoji=emoji,
        text=text,
        mode=mode,
        prompt_used=md_prompt + "\n\nJSON CONFIG:\n" + user_json,
        tokens=tokens,
        cost=cost,
    )

    return lyrics_id, title, emoji, text
