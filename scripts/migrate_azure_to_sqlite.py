import argparse
import datetime as dt
import decimal
import os
import sqlite3
from pathlib import Path

import pyodbc

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None


TABLE_ORDER = [
    "Plantas",
    "Divisiones",
    "Areas",
    "Categorias",
    "Subcategorias",
    "Prioridades",
    "Estados",
    "Users",
    "Tickets",
    "TicketLogs",
    "Subtasks",
]


def load_conn_str():
    env_value = os.getenv("ODBC_CONN_STR")
    if env_value:
        return env_value, "env"

    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists() and tomllib is not None:
        data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
        conn = data.get("ODBC_CONN_STR")
        if conn:
            return conn, str(secrets_path)

    return None, None


def split_sql_statements(sql_text):
    return [chunk.strip() for chunk in sql_text.split(";") if chunk.strip()]


def ensure_sqlite_schema(sqlite_conn, schema_path, seed_path):
    schema_sql = Path(schema_path).read_text(encoding="utf-8")
    cur = sqlite_conn.cursor()
    for stmt in split_sql_statements(schema_sql):
        cur.execute(stmt)

    if seed_path and Path(seed_path).exists():
        seed_sql = Path(seed_path).read_text(encoding="utf-8")
        for stmt in split_sql_statements(seed_sql):
            cur.execute(stmt)
    sqlite_conn.commit()


def source_table_exists(azure_cursor, schema, table):
    azure_cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """,
        (schema, table),
    )
    return azure_cursor.fetchone() is not None


def target_table_exists(sqlite_cursor, table):
    sqlite_cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
        (table,),
    )
    return sqlite_cursor.fetchone() is not None


def get_target_columns(sqlite_cursor, table):
    sqlite_cursor.execute(f"PRAGMA table_info({table})")
    return [str(row[1]) for row in sqlite_cursor.fetchall()]


def normalize_value(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat(sep=" ") if hasattr(value, "isoformat") else str(value)
    if isinstance(value, bytes):
        return value
    return value


def copy_one_table(
    azure_cursor,
    sqlite_cursor,
    schema,
    table,
):
    if not source_table_exists(azure_cursor, schema, table):
        return {"table": table, "status": "missing_source", "copied": 0}
    if not target_table_exists(sqlite_cursor, table):
        return {"table": table, "status": "missing_target", "copied": 0}

    azure_cursor.execute(f"SELECT TOP 0 * FROM {schema}.{table}")
    source_columns = [str(c[0]) for c in azure_cursor.description]
    target_columns = get_target_columns(sqlite_cursor, table)
    target_set = {c.lower(): c for c in target_columns}
    common_columns = [c for c in source_columns if c.lower() in target_set]

    if not common_columns:
        return {"table": table, "status": "no_common_columns", "copied": 0}

    col_list = ", ".join(common_columns)
    azure_cursor.execute(f"SELECT {col_list} FROM {schema}.{table}")
    rows = azure_cursor.fetchall()

    if rows:
        placeholders = ", ".join(["?"] * len(common_columns))
        insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
        payload = [tuple(normalize_value(v) for v in row) for row in rows]
        sqlite_cursor.executemany(insert_sql, payload)

    return {"table": table, "status": "ok", "copied": len(rows)}


def count_source_rows(azure_cursor, schema, table):
    azure_cursor.execute(f"SELECT COUNT(1) FROM {schema}.{table}")
    row = azure_cursor.fetchone()
    return int(row[0]) if row else 0


def count_target_rows(sqlite_cursor, table):
    sqlite_cursor.execute(f"SELECT COUNT(1) FROM {table}")
    row = sqlite_cursor.fetchone()
    return int(row[0]) if row else 0


def migrate(args):
    conn_str, source = load_conn_str()
    if not conn_str:
        raise RuntimeError(
            "No se encontró ODBC_CONN_STR en variables de entorno ni en .streamlit/secrets.toml"
        )

    print(f"ODBC_CONN_STR leído desde: {source}")
    print(f"Schema Azure: {args.schema}")
    print(f"SQLite destino: {args.sqlite}")

    azure_conn = pyodbc.connect(conn_str)
    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.execute("PRAGMA busy_timeout = 5000")
    sqlite_conn.execute("PRAGMA journal_mode = WAL")
    sqlite_conn.execute("PRAGMA foreign_keys = OFF")

    try:
        ensure_sqlite_schema(sqlite_conn, args.schema_sqlite, args.seed_sqlite)
        sqlite_conn.execute("PRAGMA foreign_keys = OFF")

        az_cur = azure_conn.cursor()
        sq_cur = sqlite_conn.cursor()

        if not args.no_truncate:
            for table in reversed(TABLE_ORDER):
                if target_table_exists(sq_cur, table):
                    sq_cur.execute(f"DELETE FROM {table}")
            sqlite_conn.commit()

        results = []
        for table in TABLE_ORDER:
            res = copy_one_table(
                azure_cursor=az_cur,
                sqlite_cursor=sq_cur,
                schema=args.schema,
                table=table,
            )
            results.append(res)
            print(f"{table}: {res['status']} (copiadas={res['copied']})")

        sqlite_conn.commit()
        sqlite_conn.execute("PRAGMA foreign_keys = ON")

        print("\nVerificación de conteos:")
        mismatch = []
        for item in results:
            table = item["table"]
            if item["status"] != "ok":
                continue
            src_count = count_source_rows(az_cur, args.schema, table)
            dst_count = count_target_rows(sq_cur, table)
            status = "OK" if src_count == dst_count else "MISMATCH"
            print(f"- {table}: Azure={src_count} | SQLite={dst_count} => {status}")
            if status != "OK":
                mismatch.append(table)

        if mismatch:
            raise RuntimeError(
                "Falló verificación de conteos para: " + ", ".join(mismatch)
            )

        print("\nMigración y verificación completadas correctamente.")
    finally:
        azure_conn.close()
        sqlite_conn.close()


def build_parser():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Migra datos desde Azure SQL a SQLite y verifica conteos."
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("DB_SCHEMA", "gestar"),
        help="Schema en Azure SQL (default: gestar).",
    )
    parser.add_argument(
        "--sqlite",
        default=os.getenv("SQLITE_PATH", str(repo_root / "tickets_mvp.db")),
        help="Archivo SQLite destino.",
    )
    parser.add_argument(
        "--schema-sqlite",
        default=str(repo_root / "schema_sqlite.sql"),
        help="Ruta a schema_sqlite.sql.",
    )
    parser.add_argument(
        "--seed-sqlite",
        default=str(repo_root / "seed_sqlite.sql"),
        help="Ruta a seed_sqlite.sql.",
    )
    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="No borrar tablas destino antes de copiar.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    migrate(args)


if __name__ == "__main__":
    main()
