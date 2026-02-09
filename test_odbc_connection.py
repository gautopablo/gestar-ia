import os
from pathlib import Path

import pyodbc

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None


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


def main():
    conn_str, source = load_conn_str()
    if not conn_str:
        print("ERROR: No se encontró ODBC_CONN_STR en env ni en .streamlit/secrets.toml")
        raise SystemExit(1)

    print(f"Usando ODBC_CONN_STR desde: {source}")
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
            print(f"Conexion OK. SELECT 1 => {row[0]}")
    except Exception as exc:
        print(f"ERROR conectando a Azure SQL: {exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
