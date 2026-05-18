"""
轻量级 SQLite 数据库层，零外部依赖。
"""
import sqlite3
import json
import os
import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = os.getenv("TRIP_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "trips.db"))

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


@contextmanager
def get_db():
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _migrate(conn: sqlite3.Connection):
    """Add missing columns/tables for existing databases."""
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    # trips: add user_id column if missing
    if "trips" in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(trips)").fetchall()}
        if "user_id" not in cols:
            conn.execute("ALTER TABLE trips ADD COLUMN user_id INTEGER")
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(trips)").fetchall()}
        if "idx_trips_user_id" not in indexes:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id)")

    # favorites: replace user_tag with user_id
    if "favorites" in tables:
        fav_cols = {row[1] for row in conn.execute("PRAGMA table_info(favorites)").fetchall()}
        if "user_tag" in fav_cols and "user_id" not in fav_cols:
            conn.execute("ALTER TABLE favorites ADD COLUMN user_id INTEGER")
            conn.execute("UPDATE favorites SET user_id = NULL WHERE user_tag = 'default'")
            conn.execute("ALTER TABLE favorites DROP COLUMN user_tag")
        elif "user_id" not in fav_cols:
            conn.execute("ALTER TABLE favorites ADD COLUMN user_id INTEGER")
        try:
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_favorites_unique ON favorites(trip_id, user_id)")
        except Exception:
            pass

    # transport_cache: create if missing
    if "transport_cache" not in tables:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transport_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days_count INTEGER NOT NULL,
                plan_data TEXT NOT NULL,
                share_token TEXT UNIQUE,
                user_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_trips_city ON trips(city);
            CREATE INDEX IF NOT EXISTS idx_trips_share_token ON trips(share_token);

            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT NOT NULL,
                user_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS share_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_token TEXT NOT NULL,
                viewer_ip TEXT,
                viewed_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                called_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_api_usage_client ON api_usage(client_id, called_at);

            CREATE TABLE IF NOT EXISTS transport_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Schema migration: add missing columns for existing databases
        _migrate(conn)


# --- CRUD 操作 ---

def save_trip(trip_id: str, city: str, start_date: str, end_date: str,
              days_count: int, plan_data: dict, share_token: Optional[str] = None,
              user_id: Optional[int] = None) -> dict:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO trips (id, city, start_date, end_date, days_count, plan_data, share_token, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM trips WHERE id=?), ?), ?)
        """, (trip_id, city, start_date, end_date, days_count, json.dumps(plan_data, ensure_ascii=False),
              share_token, user_id, trip_id, now, now))
    return {"id": trip_id, "city": city, "created_at": now}


def get_trip(trip_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM trips WHERE id=?", (trip_id,)).fetchone()
        if row:
            return {
                "id": row["id"],
                "city": row["city"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "days_count": row["days_count"],
                "plan_data": json.loads(row["plan_data"]),
                "share_token": row["share_token"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
    return None


def get_trip_by_share_token(token: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM trips WHERE share_token=?", (token,)).fetchone()
        if row:
            # 记录浏览
            conn.execute(
                "INSERT INTO share_views (share_token, viewer_ip) VALUES (?, ?)",
                (token, None)
            )
            return {
                "id": row["id"],
                "city": row["city"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "days_count": row["days_count"],
                "plan_data": json.loads(row["plan_data"]),
                "share_token": row["share_token"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
    return None


def update_trip(trip_id: str, plan_data: dict) -> bool:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        result = conn.execute(
            "UPDATE trips SET plan_data=?, updated_at=? WHERE id=?",
            (json.dumps(plan_data, ensure_ascii=False), now, trip_id)
        )
        return result.rowcount > 0


def list_trips(limit: int = 50, offset: int = 0, user_id: Optional[int] = None) -> List[dict]:
    with get_db() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT id, city, start_date, end_date, days_count, share_token, created_at FROM trips WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset)
            ).fetchall()
        else:
            rows = []
        return [dict(row) for row in rows]


def delete_trip(trip_id: str) -> bool:
    with get_db() as conn:
        result = conn.execute("DELETE FROM trips WHERE id=?", (trip_id,))
        return result.rowcount > 0


def add_favorite(trip_id: str, user_id: Optional[int] = None) -> bool:
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO favorites (trip_id, user_id) VALUES (?, ?)",
                (trip_id, user_id)
            )
            return True
        except sqlite3.IntegrityError:
            return False


def remove_favorite(trip_id: str, user_id: Optional[int] = None) -> bool:
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM favorites WHERE trip_id=? AND user_id=?",
            (trip_id, user_id)
        )
        return result.rowcount > 0


def list_favorites(user_id: Optional[int] = None) -> List[dict]:
    with get_db() as conn:
        if user_id is not None:
            rows = conn.execute("""
                SELECT t.id, t.city, t.start_date, t.end_date, t.days_count, t.created_at
                FROM favorites f JOIN trips t ON f.trip_id = t.id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
            """, (user_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT t.id, t.city, t.start_date, t.end_date, t.days_count, t.created_at
                FROM favorites f JOIN trips t ON f.trip_id = t.id
                ORDER BY f.created_at DESC
            """).fetchall()
        return [dict(row) for row in rows]


def check_favorite(trip_id: str, user_id: Optional[int] = None) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE trip_id=? AND user_id=?",
            (trip_id, user_id)
        ).fetchone()
        return row is not None


def log_api_usage(client_id: str, endpoint: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO api_usage (client_id, endpoint) VALUES (?, ?)",
            (client_id, endpoint)
        )


def count_api_usage(client_id: str, minutes: int = 60) -> int:
    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM api_usage
            WHERE client_id=? AND called_at > datetime('now', ? || ' minutes')
        """, (client_id, f"-{minutes}")).fetchone()
        return row["cnt"] if row else 0


# --- 用户 CRUD ---

def create_user(email: str, password_hash: str) -> Optional[dict]:
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            return {"id": user_id, "email": email}
        except sqlite3.IntegrityError:
            return None


def get_user_by_email(email: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row:
            return {"id": row["id"], "email": row["email"], "password_hash": row["password_hash"]}
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT id, email FROM users WHERE id=?", (user_id,)).fetchone()
        if row:
            return {"id": row["id"], "email": row["email"]}
    return None


# --- 交通缓存 ---

def save_transport_cache(cache_key: str, data: dict):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO transport_cache (cache_key, data, created_at)
            VALUES (?, ?, ?)
        """, (cache_key, json.dumps(data, ensure_ascii=False), now))


def get_transport_cache(cache_key: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT data, created_at FROM transport_cache WHERE cache_key=?",
            (cache_key,)
        ).fetchone()
        if row:
            created = datetime.fromisoformat(row["created_at"])
            if (datetime.utcnow() - created).total_seconds() < 86400:  # 24h TTL
                return json.loads(row["data"])
            conn.execute("DELETE FROM transport_cache WHERE cache_key=?", (cache_key,))
    return None
