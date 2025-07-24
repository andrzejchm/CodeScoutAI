import sys
from typing import List

import git

from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff

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

            diff_list.append(
                CodeDiff(
                    diff=diff_content,
                    file_path=file_path,
                    old_file_path=old_file_path,
                    change_type=change_type,
                )
            )

        return diff_list


if __name__ == "__main__":
    # Example usage for branch/commit diff
    repo_path = "/Users/andrzejchm/Developer/andrzejchm/CodeScoutAI"
    source_branch = "HEAD"
    target_branch = "HEAD~1"

    try:
        print("--- Diffing between branches/commits ---")
        diff_provider = GitDiffProvider(
            repo_path=repo_path, source=source_branch, target=target_branch
        )
        diffs = diff_provider.get_diff()

        print(f"Found {len(diffs)} changes:")
        for diff in diffs:
            print(f"\nFile: {diff.file_path}")
            if diff.old_file_path:
                print(f"Old File: {diff.old_file_path}")
            print(f"Change Type: {diff.change_type}")
            print(f"Diff Content: {len(diff.diff)} characters")
            if diff.diff:
                print("Content preview:")
                preview = (
                    diff.diff[:PREVIEW_LENGTH] + "..."
                    if len(diff.diff) > PREVIEW_LENGTH
                    else diff.diff
                )
                print(preview)
            else:
                print("No content changes (e.g., file move/rename)")
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
