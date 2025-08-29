from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CodeSymbol(BaseModel):
    """Represents a single code symbol from the code_index table."""

    id: int | None = None
    name: str
    symbol_type: str  # 'function', 'class', 'method', 'variable', 'import'
    file_path: str
    start_line_number: int
    start_column_number: int | None = None
    end_line_number: int | None = None
    end_column_number: int | None = None
    language: str
    signature: str | None = None  # Function/method signature
    docstring: str | None = None  # Documentation string
    parent_symbol: str | None = None  # For methods/nested functions
    scope: str | None = None  # 'public', 'private', 'protected'
    parameters: str | None = None  # JSON array of parameter info
    return_type: str | None = None
    file_hash: str  # For change detection
    source_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CodeFile(BaseModel):
    """Represents a code file with its path, language, and hash."""

    file_path: str
    language: str
    file_hash: str


class CodeIndexQuery(BaseModel):
    """Represents a search query for code symbols."""

    text: str
    symbol_type: str | None = None
    file_pattern: str | None = None
    limit: int = 20
    boost_paths: list[str] | None = None
    language: str | None = None


class IndexResult(BaseModel):
    """Reports the outcome of an indexing operation."""

    success: bool
    message: str
    symbols_indexed: int = 0
    files_processed: int = 0
    errors: list[str] = []


class UpdateResult(BaseModel):
    """Reports the outcome of a file update operation."""

    success: bool
    message: str
    symbols_updated: int = 0
    symbols_added: int = 0
    symbols_removed: int = 0
    errors: list[str] = []


class IndexStats(BaseModel):
    """Holds index statistics."""

    total_symbols: int = 0
    total_files: int = 0
    symbols_by_type: dict[Any, Any] = {}
    symbols_by_language: dict[Any, Any] = {}
    last_updated: datetime | None = None
