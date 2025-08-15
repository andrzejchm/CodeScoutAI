from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class ReviewType(str, Enum):
    BUGS = "bugs"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BEST_PRACTICES = "best_practices"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"


class ReviewConfig(BaseModel):
    """Configuration for the code review pipeline."""

    # Core review types
    enabled_review_types: List[ReviewType] = [
        ReviewType.BUGS,
        ReviewType.SECURITY,
        ReviewType.PERFORMANCE,
        ReviewType.STYLE,
        ReviewType.BEST_PRACTICES,
    ]

    # Pipeline configuration
    enable_holistic_review: bool = True
    enable_file_level_review: bool = True
    enable_function_level_review: bool = True

    # Output configuration
    include_suggestions: bool = True
    include_code_examples: bool = True

    # Extensibility
    custom_chains: List[str] = []
    custom_tools: Dict[str, Any] = {}

    # LLM configuration
    max_tokens_per_request: int = 4000
    temperature: float = 0.1
    enable_structured_output: bool = True

    # Code Excerpt Configuration
    show_code_excerpts: bool = True
    context_lines_before: int = 3
    context_lines_after: int = 3
    max_excerpt_lines: int = 20
    max_file_size_kb: int = 500  # Skip files larger than this
