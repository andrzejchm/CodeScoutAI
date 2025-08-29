from io import StringIO

from unidiff import PatchSet

from core.utils.diff_parser import parse_diff_string

# Test diff content from diff.txt (real-world example)
TEST_DIFF_CONTENT = """
diff --git a/code_scout/src/cli/cli_formatter.py b/code_scout/src/cli/cli_formatter_2.py
similarity index 100%
rename from code_scout/src/cli/cli_formatter.py
rename to code_scout/src/cli/cli_formatter_2.py
diff --git a/code_scout/src/core/utils/diff_parser.py b/code_scout/src/core/utils/diff_parser.py
index 083e795..48c2a53 100644
--- a/code_scout/src/core/utils/diff_parser.py
+++ b/code_scout/src/core/utils/diff_parser.py
@@ -7,7 +7,9 @@ from core.models.diff_hunk import DiffHunk, DiffLine
 from core.models.parsed_diff import ParsedDiff


-def parse_github_file(file_obj: Any) -> Optional[ParsedDiff]:
+def parse_github_file(
+    file_obj: Any,
+) -> Optional[ParsedDiff]:
     \"\"\"
     Parses a GitHub file object from PyGithub into a structured ParsedDiff object.

diff --git a/code_scout/tests/test_tool_integration.py b/code_scout/tests/test_tool_integration.py
index aa13227..6fc6fc6 100644
--- a/code_scout/tests/test_tool_integration.py
+++ b/code_scout/tests/test_tool_integration.py
@@ -79,6 +79,10 @@ diff --git a/tests/temp_test_file.py +++ b/tests/temp_test_file.py

 +   def calculate_product(a, b):
 +        return a * b
+diff --git a/code_scout/src/cli/cli_formatter.py b/code_scout/src/cli/cli_formatter_2.py
+similarity index 100%
+rename from code_scout/src/cli/cli_formatter.py
+rename to code_scout/src/cli/cli_formatter_2.py
 \"\"\"
     parsed_diff = parse_diff_string(
         diff_string=diff_content,
@@ -124,7 +128,8 @@ def test_basic_review_chain_with_tools(mock_llm, sample_code_diff):
 def test_basic_review_chain_without_tools(mock_llm_no_tools, sample_code_diff):
     \"\"\"Test BasicReviewChain without LangChain tools enabled (agent still used).\"\"\"
     mock_llm_no_tools.responses[0] = mock_llm_no_tools.responses[0].replace(
-        '"severity": "suggestion",', '"severity": "suggestion", "file_path": "tests/temp_test_file.py",'
+        '"severity": "suggestion",',
+        '"severity": "suggestion", "file_path": "tests/temp_test_file.py",',
     )
     config = ReviewConfig(
         langchain_tools=[],  # No tools provided

"""


def test_parse_diff_string_empty_diff():
    """
    Test parsing an empty diff string.
    """
    parsed_diff = parse_diff_string("", filename="test.txt")
    assert parsed_diff is None


