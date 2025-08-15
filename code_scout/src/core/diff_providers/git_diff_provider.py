import os
from typing import List, Optional

import git
from git.exc import GitCommandError

from cli.cli_utils import echo_debug, echo_warning
from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff
from core.utils.code_excerpt_extractor import CodeExcerptExtractor

PREVIEW_LENGTH = 200


class GitDiffProvider(DiffProvider):
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
            raise ValueError(
                "Source and target branches cannot be the same when not reviewing staged files."
            )
        if not repo_path:
            raise ValueError("Repository path cannot be empty.")

    def get_diff(self) -> List[CodeDiff]:
        repo = git.Repo(path=self.repo_path)

        if self.staged:
            # Get diff of staged files (index vs HEAD)
            # repo.index.diff(None) compares the index (staged changes) with the working tree.
            # To compare staged changes against the last commit (HEAD), use
            # repo.head.commit.diff(None) or repo.index.diff("HEAD")
            diff = repo.index.diff("HEAD", create_patch=True)
        else:
            # Get diff between source and target commits
            diff = repo.commit(self.source).diff(self.target, create_patch=True)

        diff_list = []
        for diff_item in diff:
            # Extract diff content - GitPython requires create_patch=True for patch content
            diff_content = ""
            if hasattr(diff_item, "diff") and diff_item.diff:
                if isinstance(diff_item.diff, bytes):
                    diff_content = diff_item.diff.decode("utf-8", errors="replace")
                else:
                    diff_content = str(diff_item.diff)

            # Determine file path (prefer b_path for new files, a_path for deleted files)
            file_path = diff_item.b_path or diff_item.a_path or ""
            old_file_path = diff_item.a_path if diff_item.renamed_file else None

            # Determine change type based on GitPython's diff item properties
            change_type = "modified"
            if diff_item.new_file:
                change_type = "added"
            elif diff_item.deleted_file:
                change_type = "deleted"
            elif diff_item.renamed_file:
                change_type = "renamed"
            elif diff_item.change_type:
                change_type = diff_item.change_type

            # Get current file content for excerpt extraction
            current_file_content = self._get_file_content(repo, file_path, change_type)

            diff_list.append(
                CodeDiff(
                    diff=diff_content,
                    file_path=file_path,
                    old_file_path=old_file_path,
                    change_type=change_type,
                    current_file_content=current_file_content,
                )
            )

        return diff_list

    def _get_file_content(self, repo: git.Repo, file_path: str, change_type: str) -> Optional[str]:
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

            content = self._read_file_content(repo, file_path)
            if content is None:
                return None

            # Check if content is binary or too large
            if CodeExcerptExtractor.is_binary_content(content):
                echo_debug(f"Skipping binary file: {file_path}")
                return None

            if CodeExcerptExtractor.is_file_too_large(content):
                echo_debug(f"Skipping large file: {file_path}")
                return None

            return content

        except Exception as e:
            echo_warning(f"Failed to read file content for {file_path}: {e}")
            return None

    def _read_file_content(self, repo: git.Repo, file_path: str) -> Optional[str]:
        """Helper method to read file content from either working directory or Git."""
        if self.staged:
            return self._read_staged_file_content(file_path)
        else:
            return self._read_committed_file_content(repo, file_path)

    def _read_staged_file_content(self, file_path: str) -> Optional[str]:
        """Read file content from working directory for staged files."""
        full_path = os.path.join(self.repo_path, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return None

    def _read_committed_file_content(self, repo: git.Repo, file_path: str) -> Optional[str]:
        """Read file content from Git commit for committed files."""
        try:
            target_commit = repo.commit(self.target)
            file_content = target_commit.tree[file_path].data_stream.read()
            return file_content.decode("utf-8", errors="replace")
        except (KeyError, GitCommandError):
            echo_warning(f"File not found in target commit: {file_path}")
            return None
