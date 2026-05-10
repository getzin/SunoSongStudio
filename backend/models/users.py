# backend/models/users.py

from typing import Dict, Optional

from backend.db import execute, query_one
from backend.db import execute_returning_id


def get_user_by_email(email: str) -> Optional[Dict]:
    return query_one("SELECT * FROM users WHERE email = ?;", (email,))


def get_user_by_id(user_id: int) -> Optional[Dict]:
    return query_one("SELECT * FROM users WHERE id = ?;", (user_id,))


def create_user(email: str, username: str, password_hash: str, is_admin: int = 0) -> int:
    return execute_returning_id(
        """
        INSERT INTO users (email, username, password_hash, is_admin)
        VALUES (?, ?, ?, ?);
        """,
        (email, username, password_hash, is_admin),
    )


# --------------------------
# API KEY MANAGEMENT
# --------------------------

def get_api_keys(user_id: int) -> Optional[Dict]:
    return query_one("SELECT * FROM api_keys WHERE user_id = ?;", (user_id,))


def upsert_api_keys(user_id: int, openai_key: Optional[str], suno_key: Optional[str]) -> None:
    exists = get_api_keys(user_id)
    if exists:
        execute(
            """
            UPDATE api_keys
            SET openai_key = ?, suno_key = ?
            WHERE user_id = ?;
            """,
            (openai_key, suno_key, user_id),
        )
    else:
        execute(
            """
            INSERT INTO api_keys (user_id, openai_key, suno_key)
            VALUES (?, ?, ?);
            """,
            (user_id, openai_key, suno_key),
        )
