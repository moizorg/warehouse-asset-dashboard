import sqlite3
from pathlib import Path
from contextlib import contextmanager
import os


class DictRow:
    def __init__(self, values, columns):
        self._values = values
        self._columns = columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._columns.index(key)]

    def keys(self):
        return tuple(self._columns)


class RemoteCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        description = getattr(cursor, "description", None)
        self.columns = [column[0] for column in description] if description else []

    def fetchone(self):
        row = self._cursor.fetchone()
        return DictRow(row, self.columns) if row is not None else None

    def fetchall(self):
        return [DictRow(row, self.columns) for row in self._cursor.fetchall()]

    @property
    def lastrowid(self):
        return getattr(self._cursor, "lastrowid", None)


class RemoteConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, parameters=()):
        cursor = self._connection.execute(sql, parameters)
        return RemoteCursor(cursor)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


class Database:
    def __init__(self, path):
        if str(path).startswith(("libsql://", "https://")):
            self.path = str(path)
        else:
            self.path = str(Path(path).resolve())
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        if self.path.startswith("libsql://") or self.path.startswith("https://"):
            import libsql
            connection = RemoteConnection(libsql.connect(
                self.path,
                auth_token=os.getenv("TURSO_AUTH_TOKEN", ""),
            ))
        else:
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_identifier TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    category TEXT NOT NULL,
                    photograph_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_assets_identifier ON assets(asset_identifier)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category)"
            )
            columns = connection.execute("PRAGMA table_info(assets)").fetchall()
            column_names = {row["name"] for row in columns}
            if "photograph_data" not in column_names:
                connection.execute(
                    "ALTER TABLE assets ADD COLUMN photograph_data BLOB"
                )
