from enum import Enum

from core.interfaces.langchain_review_tool import LangChainReviewTool
from src.core.models.review_finding import Severity, Category


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

    langchain_tools: list[LangChainReviewTool]
    show_code_excerpts: bool
    context_lines_before: int
    context_lines_after: int
    max_excerpt_lines: int
    max_tool_calls_per_review: int
    allowed_severities: list[str] | None = None
    banned_severities: list[str] | None = None
    allowed_categories: list[str] | None = None
    banned_categories: list[str] | None = None

    def __init__(  # noqa: PLR0913
        self,
        langchain_tools: list["LangChainReviewTool"],
        max_tool_calls_per_review: int = 10,
        show_code_excerpts: bool = True,
        context_lines_before: int = 3,
        context_lines_after: int = 3,
        max_excerpt_lines: int = 20,
        allowed_severities: list[str] | None = None,
        banned_severities: list[str] | None = None,
        allowed_categories: list[str] | None = None,
        banned_categories: list[str] | None = None,
    ):
        self.langchain_tools = langchain_tools
        self.show_code_excerpts = show_code_excerpts
        self.context_lines_before = context_lines_before
        self.context_lines_after = context_lines_after
        self.max_excerpt_lines = max_excerpt_lines
        self.max_tool_calls_per_review = max_tool_calls_per_review
        self.allowed_severities = allowed_severities
        self.banned_severities = banned_severities
        self.allowed_categories = allowed_categories
        self.banned_categories = banned_categories
