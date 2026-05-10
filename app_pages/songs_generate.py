# app_pages/songs_generate.py

import streamlit as st

from backend.models.lyrics import (
    list_lyrics_for_user,
    get_lyrics_by_id,
)
from backend.models.users import get_api_keys
from backend.services.suno_service import create_tracks_from_suno, process_pending_songs
from shared.session import get_current_user
from shared.layout import require_login
from shared.utils import can_use_cooldown, trigger_cooldown, within_lyrics_limits

from backend.db import execute_returning_id
from constants import (
    SONG_PRESETS,
    SUNO_MODELS,
    VOCAL_GENDERS,
    MODE_NORMAL,
    LYRICS_MIN_WORDS,
    LYRICS_MAX_WORDS,
    ENABLE_DEBUG_TOOLS,
)

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _build_lyrics_choices(user_id):
    lyrics_list = list_lyrics_for_user(user_id, include_archived=False)
    if not lyrics_list:
        return [], {}

    choices, mapping = [], {}
    for row in lyrics_list:
        emoji = row["emoji"] or ""
        title = row["title"] or "Untitled"
        label = f"{emoji} {title} · #{row['id']}".strip()
        choices.append(label)
        mapping[label] = row["id"]
    return choices, mapping


def _should_apply_preset(new_name, key="sg_preset_last"):
    last = st.session_state.get(key)
    st.session_state[key] = new_name
    if last is None:
        return True
    return last != new_name


