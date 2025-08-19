from typing import Annotated, List

from langchain_core.tools import BaseTool, tool

from core.interfaces.langchain_review_tool import LangChainReviewTool
from core.models.code_diff import CodeDiff


class FileContentTool(LangChainReviewTool):
    """Tool that allows LLM to access full file content during code review."""

    def __init__(self):
        self.file_content_map = {}

    def get_tool(self, diffs: List[CodeDiff]) -> BaseTool:
        """Create file content access tool configured for the given diffs."""
        # Build file content map from diffs
        self.file_content_map = {
            diff.file_path: diff.current_file_content for diff in diffs if diff.current_file_content
        }

        @tool("get_full_file_content")
        def get_full_file_content(
            file_path: Annotated[str, "Path to the file (must be one of the files in the current diff)"],
        ) -> str:
            """Get the complete content of a file that's part of the current code review.

            Returns:
                Complete file content as string, or error message if file not available
            """
            if file_path not in self.file_content_map:
                available_files = list(self.file_content_map.keys())
                return f"File '{file_path}' not available. Available files: {available_files}"

            content = self.file_content_map[file_path]
            if not content:
                return f"File '{file_path}' has no content available."

            return content

        return get_full_file_content

    def get_tool_prompt_addition(self) -> str:
        """Return additional prompt text for file content tool."""
        return """
AVAILABLE TOOL:
- get_full_file_content(file_path): Get complete content of files in the current review

WHEN TO USE get_full_file_content:
- When diff context is insufficient to understand the change
- To see complete function/class definitions
- To understand imports and dependencies
- To analyze broader code patterns and architecture
- To check how modified code fits within the overall file structure

USAGE GUIDELINES:
- Only request files that are part of the current code review
- Use strategically - don't request files unless you need the additional context
- Focus on files where the diff doesn't provide enough information for thorough review
"""

    def get_tool_name(self) -> str:
        """Return the name of this tool."""
        return "File Content Access"
