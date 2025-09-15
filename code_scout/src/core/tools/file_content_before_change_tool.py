from typing import Annotated, override

from langchain_core.tools import BaseTool, tool

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.langchain_review_tool import LangChainReviewTool
from core.models.code_diff import CodeDiff


class FileContentBeforeChangeTool(LangChainReviewTool):
    """Tool that allows LLM to access full file content before the change during code review."""

    def __init__(self) -> None:
        self.diff_provider: DiffProvider | None = None

    @override
    def get_tool(self, diffs: list[CodeDiff], diff_provider: DiffProvider) -> BaseTool | None:
        self.diff_provider = diff_provider

        @tool("get_file_content_before_change")
        def get_file_content_before_change(
            file_path: Annotated[str, "Path to the file in the repository"],
        ) -> str:
            """Get the complete content of any file in the repository before the change.

            WHEN TO USE get_file_content_before_change:
            - When diff context is insufficient to understand the change
            - To see complete function/class definitions in the old version of any file
            - To understand imports and dependencies in the old version of any file
            - To analyze broader code patterns and architecture in the old version of any file
            - To check how modified code fits within the overall file structure in the old version of any file

            USAGE GUIDELINES:
            - Use strategically - don't request files unless you need the additional context
            - Focus on files where the diff doesn\'t provide enough information for thorough review, or to get context from related files.
            """
            print(f"File content before change tool invoked, returning content for: {file_path}")

            if not self.diff_provider:
                return "Diff provider not initialized for this tool."

            content = self.diff_provider.get_file_contents_before_change(file_path)
            if content is None:
                return f"File '{file_path}' has no content available before change."

            return content

        return get_file_content_before_change

