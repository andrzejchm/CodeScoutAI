from abc import ABC, abstractmethod

from langchain_core.tools import BaseTool

from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff


class LangChainReviewTool(ABC):
    """Abstract base class for LangChain tools used in code review."""

    @abstractmethod
    def get_tool(self, diffs: list[CodeDiff], diff_provider: DiffProvider) -> BaseTool | None:
        """Create and return a LangChain tool configured for the given diffs.

        Returns:
            BaseTool if the tool is available, None if the tool should not be loaded
        """
        pass
