from enum import Enum
from typing import Any

from pydantic import BaseModel


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"


class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    ARCHITECTURE = "architecture"
    BEST_PRACTICES = "best_practices"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    OTHER = "other"


class ReviewFinding(BaseModel):
    """Represents a single finding from the code review."""

    severity: Severity
    category: Category
    file_path: str
    line_number: int | None = None
    line_range: tuple[int, int] | None = None
    message: str
    suggestion: str | None = None
    code_example: str | None = None
    confidence: float = 1.0  # Confidence score from 0.0 to 1.0
    tool_name: str | None = None  # Which tool/chain generated this finding
    metadata: dict[str, Any] = {}

    # Code excerpt fields for showing context around the finding
    code_excerpt: str | None = None  # The actual code lines with context
    excerpt_start_line: int | None = None  # Starting line number of excerpt
    excerpt_end_line: int | None = None  # Ending line number of excerpt
