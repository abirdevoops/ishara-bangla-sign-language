import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent / "ishara.db"

def connect():
    return sqlite3.connect(DB)

def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS translations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        label TEXT NOT NULL,
        confidence REAL NOT NULL,
        created_at TEXT NOT NULL
    )""")
    con.commit()
    con.close()

def _hash(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def seed_admin():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", ("admin",))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users VALUES(?,?,?,?)",
                    ("admin", _hash("Ishara@2026"), 1, datetime.now().isoformat()))
    con.commit()
    con.close()

def create_user(username, password):
    if not username or not password:
        return False
    con = connect()
    try:
        con.execute("INSERT INTO users VALUES(?,?,?,?)",
                    (username, _hash(password), 0, datetime.now().isoformat()))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def authenticate_user(username, password):
    con = connect()
    row = con.execute(
        "SELECT username FROM users WHERE username=? AND password_hash=?",
        (username, _hash(password))
    ).fetchone()
    con.close()
    return bool(row)

def is_admin(username):
    con = connect()
    row = con.execute("SELECT is_admin FROM users WHERE username=?", (username,)).fetchone()
    con.close()
    return bool(row and row[0])

def save_translation(username, label, confidence):
    con = connect()
    con.execute(
        "INSERT INTO translations(username,label,confidence,created_at) VALUES(?,?,?,?)",
        (username, label, float(confidence), datetime.now().isoformat(timespec="seconds"))
    )
    con.commit()
    con.close()

def get_history(username):
    con = connect()
    rows = con.execute(
        "SELECT label AS Sign, ROUND(confidence*100,1) AS Confidence, created_at AS Time "
        "FROM translations WHERE username=? ORDER BY id DESC LIMIT 100",
        (username,)
    ).fetchall()
    con.close()
    return rows and [{"Sign":r[0],"Confidence":f"{r[1]}%","Time":r[2]} for r in rows] or []

def get_stats():
    con = connect()
    users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    translations = con.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
    con.close()
    from gesture_engine import sample_count
    return {"users": users, "translations": translations, "samples": sample_count()}
