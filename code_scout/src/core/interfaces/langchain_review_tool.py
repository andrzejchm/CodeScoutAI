from abc import ABC, abstractmethod
from typing import List

from langchain_core.tools import BaseTool

from core.models.code_diff import CodeDiff


class LangChainReviewTool(ABC):
    """Abstract base class for LangChain tools used in code review."""

    @abstractmethod
    def get_tool(self, diffs: List[CodeDiff]) -> BaseTool:
        """Create and return a LangChain tool configured for the given diffs."""
        pass

    @abstractmethod
    def get_tool_prompt_addition(self) -> str:
        """Return additional prompt text to be added to the system message."""
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """Return the name of this tool."""
        pass
