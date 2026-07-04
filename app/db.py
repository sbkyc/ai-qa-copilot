from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  price_cents INTEGER NOT NULL,
  stock INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
"""

DEMO_USERS = [
    ("alice", "password123"),
    ("bob", "password123"),
]

DEMO_PRODUCTS = [
    (1, "无线鼠标", 2599, 10),
    (2, "机械键盘", 7999, 5),
    (3, "USB-C 扩展坞", 4299, 8),
]


def connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def seed_database(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO users (username, password) VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET password = excluded.password
        """,
        DEMO_USERS,
    )
    connection.executemany(
        """
        INSERT INTO products (id, name, price_cents, stock) VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name = excluded.name,
          price_cents = excluded.price_cents,
          stock = excluded.stock
        """,
        DEMO_PRODUCTS,
    )
    connection.commit()
