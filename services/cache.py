import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "profile_cache.db"
TIMEZONE = ZoneInfo("Asia/Jakarta")

# Time initialization
def get_now():
    return datetime.now(TIMEZONE)

# Connect
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
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

# Get profile
def get_profile(
    username: str,
    language: str
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

    result = json.loads(
        row["result_json"]
    )

    created_at = datetime.fromisoformat(
        row["created_at"]
    )

    if created_at.tzinfo is None:
        created_at = created_at.replace(
            tzinfo=TIMEZONE
        )

    result["last_updated"] = created_at.isoformat()

    return result

# Get all profiles
def get_all_profiles():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            username,
            language,
            created_at AS last_updated
        FROM profile_cache
        ORDER BY username DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]

# Save profile
def save_profile(
    username: str,
    language: str,
    result: dict
):
    conn = get_connection()

    created_at = datetime.now(
        ZoneInfo("Asia/Jakarta")
    ).isoformat()

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
        created_at
    ))

    conn.commit()
    conn.close()

# Get existing language
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

# Get updated at
def get_profile_updated_at(
    username: str,
    language: str
):
    conn = get_connection()

    row = conn.execute("""
        SELECT created_at
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

    return row["created_at"]

# Delete profile
def delete_profile(
    username: str,
    language: str
):
    conn = get_connection()

    conn.execute("""
        DELETE FROM profile_cache
        WHERE username = ?
        AND language = ?
    """, (
        username,
        language
    ))

    conn.commit()
    conn.close()
