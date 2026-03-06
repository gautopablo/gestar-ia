import argparse
import pathlib
import sqlite3


def _read_sql_file(path):
    text = path.read_text(encoding="utf-8")
    return [chunk.strip() for chunk in text.split(";") if chunk.strip()]


def bootstrap(db_path, schema_path, seed_path=None):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        cur = conn.cursor()

        for stmt in _read_sql_file(schema_path):
            cur.execute(stmt)

        if seed_path and seed_path.exists():
            for stmt in _read_sql_file(seed_path):
                cur.execute(stmt)

        conn.commit()
    finally:
        conn.close()


def main():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Bootstrap SQLite database for Gestar.")
    parser.add_argument(
        "--db",
        default=str(repo_root / "tickets_mvp.db"),
        help="Ruta del archivo SQLite a inicializar.",
    )
    parser.add_argument(
        "--schema",
        default=str(repo_root / "schema_sqlite.sql"),
        help="Ruta al schema_sqlite.sql.",
    )
    parser.add_argument(
        "--seed",
        default=str(repo_root / "seed_sqlite.sql"),
        help="Ruta al seed_sqlite.sql.",
    )
    args = parser.parse_args()

    db_path = pathlib.Path(args.db)
    schema_path = pathlib.Path(args.schema)
    seed_path = pathlib.Path(args.seed)

    if not schema_path.exists():
        raise FileNotFoundError(f"No existe schema: {schema_path}")

    bootstrap(db_path=db_path, schema_path=schema_path, seed_path=seed_path)
    print(f"SQLite inicializada en: {db_path}")


if __name__ == "__main__":
    main()
