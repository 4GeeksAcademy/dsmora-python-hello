from pathlib import Path

from tinydb import Query, TinyDB


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "db.json"
DEFAULT_TABLES = ("books", "users", "profiles", "reserved_books", "telemetry_events")


def get_db() -> TinyDB:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return TinyDB(DB_PATH)


def init_tables(table_names: tuple[str, ...] = DEFAULT_TABLES) -> None:
    db = get_db()
    try:
        for table_name in table_names:
            table = db.table(table_name)
            if len(table) == 0:
                table.insert({"__bootstrap__": True})
                table.remove(Query().__bootstrap__ == True)
    finally:
        db.close()