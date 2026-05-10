# backend/db.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import bcrypt

from constants import DB_PATH, ADMIN_EMAIL, ADMIN_PASSWORD




def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def execute(query: str, params: Iterable[Any] = ()) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        conn.commit()
    finally:
        conn.close()


def execute_returning_id(query: str, params: Iterable[Any] = ()) -> int:
    """
    Execute an INSERT and return the last inserted row ID.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def query_one(query: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def query_all(query: str, params: Iterable[Any] = ()) -> list[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        # allow params to be None / empty
        cur.execute(query, tuple(params) if params is not None else [])
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _ensure_songs_extra_columns(conn: sqlite3.Connection) -> None:
    """
    Add new nullable columns to `songs` if they don't exist yet.
    This keeps old DBs compatible with newer code.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(songs);")
    cols = {row["name"] for row in cur.fetchall()}

    # task_id: AceData / Suno task identifier
    if "task_id" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN task_id TEXT;")
        print("[MIGRATION] Added songs.task_id (TEXT)")

    # job_status: high-level status of the Suno job (queued/running/completed/failed)
    if "job_status" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN job_status TEXT;")
        print("[MIGRATION] Added songs.job_status (TEXT)")

    # song_id: Suno's per-track ID (used by some queries in songs.py)
    if "song_id" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN song_id TEXT;")
        print("[MIGRATION] Added songs.song_id (TEXT)")

    # audio_url_remote: original CDN URL for the audio file
    if "audio_url_remote" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN audio_url_remote TEXT;")
        print("[MIGRATION] Added songs.audio_url_remote (TEXT)")

    # video_url_remote: original CDN URL for the video file (if any)
    if "video_url_remote" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN video_url_remote TEXT;")
        print("[MIGRATION] Added songs.video_url_remote (TEXT)")

    # archived: user-requested hide flag for songs
    if "archived" not in cols:
        cur.execute("ALTER TABLE songs ADD COLUMN archived INTEGER NOT NULL DEFAULT 0;")
        print("[MIGRATION] Added songs.archived (INTEGER DEFAULT 0)")

    conn.commit()


def run_migrations() -> None:
    """
    Create all tables (idempotent), auto-upgrade schema,
    and insert admin if DB is empty.
    """
    # --- base schema creation ---
    conn = get_connection()
    try:
        cur = conn.cursor()

        # users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # api_keys
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                openai_key TEXT,
                suno_key TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # lyrics
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lyrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                emoji TEXT NOT NULL,
                text TEXT NOT NULL,
                mode TEXT NOT NULL,
                prompt_used TEXT NOT NULL,
                tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                archived INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # songs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                lyrics_id INTEGER REFERENCES lyrics(id),
                mode TEXT NOT NULL,
                job_id TEXT,
                task_id TEXT,
                song_id TEXT,
                track_label TEXT NOT NULL,
                audio_path TEXT,
                video_path TEXT,
                audio_url_remote TEXT,
                video_url_remote TEXT,
                status TEXT NOT NULL,
                job_status TEXT,
                error_message TEXT,
                suno_params_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            """
        )

        conn.commit()
    finally:
        conn.close()

    # --- auto-migrations for older DBs (no noisy logs on every run) ---
    conn = get_connection()
    try:
        _ensure_songs_extra_columns(conn)
    finally:
        conn.close()

    # --- create admin user if DB empty ---
    row = query_one("SELECT COUNT(*) AS c FROM users;")
    if row and row["c"] == 0 and ADMIN_EMAIL and ADMIN_PASSWORD:
        hash_pw = bcrypt.hashpw(
            ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        execute(
            """
            INSERT INTO users (email, username, password_hash, is_admin)
            VALUES (?, ?, ?, 1);
            """,
            (ADMIN_EMAIL, ADMIN_EMAIL.split("@")[0], hash_pw),
        )
