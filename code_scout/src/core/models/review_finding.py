from enum import Enum
from typing import Any, Dict, Optional, Tuple

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
    line_number: Optional[int] = None
    line_range: Optional[Tuple[int, int]] = None
    message: str
    suggestion: Optional[str] = None
    code_example: Optional[str] = None
    confidence: float = 1.0  # Confidence score from 0.0 to 1.0
    tool_name: Optional[str] = None  # Which tool/chain generated this finding
    metadata: Dict[str, Any] = {}

    # Code excerpt fields for showing context around the finding
    code_excerpt: Optional[str] = None  # The actual code lines with context
    excerpt_start_line: Optional[int] = None  # Starting line number of excerpt
    excerpt_end_line: Optional[int] = None  # Ending line number of excerpt
