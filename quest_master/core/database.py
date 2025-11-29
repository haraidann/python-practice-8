from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
import datetime
import threading
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "quests.db")


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE NOT NULL,
                    difficulty TEXT CHECK(difficulty IN ('Легкий','Средний','Сложный','Эпический')),
                    reward INTEGER,
                    description TEXT,
                    deadline TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quest_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quest_id INTEGER,
                    title TEXT,
                    difficulty TEXT,
                    reward INTEGER,
                    description TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (quest_id) REFERENCES quests(id)
                );
                """
            )

            cur.execute("""
                CREATE TABLE IF NOT EXISTS quest_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quest_id INTEGER NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    type TEXT CHECK(type IN ('city','lair','tavern')),
                    label TEXT,
                    FOREIGN KEY (quest_id) REFERENCES quests(id)
                );
                """)
            
            self._conn.commit()

    def create_quest(self, title: str, difficulty: str = "Легкий",
                     reward: int = 10, description: str = "",
                     deadline: Optional[str] = None) -> int:

        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO quests (title, difficulty, reward, description, deadline)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, difficulty, reward, description, deadline),
            )
            quest_id = cur.lastrowid
            self._insert_version(quest_id, title, difficulty, reward, description)
            self._conn.commit()
            return quest_id

    def _insert_version(self, quest_id: int, title: str, difficulty: str,
                        reward: int, description: str) -> None:
        created_at = datetime.datetime.utcnow().isoformat()
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO quest_versions (quest_id, title, difficulty, reward, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (quest_id, title, difficulty, reward, description, created_at),
        )

    def update_quest(self, quest_id: int, fields: Dict[str, Any]) -> None:
        allowed = {"title", "difficulty", "reward", "description", "deadline"}
        set_parts = []
        values = []
        for k, v in fields.items():
            if k in allowed:
                set_parts.append(f"{k} = ?")
                values.append(v)
        if not set_parts:
            return
        values.append(quest_id)
        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute(
                f"UPDATE quests SET {', '.join(set_parts)} WHERE id = ?",
                tuple(values),
            )

            cur.execute("SELECT title, difficulty, reward, description FROM quests WHERE id = ?", (quest_id,))
            row = cur.fetchone()
            if row:
                self._insert_version(quest_id, row["title"], row["difficulty"], row["reward"], row["description"])
            self._conn.commit()

    def autosave_field(self, quest_id: int, field: str, value: Any) -> None:

        if field not in {"title", "difficulty", "reward", "description", "deadline"}:
            return
        self.update_quest(quest_id, {field: value})

    def get_quest(self, quest_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def find_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM quests WHERE title = ?", (title,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_all_quests(self) -> list[dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM quests ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
        

    def add_location(self, quest_id: int, x: float, y: float, type_: str, label: str = None):
        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute("""
                INSERT INTO quest_locations (quest_id, x, y, type, label)
                VALUES (?, ?, ?, ?, ?)
            """, (quest_id, x, y, type_, label))
            self._conn.commit()

    def delete_last_location(self, quest_id: int):
        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute("""
                DELETE FROM quest_locations
                WHERE id = (
                    SELECT id FROM quest_locations WHERE quest_id = ? ORDER BY id DESC LIMIT 1
                )
            """, (quest_id,))
            self._conn.commit()

    def get_locations(self, quest_id: int) -> List[Tuple[int, float, float, str, Optional[str]]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT id, x, y, type, label FROM quest_locations
                WHERE quest_id = ?
                ORDER BY id ASC
            """, (quest_id,))
            return cur.fetchall()
