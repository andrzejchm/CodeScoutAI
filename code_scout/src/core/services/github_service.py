from typing import List

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

HTTP_NOT_FOUND = 404


class GitHubService:
    """
    Service class to encapsulate GitHub API interactions.
    """

    def __init__(self, github_token: str) -> None:
        if not github_token:
            raise ValueError("GitHub token cannot be empty.")
        self.github_client = Github(github_token)

    def get_repository(self, repo_owner: str, repo_name: str) -> Repository:
        """
        Retrieves a GitHub repository.

        Args:
            repo_owner: The owner of the repository.
            repo_name: The name of the repository.

        Returns:
            A PyGithub Repository object.

        Raises:
            ValueError: If the repository is not found or an API error occurs.
        """
        try:
            user = self.github_client.get_user(repo_owner)
            repo = user.get_repo(repo_name)
            return repo
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                raise ValueError(f"Repository '{repo_owner}/{repo_name}' not found.") from e
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting repository: {e}") from e

    def get_pull_request(self, repo: Repository, pr_number: int) -> PullRequest:
        """
        Retrieves a specific pull request from a repository.

        Args:
            repo: The PyGithub Repository object.
            pr_number: The pull request number.

        Returns:
            A PyGithub PullRequest object.

        Raises:
            ValueError: If the pull request is not found or an API error occurs.
        """
        try:
            pull = repo.get_pull(pr_number)
            return pull
        except GithubException as e:
            if e.status == HTTP_NOT_FOUND:
                raise ValueError(
                    f"Pull request #{pr_number} not found in '{repo.full_name}'."
                ) from e
            raise ValueError(f"GitHub API error: {e.status} - {e.data}") from e
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while getting pull request: {e}") from e

    def get_open_pull_requests(self, repo: Repository) -> List[PullRequest]:
        """
        Retrieves all open pull requests for a given repository.

        Args:
            repo: The PyGithub Repository object.

        Returns:
            A list of PyGithub PullRequest objects.

        Raises:
            ValueError: If an API error occurs.
        """
        try:
            return list(repo.get_pulls(state="open"))
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
