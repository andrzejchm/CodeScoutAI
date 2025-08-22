from typing import List

from pydantic import BaseModel

from .diff_hunk import DiffHunk


class ParsedDiff(BaseModel):
    """Represents the complete, parsed diff for a single file."""

    source_file: str
    target_file: str
    hunks: List[DiffHunk]
    is_added_file: bool
    is_removed_file: bool
    is_modified_file: bool
    is_renamed_file: bool

    @property
    def llm_repr(self) -> str:
        """
        Returns a string representation of the ParsedDiff suitable for LLM input.
        """
        hunks_repr = "\n\n".join([hunk.llm_repr for hunk in self.hunks])

        file_identifier = ""
        change_type_str = ""

        if self.is_added_file:
            change_type_str = "Added"
            file_identifier = self.target_file
        elif self.is_removed_file:
            change_type_str = "Removed"
            file_identifier = self.source_file
        elif self.is_renamed_file:
            change_type_str = "Renamed"
            file_identifier = f"from {self.source_file} to {self.target_file}"
        elif self.is_modified_file:
            change_type_str = "Modified"
            file_identifier = self.target_file

        return f"File: {file_identifier}\nChange Type: {change_type_str}\nHunks:\n{hunks_repr}"
