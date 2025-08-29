from pydantic import BaseModel


class DiffLine(BaseModel):
    """Represents a single line in a diff hunk."""

    line_type: str
    source_line_no: int | None = None
    target_line_no: int | None = None
    value: str


class DiffHunk(BaseModel):
    """Represents a 'hunk' or a contiguous block of changes in a diff."""

    source_start: int
    source_length: int
    target_start: int
    target_length: int
    heading: str
    lines: list[DiffLine]

    @property
    def llm_repr(self) -> str:
        """
        Returns a string representation of the DiffHunk suitable for LLM input,
        including the actual diff lines.
        """
        lines_content = []
        max_line_no_len = len(str(max(self.source_start + self.source_length, self.target_start + self.target_length)))

        for line in self.lines:
            prefix = ""
            source_line_str = ""
            target_line_str = ""

            if line.line_type in ["add", "+"]:
                prefix = "+"
                target_line_str = str(line.target_line_no).ljust(max_line_no_len)
                source_line_str = "".ljust(max_line_no_len)
            elif line.line_type in ["delete", "-"]:
                prefix = "-"
                source_line_str = str(line.source_line_no).ljust(max_line_no_len)
                target_line_str = "".ljust(max_line_no_len)
            elif line.line_type in ["normal", "", " "]:
                prefix = " "
                source_line_str = str(line.source_line_no).ljust(max_line_no_len)
                target_line_str = str(line.target_line_no).ljust(max_line_no_len)

            lines_content.append(f"{prefix} {source_line_str} {target_line_str} {line.value}")

        diff = f"```diff\n{''.join(lines_content)}\n```"
        hunk_header = f"Hunk Header: {self.heading}\n" if self.heading.strip() else ""
        return f"{hunk_header}{diff}"
