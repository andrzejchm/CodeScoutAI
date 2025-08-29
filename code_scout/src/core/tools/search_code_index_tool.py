from typing import Annotated, override

from langchain_core.tools import BaseTool, tool  # pyright: ignore[reportUnknownVariableType]

from core.code_index.code_index_config import CodeIndexConfig
from core.code_index.code_index_manager import CodeIndexManager
from core.code_index.models import CodeIndexQuery, CodeSymbol
from core.interfaces.langchain_review_tool import LangChainReviewTool
from core.models.code_diff import CodeDiff


class SearchCodeIndexTool(LangChainReviewTool):
    """Tool that allows LLM to search code symbols using the code index during code review."""

    # Maximum length for docstring display
    MAX_DOCSTRING_LENGTH: int = 100

    def __init__(self, db_path: str = "./.codescout/code_index.db"):
        """
        Initialize the search code index tool.

        Args:
            db_path: Path to the code index database file
        """
        self.db_path: str = db_path

    @override
    def get_tool(self, diffs: list[CodeDiff]) -> BaseTool | None:
        """
        Create code index search tool configured for the given diffs.

        Args:
            diffs: List of code diffs being reviewed

        Returns:
            BaseTool for searching code symbols, or None if index is not available
        """
        # Initialize the code index manager
        config = CodeIndexConfig(db_path=self.db_path)
        manager = CodeIndexManager(config)

        # Check if index exists and schema is valid
        if not manager.index_exists() or not manager.validate_schema():
            # Return None when index is not available - tool will not be loaded
            return None

        # Extract file paths from diffs for relevance boosting
        diff_file_paths = [diff.file_path for diff in diffs if diff.file_path]

        @tool("search_code_index")
        def search_code_index(
            query: Annotated[str, "Search query for finding code symbols (functions, classes, methods, etc.)"],
            symbol_type: Annotated[
                str | None, "Filter by symbol type: 'function', 'class', 'method', 'variable', 'import'"
            ] = None,
            file_pattern: Annotated[str | None, "Filter by file pattern (e.g., '*.py', 'src/*')"] = None,
            limit: Annotated[int, "Maximum number of results to return"] = 20,
        ) -> str:
            """Search the code index for symbols (functions, classes, methods, variables, imports).

            WHEN TO USE search_code_index:
            - To find function/class definitions referenced in the diff
            - To understand how modified code relates to the broader codebase
            - To locate similar patterns or implementations
            - To find dependencies and usage examples
            - To understand the context of imported modules or functions
            - To identify potential impact areas for the changes

            USAGE GUIDELINES:
            - Use descriptive search terms (function names, class names, keywords)
            - Filter by symbol_type when looking for specific kinds of symbols
            - Use file_pattern to narrow search to specific directories or file types
            - Results are ranked by relevance, with files from the current diff boosted
            """
            try:
                # Create search query with boost paths from current diffs
                search_query = CodeIndexQuery(
                    text=query,
                    symbol_type=symbol_type,
                    file_pattern=file_pattern,
                    limit=limit,
                    boost_paths=diff_file_paths if diff_file_paths else None,
                )

                # Perform the search
                results = manager.search_symbols(search_query)

                # Format results for LLM consumption
                return self._format_search_results(results)

            except Exception as e:
                return f"Error searching code index: {e!s}"

        return search_code_index

    def _format_search_results(self, results: list[CodeSymbol]) -> str:
        """
        Format search results into a clear, concise string for the LLM.

        Args:
            results: List of CodeSymbol objects from the search

        Returns:
            Formatted string representation of the search results
        """
        if not results:
            return "No symbols found matching the search criteria."

        formatted_lines = [f"Found {len(results)} symbol(s):\n"]

        for i, symbol in enumerate(results, 1):
            # Build symbol info line
            symbol_info = f"{i}. {symbol.name} ({symbol.symbol_type})"

            # Add parent context if available
            if symbol.parent_symbol:
                symbol_info += f" in {symbol.parent_symbol}"

            # Add location info
            location = f"{symbol.file_path}:{symbol.start_line_number}"
            if symbol.end_line_number and symbol.end_line_number != symbol.start_line_number:
                location += f"-{symbol.end_line_number}"

            formatted_lines.append(f"   {symbol_info}")
            formatted_lines.append(f"   Location: {location}")

            # Add signature if available
            if symbol.signature:
                formatted_lines.append(f"   Signature: {symbol.signature}")

            # Add docstring if available (truncated)
            if symbol.docstring:
                docstring = symbol.docstring.strip()
                if len(docstring) > self.MAX_DOCSTRING_LENGTH:
                    docstring = docstring[:97] + "..."
                formatted_lines.append(f"   Doc: {docstring}")

            # Add scope if available
            if symbol.scope:
                formatted_lines.append(f"   Scope: {symbol.scope}")

            formatted_lines.append("")  # Empty line between results

        return "\n".join(formatted_lines)
