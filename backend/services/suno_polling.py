# backend/services/suno_polling.py

import os
import time
import json
import requests
from pathlib import Path

from constants import (
    STATUS_QUEUED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_GENERATING,
    ENABLE_DEBUG_TOOLS,
)

from backend.models.songs import (
    update_song_status,
    update_song_error,
    update_local_paths,
    get_song_by_id,
)


# =========================================================
# ✓ SAFE LOCAL PATH BUILDER
# =========================================================
def _safe_local_path(track_id: int, title: str | None, ext: str = "mp3") -> Path:
    """
    Builds:  data/audio/<track_id>_<title>.mp3
    Ensures filesystem-safe slugs.
    """
    safe_title = (title or "Untitled").strip().lower()
    safe_title = safe_title.replace(" ", "_")
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in ("_", "-"))

    if not safe_title:
        safe_title = "untitled"

    base_dir = Path("data/audio")
    base_dir.mkdir(parents=True, exist_ok=True)

    final_path = base_dir / f"{track_id}_{safe_title}.{ext}"

    if ENABLE_DEBUG_TOOLS:
        print(f"[Polling] Local save path resolved → {final_path}")

    return final_path


# =========================================================
# ✓ DOWNLOAD HELPER
# =========================================================
def _download_file(url: str, dest_path: Path) -> bool:
    """
    Downloads the remote file.
    Returns True if saved; False on error.
    """
    try:
        if ENABLE_DEBUG_TOOLS:
            print(f"[Polling] Attempting download from URL: {url}")

        resp = requests.get(url, timeout=60)

        if resp.status_code != 200:
            if ENABLE_DEBUG_TOOLS:
                print(f"[Polling] ERROR: HTTP {resp.status_code} while downloading {url}")
            return False

        with open(dest_path, "wb") as f:
            f.write(resp.content)

        if ENABLE_DEBUG_TOOLS:
            print(f"[Polling] Download SUCCESS → {dest_path}")

        return True

    except Exception as e:
        if ENABLE_DEBUG_TOOLS:
            print(f"[Polling] EXCEPTION during download: {e}")
        return False


# =========================================================
# ✓ MAIN FETCH FUNCTION
# =========================================================
def try_fetch_missing_media_for_song(row: dict):
    """
    row: dict of one song entry from DB (list_unfinished_songs)
    Downloads audio/video and updates DB paths & status.
    """

    track_id = row["id"]

    # Title must come from suno_params_json
    title = None
    if "suno_params_json" in row:
        try:
            params = row["suno_params_json"]
            if isinstance(params, str):
                params = json.loads(params)
            title = params.get("title")
        except Exception:
            title = None

    if not title:
        title = "Untitled"

    audio_url = row.get("audio_url_remote")
    video_url = (row.get("video_url_remote") or "").strip()

    if ENABLE_DEBUG_TOOLS:
        print("\n===============================")
        print(f"[Polling] PROCESSING TRACK ID: {track_id}")
        print(f"[Polling] Title: {title}")
        print(f"[Polling] audio_url_remote: {audio_url}")
        print(f"[Polling] video_url_remote: {video_url}")
        print("===============================\n")

    audio_target = _safe_local_path(track_id, title, "mp3")
    video_target = _safe_local_path(track_id, title, "mp4")

    audio_ok = True
    video_ok = True

    # ------------------------------------------------------
    # AUDIO DOWNLOAD
    # ------------------------------------------------------
    if audio_url and not row.get("audio_path"):
        if ENABLE_DEBUG_TOOLS:
            print("[Polling] Audio missing → downloading…")

        audio_ok = _download_file(audio_url, audio_target)

        if audio_ok:
            update_local_paths(track_id, audio_path=str(audio_target), video_path=None)
        else:
            update_song_error(track_id, "Failed to download audio")
            update_song_status(track_id, STATUS_FAILED)
            return

    # ------------------------------------------------------
    # VIDEO DOWNLOAD
    # ------------------------------------------------------
    if video_url and not row.get("video_path"):
        if ENABLE_DEBUG_TOOLS:
            print("[Polling] Video missing → downloading…")

        video_ok = _download_file(video_url, video_target)

        if video_ok:
            update_local_paths(track_id, audio_path=None, video_path=str(video_target))
        else:
            update_song_error(track_id, "Failed to download video")
            update_song_status(track_id, STATUS_FAILED)
            return

    # ------------------------------------------------------
    # FINAL STATUS UPDATE
    # ------------------------------------------------------
    if audio_ok and video_ok:
        update_song_status(track_id, STATUS_COMPLETED)

        if ENABLE_DEBUG_TOOLS:
            print(f"[Polling] Track {track_id} marked COMPLETED.\n")
