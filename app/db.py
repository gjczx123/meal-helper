"""台账：每顿一条记录 + 去重表 + 发送日志。"""
import json
import sqlite3
from datetime import datetime, timedelta

from . import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS meal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    meal TEXT NOT NULL,
    msg_time TEXT,
    source TEXT,
    raw_text TEXT,
    image_path TEXT,
    plan_day INTEGER,
    items_json TEXT,
    status TEXT,
    verdict_reason TEXT,
    analysis_json TEXT,
    reply_text TEXT,
    sent_at TEXT,
    verify_ok INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message_seen (
    msg_id TEXT PRIMARY KEY,
    ts TEXT
);
CREATE TABLE IF NOT EXISTS send_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    action TEXT,
    target TEXT,
    content TEXT,
    ok INTEGER DEFAULT 1,
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_meal_date ON meal_records(date);
"""


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def conn():
    c = sqlite3.connect(paths.db_path())
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def insert_meal(rec: dict) -> int:
    c = conn()
    try:
        cur = c.execute(
            """INSERT INTO meal_records
               (date, meal, msg_time, source, raw_text, image_path, plan_day,
                items_json, status, verdict_reason, analysis_json, reply_text,
                sent_at, verify_ok, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                rec.get("date"), rec.get("meal"), rec.get("msg_time"),
                rec.get("source", "text"), rec.get("raw_text", ""),
                rec.get("image_path", ""), rec.get("plan_day"),
                json.dumps(rec.get("items", []), ensure_ascii=False),
                rec.get("status", "unparsed"), rec.get("verdict_reason", ""),
                json.dumps(rec.get("analysis", {}), ensure_ascii=False),
                rec.get("reply_text", ""), rec.get("sent_at", ""),
                int(rec.get("verify_ok", 0)), _now(),
            ),
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def update_status(rid: int, status: str, reply: str = ""):
    c = conn()
    try:
        c.execute("UPDATE meal_records SET status=?, reply_text=? WHERE id=?", (status, reply, rid))
        c.commit()
    finally:
        c.close()


def recent(limit: int = 50) -> list:
    c = conn()
    try:
        rows = c.execute(
            "SELECT * FROM meal_records ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def by_date(d: str) -> list:
    c = conn()
    try:
        rows = c.execute("SELECT * FROM meal_records WHERE date=? ORDER BY id", (d,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()


def today_map(d: str) -> dict:
    return {r["meal"]: r for r in by_date(d)}


def is_seen(msg_id: str) -> bool:
    c = conn()
    try:
        return c.execute("SELECT 1 FROM message_seen WHERE msg_id=?", (str(msg_id),)).fetchone() is not None
    finally:
        c.close()


def mark_seen(msg_id: str):
    c = conn()
    try:
        c.execute("INSERT OR IGNORE INTO message_seen (msg_id, ts) VALUES (?,?)", (str(msg_id), _now()))
        c.commit()
    finally:
        c.close()


def log(action: str, target: str = "", content: str = "", ok: int = 1, note: str = ""):
    c = conn()
    try:
        c.execute(
            "INSERT INTO send_log (ts, action, target, content, ok, note) VALUES (?,?,?,?,?,?)",
            (_now(), action, target, content, int(ok), note),
        )
        c.commit()
    finally:
        c.close()


def recent_logs(limit: int = 20) -> list:
    c = conn()
    try:
        return [dict(r) for r in c.execute(
            "SELECT * FROM send_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    finally:
        c.close()


def cleanup(keep_days: int = 60):
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
    c = conn()
    try:
        c.execute("DELETE FROM meal_records WHERE date < ?", (cutoff,))
        c.commit()
    finally:
        c.close()
