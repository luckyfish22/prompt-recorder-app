import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts.db")


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            original_text TEXT NOT NULL,
            optimized_text TEXT,
            category_id INTEGER,
            is_optimized INTEGER DEFAULT 0,
            optimization_note TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category_id);
        CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at DESC);
    """)
    # Migration: add title column if missing (for DBs created before this column existed)
    try:
        conn.execute("SELECT title FROM prompts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE prompts ADD COLUMN title TEXT")
    conn.commit()
    conn.close()


# --- Category CRUD ---

def get_all_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY created_at").fetchall()
    conn.close()
    return rows


def add_category(name):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_category(category_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# --- Prompt CRUD ---

def save_prompt(original_text, category_id, optimized_text=None, is_optimized=0, optimization_note=None, title=None):
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO prompts (title, original_text, optimized_text, category_id, is_optimized, optimization_note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, original_text, optimized_text, category_id, is_optimized, optimization_note)
    )
    conn.commit()
    prompt_id = cursor.lastrowid
    conn.close()
    return prompt_id


def get_all_prompts(search=None):
    conn = get_connection()
    if search:
        rows = conn.execute(
            """SELECT p.*, c.name as category_name
               FROM prompts p LEFT JOIN categories c ON p.category_id = c.id
               WHERE p.title LIKE ? OR p.original_text LIKE ? OR p.optimized_text LIKE ?
               ORDER BY p.created_at DESC""",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.*, c.name as category_name
               FROM prompts p LEFT JOIN categories c ON p.category_id = c.id
               ORDER BY p.created_at DESC"""
        ).fetchall()
    conn.close()
    return rows


def delete_prompt(prompt_id):
    conn = get_connection()
    conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    conn.commit()
    conn.close()


# Initialize DB on module load
init_db()
