import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "profile_cache.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profile_cache (
            username TEXT NOT NULL,
            language TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,

            PRIMARY KEY (username, language)
        )
    """)

    conn.commit()
    conn.close()


def get_profile(
    username: str,
    language: str,
    ttl_hours: int = 24
):
    conn = get_connection()

    row = conn.execute("""
        SELECT result_json, created_at
        FROM profile_cache
        WHERE username = ?
        AND language = ?
    """, (
        username,
        language
    )).fetchone()

    conn.close()

    if row is None:
        return None

    created_at = datetime.fromisoformat(
        row["created_at"]
    )

    if datetime.utcnow() - created_at > timedelta(hours=ttl_hours):
        return None

    return json.loads(
        row["result_json"]
    )


def save_profile(
    username: str,
    language: str,
    result: dict
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO profile_cache (
            username,
            language,
            result_json,
            created_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(username, language)
        DO UPDATE SET
            result_json = excluded.result_json,
            created_at = excluded.created_at
    """, (
        username,
        language,
        json.dumps(result),
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

def get_existing_language(username: str):
    conn = get_connection()

    row = conn.execute("""
        SELECT language
        FROM profile_cache
        WHERE username = ?
        LIMIT 1
    """, (username,)).fetchone()

    conn.close()

    if row is None:
        return None

    return row["language"]