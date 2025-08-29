from abc import ABC, abstractmethod
from typing import Any

from core.models.code_diff import CodeDiff


class ReviewTool(ABC):
    """Abstract base class for external tools integration."""

    @abstractmethod
    def analyze(self, diffs: list[CodeDiff]) -> dict[str, Any]:
        """
        Analyzes the provided code differences using the external tool.

        Args:
            diffs (list[CodeDiff]): A list of CodeDiff objects representing the changes.

        Returns:
            dict[str, Any]: A dictionary containing the analysis results from the tool.
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """
        Returns the name of the review tool.
        """
        pass
