from typing import List, Optional

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

HTTP_NOT_FOUND = 404
HTTP_FORBIDDEN = 403


class GitHubService:
    """
    Service class to encapsulate GitHub API interactions for a specific repository.
    """

    def __init__(self, github_token: str, repo_owner: str, repo_name: str) -> None:
        if not github_token:
            raise ValueError("GitHub token cannot be empty.")
        if not repo_owner:
            raise ValueError("Repository owner cannot be empty.")
        if not repo_name:
            raise ValueError("Repository name cannot be empty.")

        self.github_client = Github(github_token)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo: Repository = self._get_repository()

    def _get_repository(self) -> Repository:
        """
        Internal method to retrieve the GitHub repository during initialization.
        """
        try:
            user = self.github_client.get_user(self.repo_owner)
            repo = user.get_repo(self.repo_name)
            return repo
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                raise ValueError(
                    f"Repository '{self.repo_owner}/{self.repo_name}' not found."
                ) from e
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting repository: {e}") from e

    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Retrieves a specific pull request from the encapsulated repository.

        Args:
            pr_number: The number of the pull request.

        Returns:
            A PyGithub PullRequest object.

        Raises:
            ValueError: If the pull request is not found or an API error occurs.
        """
        try:
            pull = self.repo.get_pull(pr_number)
            return pull
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                raise ValueError(
                    f"Pull request #{pr_number} not found in '{self.repo.full_name}'."
                ) from e
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting pull request: {e}") from e

    def get_open_pull_requests(self) -> List[PullRequest]:
        """
        Retrieves all open pull requests for the encapsulated repository.

        Returns:
            A list of PyGithub PullRequest objects.

        Raises:
            ValueError: If an API error occurs.
        """
        try:
            return list(self.repo.get_pulls(state="open"))
        except GithubException as e:
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while listing pull requests: {e}"
            ) from e

    def get_pull_request_files(self, pull: PullRequest):
        """
        Retrieves the files changed in a pull request.

        Args:
            pull: The PyGithub PullRequest object.

        Returns:
            An iterable of PyGithub File objects.

        Raises:
            ValueError: If an API error occurs.
        """
        try:
            return pull.get_files()
        except GithubException as e:
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting PR files: {e}") from e

    def get_file_content(self, file_path: str, ref: str) -> Optional[str]:
        try:
            contents = self.repo.get_contents(file_path, ref=ref)
            if isinstance(contents, list):
                raise ValueError(f"Path '{file_path}' is a directory, not a file.")
            return contents.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                return (
                    None  # File not found at this ref, which is acceptable for some diff scenarios
                )
            elif e.status == HTTP_FORBIDDEN:
                raise ValueError(
                    (
                        f"Access to file '{file_path}' at ref '{ref}' is forbidden."
                        f"\nCheck your permissions and make sure your access token has 'Contents' "
                        f"permission with at least read-only access."
                    )
                ) from e
            raise ValueError(f"GitHub API error getting file content: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting file content: {e}") from e
