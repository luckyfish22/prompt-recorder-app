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
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            original_text TEXT NOT NULL,
            optimized_text TEXT,
            folder_id INTEGER,
            is_optimized INTEGER DEFAULT 0,
            optimization_note TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        );

        CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at DESC);
    """)
    # Migration: add title column if missing
    try:
        conn.execute("SELECT title FROM prompts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE prompts ADD COLUMN title TEXT")
    # Migration: add folder_id column if missing
    try:
        conn.execute("SELECT folder_id FROM prompts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE prompts ADD COLUMN folder_id INTEGER REFERENCES folders(id)")
    # Migration: add position column if missing
    try:
        conn.execute("SELECT position FROM prompts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE prompts ADD COLUMN position INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


# --- Prompt CRUD ---

def save_prompt(original_text, optimized_text=None, is_optimized=0, optimization_note=None,
                title=None, folder_id=None):
    conn = get_connection()
    # Auto-assign position: max position in this folder + 1
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM prompts WHERE folder_id IS ?",
        (folder_id,)
    ).fetchone()
    position = row["next_pos"] if row else 0
    cursor = conn.execute(
        """INSERT INTO prompts (title, original_text, optimized_text, is_optimized, optimization_note, folder_id, position)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, original_text, optimized_text, is_optimized, optimization_note, folder_id, position)
    )
    conn.commit()
    prompt_id = cursor.lastrowid
    conn.close()
    return prompt_id


def get_all_prompts(search=None, folder_id=None):
    conn = get_connection()
    base = """SELECT p.*, f.name as folder_name
              FROM prompts p LEFT JOIN folders f ON p.folder_id = f.id"""
    where = []
    params = []
    if folder_id is not None:
        where.append("p.folder_id = ?")
        params.append(folder_id)
    if search:
        where.append("(p.title LIKE ? OR p.original_text LIKE ? OR p.optimized_text LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    sql = base
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY p.position ASC, p.created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def update_prompt(prompt_id, title=None, original_text=None, optimized_text=None,
                  is_optimized=None, optimization_note=None):
    conn = get_connection()
    sets = []
    params = []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if original_text is not None:
        sets.append("original_text = ?")
        params.append(original_text)
    if optimized_text is not None:
        sets.append("optimized_text = ?")
        params.append(optimized_text)
    if is_optimized is not None:
        sets.append("is_optimized = ?")
        params.append(is_optimized)
    if optimization_note is not None:
        sets.append("optimization_note = ?")
        params.append(optimization_note)
    if sets:
        params.append(prompt_id)
        conn.execute(f"UPDATE prompts SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def update_prompt_position(prompt_id, position):
    conn = get_connection()
    conn.execute("UPDATE prompts SET position = ? WHERE id = ?", (position, prompt_id))
    conn.commit()
    conn.close()


def delete_prompt(prompt_id):
    conn = get_connection()
    conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    conn.commit()
    conn.close()


# --- Folder CRUD ---

def get_all_folders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM folders ORDER BY created_at").fetchall()
    conn.close()
    return rows


def add_folder(name):
    conn = get_connection()
    cursor = conn.execute("INSERT INTO folders (name) VALUES (?)", (name,))
    conn.commit()
    folder_id = cursor.lastrowid
    conn.close()
    return folder_id


def rename_folder(folder_id, name):
    conn = get_connection()
    conn.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
    conn.commit()
    conn.close()


def delete_folder(folder_id):
    conn = get_connection()
    conn.execute("UPDATE prompts SET folder_id = NULL WHERE folder_id = ?", (folder_id,))
    conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.commit()
    conn.close()


def move_prompt_to_folder(prompt_id, folder_id):
    conn = get_connection()
    conn.execute("UPDATE prompts SET folder_id = ? WHERE id = ?", (folder_id, prompt_id))
    conn.commit()
    conn.close()


# Initialize DB on module load
init_db()