def test_parse_diff_string_git_diff():
    """
    Test parsing a real-world GitHub diff with multiple files and hunks.
    """
    # The unidiff library's PatchSet can parse multiple files from a single diff string.
    # We need to iterate over the PatchSet to get individual PatchedFile objects.
    patch_set = PatchSet(StringIO(TEST_DIFF_CONTENT))
    parsed_files = [parse_diff_string(str(pf), filename=pf.path) for pf in patch_set]
    assert len(parsed_files) == 3

    # Test for the first file: renamed file
    file1 = parsed_files[0]
    assert file1 is not None
    assert file1.source_file == "code_scout/src/cli/cli_formatter.py"
    assert file1.target_file == "code_scout/src/cli/cli_formatter_2.py"
    assert file1.is_renamed_file is True
    assert file1.is_modified_file is True
    assert file1.is_added_file is False
    assert file1.is_removed_file is False
    assert len(file1.hunks) == 0  # Renamed files with 100% similarity often have no hunks

    # Test for the second file: modified file (diff_parser.py)
    file2 = parsed_files[1]
    assert file2 is not None
    assert file2.source_file == "code_scout/src/core/utils/diff_parser.py"
    assert file2.target_file == "code_scout/src/core/utils/diff_parser.py"
    assert file2.is_modified_file is True
    assert file2.is_added_file is False
    assert file2.is_removed_file is False
    assert file2.is_renamed_file is False
    assert len(file2.hunks) == 1
    hunk2 = file2.hunks[0]
    assert hunk2.source_start == 7
    assert hunk2.source_length == 7
    assert hunk2.target_start == 7
    assert hunk2.target_length == 9
    assert len(hunk2.lines) == 10
    assert hunk2.llm_repr == (
        "Hunk Header: from core.models.diff_hunk import DiffHunk, DiffLine\n"
        "```diff\n"
        "  7  7  from core.models.parsed_diff import ParsedDiff\n"
        "  8  8  \n"
        "  9  9  \n"
        "- 10    def parse_github_file(file_obj: Any) -> Optional[ParsedDiff]:\n"
        "+    10 def parse_github_file(\n"
        "+    11     file_obj: Any,\n"
        "+    12 ) -> Optional[ParsedDiff]:\n"
        '  11 13     """\n'
        "  12 14     Parses a GitHub file object from PyGithub into a structured "
        "ParsedDiff object.\n"
        "  13 15 \n"
        "\n"
        "```"
    )

    # Test for the third file: modified file (test_tool_integration.py)
    file3 = parsed_files[2]
    assert file3 is not None
    assert file3.source_file == "code_scout/tests/test_tool_integration.py"
    assert file3.target_file == "code_scout/tests/test_tool_integration.py"
    assert file3.is_modified_file is True
    assert file3.is_added_file is False
    assert file3.is_removed_file is False
    assert file3.is_renamed_file is False
    assert len(file3.hunks) == 2
    hunk3_1 = file3.hunks[0]
    hunk3_2 = file3.hunks[1]
    assert hunk3_1.source_start == 79
    assert hunk3_1.source_length == 6
    assert hunk3_1.target_start == 79
    assert hunk3_1.target_length == 10
    assert hunk3_1.llm_repr == (
        "Hunk Header: diff --git a/tests/temp_test_file.py +++ "
        "b/tests/temp_test_file.py\n"
        "```diff\n"
        "  79 79 \n"
        "  80 80 +   def calculate_product(a, b):\n"
        "  81 81 +        return a * b\n"
        "+    82 diff --git a/code_scout/src/cli/cli_formatter.py "
        "b/code_scout/src/cli/cli_formatter_2.py\n"
        "+    83 similarity index 100%\n"
        "+    84 rename from code_scout/src/cli/cli_formatter.py\n"
        "+    85 rename to code_scout/src/cli/cli_formatter_2.py\n"
        '  82 86 """\n'
        "  83 87     parsed_diff = parse_diff_string(\n"
        "  84 88         diff_string=diff_content,\n"
        "\n"
        "```"
    )
    assert hunk3_2.source_start == 124
    assert hunk3_2.source_length == 7
    assert hunk3_2.target_start == 128
    assert hunk3_2.target_length == 8
    assert hunk3_2.llm_repr == (
        "Hunk Header: def test_basic_review_chain_with_tools(mock_llm, "
        "sample_code_diff):\n"
        "```diff\n"
        "  124 128 def test_basic_review_chain_without_tools(mock_llm_no_tools, "
        "sample_code_diff):\n"
        '  125 129     """Test BasicReviewChain without LangChain tools enabled '
        '(agent still used)."""\n'
        "  126 130     mock_llm_no_tools.responses[0] = "
        "mock_llm_no_tools.responses[0].replace(\n"
        '- 127             \'"severity": "suggestion",\', \'"severity": "suggestion", '
        '"file_path": "tests/temp_test_file.py",\'\n'
        '+     131         \'"severity": "suggestion",\',\n'
        '+     132         \'"severity": "suggestion", "file_path": '
        '"tests/temp_test_file.py",\',\n'
        "  128 133     )\n"
        "  129 134     config = ReviewConfig(\n"
        "  130 135         langchain_tools=[],  # No tools provided\n"
        "  None None \n"
        "\n"
        "```"
    )
