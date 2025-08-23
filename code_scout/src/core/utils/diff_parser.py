from io import StringIO
from typing import Any, Optional

from unidiff import PatchSet, UnidiffParseError

from core.models.diff_hunk import DiffHunk, DiffLine
from core.models.parsed_diff import ParsedDiff


def parse_github_file(
    file_obj: Any,
) -> Optional[ParsedDiff]:
    """
    Parses a GitHub file object from PyGithub into a structured ParsedDiff object.

    It constructs a full diff string from the file object's metadata and patch,
    then uses parse_diff_string to parse it.

    Args:
        file_obj: A file object from the PyGithub library.

    Returns:
        A ParsedDiff object if parsing is successful, otherwise None.
    """
    if not file_obj.patch:
        return None

    source_path = file_obj.filename
    target_path = file_obj.filename

    if file_obj.status == "added":
        source_path = "/dev/null"
    elif file_obj.status == "removed":
        target_path = "/dev/null"
    elif file_obj.status == "renamed":
        source_path = file_obj.previous_filename

    # The patch from GitHub API doesn't include the ---/+++ headers, so we construct them.
    full_diff = f"--- a/{source_path}\n+++ b/{target_path}\n{file_obj.patch}"

    return parse_diff_string(full_diff, file_obj.filename)


def parse_diff_string(diff_string: str, filename: str) -> Optional[ParsedDiff]:
    """
    Parses a raw unified diff string into a structured ParsedDiff object.

    Args:
        diff_string: The raw diff content for a single file.

    Returns:
        A ParsedDiff object if parsing is successful, otherwise None.
    """
    try:
        if not diff_string:
            return None

        # PatchSet expects the diff content to be iterable, e.g., a list of lines
        patch_set = PatchSet(StringIO(diff_string))
        patched_file = next(iter(patch_set), None)

        if patched_file is None:
            return None

        hunks = []
        for hunk in patched_file:
            lines = [
                DiffLine(
                    line_type=line.line_type,
                    source_line_no=line.source_line_no,
                    target_line_no=line.target_line_no,
                    value=line.value,
                )
                for line in hunk
            ]
            hunks.append(
                DiffHunk(
                    source_start=hunk.source_start,
                    source_length=hunk.source_length,
                    target_start=hunk.target_start,
                    target_length=hunk.target_length,
                    heading=hunk.section_header,
                    lines=lines,
                )
            )

        # Strip 'a/' and 'b/' prefixes from file paths
        source_file = (
            patched_file.source_file[2:] if patched_file.source_file.startswith("a/") else patched_file.source_file
        )
        target_file = (
            patched_file.target_file[2:] if patched_file.target_file.startswith("b/") else patched_file.target_file
        )

        return ParsedDiff(
            source_file=source_file,
            target_file=target_file,
            hunks=hunks,
            is_added_file=patched_file.is_added_file,
            is_removed_file=patched_file.is_removed_file,
            is_modified_file=patched_file.is_modified_file,
            is_renamed_file=patched_file.is_rename,
        )
    except UnidiffParseError as e:
        raise DiffParsingError(f"Error while parsing diff for file {filename}.\ncause: {e}") from e


class DiffParsingError(Exception):
    pass
