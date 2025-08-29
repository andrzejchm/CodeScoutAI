from dataclasses import dataclass


@dataclass
class CodeExcerpt:
    """Represents a code excerpt with context lines."""

    content: str
    start_line: int
    end_line: int
    target_line: int | None = None  # The specific line that was highlighted
    target_range: tuple[int, int] | None = None  # The specific range that was highlighted


class CodeExcerptExtractor:
    """Utility for extracting code excerpts with context from file content."""

    @staticmethod
    def extract_with_context(
        file_content: str,
        line_number: int | None = None,
        line_range: tuple[int, int] | None = None,
        context_lines: int = 3,
        max_excerpt_lines: int = 20,
    ) -> "CodeExcerpt | None":
        """
        Extract code excerpt with context lines around a specific line or range.

        Args:
            file_content: The full content of the file
            line_number: Specific line number to extract context around (1-based)
            line_range: Range of lines to extract context around (1-based, inclusive)
            context_lines_before: Number of context lines before the target
            context_lines_after: Number of context lines after the target
            max_excerpt_lines: Maximum total lines in the excerpt

        Returns:
            CodeExcerpt object or None if extraction fails
        """
        if not file_content:
            return None

        if not line_number and not line_range:
            return None

        lines = file_content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return None

        # Determine target range
        if line_number:
            target_start = line_number
            target_end = line_number
        elif line_range:
            target_start, target_end = line_range
        else:
            return None

        # Validate line numbers (convert to 0-based for array access)
        target_start_idx = max(0, target_start - 1)
        target_end_idx = min(total_lines - 1, target_end - 1)

        if target_start_idx >= total_lines or target_end_idx < 0:
            return None

        # Calculate excerpt boundaries with context
        excerpt_start_idx = max(0, target_start_idx - context_lines)
        excerpt_end_idx = min(total_lines - 1, target_end_idx + context_lines)

        # Limit excerpt size
        if (excerpt_end_idx - excerpt_start_idx + 1) > max_excerpt_lines:
            # Prioritize showing the target lines by centering them
            available_context = max_excerpt_lines - (target_end_idx - target_start_idx + 1)
            context_before = available_context // 2
            context_after = available_context - context_before

            excerpt_start_idx = max(0, target_start_idx - context_before)
            excerpt_end_idx = min(total_lines - 1, target_end_idx + context_after)

        # Extract the lines
        excerpt_lines = lines[excerpt_start_idx : excerpt_end_idx + 1]
        excerpt_content = "\n".join(excerpt_lines)

        return CodeExcerpt(
            content=excerpt_content,
            start_line=excerpt_start_idx + 1,  # Convert back to 1-based
            end_line=excerpt_end_idx + 1,  # Convert back to 1-based
            target_line=line_number,
            target_range=line_range,
        )

    @staticmethod
    def is_binary_content(content: str) -> bool:
        """
        Check if content appears to be binary (contains null bytes or high
        ratio of non-printable chars).

        Args:
            content: File content to check

        Returns:
            True if content appears to be binary
        """
        if not content:
            return False

        # Check for null bytes (common in binary files)
        if "\x00" in content:
            return True

        # Check ratio of printable characters
        if len(content) > 0:
            printable_chars = sum(1 for c in content if c.isprintable() or c in "\n\r\t")
            ratio = printable_chars / len(content)
            min_printable_ratio = 0.7
            return ratio < min_printable_ratio  # If less than 70% printable, consider binary

        return False

    @staticmethod
    def is_file_too_large(content: str, max_size_kb: int = 500) -> bool:
        """
        Check if file content is too large for excerpt extraction.

        Args:
            content: File content to check
            max_size_kb: Maximum file size in KB

        Returns:
            True if file is too large
        """
        if not content:
            return False

        size_bytes = len(content.encode("utf-8"))
        size_kb = size_bytes / 1024
        return size_kb > max_size_kb
