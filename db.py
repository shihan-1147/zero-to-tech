"""
【数据持久化层】db.py
职责：封装所有数据库读写。上层（路由）只调用这里导出的函数，
     不关心 SQL 细节 —— 这就是「数据访问层 / Repository」模式。
技术：Python 标准库 sqlite3，零第三方依赖。
     换成 MySQL/PostgreSQL 时只需改写本文件，上层代码不动。
"""
import sqlite3
import threading
from datetime import datetime

import config

# FastAPI 的同步端点运行在线程池中，sqlite3 连接默认不能跨线程，
# 因此 check_same_thread=False + 一把锁保证串行写入（demo 规模足够）
_conn = sqlite3.connect(config.DB_FILE, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_lock = threading.Lock()

with _lock:
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    _conn.commit()


def save_message(role: str, content: str) -> dict:
    """保存一条消息，返回完整记录"""
    with _lock:
        cur = _conn.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        _conn.commit()
        return {"id": cur.lastrowid, "role": role, "content": content}


def list_messages() -> list[dict]:
    """全部历史（供前端渲染）"""
    rows = _conn.execute(
        "SELECT id, role, content, created_at FROM messages ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def recent_messages(n: int = 10) -> list[dict]:
    """最近 n 条（供 AI 模块拼接上下文，按时间正序返回）"""
    rows = _conn.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def clear_messages() -> None:
    """清空历史"""
    with _lock:
        _conn.execute("DELETE FROM messages")
        _conn.commit()
