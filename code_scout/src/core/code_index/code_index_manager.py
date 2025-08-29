import hashlib
import os
from pathlib import Path
from typing import Any, Callable

from gitignore_parser import parse_gitignore  # pyright: ignore[reportUnknownVariableType]

from cli.cli_utils import echo_info
from core.code_index.code_index_config import CodeIndexConfig
from core.code_index.code_index_extractor import CodeIndexExtractor
from core.code_index.code_index_repository import CodeIndexRepository
from core.code_index.models import CodeIndexQuery, CodeSymbol, IndexResult, IndexStats, UpdateResult


class CodeIndexManager:
    """
    Main orchestration layer for all code index operations.

    Coordinates the CodeIndexRepository and CodeIndexExtractor to provide
    high-level operations for building, updating, and searching code indexes.
    """

    config: CodeIndexConfig
    repository: CodeIndexRepository
    extractor: CodeIndexExtractor

    def __init__(self, config: CodeIndexConfig):
        self.config = config
        self.repository = CodeIndexRepository(config.db_path)
        self.extractor = CodeIndexExtractor()

    def build_index(
        self,
        code_paths: list[str],
        print_file_paths: bool,
    ) -> IndexResult:
        """
        Builds the code index for the configured code paths.

        Returns:
            An IndexResult object indicating success or failure and statistics.
        """
        self.repository.clear_index()
        return self._index_code_paths(
            code_paths=code_paths,
            print_file_paths=print_file_paths,
        )

    def update_file(self, file_path: str) -> UpdateResult:
        """
        Updates the code index for a specific file.

        Args:
            file_path: The path to the file to update.

        Returns:
            An UpdateResult object indicating the outcome of the update.
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.is_file():
            return UpdateResult(success=False, message=f"File not found: {file_path}")

        current_hash = _calculate_file_hash(file_path)
        stored_hash = self.repository.get_file_hash(file_path)

        if current_hash == stored_hash:
            return UpdateResult(success=True, message="No changes detected", symbols_added=0, symbols_removed=0)

        old_symbol_count = self.repository.count_symbols_by_file(file_path)
        self.repository.delete_symbols_by_file(file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            symbols = self.extractor.extract_symbols(file_path, content)
            self.repository.insert_symbols(symbols)
            self.repository.update_file_tracking(file_path, current_hash, len(symbols))

            return UpdateResult(
                success=True,
                message="File updated successfully",
                symbols_added=len(symbols),
                symbols_removed=old_symbol_count,
            )
        except Exception as e:
            return UpdateResult(success=False, message=f"Error processing file {file_path}: {e}")

    def rebuild_index(
        self,
        code_paths: list[str],
        print_file_paths: bool,
    ) -> IndexResult:
        """
        Rebuilds the entire code index from scratch for the configured code paths.

        Arguments:
            code_paths: The code paths to rebuild.
            print_file_paths: whether to print paths of files that are being rebuilt.

        Returns:
            An IndexResult object indicating success or failure and statistics.
        """
        self.repository.clear_index()
        return self._index_code_paths(
            code_paths=code_paths,
            print_file_paths=print_file_paths,
        )

    def search_symbols(self, query: CodeIndexQuery) -> list[CodeSymbol]:
        """
        Searches for code symbols in the index.

        Args:
            query: A CodeIndexQuery object specifying the search criteria.

        Returns:
            A list of CodeSymbol objects matching the query.
        """
        filters = {
            "symbol_type": query.symbol_type,
            "file_pattern": query.file_pattern,
            "language": query.language,
            "limit": query.limit,
        }
        return self.repository.search_fts(query.text, filters)

    def get_index_stats(self) -> IndexStats:
        """
        Retrieves statistics about the code index.

        Returns:
            An IndexStats object containing various statistics.
        """
        return self.repository.get_index_stats()

    def get_symbol_types(self) -> list[str]:
        """
        Retrieves a list of distinct symbol types present in the index.

        Returns:
            A list of strings, each representing a unique symbol type.
        """
        return self.repository.get_distinct_symbol_types()

    def index_exists(self) -> bool:
        """
        Checks if the code index database file exists.

        Returns:
            True if the database exists, False otherwise.
        """
        return self.repository.index_exists()

    def validate_schema(self) -> bool:
        """
        Validates the schema of the code index database.

        Returns:
            True if the schema is valid, False otherwise.
        """
        return self.repository.validate_schema()

    def _index_code_paths(
        self,
        code_paths: list[str],
        print_file_paths: bool,
    ) -> IndexResult:
        """
        Internal method to index a list of code paths.
        """
        total_symbols_indexed = 0
        total_files_processed = 0
        errors: list[str] = []

        for code_path in code_paths:
            repo_path_obj = Path(code_path)
            if not repo_path_obj.exists():
                errors.append(f"Code path does not exist: {code_path}")
                continue

            gitignore_path = repo_path_obj / ".gitignore"
            matches: Callable[..., bool] | None = (
                parse_gitignore(gitignore_path, repo_path_obj.as_posix()) if gitignore_path.exists() else None
            )  # pyright: ignore[reportUnknownVariableType]

            for file_path_str in self._scan_files(code_path, matches):
                relative_file_path = str(Path(file_path_str).relative_to(repo_path_obj))

                total_files_processed += 1
                try:
                    if print_file_paths:
                        echo_info(file_path_str)
                    current_hash = _calculate_file_hash(file_path_str)
                    with open(file_path_str, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    symbols = self.extractor.extract_symbols(file_path_str, content)

                    for symbol in symbols:
                        symbol.file_path = relative_file_path
                        symbol.file_hash = current_hash

                    self.repository.insert_symbols(symbols)
                    self.repository.update_file_tracking(relative_file_path, current_hash, len(symbols))
                    total_symbols_indexed += len(symbols)
                except Exception as e:
                    errors.append(f"Error processing file {file_path_str}: {e}")

        return IndexResult(
            success=not errors,
            message="Index built successfully" if not errors else "Index built with errors",
            symbols_indexed=total_symbols_indexed,
            files_processed=total_files_processed,
            errors=errors,
        )

    def _scan_files(self, code_path: str, gitignore_matches: Any) -> list[str]:
        """
        Scans the given code path for files to be indexed, respecting .gitignore and file extensions.
        """
        file_paths: list[str] = []
        code_path_obj = Path(code_path)
        for root, _, files in os.walk(code_path):
            for file in files:
                file_path = Path(root) / file
                file_path_str = file_path.as_posix()
                relative_to_code_path = file_path.relative_to(code_path_obj).as_posix()

                if gitignore_matches and gitignore_matches(relative_to_code_path):
                    continue

                if self.config.file_extensions:
                    file_extension = file_path.suffix.lstrip(".")
                    if file_extension not in self.config.file_extensions:
                        continue

                if not self.extractor.detect_language(file_path_str):
                    continue

                file_paths.append(file_path_str)
        return file_paths


def _calculate_file_hash(file_path: str) -> str:
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()
