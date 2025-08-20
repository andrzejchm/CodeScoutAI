import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List

from .code_index_config import CodeIndexConfig
from .code_index_extractor import CodeIndexExtractor
from .code_index_repository import CodeIndexRepository
from .models import CodeIndexQuery, CodeSymbol, IndexResult, IndexStats, UpdateResult


class CodeIndexManager:
    """
    Main orchestration layer for all code index operations.

    Coordinates the CodeIndexRepository and CodeIndexExtractor to provide
    high-level operations for building, updating, and searching code indexes.
    """

    def __init__(self, config: CodeIndexConfig):
        """
        Initialize the manager with configuration.

        Args:
            config: Configuration object containing database path and other settings
        """
        self.config = config
        self.repository = CodeIndexRepository(config.db_path)
        self.extractor = CodeIndexExtractor()

    def build_index(self, repo_path: str) -> IndexResult:
        """
        Build a complete index for the repository.

        Args:
            repo_path: Path to the repository root

        Returns:
            IndexResult with operation status and statistics
        """
        try:
            # Initialize the database
            self.repository.initialize_database()

            # Scan for files
            files_to_index = self._scan_files(repo_path)

            total_symbols = 0
            total_files = 0
            errors = []

            for file_path in files_to_index:
                try:
                    # Calculate file hash
                    file_hash = self._calculate_file_hash(file_path)

                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Extract symbols
                    symbols = self.extractor.extract_symbols(file_path, content)

                    if symbols:
                        # Update file paths to be relative to repo_path
                        relative_path = os.path.relpath(file_path, repo_path)
                        for symbol in symbols:
                            symbol.file_path = relative_path
                            symbol.file_hash = file_hash

                        # Insert symbols into database
                        self.repository.insert_symbols(symbols)
                        total_symbols += len(symbols)

                    # Update file tracking
                    relative_path = os.path.relpath(file_path, repo_path)
                    self.repository.update_file_tracking(relative_path, file_hash, len(symbols))
                    total_files += 1

                except Exception as e:
                    errors.append(f"Error processing {file_path}: {e!s}")

            return IndexResult(
                success=True,
                message=f"Successfully indexed {total_files} files with {total_symbols} symbols",
                symbols_indexed=total_symbols,
                files_processed=total_files,
                errors=errors,
            )

        except Exception as e:
            return IndexResult(
                success=False,
                message=f"Failed to build index: {e!s}",
                symbols_indexed=0,
                files_processed=0,
                errors=[str(e)],
            )

    def update_file(self, file_path: str) -> UpdateResult:
        """
        Update the index for a single file.

        Args:
            file_path: Path to the file to update

        Returns:
            UpdateResult with operation status and statistics
        """
        try:
            # Calculate new file hash
            new_hash = self._calculate_file_hash(file_path)

            # Get stored hash
            stored_hash = self.repository.get_file_hash(file_path)

            # If hashes match, no update needed
            if stored_hash == new_hash:
                return UpdateResult(
                    success=True,
                    message="File unchanged, no update needed",
                    symbols_updated=0,
                    symbols_added=0,
                    symbols_removed=0,
                )

            # Check if this is a file rename (hash exists at different path)
            if stored_hash is None:
                # Check if the hash exists for a different file
                indexed_files = self.repository.get_indexed_files()
                for indexed_file in indexed_files:
                    if indexed_file["file_hash"] == new_hash:
                        # This is likely a renamed file
                        old_path = indexed_file["file_path"]
                        self.repository.delete_symbols_by_file(old_path)
                        break

            # Remove old symbols for this file
            old_symbols_count = 0
            if stored_hash:
                # Count existing symbols before deletion
                with self.repository._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM code_index WHERE file_path = ?", (file_path,))
                    old_symbols_count = cursor.fetchone()["count"]

                self.repository.delete_symbols_by_file(file_path)

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extract new symbols
            symbols = self.extractor.extract_symbols(file_path, content)

            symbols_added = 0
            if symbols:
                # Update file hash for all symbols
                for symbol in symbols:
                    symbol.file_hash = new_hash

                # Insert new symbols
                self.repository.insert_symbols(symbols)
                symbols_added = len(symbols)

            # Update file tracking
            self.repository.update_file_tracking(file_path, new_hash, symbols_added)

            return UpdateResult(
                success=True,
                message=f"Successfully updated file with {symbols_added} symbols",
                symbols_updated=0,  # We replace rather than update
                symbols_added=symbols_added,
                symbols_removed=old_symbols_count,
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"Failed to update file: {e!s}",
                symbols_updated=0,
                symbols_added=0,
                symbols_removed=0,
                errors=[str(e)],
            )

    def rebuild_index(self, repo_path: str) -> IndexResult:
        """
        Clear the existing index and rebuild it from scratch.

        Args:
            repo_path: Path to the repository root

        Returns:
            IndexResult with operation status and statistics
        """
        try:
            # Clear existing data
            if self.index_exists():
                with self.repository._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM code_index")
                    cursor.execute("DELETE FROM indexed_files")
                    conn.commit()

            # Rebuild from scratch
            return self.build_index(repo_path)

        except Exception as e:
            return IndexResult(
                success=False,
                message=f"Failed to rebuild index: {e!s}",
                symbols_indexed=0,
                files_processed=0,
                errors=[str(e)],
            )

    def search_symbols(self, query: CodeIndexQuery) -> List[CodeSymbol]:
        """
        Search for symbols using the provided query.

        Args:
            query: Search query with text and optional filters

        Returns:
            List of matching CodeSymbol objects
        """
        try:
            # Build filters dictionary
            filters: Dict[str, Any] = {"limit": query.limit}

            if query.symbol_type:
                filters["symbol_type"] = query.symbol_type

            if query.file_pattern:
                filters["file_pattern"] = query.file_pattern

            # Use repository's FTS search
            return self.repository.search_fts(query.text, filters)

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_index_stats(self) -> IndexStats:
        """
        Retrieve statistics about the current index.

        Returns:
            IndexStats object with current statistics
        """
        return self.repository.get_index_stats()

    def get_symbol_types(self) -> List[str]:
        """
        Get distinct symbol types present in the index.

        Returns:
            List of symbol type strings
        """
        try:
            with self.repository._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol_type FROM code_index ORDER BY symbol_type")
                rows = cursor.fetchall()
                return [row["symbol_type"] for row in rows]
        except Exception:
            return []

    def index_exists(self) -> bool:
        """
        Check if the index database file exists.

        Returns:
            True if the database file exists, False otherwise
        """
        return Path(self.config.db_path).exists()

    def validate_schema(self) -> bool:
        """
        Validate that the database schema is correct.

        Returns:
            True if schema is valid, False otherwise
        """
        return self.repository.validate_schema()

    def _scan_files(self, repo_path: str) -> List[str]:
        """
        Scan repository for source files, respecting .gitignore.

        Args:
            repo_path: Path to repository root

        Returns:
            List of file paths to index
        """
        repo_path_obj = Path(repo_path)
        files_to_index = []

        # Load .gitignore patterns
        gitignore_patterns = self._load_gitignore_patterns(repo_path_obj)

        # Scan for files
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file():
                # Check if file should be ignored
                relative_path = file_path.relative_to(repo_path_obj)
                if not self._should_ignore_file(relative_path, gitignore_patterns) and self.extractor._detect_language(
                    str(file_path)
                ):
                    files_to_index.append(str(file_path))

        return files_to_index

    def _load_gitignore_patterns(self, repo_path: Path) -> List[str]:
        """
        Load patterns from .gitignore file.

        Args:
            repo_path: Path to repository root

        Returns:
            List of gitignore patterns
        """
        gitignore_path = repo_path / ".gitignore"
        patterns = []

        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for file_line in f:
                        line = file_line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception:
                pass  # Ignore errors reading .gitignore

        # Add common patterns to ignore
        patterns.extend(
            [
                ".git/*",
                ".git/**",
                "*.pyc",
                "__pycache__/*",
                "__pycache__/**",
                ".venv/*",
                ".venv/**",
                "node_modules/*",
                "node_modules/**",
                ".DS_Store",
                "*.log",
            ]
        )

        return patterns

    def _should_ignore_file(self, file_path: Path, patterns: List[str]) -> bool:
        """
        Check if a file should be ignored based on gitignore patterns.

        Args:
            file_path: Relative path to the file
            patterns: List of gitignore patterns

        Returns:
            True if file should be ignored, False otherwise
        """
        file_str = str(file_path)

        for pattern in patterns:
            # Simple pattern matching - could be enhanced with proper gitignore parsing
            if pattern.endswith("/*") or pattern.endswith("/**"):
                # Directory pattern
                dir_pattern = pattern.rstrip("/*")
                if file_str.startswith(dir_pattern + "/"):
                    return True
            elif "*" in pattern:
                # Wildcard pattern - basic implementation
                import fnmatch

                if fnmatch.fnmatch(file_str, pattern):
                    return True
            # Exact match or directory
            elif file_str == pattern or file_str.startswith(pattern + "/"):
                return True

        return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file contents.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()
