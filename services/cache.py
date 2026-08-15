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
def get_all_profiles(
    page=1,
    per_page=20,
    search="",
    sort_by="last_updated",
    sort_order="desc"
):
    conn = get_connection()

    allowed_sort_columns = {
        "username": "username",
        "language": """
            CASE language
                WHEN 'en' THEN 1
                WHEN 'id' THEN 2
                WHEN 'es' THEN 3
                ELSE 99
            END
        """,
        "last_updated": "created_at",
    }

    sort_column = allowed_sort_columns.get(
        sort_by,
        "created_at"
    )

    sort_direction = (
        "ASC"
        if sort_order.lower() == "asc"
        else "DESC"
    )

    offset = (page - 1) * per_page

    search = search.strip()

    if search:
        search_pattern = f"%{search}%"

        rows = conn.execute(
            f"""
            SELECT
                username,
                language,
                created_at AS last_updated
            FROM profile_cache
            WHERE username LIKE ?
            ORDER BY {sort_column} {sort_direction}
            LIMIT ? OFFSET ?
            """,
            (
                search_pattern,
                per_page,
                offset
            )
        ).fetchall()

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM profile_cache
            WHERE username LIKE ?
            """,
            (search_pattern,)
        ).fetchone()[0]

    else:
        rows = conn.execute(
            f"""
            SELECT
                username,
                language,
                created_at AS last_updated
            FROM profile_cache
            ORDER BY {sort_column} {sort_direction}
            LIMIT ? OFFSET ?
            """,
            (
                per_page,
                offset
            )
        ).fetchall()

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM profile_cache
            """
        ).fetchone()[0]

    conn.close()

    return {
        "profiles": [dict(row) for row in rows],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (
                (total + per_page - 1) // per_page
            )
        }
    }

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
