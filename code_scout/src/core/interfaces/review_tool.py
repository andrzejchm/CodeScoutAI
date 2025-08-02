from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.models.code_diff import CodeDiff


class ReviewTool(ABC):
    """Abstract base class for external tools integration."""

    @abstractmethod
    def analyze(self, diffs: List[CodeDiff]) -> Dict[str, Any]:
        """Analyze code diffs and return tool-specific results."""
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Return the name of this tool."""
        pass
