from typing import List, Optional

from pydantic import BaseModel

from .diff_hunk import DiffHunk
from .parsed_diff import ParsedDiff


class CodeDiff(BaseModel):
    diff: str  # The raw diff string
    hunks: List[DiffHunk]  # A list of hunks for direct access by the review chain
    parsed_diff: Optional[ParsedDiff] = None  # The full parsed object for detailed analysis
    file_path: str
    old_file_path: Optional[str] = None
    change_type: str
    current_file_content: Optional[str] = None  # Full current file content for excerpt extraction

    @property
    def llm_repr(self) -> str:
        """
        Returns a string representation of the CodeDiff suitable for LLM input.
        """
        if self.parsed_diff:
            return self.parsed_diff.llm_repr
        else:
            # Fallback if parsed_diff is not available, though it should be.
            hunks_repr = "\n".join([hunk.llm_repr for hunk in self.hunks])
            return f"File: {self.file_path}\nChange Type: {self.change_type}\nDiff:\n{hunks_repr}"
