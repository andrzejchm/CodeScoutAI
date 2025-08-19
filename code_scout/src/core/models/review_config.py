from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.interfaces.langchain_review_tool import LangChainReviewTool


class ReviewType(str, Enum):
    BUGS = "bugs"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BEST_PRACTICES = "best_practices"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"


class ReviewConfig:
    """Configuration for the code review pipeline."""

    def __init__(  # noqa: PLR0913
        self,
        langchain_tools: List["LangChainReviewTool"],
        max_tool_calls_per_review: int = 10,
        show_code_excerpts: bool = True,
        context_lines_before: int = 3,
        context_lines_after: int = 3,
        max_excerpt_lines: int = 20,
    ):
        self.langchain_tools = langchain_tools
        self.show_code_excerpts = show_code_excerpts
        self.context_lines_before = context_lines_before
        self.context_lines_after = context_lines_after
        self.max_excerpt_lines = max_excerpt_lines
        self.max_tool_calls_per_review = max_tool_calls_per_review
