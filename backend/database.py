import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nexora.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'Admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS facebook_pages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_name TEXT NOT NULL,
        page_id TEXT UNIQUE NOT NULL,
        access_token TEXT NOT NULL,
        niche TEXT,
        status TEXT DEFAULT 'Connected',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL,
        platform TEXT,
        tone TEXT,
        language TEXT,
        generated_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    admin = cur.execute(
        "SELECT id FROM users WHERE email=?",
        ("admin@nexora.ai",)
    ).fetchone()

    if not admin:
        cur.execute(
            "INSERT INTO users(email,password,full_name) VALUES(?,?,?)",
            (
                "admin@nexora.ai",
                generate_password_hash("admin123"),
                "Administrator"
            )
        )

    conn.commit()
    conn.close()


def verify_user(email, password):
    conn = get_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):
        return user

    return None


# ==========================
# Facebook Pages
# ==========================

def get_all_pages():
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM facebook_pages ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return rows


def add_page(page_name, page_id, access_token, niche):
    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO facebook_pages
            (
                page_name,
                page_id,
                access_token,
                niche
            )
            VALUES
            (
                ?,?,?,?
            )
            """,
            (
                page_name,
                page_id,
                access_token,
                niche
            )
        )

        conn.commit()

        return True, "Facebook Page added successfully."

    except sqlite3.IntegrityError:

        return False, "Page ID already exists."

    finally:

        conn.close()


def delete_page(page_id):
    conn = get_connection()

    conn.execute(
        "DELETE FROM facebook_pages WHERE page_id=?",
        (page_id,)
    )

    conn.commit()
    conn.close()


def get_page(page_id):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM facebook_pages WHERE page_id=?",
        (page_id,)
    ).fetchone()

    conn.close()

    return row


def update_page(page_name, access_token, niche, page_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE facebook_pages
        SET
            page_name=?,
            access_token=?,
            niche=?
        WHERE
            page_id=?
        """,
        (
            page_name,
            access_token,
            niche,
            page_id
        )
    )

    conn.commit()
    conn.close()


def count_pages():
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM facebook_pages"
    ).fetchone()[0]

    conn.close()

    return total


# ==========================
# AI POSTS
# ==========================

def save_ai_post(prompt, platform, tone, language, generated_text):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO ai_posts
        (
            prompt,
            platform,
            tone,
            language,
            generated_text
        )
        VALUES
        (
            ?,?,?,?,?
        )
        """,
        (
            prompt,
            platform,
            tone,
            language,
            generated_text
        )
    )

    conn.commit()
    conn.close()


def get_ai_posts():
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM ai_posts ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return rows


def delete_ai_post(post_id):
    conn = get_connection()

    conn.execute(
        "DELETE FROM ai_posts WHERE id=?",
        (post_id,)
    )

    conn.commit()
    conn.close()


def count_ai_posts():
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM ai_posts"
    ).fetchone()[0]

    conn.close()

    return total