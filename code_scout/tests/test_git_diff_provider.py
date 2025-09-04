from unittest.mock import MagicMock, patch

import pytest
from git import Diff, DiffIndex, Repo
from git.objects.base import IndexObject
from git.objects.commit import Commit
from git.objects.tree import Tree

from core.diff_providers.git_diff_provider import GitDiffProvider
from core.models.code_diff import CodeDiff


# --- Fixtures for GitDiffProvider tests ---
@pytest.fixture
def mock_git_repo():
    with patch("git.Repo") as mock_repo_class:
        mock_repo = MagicMock(spec=Repo)
        mock_repo_class.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def mock_diff_item_modified():
    mock_diff = MagicMock(spec=Diff)
    mock_diff.a_path = "path/to/file.py"
    mock_diff.b_path = "path/to/file.py"
    mock_diff.diff = (
        b"--- a/path/to/file.py\n+++ b/path/to/file.py\n@@ -1,2 +1,3 @@\n-old line\n+new line\n+another new line\n"
    )
    mock_diff.change_type = "M"
    return mock_diff


@pytest.fixture
def mock_diff_item_added():
    mock_diff = MagicMock(spec=Diff)
    mock_diff.a_path = None
    mock_diff.b_path = "path/to/new_file.py"
    mock_diff.diff = b"--- /dev/null\n+++ b/path/to/new_file.py\n@@ -0,0 +1,2 @@\n+new file line 1\n+new file line 2\n"
    mock_diff.change_type = "A"
    return mock_diff


@pytest.fixture
def mock_diff_item_deleted():
    mock_diff = MagicMock(spec=Diff)
    mock_diff.a_path = "path/to/old_file.py"
    mock_diff.b_path = None
    mock_diff.diff = b"--- a/path/to/old_file.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-old file line 1\n-old file line 2\n"
    mock_diff.change_type = "D"
    return mock_diff


@pytest.fixture
def mock_diff_item_renamed():
    mock_diff = MagicMock(spec=Diff)
    mock_diff.a_path = "old/path/file.py"
    mock_diff.b_path = "new/path/file.py"
    mock_diff.diff = b"--- a/old/path/file.py\n+++ b/new/path/file.py\n@@ -1,1 +1,1 @@\n-content\n+content\n"
    mock_diff.change_type = "R"
    return mock_diff


@pytest.fixture
def mock_code_excerpt_extractor():
    with patch("core.utils.code_excerpt_extractor.CodeExcerptExtractor") as mock_extractor:
        mock_extractor.is_binary_content.return_value = False
        mock_extractor.is_file_too_large.return_value = False
        yield mock_extractor


