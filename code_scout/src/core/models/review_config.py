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
    output_format: str = "cli"  # cli, json, markdown, github
    include_suggestions: bool = True
    include_code_examples: bool = True
    
    # Extensibility
    custom_chains: List[str] = []
    custom_tools: Dict[str, Any] = {}
    
    # LLM configuration
    max_tokens_per_request: int = 4000
    temperature: float = 0.1
    enable_structured_output: bool = True
