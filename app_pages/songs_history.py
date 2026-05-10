import streamlit as st
from pathlib import Path
import json
import requests

from backend.models.songs import (
    list_songs_for_user,
    list_archived_songs_for_user,
    archive_song,
    list_unfinished_songs,
)
from backend.models.lyrics import get_lyrics_by_id
from backend.services.suno_polling import try_fetch_missing_media_for_song

from shared.layout import require_login
from shared.session import get_current_user
from shared.utils import can_use_cooldown, trigger_cooldown

COOLDOWN_KEY_SUNO_HISTORY = "suno_pending_check_history"


# ---------------------------------------------------------
# Emoji resolver — prefer lyrics.emoji
# ---------------------------------------------------------
def _resolve_song_emoji(row: dict, params: dict) -> str:
    emoji = None

    lyrics_id = row.get("lyrics_id")
    if lyrics_id:
        try:
            lyr = get_lyrics_by_id(lyrics_id)
            if lyr:
                emoji = (lyr.get("emoji") or "").strip() or None
        except Exception:
            pass

    if not emoji:
        emoji = (params.get("emoji") or "").strip() or "🎵"

    return emoji


# ---------------------------------------------------------
# Expanded View
# ---------------------------------------------------------
def _render_expanded(row: dict):
    st.markdown("<div class='song-expanded'>", unsafe_allow_html=True)

    track_label = row.get("track_label")
    status = row.get("status")
    audio_path = row.get("audio_path")
    video_path = row.get("video_path")
    audio_url = row.get("audio_url_remote")
    video_url = row.get("video_url_remote")
    error_msg = row.get("error_message")

    raw_params = row.get("suno_params_json") or "{}"
    params = json.loads(raw_params)

    title = params.get("title", "") or "Untitled"
    emoji = _resolve_song_emoji(row, params)

    provider = params.get("provider_raw", {})
    image_large = provider.get("image_large_url") or provider.get("image_url")

    # Nicely sized expanded image (90% width, centered, rounded)
    if image_large:
        st.markdown(
            f"""
            <div style="width:90%; max-width:900px; margin:auto;">
                <img src="{image_large}" style="width:100%; border-radius:12px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"### {emoji} {title} — Track {track_label}")

    # Status
    if status == "completed":
        st.success("Completed")
    elif status == "failed":
        st.error(f"Failed: {error_msg or 'Unknown error'}")
    else:
        st.info(f"Status: {status}")

    # Audio
    st.markdown("#### ▶️ Audio")
    if audio_path and Path(audio_path).exists():
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes)
        st.download_button("⬇ Download audio", audio_bytes, Path(audio_path).name)
    elif audio_url:
        st.info("Download from CDN:")
        data = requests.get(audio_url).content
        st.audio(data)
        st.download_button("⬇ Download audio from CDN", data, f"{track_label}.mp3")
    else:
        st.warning("No audio found")

    # Video
    st.markdown("#### 🎬 Video")
    if video_path and Path(video_path).exists():
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        st.video(video_bytes)
        st.download_button("⬇ Download video", video_bytes, Path(video_path).name)
    elif video_url:
        data = requests.get(video_url).content
        st.video(data)
        st.download_button("⬇ Download video from CDN", data, f"{track_label}.mp4")
    else:
        st.info("No video available")

    # Metadata
    st.markdown("#### 📝 Metadata")
    st.json(params)

    # Archive button
    if st.button(f"Archive Track {track_label}", key=f"arc_{row['id']}"):
        archive_song(row["id"])
        st.success("Archived.")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Compact ROW — image + info side by side
# ---------------------------------------------------------
def _compact_row(row: dict):
    raw_params = row.get("suno_params_json") or "{}"
    params = json.loads(raw_params)

    title = params.get("title", "Untitled")
    emoji = _resolve_song_emoji(row, params)

    provider = params.get("provider_raw", {})
    img_thumb = provider.get("image_url") or provider.get("image_large_url")

    status = row.get("status")
    created = row.get("created_at")
    track_label = row.get("track_label")

    # Status badge logic
    if status == "completed":
        badge = "song-ok"
        stext = "OK"
    elif status == "failed":
        badge = "song-failed"
        stext = "Failed"
    else:
        badge = "song-pending"
        stext = "Pending"

    card_id = f"songcard_{row['id']}"

    # 2-column layout: [image] [text + button]
    col_img, col_info = st.columns([1, 8])

    with col_img:
        if img_thumb:
            st.image(img_thumb, width=120)

    with col_info:
        st.markdown(
            f"""
            <div class="song-row" id="{card_id}">
                <div class="song-row-title">{emoji} {title}</div>
                <div class="song-row-meta">
                    Track {track_label} · {created}
                    <span class="song-row-status {badge}">{stext}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        clicked = st.button(
            "open_" + card_id,
            key=f"open_btn_{row['id']}",
            help="Click to expand",
            width="stretch",
        )

    return clicked


# ---------------------------------------------------------
# MAIN PAGE
# ---------------------------------------------------------
def run():
    require_login()
    user = get_current_user()

    st.subheader("📜 Your Generated Songs")

    # Sync pending CDN downloads
    if can_use_cooldown(COOLDOWN_KEY_SUNO_HISTORY, 30):
        pending = list_unfinished_songs(user["id"])
        for row in pending:
            try_fetch_missing_media_for_song(row)
        trigger_cooldown(COOLDOWN_KEY_SUNO_HISTORY)

    # Archived toggle
    show_archived = st.checkbox("Show archived songs", value=False)

    rows = (
        list_songs_for_user(user["id"])
        if not show_archived
        else list_archived_songs_for_user(user["id"])
    )

    if not rows:
        st.info("No songs found.")
        return

    st.markdown("### ⭐ Active Songs" if not show_archived else "### 📦 Archived")

    for row in rows:
        if _compact_row(row):
            _render_expanded(row)
            st.markdown("---")
