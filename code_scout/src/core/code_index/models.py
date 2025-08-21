from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CodeSymbol(BaseModel):
    """Represents a single code symbol from the code_index table."""

    id: Optional[int] = None
    name: str
    symbol_type: str  # 'function', 'class', 'method', 'variable', 'import'
    file_path: str
    start_line_number: int
    start_column_number: Optional[int] = None
    end_line_number: Optional[int] = None
    end_column_number: Optional[int] = None
    language: str
    signature: Optional[str] = None  # Function/method signature
    docstring: Optional[str] = None  # Documentation string
    parent_symbol: Optional[str] = None  # For methods/nested functions
    scope: Optional[str] = None  # 'public', 'private', 'protected'
    parameters: Optional[str] = None  # JSON array of parameter info
    return_type: Optional[str] = None
    file_hash: str  # For change detection
    source_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CodeFile(BaseModel):
    """Represents a code file with its path, language, and hash."""

    file_path: str
    language: str
    file_hash: str


class CodeIndexQuery(BaseModel):
    """Represents a search query for code symbols."""

    text: str
    symbol_type: Optional[str] = None
    file_pattern: Optional[str] = None
    limit: int = 20
    boost_paths: Optional[List[str]] = None
    language: Optional[str] = None


class IndexResult(BaseModel):
    """Reports the outcome of an indexing operation."""

    success: bool
    message: str
    symbols_indexed: int = 0
    files_processed: int = 0
    errors: List[str] = []


class UpdateResult(BaseModel):
    """Reports the outcome of a file update operation."""

    success: bool
    message: str
    symbols_updated: int = 0
    symbols_added: int = 0
    symbols_removed: int = 0
    errors: List[str] = []


class IndexStats(BaseModel):
    """Holds index statistics."""

    total_symbols: int = 0
    total_files: int = 0
    symbols_by_type: dict = {}
    symbols_by_language: dict = {}
    last_updated: Optional[datetime] = None
