# backend/models/lyrics.py

from backend.db import execute, execute_returning_id, query_all, query_one


def create_lyrics(user_id, title, emoji, text, mode, prompt_used, tokens, cost):
    sql = """
        INSERT INTO lyrics (user_id, title, emoji, text, mode, prompt_used, tokens, cost, archived)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """
    return execute_returning_id(
        sql,
        (user_id, title, emoji, text, mode, prompt_used, tokens, cost)
    )


def list_lyrics_for_user(user_id, include_archived=False):
    """
    New → supports include_archived=True
    """

    if include_archived:
        sql = """
            SELECT *
            FROM lyrics
            WHERE user_id = ?
            ORDER BY id DESC
        """
        return query_all(sql, (user_id,))

    sql = """
        SELECT *
        FROM lyrics
        WHERE user_id = ?
          AND archived = 0
        ORDER BY id DESC
    """
    return query_all(sql, (user_id,))


def get_lyrics_by_id(lyrics_id):
    sql = "SELECT * FROM lyrics WHERE id = ?"
    return query_one(sql, (lyrics_id,))


def update_lyrics_title(lyrics_id, new_title):
    sql = "UPDATE lyrics SET title = ? WHERE id = ?"
    execute(sql, (new_title, lyrics_id))


def update_lyrics_emoji(lyrics_id, new_emoji):
    sql = "UPDATE lyrics SET emoji = ? WHERE id = ?"
    execute(sql, (new_emoji, lyrics_id))


def archive_lyrics(lyrics_id):
    sql = "UPDATE lyrics SET archived = 1 WHERE id = ?"
    execute(sql, (lyrics_id,))
