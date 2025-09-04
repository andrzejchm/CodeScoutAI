from unittest.mock import MagicMock, patch

import pytest
from github.File import File
from github.PullRequest import PullRequest

from core.diff_providers.github_diff_provider import GitHubDiffProvider
from core.services.github_service import GitHubService


# --- Fixtures for GitHubDiffProvider tests ---
@pytest.fixture
def mock_github_service():
    with patch("core.services.github_service.GitHubService") as mock_service_class:
        mock_service = MagicMock(spec=GitHubService)
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_github_pull_request():
    mock_pr = MagicMock(spec=PullRequest)
    mock_pr.head.sha = "abcdef12345"
    return mock_pr


@pytest.fixture
def mock_github_file_modified():
    mock_file = MagicMock(spec=File)
    mock_file.filename = "src/main.py"
    mock_file.patch = "--- a/src/main.py\n+++ b/src/main.py\n@@ -1,2 +1,3 @@\n-old\n+new\n+another\n"
    mock_file.status = "modified"
    mock_file.additions = 2
    mock_file.deletions = 1
    mock_file.changes = 3
    return mock_file


@pytest.fixture
def mock_github_file_added():
    mock_file = MagicMock(spec=File)
    mock_file.filename = "src/new_file.py"
    mock_file.patch = "--- /dev/null\n+++ b/src/new_file.py\n@@ -0,0 +1,1 @@\n+added content\n"
    mock_file.status = "added"
    mock_file.additions = 1
    mock_file.deletions = 0
    mock_file.changes = 1
    return mock_file


@pytest.fixture
def mock_github_file_deleted():
    mock_file = MagicMock(spec=File)
    mock_file.filename = "src/old_file.py"
    mock_file.patch = "--- a/src/old_file.py\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-deleted content\n"
    mock_file.status = "removed"
    mock_file.additions = 0
    mock_file.deletions = 1
    mock_file.changes = 1
    return mock_file


@pytest.fixture
def mock_github_file_renamed():
    mock_file = MagicMock(spec=File)
    mock_file.filename = "src/renamed_file_new.py"
    mock_file.previous_filename = "src/renamed_file_old.py"
    mock_file.patch = (
        "--- a/src/renamed_file_old.py\n+++ b/src/renamed_file_new.py\n@@ -1,1 +1,1 @@\n-content\n+content\n"
    )
    mock_file.status = "renamed"
    mock_file.additions = 0
    mock_file.deletions = 0
    mock_file.changes = 0
    return mock_file


# --- Tests for GitHubDiffProvider ---
class TestGitHubDiffProvider:
    OWNER = "test_owner"
    REPO = "test_repo"
    PR_NUMBER = 123
    TOKEN = "test_token"

    def test_init_validation(self):
        with pytest.raises(ValueError, match="Repository owner cannot be empty."):
            GitHubDiffProvider(repo_owner="", repo_name=self.REPO, pr_number=self.PR_NUMBER, github_token=self.TOKEN)
        with pytest.raises(ValueError, match="Pull request number must be a positive integer."):
            GitHubDiffProvider(repo_owner=self.OWNER, repo_name=self.REPO, pr_number=0, github_token=self.TOKEN)
        with pytest.raises(ValueError, match="GitHub token cannot be empty."):
            GitHubDiffProvider(repo_owner=self.OWNER, repo_name=self.REPO, pr_number=self.PR_NUMBER, github_token="")

    def test_get_diff_modified_file(self, mock_github_service, mock_github_pull_request, mock_github_file_modified):
        mock_github_service.get_pull_request.return_value = mock_github_pull_request
        mock_github_service.get_pull_request_files.return_value = [mock_github_file_modified]
        mock_github_service.get_file_content.return_value = "old\nnew\nanother\n"

        provider = GitHubDiffProvider(self.OWNER, self.REPO, self.PR_NUMBER, self.TOKEN)
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "src/main.py"
        assert code_diff.change_type == "modified"
        assert "new" in code_diff.diff
        assert code_diff.current_file_content == "old\nnew\nanother\n"
        assert code_diff.parsed_diff.is_modified_file is True

    def test_get_diff_added_file(self, mock_github_service, mock_github_pull_request, mock_github_file_added):
        mock_github_service.get_pull_request.return_value = mock_github_pull_request
        mock_github_service.get_pull_request_files.return_value = [mock_github_file_added]
        mock_github_service.get_file_content.return_value = "added content\n"

        provider = GitHubDiffProvider(self.OWNER, self.REPO, self.PR_NUMBER, self.TOKEN)
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "src/new_file.py"
        assert code_diff.change_type == "added"
        assert "added content" in code_diff.diff
        assert code_diff.current_file_content == "added content\n"
        assert code_diff.parsed_diff.is_added_file is True

    def test_get_diff_deleted_file(self, mock_github_service, mock_github_pull_request, mock_github_file_deleted):
        mock_github_service.get_pull_request.return_value = mock_github_pull_request
        mock_github_service.get_pull_request_files.return_value = [mock_github_file_deleted]
        mock_github_service.get_file_content.return_value = None  # Content for deleted files is None

        provider = GitHubDiffProvider(self.OWNER, self.REPO, self.PR_NUMBER, self.TOKEN)
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "src/old_file.py"
        assert code_diff.change_type == "deleted"
        assert "deleted content" in code_diff.diff
        assert code_diff.current_file_content is None
        assert code_diff.parsed_diff.is_removed_file is True

    def test_get_diff_renamed_file(self, mock_github_service, mock_github_pull_request, mock_github_file_renamed):
        mock_github_service.get_pull_request.return_value = mock_github_pull_request
        mock_github_service.get_pull_request_files.return_value = [mock_github_file_renamed]
        mock_github_service.get_file_content.return_value = "content\n"

        provider = GitHubDiffProvider(self.OWNER, self.REPO, self.PR_NUMBER, self.TOKEN)
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "src/renamed_file_new.py"
        assert code_diff.old_file_path == "src/renamed_file_old.py"
        assert code_diff.change_type == "renamed"
        assert "content" in code_diff.diff
        assert code_diff.current_file_content == "content\n"
        assert code_diff.parsed_diff.is_renamed_file is True

    @patch("core.utils.diff_parser.parse_github_file", return_value=None)
    def test_get_diff_skips_unparseable_file(
        self, mock_parse_github_file, mock_github_service, mock_github_pull_request, mock_github_file_modified
    ):
        mock_github_service.get_pull_request.return_value = mock_github_pull_request
        mock_github_service.get_pull_request_files.return_value = [mock_github_file_modified]

        provider = GitHubDiffProvider(self.OWNER, self.REPO, self.PR_NUMBER, self.TOKEN)
        diffs = provider.get_diff()

        assert len(diffs) == 0
        mock_parse_github_file.assert_called_once()