# --- Tests for GitDiffProvider ---
class TestGitDiffProvider:
    REPO_PATH = "/tmp/test_repo"

    def test_init_validation(self):
        with pytest.raises(ValueError, match="Repository path cannot be empty."):
            GitDiffProvider(repo_path="")
        with pytest.raises(
            ValueError, match="Source and target branches cannot be the same when not reviewing staged files."
        ):
            GitDiffProvider(repo_path=self.REPO_PATH, source="main", target="main", staged=False)

    def test_get_diff_committed_modified_file(
        self, mock_git_repo, mock_diff_item_modified, mock_code_excerpt_extractor
    ):
        # Mock diff index
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_modified]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        # Mock file content reading
        mock_commit = MagicMock(spec=Commit)
        mock_git_repo.commit.return_value = mock_commit
        mock_tree = MagicMock(spec=Tree)
        mock_commit.tree = mock_tree
        mock_index_object = MagicMock(spec=IndexObject)
        mock_tree.__getitem__.return_value = mock_index_object
        mock_index_object.data_stream.read.return_value = b"old line\nnew line\nanother new line\n"

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert isinstance(code_diff, CodeDiff)
        assert code_diff.file_path == "path/to/file.py"
        assert code_diff.change_type == "modified"
        assert "new line" in code_diff.diff
        assert code_diff.current_file_content == "old line\nnew line\nanother new line\n"
        assert len(code_diff.hunks) == 1
        assert code_diff.parsed_diff.is_modified_file is True

    def test_get_diff_committed_added_file(self, mock_git_repo, mock_diff_item_added, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_added]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        mock_commit = MagicMock(spec=Commit)
        mock_git_repo.commit.return_value = mock_commit
        mock_tree = MagicMock(spec=Tree)
        mock_commit.tree = mock_tree
        mock_index_object = MagicMock(spec=IndexObject)
        mock_tree.__getitem__.return_value = mock_index_object
        mock_index_object.data_stream.read.return_value = b"new file line 1\nnew file line 2\n"

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "path/to/new_file.py"
        assert code_diff.change_type == "added"
        assert "new file line 1" in code_diff.diff
        assert code_diff.current_file_content == "new file line 1\nnew file line 2\n"
        assert len(code_diff.hunks) == 1
        assert code_diff.parsed_diff.is_added_file is True

    def test_get_diff_committed_deleted_file(self, mock_git_repo, mock_diff_item_deleted, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_deleted]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "path/to/old_file.py"
        assert code_diff.change_type == "deleted"
        assert "old file line 1" in code_diff.diff
        assert code_diff.current_file_content is None  # Deleted files should have None content
        assert len(code_diff.hunks) == 1
        assert code_diff.parsed_diff.is_removed_file is True

    def test_get_diff_committed_renamed_file(self, mock_git_repo, mock_diff_item_renamed, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_renamed]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        mock_commit = MagicMock(spec=Commit)
        mock_git_repo.commit.return_value = mock_commit
        mock_tree = MagicMock(spec=Tree)
        mock_commit.tree = mock_tree
        mock_index_object = MagicMock(spec=IndexObject)
        mock_tree.__getitem__.return_value = mock_index_object
        mock_index_object.data_stream.read.return_value = b"content\n"

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.file_path == "new/path/file.py"
        assert code_diff.old_file_path == "old/path/file.py"
        assert code_diff.change_type == "renamed"
        assert "content" in code_diff.diff
        assert code_diff.current_file_content == "content\n"
        assert len(code_diff.hunks) == 0  # Renamed files with 100% similarity often have no hunks
        assert code_diff.parsed_diff.is_renamed_file is True

    def test_get_diff_staged_modified_file(self, mock_git_repo, mock_diff_item_modified, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_modified]
        mock_git_repo.index.diff.return_value = mock_diff_index

        # Mock os.path.exists and open for staged file content
        with (
            patch("os.path.exists", return_value=True),
            patch(
                "builtins.open",
                MagicMock(return_value=MagicMock(read=lambda: "old line\nnew line\nanother new line\n")),
            ),
        ):
            provider = GitDiffProvider(repo_path=self.REPO_PATH, staged=True)
            diffs = provider.get_diff()

            assert len(diffs) == 1
            code_diff = diffs[0]
            assert code_diff.file_path == "path/to/file.py"
            assert code_diff.change_type == "modified"
            assert code_diff.current_file_content == "old line\nnew line\nanother new line\n"

    def test_get_diff_staged_added_file(self, mock_git_repo, mock_diff_item_added, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_added]
        mock_git_repo.index.diff.return_value = mock_diff_index

        with (
            patch("os.path.exists", return_value=True),
            patch(
                "builtins.open", MagicMock(return_value=MagicMock(read=lambda: "new file line 1\nnew file line 2\n"))
            ),
        ):
            provider = GitDiffProvider(repo_path=self.REPO_PATH, staged=True)
            diffs = provider.get_diff()

            assert len(diffs) == 1
            code_diff = diffs[0]
            assert code_diff.file_path == "path/to/new_file.py"
            assert code_diff.change_type == "added"
            assert code_diff.current_file_content == "new file line 1\nnew file line 2\n"

    def test_get_diff_staged_deleted_file(self, mock_git_repo, mock_diff_item_deleted, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_deleted]
        mock_git_repo.index.diff.return_value = mock_diff_index

        # For deleted files, os.path.exists should return False
        with patch("os.path.exists", return_value=False):
            provider = GitDiffProvider(repo_path=self.REPO_PATH, staged=True)
            diffs = provider.get_diff()

            assert len(diffs) == 1
            code_diff = diffs[0]
            assert code_diff.file_path == "path/to/old_file.py"
            assert code_diff.change_type == "deleted"
            assert code_diff.current_file_content is None

    def test_get_diff_binary_file(self, mock_git_repo, mock_diff_item_modified, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_modified]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        mock_commit = MagicMock(spec=Commit)
        mock_git_repo.commit.return_value = mock_commit
        mock_tree = MagicMock(spec=Tree)
        mock_commit.tree = mock_tree
        mock_index_object = MagicMock(spec=IndexObject)
        mock_tree.__getitem__.return_value = mock_index_object
        mock_index_object.data_stream.read.return_value = b"\x00\x01\x02\x03"  # Binary content

        mock_code_excerpt_extractor.is_binary_content.return_value = True

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.current_file_content is None  # Binary files should have None content

    def test_get_diff_large_file(self, mock_git_repo, mock_diff_item_modified, mock_code_excerpt_extractor):
        mock_diff_index = MagicMock(spec=DiffIndex)
        mock_diff_index.__iter__.return_value = [mock_diff_item_modified]
        mock_git_repo.commit.return_value.diff.return_value = mock_diff_index

        mock_commit = MagicMock(spec=Commit)
        mock_git_repo.commit.return_value = mock_commit
        mock_tree = MagicMock(spec=Tree)
        mock_commit.tree = mock_tree
        mock_index_object = MagicMock(spec=IndexObject)
        mock_tree.__getitem__.return_value = mock_index_object
        mock_index_object.data_stream.read.return_value = b"a" * (500 * 1024 + 1)  # Content > 500KB

        mock_code_excerpt_extractor.is_file_too_large.return_value = True

        provider = GitDiffProvider(repo_path=self.REPO_PATH, source="HEAD~1", target="HEAD")
        diffs = provider.get_diff()

        assert len(diffs) == 1
        code_diff = diffs[0]
        assert code_diff.current_file_content is None  # Large files should have None content
