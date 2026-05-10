# backend/models/songs.py

import json
import time
from typing import Dict, List, Optional, Union

from backend.db import execute, execute_returning_id, query_all, query_one
from constants import (
    STATUS_QUEUED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_GENERATING,
)

UserLike = Union[int, Dict]


# ---------------------------------------------------------
# Normalize user_id helper
# ---------------------------------------------------------
def _normalize_user_id(user_or_id: UserLike) -> int:
    if isinstance(user_or_id, dict):
        if "id" in user_or_id:
            return int(user_or_id["id"])
        if "user_id" in user_or_id:
            return int(user_or_id["user_id"])
        raise ValueError("Invalid user dict: missing 'id'")
    return int(user_or_id)


# ---------------------------------------------------------
# CREATE TRACK
# ---------------------------------------------------------
def create_song_track(
    user_id: int,
    lyrics_id: Optional[int],
    mode: str,
    job_id: str,
    track_label: str,
    suno_params: Dict,
    song_id: Optional[str] = None,
    status: str = STATUS_QUEUED,
    job_status: Optional[str] = None,
    audio_path: Optional[str] = None,
    video_path: Optional[str] = None,
    audio_url_remote: Optional[str] = None,
    video_url_remote: Optional[str] = None,
    error_message: Optional[str] = None,
) -> int:

    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    suno_params_json = json.dumps(suno_params or {}, ensure_ascii=False)

    sql = """
        INSERT INTO songs (
            user_id,
            lyrics_id,
            mode,
            job_id,
            task_id,
            song_id,
            track_label,
            audio_path,
            video_path,
            audio_url_remote,
            video_url_remote,
            status,
            job_status,
            error_message,
            suno_params_json,
            created_at,
            completed_at,
            archived
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0);
    """

    return execute_returning_id(
        sql,
        (
            user_id,
            lyrics_id,
            mode,
            job_id,
            job_id,  # task_id (legacy)
            song_id,
            track_label,
            audio_path,
            video_path,
            audio_url_remote,
            video_url_remote,
            status,
            job_status,
            error_message,
            suno_params_json,
            created_at,
        ),
    )


# ---------------------------------------------------------
# GETTERS
# ---------------------------------------------------------
def get_song_by_id(song_id: int) -> Optional[Dict]:
    return query_one("SELECT * FROM songs WHERE id = ?;", (song_id,))


def list_songs_for_user(user_or_id: UserLike) -> List[Dict]:
    uid = _normalize_user_id(user_or_id)
    return query_all(
        """
        SELECT *
        FROM songs
        WHERE user_id = ?
          AND (archived IS NULL OR archived = 0)
        ORDER BY created_at DESC;
        """,
        (uid,),
    )


def list_archived_songs_for_user(user_or_id: UserLike) -> List[Dict]:
    uid = _normalize_user_id(user_or_id)
    return query_all(
        """
        SELECT *
        FROM songs
        WHERE user_id = ?
          AND archived = 1
        ORDER BY created_at DESC;
        """,
        (uid,),
    )


def list_unfinished_songs(user_or_id: UserLike) -> List[Dict]:
    uid = _normalize_user_id(user_or_id)
    return query_all(
        """
        SELECT *
        FROM songs
        WHERE user_id = ?
          AND status IN (?, ?)
          AND (archived IS NULL OR archived = 0);
        """,
        (uid, STATUS_QUEUED, STATUS_GENERATING),
    )


# ---------------------------------------------------------
# UPDATE HELPERS
# ---------------------------------------------------------
def update_song_status(
    song_db_id: int,
    status: str,
    error_message: Optional[str] = None,
    job_status: Optional[str] = None,
) -> None:
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if status in (STATUS_COMPLETED, STATUS_FAILED):
        sql = """
            UPDATE songs
            SET status = ?,
                error_message = ?,
                job_status = ?,
                completed_at = ?
            WHERE id = ?;
        """
        execute(sql, (status, error_message, job_status, now, song_db_id))
    else:
        sql = """
            UPDATE songs
            SET status = ?,
                error_message = ?,
                job_status = ?
            WHERE id = ?;
        """
        execute(sql, (status, error_message, job_status, song_db_id))


def update_song_error(song_db_id: int, message: str) -> None:
    """
    REQUIRED by suno_polling.py.
    Marks the song with an error but does NOT change status.
    """
    execute(
        """
        UPDATE songs
        SET error_message = ?
        WHERE id = ?;
        """,
        (message, song_db_id),
    )


def update_local_paths(song_db_id: int, audio_path: Optional[str], video_path: Optional[str]) -> None:
    """
    REQUIRED by suno_polling.py.
    Updates audio/video local file paths.
    """
    row = get_song_by_id(song_db_id)
    if not row:
        return

    new_audio = audio_path or row.get("audio_path")
    new_video = video_path or row.get("video_path")

    execute(
        """
        UPDATE songs
        SET audio_path = ?, video_path = ?
        WHERE id = ?;
        """,
        (new_audio, new_video, song_db_id),
    )


def save_remote_urls(song_db_id: int, audio_url: Optional[str], video_url: Optional[str]):
    execute(
        """
        UPDATE songs
        SET audio_url_remote = ?, video_url_remote = ?
        WHERE id = ?;
        """,
        (audio_url, video_url, song_db_id),
    )


def mark_song_failed(song_db_id: int, error: str) -> None:
    update_song_status(
        song_db_id,
        STATUS_FAILED,
        error_message=error,
        job_status="failed",
    )


# ---------------------------------------------------------
# ARCHIVING
# ---------------------------------------------------------
def archive_song(song_id: int):
    execute("UPDATE songs SET archived = 1 WHERE id = ?;", (song_id,))
