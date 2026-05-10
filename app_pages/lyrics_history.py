# app_pages/lyrics_history.py

import streamlit as st

from shared.session import get_current_user
from backend.models.lyrics import (
    list_lyrics_for_user,
    archive_lyrics,
    update_lyrics_title,
    update_lyrics_emoji,
)
from constants import (
    MODE_NORMAL,
    MODE_CAT,
    MODE_XMAS,
)
from backend.services.openai_service import get_mode_emoji_list


def _mode_label(mode: str) -> str:
    if mode == MODE_CAT:
        return "Cat"
    if mode == MODE_XMAS:
        return "Xmas"
    return "Normal"


def run():
    st.title("Lyrics History 📜")

    user = get_current_user()
    if not user:
        st.error("Not logged in.")
        return

    include_archived = st.checkbox("Show archived lyrics", value=False)

    lyrics_list = list_lyrics_for_user(user["id"], include_archived=include_archived)

    if not lyrics_list:
        st.info("No lyrics yet. Go to **Lyrics Generate** to create some.")
        return

    for row in lyrics_list:
        lid = row["id"]
        emoji = row.get("emoji") or ""
        title = row["title"]
        mode = row["mode"]
        created_at = row["created_at"]
        cost = row.get("cost", 0.0)
        tokens = row.get("tokens", 0)

        # --------------------------
        # CARD WRAPPER
        # --------------------------
        with st.container():
            st.markdown('<div class="card lyrics-card">', unsafe_allow_html=True)

            st.markdown(f"## {emoji} {title}")
            st.caption(
                f"Mode: `{_mode_label(mode)}` · Created: {created_at} · "
                f"Tokens: {tokens} · Cost: ${cost:.4f}"
            )

            st.text_area(
                "Lyrics preview",
                row["text"],
                height=180,
                disabled=True,
                key=f"lyrics_history_preview_{lid}",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🎧 Generate Song from these lyrics", key=f"btn_gen_song_{lid}"):
                    st.session_state["selected_lyrics_id"] = lid
                    st.session_state["pending_nav"] = "Songs Generate"
                    st.rerun()

            with col2:
                if not include_archived:
                    if st.button("🗂️ Archive", key=f"btn_archive_{lid}"):
                        archive_lyrics(lid)
                        st.success("Lyrics archived.")
                        st.rerun()

            # --- Edit metadata ---
            with st.expander("Edit title & emoji", expanded=False):
                new_title = st.text_input(
                    "Title",
                    value=title,
                    key=f"edit_title_{lid}",
                )

                emoji_choices = get_mode_emoji_list(mode)
                current_emoji = emoji if emoji in emoji_choices else emoji_choices[0]

                new_emoji = st.selectbox(
                    "Emoji",
                    emoji_choices,
                    index=emoji_choices.index(current_emoji),
                    key=f"edit_emoji_{lid}",
                )

                if st.button("Save changes", key=f"save_meta_{lid}"):
                    clean_title = (new_title or "").strip() or "Untitled"

                    if clean_title != title:
                        update_lyrics_title(lid, clean_title)

                    if new_emoji != emoji:
                        update_lyrics_emoji(lid, new_emoji)

                    st.success("Metadata updated.")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