# ---------------------------------------------------------
# PAGE
# ---------------------------------------------------------
def run():
    require_login()
    user = get_current_user()

    st.subheader("🎧 Generate Songs from Lyrics")

    api_keys = get_api_keys(user["id"])
    suno_key = api_keys.get("suno_key") if api_keys else None

    if not suno_key:
        st.error("Missing Suno / AceData API key. Add it in **Settings** first.")
        return

    st.info("Turn lyrics into Suno tracks. After submitting, downloads now start immediately.")

    # ---------------------------------------------------------
    # LYRIC SOURCE
    # ---------------------------------------------------------
    st.markdown("### 📜 Lyrics Source")
    source = st.radio(
        "Select lyric input mode",
        ["Use saved lyrics", "Paste custom lyrics"],
        horizontal=True,
    )

    lyrics_text, lyrics_id, title = "", None, ""

    if source == "Use saved lyrics":
        choices, mapping = _build_lyrics_choices(user["id"])

        target_id = st.session_state.pop("selected_lyrics_id", None)

        if target_id:
            for lbl, lid in mapping.items():
                if lid == target_id:
                    st.session_state["sg_selected_lyrics"] = lbl
                    st.session_state["redirect_flag"] = True
                    break

        if st.session_state.get("redirect_flag"):
            st.session_state["redirect_flag"] = False
            st.rerun()

        if not choices:
            st.warning("No saved lyrics yet. Create some in **Lyrics Generate**.")
            return

        chosen = st.selectbox(
            "Pick lyrics",
            choices,
            key="sg_selected_lyrics",
        )
        lyr = get_lyrics_by_id(mapping[chosen])

        if not lyr:
            st.error("Could not load lyrics.")
            return

        lyrics_id = lyr["id"]
        lyrics_text = lyr["text"]
        title = lyr["title"] or "Untitled"

        st.text_area("Preview of selected lyrics", lyrics_text, height=260, disabled=True)

    else:
        title = st.text_input("Song title", value="Untitled")
        lyrics_text = st.text_area(
            "Paste your lyrics here",
            value="",
            height=260,
            placeholder="Paste the full lyrics you want Suno to sing…",
        )

    clean_lyrics = (lyrics_text or "").strip()
    if not clean_lyrics:
        st.warning("Please provide some lyrics first.")
        return

    if source == "Paste custom lyrics" and not within_lyrics_limits(clean_lyrics):
        st.error(
            f"Lyrics must be between {LYRICS_MIN_WORDS} and {LYRICS_MAX_WORDS} words "
            f"(current: {len(clean_lyrics.split())})."
        )
        return

    # ---------------------------------------------------------
    # SUNO SETTINGS
    # ---------------------------------------------------------
    st.markdown("### 🎨 Suno Settings")

    preset_name = st.selectbox("Preset (optional)", list(SONG_PRESETS.keys()))
    preset = SONG_PRESETS.get(preset_name, {})
    apply_preset = _should_apply_preset(preset_name)

    col1, col2 = st.columns(2)

    with col1:
        genre = st.text_input(
            "Genre",
            value=preset.get("genre", "") if apply_preset else st.session_state.get("sg_genre", ""),
        )
        st.session_state["sg_genre"] = genre

        vocal_gender = st.selectbox(
            "Vocal Gender",
            VOCAL_GENDERS,
            index=VOCAL_GENDERS.index(
                preset.get("vocal_gender", "female")
            )
            if apply_preset
            else VOCAL_GENDERS.index(st.session_state.get("sg_gender", "female")),
        )
        st.session_state["sg_gender"] = vocal_gender

    with col2:
        style = st.text_input(
            "Style (extra descriptors)",
            value=preset.get("style", "") if apply_preset else st.session_state.get("sg_style", ""),
        )
        st.session_state["sg_style"] = style

        model = st.selectbox(
            "Model",
            SUNO_MODELS,
            index=SUNO_MODELS.index(
                preset.get("model", SUNO_MODELS[0])
            )
            if apply_preset
            else SUNO_MODELS.index(st.session_state.get("sg_model", SUNO_MODELS[0])),
        )
        st.session_state["sg_model"] = model

    tags_default = ", ".join(preset.get("tags", [])) if apply_preset else st.session_state.get("sg_tags", "")
    tags_raw = st.text_input(
        "Tags (optional, comma-separated)",
        value=tags_default,
        help="Optional extra style keywords like 'neon, retro, cinematic'.",
    )
    st.session_state["sg_tags"] = tags_raw

    with st.expander("Advanced Options"):
        instrumental = st.checkbox("Make instrumental track", value=False)
        seed = st.number_input(
            "Seed (0 = random)",
            min_value=0,
            max_value=2**31 - 1,
            value=0,
        )

    disabled = False

    if not can_use_cooldown("song_gen_cd", 30):
        st.info("⏳ Please wait before generating another song.")
        disabled = True

    # ---------------------------------------------------------
    # SUBMIT
    # ---------------------------------------------------------
    if st.button("🎵 Generate Suno Tracks", disabled=disabled):

        if ENABLE_DEBUG_TOOLS:
            print("\n==========================")
            print("[SongsGenerate] SUBMISSION DEBUG")
            print(f"User ID: {user['id']}")
            print(f"Lyrics ID (before auto-save): {lyrics_id}")
            print(f"Title input: {title}")
            print(f"Genre: {genre}")
            print(f"Style: {style}")
            print(f"Model: {model}")
            print(f"Vocal gender: {vocal_gender}")
            print(f"Tags raw: {tags_raw}")
            print(f"Instrumental: {instrumental}")
            print(f"Seed: {seed}")
            print("==========================\n")

        try:
            effective_lyrics_id = lyrics_id

            # Auto-save lyrics when pasted
            if effective_lyrics_id is None:
                prompt_used = "Manual lyrics (no OpenAI generation)"
                emoji = "🎵"

                effective_lyrics_id = execute_returning_id(
                    """
                    INSERT INTO lyrics (
                        user_id,
                        title,
                        emoji,
                        text,
                        mode,
                        prompt_used,
                        tokens,
                        cost,
                        archived
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0);
                    """,
                    (
                        user["id"],
                        title or "Untitled",
                        emoji,
                        clean_lyrics,
                        MODE_NORMAL,
                        prompt_used,
                        0,
                        0.0,
                    ),
                )

                if ENABLE_DEBUG_TOOLS:
                    print(f"[SongsGenerate] Auto-saved lyrics → ID {effective_lyrics_id}")

            tags = [t.strip() for t in (tags_raw or "").split(",") if t.strip()]

            if ENABLE_DEBUG_TOOLS:
                print("\n[SongsGenerate] Final Suno Parameters:")
                print({
                    "title": title,
                    "genre": genre,
                    "style": style,
                    "model": model,
                    "vocal_gender": vocal_gender,
                    "instrumental": instrumental,
                    "seed": seed,
                    "tags": tags,
                })
                print()

            # Create suno job
            with st.spinner("Sending request to Suno…"):
                job_id = create_tracks_from_suno(
                    user_id=user["id"],
                    lyrics_id=effective_lyrics_id,
                    lyrics_text=clean_lyrics,
                    suno_params={
                        "title": title,
                        "genre": genre,
                        "style": style,
                        "model": model,
                        "vocal_gender": vocal_gender,
                        "instrumental": instrumental,
                        "seed": seed,
                        "tags": tags,
                    },
                )

            trigger_cooldown("song_gen_cd")

            st.success(
                f"Task created! Job ID: `{job_id}`\n"
                "Downloading will begin automatically…"
            )

            # ---------------------------------------------------------
            # NEW: AUTO DOWNLOAD / POLLING
            # ---------------------------------------------------------
            with st.spinner("Checking CDN for your audio…"):
                try:
                    if ENABLE_DEBUG_TOOLS:
                        print("[SongsGenerate] Auto-polling now…")
                    process_pending_songs(user["id"])
                    st.success("Audio downloaded! View it in **Songs History**.")
                except Exception as e:
                    st.error(f"Auto-download error: {e}")
                    if ENABLE_DEBUG_TOOLS:
                        print("[SongsGenerate] AUTO-POLL ERROR:", e)

        except Exception as e:
            st.error(f"Error: {e}")
            if ENABLE_DEBUG_TOOLS:
                print("[SongsGenerate] ERROR:", e)
