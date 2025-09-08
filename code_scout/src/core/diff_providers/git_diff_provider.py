import os
from typing import override

import git
from git import Diff, DiffIndex
from git.exc import GitCommandError

from cli.cli_utils import echo_debug, echo_warning
from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff
from core.models.parsed_diff import ParsedDiff
from core.utils.code_excerpt_extractor import CodeExcerptExtractor
from core.utils.diff_parser import parse_diff_string

PREVIEW_LENGTH = 200


class GitDiffProvider(DiffProvider):
    repo_path: str
    source: str
    target: str
    staged: bool

    def __init__(
        self,
        repo_path: str,
        source: str = "HEAD",
        target: str = "HEAD",
        staged: bool = False,
    ) -> None:
        self.repo_path = repo_path
        self.source = source
        self.target = target
        self.staged = staged
        if not self.staged and source == target:
            raise ValueError("Source and target branches cannot be the same when not reviewing staged files.")
        if self.staged and source and target:
            echo_warning("Ignoring source and target branches when reviewing staged files.")
        if not repo_path:
            raise ValueError("Repository path cannot be empty.")

    @override
    def get_diff(self) -> list[CodeDiff]:
        repo = git.Repo(path=self.repo_path)
        self._fetch_origin(repo)  # Fetch origin before getting the diff
        diff_index: DiffIndex[Diff] = self._get_diff_index(repo)
        echo_debug(f"found {len(diff_index)} changes")

        diff_list: list[CodeDiff] = []
        for diff_item in diff_index:
            diff_content = self._get_diff_content(diff_item)
            # Use a_path or b_path for the filename to ensure parse_diff_string gets a valid file path
            # b_path is the new path, a_path is the old path
            filename_for_parsing = (
                diff_item.b_path if diff_item.b_path else (diff_item.a_path if diff_item.a_path else "")
            )
            parsed_diff = parse_diff_string(diff_content, filename=filename_for_parsing)

            if parsed_diff:
                change_type = self._map_parsed_diff_to_change_type(parsed_diff)
                # parsed_diff already contains the correct file paths without needing replacement
                file_path = parsed_diff.target_file
                old_file_path = parsed_diff.source_file if parsed_diff.is_renamed_file else None

                current_file_content = self._get_file_content(repo, file_path, change_type)

                code_diff = CodeDiff(
                    diff=diff_content,
                    hunks=parsed_diff.hunks,
                    parsed_diff=parsed_diff,
                    file_path=file_path,
                    old_file_path=old_file_path,
                    change_type=change_type,
                    current_file_content=current_file_content,
                )
                echo_debug(f"Processed {file_path}: {change_type}")
                diff_list.append(code_diff)

        return diff_list

    def _get_diff_index(self, repo: git.Repo) -> DiffIndex[Diff]:
        if self.staged:
            # staged vs HEAD
            return repo.index.diff("HEAD", create_patch=True)

        echo_debug(f"Getting diff for source='{self.source}', target='{self.target}'")
        # PR-style 3-dot diff: merge-base(source, target) .. target
        # (changes introduced by target since it diverged from source)
        try:
            base = repo.git.merge_base(self.source, self.target).strip()
            echo_debug(f"Merge base between '{self.source}' and '{self.target}': {base}")
            diff_index = repo.commit(base).diff(self.source, create_patch=True)
            echo_debug(f"Found {len(diff_index)} diffs using merge-base strategy.")
            return diff_index
        except GitCommandError as e:
            echo_warning(f"Could not determine merge base or get diff: {e}")
            echo_warning(f"Attempting direct diff between '{self.source}' and '{self.target}' as a fallback.")
            diff_index = repo.head.commit.diff(self.source, self.target, create_patch=True)
            echo_debug(f"Found {len(diff_index)} diffs using direct diff strategy.")
            return diff_index

    def _fetch_origin(self, repo: git.Repo) -> None:
        """Fetches the latest changes from the origin remote."""
        try:
            for remote in repo.remotes:
                if remote.name == "origin":
                    echo_debug(f"Fetching latest changes from origin '{remote.url}'...")
                    _ = remote.fetch()
                    echo_debug("Fetch complete.")
                    return
            echo_warning("No 'origin' remote found. Skipping fetch.")
        except GitCommandError as e:
            echo_warning(f"Failed to fetch from origin: {e}")

    def _get_diff_content(self, diff_item: Diff) -> str:
        # Ensure diff_item.diff is not None before decoding
        a_path = diff_item.a_path if diff_item.a_path else "/dev/null"
        b_path = diff_item.b_path if diff_item.b_path else "/dev/null"

        diff_header = f"--- a/{a_path}\n+++ b/{b_path}\n"

        diff_content_str = ""
        if diff_item.diff is not None:
            diff_content_str = (
                diff_item.diff.decode("utf-8", errors="replace")
                if isinstance(diff_item.diff, bytes)
                else str(diff_item.diff)
            )

        return diff_header + diff_content_str

    def _map_parsed_diff_to_change_type(self, parsed_diff: ParsedDiff) -> str:
        if parsed_diff.is_added_file:
            return "added"
        if parsed_diff.is_removed_file:
            return "deleted"
        if parsed_diff.is_renamed_file:
            return "renamed"
        if parsed_diff.is_modified_file:
            return "modified"
        return "unknown"

    def _get_file_content(self, repo: git.Repo, file_path: str, change_type: str) -> str | None:
        """
        Get file content from the local Git repository.

        Args:
            repo: GitPython Repo object
            file_path: Path to the file in the repository
            change_type: Type of change (added, modified, deleted, etc.)

        Returns:
            File content as string, or None if unable to read
        """
        try:
            # Skip deleted files
            if change_type == "deleted":
                return None

            content = self._read_file_content(repo, file_path, change_type)
            if content is None:
                return None

            # Check if content is binary or too large
            if CodeExcerptExtractor.is_binary_content(content):
                return None

            if CodeExcerptExtractor.is_file_too_large(content):
                return None

            return content

        except Exception as e:
            echo_warning(f"Failed to read file content for {file_path}: {e}")
            return None

    def _read_file_content(self, repo: git.Repo, file_path: str, change_type: str) -> str | None:
        """Helper method to read file content from either working directory or Git."""
        if self.staged:
            return self._read_staged_file_content(file_path)
        else:
            # For added files, read from the working directory if not staged
            if change_type == "added":
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
                return None
            return self._read_committed_file_content(repo, file_path)

    def _read_staged_file_content(self, file_path: str) -> str | None:
        """Read file content from working directory for staged files."""
        full_path = os.path.join(self.repo_path, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return None

    def _read_committed_file_content(self, repo: git.Repo, file_path: str) -> str | None:
        """Read file content from Git commit for committed files."""
        try:
            target_commit = repo.commit(self.target)
            file_content = target_commit.tree[file_path].data_stream.read()  # type: ignore
            return file_content.decode("utf-8", errors="replace")  # type: ignore
        except (KeyError, GitCommandError):
            echo_warning(f"File not found in target commit: {file_path}")
            return None
