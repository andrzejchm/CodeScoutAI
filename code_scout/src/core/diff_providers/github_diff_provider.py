from typing import List, Optional

from core.interfaces.diff_provider import DiffProvider
from core.models.code_diff import CodeDiff
from core.services.github_service import GitHubService


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
            change_type = self._map_github_status_to_change_type(file_obj.status)
            old_file_path: Optional[str] = None

            if file_obj.status == "renamed":
                old_file_path = file_obj.previous_filename

            # Fetch current file content for excerpt extraction
            current_file_content = self.github_service.get_file_content(
                file_obj.filename, pull.head.sha
            )

            code_diffs.append(
                CodeDiff(
                    diff=file_obj.patch or "",  # patch contains the unified diff
                    file_path=file_obj.filename,
                    old_file_path=old_file_path,
                    change_type=change_type,
                    current_file_content=current_file_content,
                )
            )
        return code_diffs

    def _map_github_status_to_change_type(self, status: str) -> str:
        status_map = {
            "added": "added",
            "removed": "deleted",
            "modified": "modified",
            "renamed": "renamed",
        }
        return status_map.get(status, "unknown")
