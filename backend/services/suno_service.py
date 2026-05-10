# backend/services/suno_service.py

import json
import requests
from pathlib import Path

from constants import (
    ACE_AUDIO_URL,
    STATUS_QUEUED,
    STATUS_COMPLETED,
    generate_track_label,
    ENABLE_DEBUG_TOOLS,
)

from backend.models.songs import (
    create_song_track,
    list_unfinished_songs,
    save_remote_urls,
)
from backend.services.suno_payload_builder import build_suno_payload


# ---------------------------------------------------------
# Gender normalization helper
# ---------------------------------------------------------
def _normalize_gender(g):
    if not g:
        return "f"
    g = g.lower().strip()
    if g in ("f", "female", "woman", "girl"):
        return "f"
    if g in ("m", "male", "man", "boy"):
        return "m"
    return "f"


# ---------------------------------------------------------
# SUNO KEY RESOLUTION
# ---------------------------------------------------------
def resolve_suno_key(api_keys_row):
    if not api_keys_row:
        return None
    return api_keys_row.get("suno_key")


# ---------------------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------------------
def create_tracks_from_suno(
    user_id: int,
    lyrics_id: int | None,
    lyrics_text: str,
    suno_params: dict,
    api_key: str = None,
    mode: str = "base",
    **kwargs,
) -> str:
    """
    Create a Suno job for 2 tracks via AceData.

    S1 STRUCTURE (final):
      - OpenAI JSON templates DO NOT include Suno data anymore.
      - All Suno config is supplied manually via `suno_params`.
      - We ALWAYS create DB rows with status=queued, then a separate
        polling step downloads media and flips them to completed.
    """

    # -----------------------------------------------------
    # Resolve Suno key
    # -----------------------------------------------------
    if not api_key:
        from backend.models.users import get_api_keys
        api_keys = get_api_keys(user_id) or {}
        api_key = api_keys.get("suno_key")

    if not api_key:
        raise RuntimeError("Missing Suno / AceData API key.")

    clean_lyrics = (lyrics_text or "").strip()
    if not clean_lyrics:
        raise RuntimeError("Lyrics text is empty.")

    # -----------------------------------------------------
    # Build Suno metadata (decoupled from OpenAI JSONs)
    # -----------------------------------------------------
    genre = (suno_params.get("genre") or "").strip()
    style = (suno_params.get("style") or "").strip()
    tags = suno_params.get("tags") or []

    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    prompt_parts: list[str] = []
    if genre:
        prompt_parts.append(genre)
    if style:
        prompt_parts.append(style)
    if tags:
        prompt_parts.append(", ".join(tags))

    # Default prompt if user leaves everything empty
    prompt = ", ".join(prompt_parts) if prompt_parts else "Pop Music, Emotional Female Vocal"

    # Default model upgraded to chirp-v5
    model = suno_params.get("model") or "chirp-v5"
    title = suno_params.get("title") or "Untitled"
    instrumental = bool(suno_params.get("instrumental", False))
    vocal_gender = _normalize_gender(suno_params.get("vocal_gender"))

    base_suno_json = {
        "model": model,
        "prompt": prompt,
        "custom": True,
        "instrumental": instrumental,
        "title": title,
        "style": style,
        "vocal_gender": vocal_gender,
        "genre": genre,
        "tags": tags,
        "seed": suno_params.get("seed"),          # stored for metadata; not sent to AceData
        "num_tracks": suno_params.get("num_tracks"),
        "mode": mode,
    }

    # -----------------------------------------------------
    # Build final AceData payload
    # -----------------------------------------------------
    payload = build_suno_payload(base_suno_json, clean_lyrics)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if ENABLE_DEBUG_TOOLS:
        print("\n==========================")
        print("[SunoService] Creating Suno job via /audios …")
        try:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        except Exception:
            print(payload)
        print("==========================\n")

    # -----------------------------------------------------
    # POST to AceData
    # -----------------------------------------------------
    res = requests.post(
        ACE_AUDIO_URL,
        json=payload,
        headers=headers,
        timeout=300,
    )

    if not res.ok:
        raise RuntimeError(f"Suno /audios error: {res.status_code} {res.text}")

    body = res.json()

    if ENABLE_DEBUG_TOOLS:
        print("\n========== ACE DATA RAW RESPONSE ==========")
        try:
            print(json.dumps(body, indent=2, ensure_ascii=False))
        except Exception:
            print(body)
        print("===========================================\n")

    job_id = body.get("task_id") or body.get("id")
    tracks = body.get("data") or body.get("outputs") or []

    if not job_id or not tracks:
        raise RuntimeError("Suno returned no tracks.")

    # -----------------------------------------------------
    # INSERT EACH TRACK INTO DATABASE
    # -----------------------------------------------------
    for i, track in enumerate(tracks):
        if ENABLE_DEBUG_TOOLS:
            print("\n=== TRACK DEBUG ===")
            print("RAW TRACK KEYS:", list(track.keys()))
            try:
                print(json.dumps(track, indent=2, ensure_ascii=False))
            except Exception:
                print(track)
            print("====================\n")

        track_label = generate_track_label(i)
        provider_song_id = track.get("id")

        audio_url = track.get("audio_url")
        video_url = track.get("video_url") or None
        provider_state = track.get("state") or track.get("status")
        provider_title = track.get("title") or None
        provider_duration = track.get("duration")  # may be None

        if ENABLE_DEBUG_TOOLS:
            print(f"[DEBUG] Extracted URLs for {track_label}:")
            print("  audio_url =", repr(audio_url))
            print("  video_url =", repr(video_url))

        # 1. Suno may return "Untitled" even when user supplied a title.
        # 2. Prefer Suno’s title ONLY if it is meaningful.
        if provider_title and provider_title.strip().lower() != "untitled":
            final_title = provider_title
        else:
            final_title = base_suno_json.get("title") or "Untitled"

        per_track_params = {
            **base_suno_json,
            "title": final_title,
            "duration": provider_duration,
            "provider_raw": track,
        }

        # IMPORTANT:
        #   We always start as QUEUED so that the polling/downloader
        #   will fetch the CDN media and then flip to COMPLETED.
        status = STATUS_QUEUED

        # CREATE DB ROW
        song_db_id = create_song_track(
            user_id=user_id,
            lyrics_id=lyrics_id,
            mode=mode,
            job_id=job_id,
            track_label=track_label,
            suno_params=per_track_params,
            song_id=provider_song_id,
            status=status,
            job_status=provider_state,
            audio_path=None,
            video_path=None,
            audio_url_remote=None,
            video_url_remote=None,
            error_message=None,
        )

        if ENABLE_DEBUG_TOOLS:
            print(f"[DEBUG] Saving URLs → DB row {song_db_id}")
        save_remote_urls(song_db_id, audio_url, video_url)
        if ENABLE_DEBUG_TOOLS:
            print(f"[SunoService] Stored {track_label} → audio={audio_url}, video={video_url}")

    return job_id


# ---------------------------------------------------------
# PROCESS PENDING SONGS (CDN only)
# ---------------------------------------------------------
def process_pending_songs(user_or_id):
    """
    Find any songs for this user that are still pending
    (e.g. have remote URLs but no local files yet) and try
    to download audio/video from the CDN.

    This is usually called from the Songs History page or Dashboard.
    """
    if isinstance(user_or_id, dict):
        uid = user_or_id.get("id")
    else:
        uid = user_or_id

    rows = list_unfinished_songs(uid)
    if not rows:
        return

    if ENABLE_DEBUG_TOOLS:
        print(f"[SunoService] Processing {len(rows)} pending songs for user {uid}…")

    # Avoid circular import
    from backend.services.suno_polling import try_fetch_missing_media_for_song

    for row in rows:
        try:
            try_fetch_missing_media_for_song(row)
        except Exception as e:
            if ENABLE_DEBUG_TOOLS:
                print(f"[SunoService] Media fetch error for song {row['id']}: {e}")
