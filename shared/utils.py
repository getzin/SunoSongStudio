# shared/utils.py

import json
import time
from pathlib import Path
from typing import Any, Optional

import streamlit as st

from constants import LYRICS_MIN_WORDS, LYRICS_MAX_WORDS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def can_use_cooldown(key: str, cooldown_seconds: int) -> bool:
    last = st.session_state.get(key)
    if not last:
        return True
    return (time.time() - last) >= cooldown_seconds


def trigger_cooldown(key: str) -> None:
    st.session_state[key] = time.time()


def _word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])

def within_lyrics_limits(text: str) -> bool:
    """
    True iff text has between LYRICS_MIN_WORDS and LYRICS_MAX_WORDS words.
    """
    wc = _word_count(text)
    return LYRICS_MIN_WORDS <= wc <= LYRICS_MAX_WORDS