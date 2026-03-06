import os
import sqlite3
from typing import Iterable

try:
    import pyodbc
except ImportError:
    pyodbc = None


class DBAdapter:
    def __init__(
        self,
        mode="azure",
        schema="gestar",
        sqlite_path="tickets_mvp.db",
        odbc_conn_str=None,
    ):
        self.mode = (mode or "azure").strip().lower()
        self.schema = (schema or "").strip()
        self.sqlite_path = sqlite_path or "tickets_mvp.db"
        self.odbc_conn_str = odbc_conn_str

    @property
    def is_sqlite(self):
        return self.mode == "sqlite"

    @property
    def is_azure(self):
        return not self.is_sqlite

    def qname(self, table_name):
        if self.is_sqlite or not self.schema:
            return table_name
        return f"{self.schema}.{table_name}"

    def now_expr(self):
        return "CURRENT_TIMESTAMP" if self.is_sqlite else "GETDATE()"

    def connect(self):
        if self.is_sqlite:
            conn = sqlite3.connect(
                self.sqlite_path,
                timeout=15,
                check_same_thread=False,
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            return conn

        if not self.odbc_conn_str:
            raise RuntimeError("Falta ODBC_CONN_STR para DB_MODE=azure")
        if pyodbc is None:
            raise RuntimeError("pyodbc no está instalado")
        return pyodbc.connect(self.odbc_conn_str)

    def table_exists(self, conn, table_name):
        cursor = conn.cursor()
        if self.is_sqlite:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
                (table_name,),
            )
            return bool(cursor.fetchone())
        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """,
            (self.schema, table_name),
        )
        return bool(cursor.fetchone())

    def list_columns(self, conn, table_name):
        cursor = conn.cursor()
        if self.is_sqlite:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [str(row[1]).lower() for row in cursor.fetchall()]
        cursor.execute(
            """
            SELECT LOWER(COLUMN_NAME)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """,
            (self.schema, table_name),
        )
        return [str(row[0]).lower() for row in cursor.fetchall()]

    def placeholder_values(self, count):
        return ", ".join(["?"] * int(count))

    def one_clause(self):
        return "LIMIT 1" if self.is_sqlite else "TOP 1"

    def limit_clause(self, n):
        if n is None:
            return ""
        n = int(n)
        return f"LIMIT {n}" if self.is_sqlite else f"TOP {n}"

    def normalize_table_name(self, table_name):
        if "." not in table_name:
            return table_name
        if self.is_sqlite:
            return table_name.split(".", 1)[1]
        return table_name


def env_db_mode(default="azure"):
    return (os.getenv("DB_MODE", default) or default).strip().lower()


def env_sqlite_path(default="tickets_mvp.db"):
    return os.getenv("SQLITE_PATH", default) or default


def env_schema(default="gestar"):
    return os.getenv("DB_SCHEMA", default) or default


def apply_sqlite_schema(conn, statements: Iterable[str]):
    cursor = conn.cursor()
    for stmt in statements:
        sql = (stmt or "").strip()
        if not sql:
            continue
        cursor.execute(sql)
    conn.commit()
