from abc import ABC, abstractmethod
from typing import List, Optional

from langchain_core.tools import BaseTool

from core.models.code_diff import CodeDiff


class LangChainReviewTool(ABC):
    """Abstract base class for LangChain tools used in code review."""

    @abstractmethod
    def get_tool(self, diffs: List[CodeDiff]) -> Optional[BaseTool]:
        """Create and return a LangChain tool configured for the given diffs.

        Returns:
            BaseTool if the tool is available, None if the tool should not be loaded
        """
        pass
