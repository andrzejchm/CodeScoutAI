import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import CodeSymbol, IndexStats


class CodeIndexRepository:
    """Manages SQLite database operations for the code index service."""

    db_path: str

    def __init__(self, db_path: str):
        """Initialize the repository with database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.initialize_database()

    def initialize_database(self) -> None:
        """Creates all tables, triggers, and indexes. This operation is idempotent."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create metadata table
            _ = cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_index_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Create main code index table
            _ = cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER,
                    end_line_number INTEGER,
                    end_column_number INTEGER,
                    language TEXT NOT NULL,
                    signature TEXT,
                    docstring TEXT,
                    parent_symbol TEXT,
                    scope TEXT,
                    parameters TEXT,
                    return_type TEXT,
                    file_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(file_path, symbol_type, name, line_number, end_line_number)
                )
            """)

            # Create FTS5 virtual table
            _ = cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS code_index_fts USING fts5(
                    name,
                    signature,
                    docstring,
                    parent_symbol,
                    file_path,
                    language,
                    content='code_index',
                    content_rowid='id',
                    prefix='2 3 4'
                )
            """)

            # Create triggers for FTS synchronization
            _ = cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS code_index_after_insert
                AFTER INSERT ON code_index BEGIN
                    INSERT INTO code_index_fts(rowid, name, signature, docstring, parent_symbol, file_path, language)
                    VALUES (
                        new.id, new.name, new.signature, new.docstring, new.parent_symbol, new.file_path, new.language
                    );
                END
            """)

            _ = cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS code_index_after_update
                AFTER UPDATE ON code_index BEGIN
                    INSERT INTO code_index_fts(code_index_fts, rowid) VALUES('delete', old.id);
                    INSERT INTO code_index_fts(rowid, name, signature, docstring, parent_symbol, file_path, language)
                    VALUES (
                        new.id, new.name, new.signature, new.docstring, new.parent_symbol, new.file_path, new.language
                    );
                END
            """)

            _ = cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS code_index_after_delete
                AFTER DELETE ON code_index BEGIN
                    INSERT INTO code_index_fts(code_index_fts, rowid) VALUES('delete', old.id);
                END
            """)

            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_code_index_name ON code_index(name)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_type ON code_index(symbol_type)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_file_path ON code_index(file_path)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_language ON code_index(language)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_parent ON code_index(parent_symbol)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_file_hash ON code_index(file_hash)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_file_line ON code_index(file_path, line_number)",
                "CREATE INDEX IF NOT EXISTS idx_code_index_composite ON code_index(name, symbol_type, file_path)",
            ]

            for index_sql in indexes:
                _ = cursor.execute(index_sql)

            # Create file tracking table
            _ = cursor.execute("""
                CREATE TABLE IF NOT EXISTS indexed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    symbol_count INTEGER DEFAULT 0,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for file tracking
            _ = cursor.execute("CREATE INDEX IF NOT EXISTS idx_indexed_files_path ON indexed_files(file_path)")
            _ = cursor.execute("CREATE INDEX IF NOT EXISTS idx_indexed_files_hash ON indexed_files(file_hash)")

            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get and configure a new SQLite connection with optimizations."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Apply SQLite optimization pragmas
        cursor = conn.cursor()
        _ = cursor.execute("PRAGMA journal_mode=WAL")
        _ = cursor.execute("PRAGMA synchronous=NORMAL")
        _ = cursor.execute("PRAGMA temp_store=MEMORY")
        _ = cursor.execute("PRAGMA cache_size=-20000")

        return conn

    def insert_symbols(self, symbols: list[CodeSymbol]) -> None:
        """Insert a batch of symbols using a transaction."""
        if not symbols:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for symbol in symbols:
                _ = cursor.execute(
                    """
                    INSERT OR REPLACE INTO code_index (
                        name, symbol_type, file_path, line_number, column_number,
                        end_line_number, end_column_number, language, signature,
                        docstring, parent_symbol, scope, parameters, return_type,
                        file_hash, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        symbol.name,
                        symbol.symbol_type,
                        symbol.file_path,
                        symbol.start_line_number,
                        symbol.start_column_number,
                        symbol.end_line_number,
                        symbol.end_column_number,
                        symbol.language,
                        symbol.signature,
                        symbol.docstring,
                        symbol.parent_symbol,
                        symbol.scope,
                        symbol.parameters,
                        symbol.return_type,
                        symbol.file_hash,
                        datetime.now(),
                    ),
                )

            conn.commit()

    def delete_symbols_by_file(self, file_path: str) -> None:
        """Delete all symbols for a given file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("DELETE FROM code_index WHERE file_path = ?", (file_path,))
            conn.commit()

    def count_symbols_by_file(self, file_path: str) -> int:
        """Count the number of symbols for a given file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT COUNT(*) as count FROM code_index WHERE file_path = ?", (file_path,))
            return cursor.fetchone()["count"]

    def search_fts(self, query: str, filters: dict[str, Any]) -> list[CodeSymbol]:
        """Perform a search against the FTS table with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build the FTS query
            fts_query = query.replace("'", "''")  # Escape single quotes

            # Base query using FTS
            sql = """
                SELECT ci.* FROM code_index ci
                JOIN code_index_fts fts ON ci.id = fts.rowid
                WHERE code_index_fts MATCH ?
            """
            params: list[Any] = [fts_query]

            # Apply filters
            if filters.get("symbol_type"):
                sql += " AND ci.symbol_type = ?"
                params.append(filters["symbol_type"])

            if filters.get("file_pattern"):
                sql += " AND ci.file_path LIKE ?"
                params.append(f"%{filters['file_pattern']}%")

            if filters.get("language"):
                sql += " AND ci.language = ?"
                params.append(filters["language"])

            # Order by relevance (FTS rank)
            sql += " ORDER BY bm25(code_index_fts) LIMIT ?"
            params.append(filters.get("limit", 20))

            _ = cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_symbol(row) for row in rows]

    def get_file_hash(self, file_path: str) -> str | None:
        """Retrieve the stored hash for a file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT file_hash FROM indexed_files WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()
            return row["file_hash"] if row else None

    def update_file_tracking(self, file_path: str, file_hash: str, symbol_count: int) -> None:
        """Update file tracking information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute(
                """
                INSERT OR REPLACE INTO indexed_files (file_path, file_hash, symbol_count, last_indexed)
                VALUES (?, ?, ?, ?)
            """,
                (file_path, file_hash, symbol_count, datetime.now()),
            )
            conn.commit()

    def get_index_stats(self) -> IndexStats:
        """Retrieve index statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get total symbols
            _ = cursor.execute("SELECT COUNT(*) as count FROM code_index")
            total_symbols = cursor.fetchone()["count"]

            # Get total files
            _ = cursor.execute("SELECT COUNT(*) as count FROM indexed_files")
            total_files = cursor.fetchone()["count"]

            # Get symbols by type
            _ = cursor.execute("""
                SELECT symbol_type, COUNT(*) as count
                FROM code_index
                GROUP BY symbol_type
            """)
            symbols_by_type = {row["symbol_type"]: row["count"] for row in cursor.fetchall()}

            # Get symbols by language
            _ = cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM code_index
                GROUP BY language
            """)
            symbols_by_language = {row["language"]: row["count"] for row in cursor.fetchall()}

            # Get last updated
            _ = cursor.execute("""
                SELECT MAX(last_indexed) as last_updated
                FROM indexed_files
            """)
            last_updated_row = cursor.fetchone()
            last_updated = None
            if last_updated_row and last_updated_row["last_updated"]:
                last_updated = datetime.fromisoformat(last_updated_row["last_updated"])

            return IndexStats(
                total_symbols=total_symbols,
                total_files=total_files,
                symbols_by_type=symbols_by_type,
                symbols_by_language=symbols_by_language,
                last_updated=last_updated,
            )

    def get_distinct_symbol_types(self) -> list[str]:
        """
        Get distinct symbol types present in the index.

        Returns:
            list of symbol type strings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("SELECT DISTINCT symbol_type FROM code_index ORDER BY symbol_type")
            rows = cursor.fetchall()
            return [row["symbol_type"] for row in rows]

    def get_indexed_files(self) -> list[dict[str, Any]]:
        """Retrieve all file paths and hashes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("""
                SELECT file_path, file_hash, symbol_count, last_indexed
                FROM indexed_files
                ORDER BY file_path
            """)
            return [dict(row) for row in cursor.fetchall()]

    def clear_index(self) -> None:
        """
        Clear all data from the code_index and indexed_files tables.
        If the database file does not exist, this method does nothing.
        """
        if not self.index_exists():
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            _ = cursor.execute("DELETE FROM code_index")
            _ = cursor.execute("DELETE FROM indexed_files")
            conn.commit()

    def index_exists(self) -> bool:
        """
        Check if the index database file exists.

        Returns:
            True if the database file exists, False otherwise
        """
        return Path(self.db_path).exists()

    def validate_schema(self) -> bool:
        """Check if the database schema is valid."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if required tables exist
            required_tables = ["code_index", "code_index_fts", "indexed_files", "code_index_meta"]
            _ = cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ({})
            """.format(",".join("?" * len(required_tables))),
                required_tables,
            )

            existing_tables = {row["name"] for row in cursor.fetchall()}

            # Check if all required tables exist
            if not all(table in existing_tables for table in required_tables):
                return False

            # Check if FTS table is properly configured
            _ = cursor.execute("SELECT sql FROM sqlite_master WHERE name='code_index_fts'")
            fts_sql = cursor.fetchone()
            return fts_sql and "fts5" in fts_sql["sql"].lower()

    def _row_to_symbol(self, row: sqlite3.Row) -> CodeSymbol:
        """Convert a database row to a CodeSymbol object."""
        return CodeSymbol(
            id=row["id"],
            name=row["name"],
            symbol_type=row["symbol_type"],
            file_path=row["file_path"],
            start_line_number=row["line_number"],
            start_column_number=row["column_number"],
            end_line_number=row["end_line_number"],
            end_column_number=row["end_column_number"],
            language=row["language"],
            signature=row["signature"],
            docstring=row["docstring"],
            parent_symbol=row["parent_symbol"],
            scope=row["scope"],
            parameters=row["parameters"],
            return_type=row["return_type"],
            file_hash=row["file_hash"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )
