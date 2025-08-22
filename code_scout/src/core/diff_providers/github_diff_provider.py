from typing import List

from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff
from core.models.parsed_diff import ParsedDiff
from core.services.github_service import GitHubService
from core.utils.diff_parser import parse_github_file


class GitHubDiffProvider(DiffProvider):
    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        github_token: str,
    ) -> None:
        if not repo_owner:
            raise ValueError("Repository owner cannot be empty.")
        if not repo_name:
            raise ValueError("Repository name cannot be empty.")
        if not pr_number or pr_number <= 0:
            raise ValueError("Pull request number must be a positive integer.")
        if not github_token:
            raise ValueError("GitHub token cannot be empty.")

        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.pr_number = pr_number
        self.github_service = GitHubService(github_token, repo_owner, repo_name)

    def get_diff(self) -> List[CodeDiff]:
        pull = self.github_service.get_pull_request(self.pr_number)

        code_diffs: List[CodeDiff] = []
        for file_obj in self.github_service.get_pull_request_files(pull):
            parsed_diff = parse_github_file(file_obj)

            if parsed_diff:
                file_path = parsed_diff.target_file
                old_file_path = parsed_diff.source_file if parsed_diff.is_renamed_file else None
                change_type = self._map_parsed_diff_to_change_type(parsed_diff)

                # Fetch current file content for excerpt extraction
                current_file_content = self.github_service.get_file_content(file_path, pull.head.sha)

                code_diffs.append(
                    CodeDiff(
                        diff=file_obj.patch or "",
                        hunks=parsed_diff.hunks,
                        parsed_diff=parsed_diff,
                        file_path=file_path,
                        old_file_path=old_file_path,
                        change_type=change_type,
                        current_file_content=current_file_content,
                    )
                )
        return code_diffs

    def _map_parsed_diff_to_change_type(self, parsed_diff: ParsedDiff) -> str:
        if parsed_diff.is_added_file:
            return "added"
        if parsed_diff.is_removed_file:
            return "deleted"
        if parsed_diff.is_modified_file:
            return "modified"
        if parsed_diff.is_renamed_file:
            return "renamed"
        return "unknown"
