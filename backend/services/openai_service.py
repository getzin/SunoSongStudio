# backend/services/openai_service.py

import json
import openai
from pathlib import Path

from constants import ENABLE_DEBUG_TOOLS

# -----------------------------
# DIRECTORY PATHS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

ASSETS_JSON_DIR = BASE_DIR / "assets" / "json"
ASSETS_PROMPT_DIR = BASE_DIR / "assets" / "prompts"


# -----------------------------
# RESOLVE OPENAI KEY
# -----------------------------
def resolve_openai_key(api_keys_row):
    if not api_keys_row:
        return None
    if "openai_key" not in api_keys_row.keys():
        return None

    key = api_keys_row["openai_key"]
    if not key:
        return None

    openai.api_key = key
    return key


# -----------------------------
# LOAD MODE FILES (NEW VERSION)
# -----------------------------
def load_mode_prompt_and_json(mode: str):
    """
    Load the OpenAI prompt + OpenAI JSON template.

    Matches existing filenames:
        metaprompt_base.md
        metaprompt_cat.md
        metaprompt_xmas.md
    """

    mode = mode.lower()

    if mode == "normal":
        mode_key = "base"
    elif mode == "cat":
        mode_key = "cat"
    elif mode == "xmas":
        mode_key = "xmas"
    else:
        mode_key = "base"

    md_path = ASSETS_PROMPT_DIR / f"metaprompt_{mode_key}.md"
    json_path = ASSETS_JSON_DIR / f"openai_{mode_key}.json"

    md_prompt = md_path.read_text(encoding="utf-8")
    template = json.loads(json_path.read_text(encoding="utf-8"))

    return md_prompt, template


# ---------------------------------------------------------
# CALL OPENAI — LYRICS GENERATION
# ---------------------------------------------------------
def call_openai_generate_lyrics(api_key: str, md_prompt: str, user_json: str):
    openai.api_key = api_key

    try:
        tpl = json.loads(user_json)
    except Exception:
        tpl = {}

    forbidden = tpl.get("forbidden-words", [])
    alpha = tpl.get("alphabet", "latin").lower()

    forbidden_clause = ""
    if forbidden:
        forbidden_clause = (
            "You MUST avoid these forbidden words entirely:\n"
            + ", ".join(forbidden)
            + "\nIf avoidance is impossible, modify the line to remove any direct usage.\n"
        )

    alphabet_clause = ""
    if alpha == "latin":
        alphabet_clause = (
            "Write ALL lyrical text using ONLY the Latin alphabet.\n"
            "No kanji, kana, cyrillic, hanzi, arabic, hebrew, etc.\n"
            "Romanization is allowed but MUST remain purely Latin characters.\n"
        )

    prompt = md_prompt + "\n\nJSON CONFIG:\n" + user_json

    if ENABLE_DEBUG_TOOLS:
        print("\n========== OPENAI LYRICS REQUEST ==========")
        print("SYSTEM EXTRA RULES:")
        print(alphabet_clause)
        print(forbidden_clause)
        print("--------------------------------------------")
        print("USER PROMPT START:")
        print(prompt)
        print("============================================\n")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional lyric generator.\n"
                    "Follow the metaprompt and JSON exactly.\n"
                    + alphabet_clause
                    + forbidden_clause
                    +
                    "Return ONLY the final lyrics.\n"
                    "Never output JSON.\n"
                    "Never explain your reasoning."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=1.0,
    )

    text = response["choices"][0]["message"]["content"].strip()

    if ENABLE_DEBUG_TOOLS:
        print("\n---------- RAW LYRICS RESPONSE ----------")
        print(text)
        print("-----------------------------------------\n")

    usage = response.get("usage", {}) or {}
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    INPUT_PRICE_PER_M = 0.15
    OUTPUT_PRICE_PER_M = 0.60

    cost = (
        prompt_tokens * INPUT_PRICE_PER_M +
        completion_tokens * OUTPUT_PRICE_PER_M
    ) / 1_000_000

    return text, total_tokens, cost


# ---------------------------------------------------------
# PICK EMOJI
# ---------------------------------------------------------
def call_openai_pick_emoji(api_key: str, emoji_list):
    openai.api_key = api_key

    prompt = (
        "Pick ONE emoji from this list:\n"
        + ", ".join(emoji_list)
        + "\nReturn ONLY the emoji."
    )

    if ENABLE_DEBUG_TOOLS:
        print("\n------ PICK EMOJI PROMPT ------")
        print(prompt)
        print("-------------------------------\n")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return one emoji only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=5,
        temperature=0.5,
    )

    result = response["choices"][0]["message"]["content"].strip()
    if ENABLE_DEBUG_TOOLS:
        print("Emoji chosen:", result)
    return result


# ---------------------------------------------------------
# TITLE GENERATION
# ---------------------------------------------------------
def call_openai_generate_title(api_key: str, lyrics_text: str, max_length: int = 60):
    openai.api_key = api_key

    prompt = f"""
Generate a short, punchy, original title (max {max_length} chars).
NO quotes, NO explanation.
Return ONLY the title.

Lyrics:
---
{lyrics_text}
---
""".strip()

    if ENABLE_DEBUG_TOOLS:
        print("\n------ TITLE GENERATION PROMPT ------")
        print(prompt)
        print("-------------------------------------\n")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate concise, punchy song titles. "
                    "Output ONLY the title text."
                )
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=20,
        temperature=0.7,
    )

    raw = response["choices"][0]["message"]["content"].strip()

    for line in raw.splitlines():
        line = line.strip()
        if line:
            return line[:max_length]

    return "Untitled"


# ---------------------------------------------------------
# EMOJI LISTS PER MODE
# ---------------------------------------------------------
def get_mode_emoji_list(mode):
    mode = mode.lower()

    # Cat Mode
    if mode in ("cat", "cat_mode"):
        return ["🐱", "😺", "🐈", "✨", "💛"]

    # Xmas Mode
    if mode in ("xmas", "christmas"):
        return ["🎄", "❄️", "🎁", "⭐", "❤️"]

    # Normal Mode — expanded set
    return [
        "🎵", "✨", "🔥", "💫", "🌙",
        "🌈", "⚡", "🎧", "🎶", "🌟",
        "💥", "🌀", "🌊", "🌬️", "🔥",
        "💖", "💎", "🌞", "🪐", "🌌",
        "🎹", "🥁", "🎸", "🎺", "🎷",
        "📻", "📀", "🎼", "💜", "💛"
    ]
