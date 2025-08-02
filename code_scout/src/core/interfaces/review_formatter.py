from abc import ABC, abstractmethod

from core.models.review_result import ReviewResult


class ReviewFormatter(ABC):
    """Abstract base class for output formatting components."""

    @abstractmethod
    def format(self, result: ReviewResult) -> str:
        """Format the review result for output."""
        pass

    @abstractmethod
    def get_formatter_name(self) -> str:
        """Return the name of this formatter."""
        pass
