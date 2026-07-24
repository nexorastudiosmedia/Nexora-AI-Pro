import sqlite3
from pathlib import Path

# =====================================================
# Database Location
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nexora.db"


# =====================================================
# Database Connection
# =====================================================

def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# Create Tables
# =====================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS facebook_pages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            page_name TEXT NOT NULL,

            page_id TEXT NOT NULL UNIQUE,

            access_token TEXT NOT NULL,

            niche TEXT,

            status TEXT DEFAULT 'Connected',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    conn.commit()

    conn.close()


# =====================================================
# Get All Pages
# =====================================================

def get_all_pages():

    conn = get_connection()

    pages = conn.execute("""

        SELECT *

        FROM facebook_pages

        ORDER BY id DESC

    """).fetchall()

    conn.close()

    return pages


# =====================================================
# Add Facebook Page
# =====================================================

def add_page(page_name, page_id, access_token, niche):

    conn = get_connection()

    try:

        conn.execute("""

            INSERT INTO facebook_pages
            (
                page_name,
                page_id,
                access_token,
                niche
            )

            VALUES
            (
                ?,
                ?,
                ?,
                ?
            )

        """, (

            page_name,
            page_id,
            access_token,
            niche

        ))

        conn.commit()

        return True, "Facebook Page added successfully."

    except sqlite3.IntegrityError:

        return False, "Page ID already exists."

    except Exception as e:

        return False, str(e)

    finally:

        conn.close()


# =====================================================
# Delete Facebook Page
# =====================================================

def delete_page(page_id):

    conn = get_connection()

    conn.execute("""

        DELETE

        FROM facebook_pages

        WHERE page_id=?

    """, (

        page_id,

    ))

    conn.commit()

    conn.close()


# =====================================================
# Update Facebook Page
# =====================================================

def update_page(page_name, access_token, niche, page_id):

    conn = get_connection()

    conn.execute("""

        UPDATE facebook_pages

        SET

            page_name=?,

            access_token=?,

            niche=?

        WHERE

            page_id=?

    """, (

        page_name,

        access_token,

        niche,

        page_id

    ))

    conn.commit()

    conn.close()


# =====================================================
# Get Single Page
# =====================================================

def get_page(page_id):

    conn = get_connection()

    page = conn.execute("""

        SELECT *

        FROM facebook_pages

        WHERE page_id=?

    """, (

        page_id,

    )).fetchone()

    conn.close()

    return page


# =====================================================
# Count Pages
# =====================================================

def count_pages():

    conn = get_connection()

    total = conn.execute("""

        SELECT COUNT(*)

        FROM facebook_pages

    """).fetchone()[0]

    conn.close()

    return total