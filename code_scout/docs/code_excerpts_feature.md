# Code Excerpts Feature

This document describes the new code excerpt functionality that shows code review findings together with the actual code context.

## Overview

The code excerpt feature enhances the CLI output by displaying the actual source code around each finding, providing better context for developers to understand and address the issues.

## How It Works

### Architecture

1. **Enhanced CodeDiff Model**: The [`CodeDiff`](../src/core/models/code_diff.py) model now includes a `current_file_content` field that stores the full file content.

2. **Enhanced Diff Providers**:
   - [`GitHubDiffProvider`](../src/core/diff_providers/github_diff_provider.py): Fetches file content via GitHub API
   - [`GitDiffProvider`](../src/core/diff_providers/git_diff_provider.py): Reads file content from local filesystem

3. **Code Excerpt Extractor**: The [`CodeExcerptExtractor`](../src/core/utils/code_excerpt_extractor.py) utility extracts code snippets with configurable context lines.

4. **Enhanced ReviewFinding**: The [`ReviewFinding`](../src/core/models/review_finding.py) model includes new fields for code excerpts.

5. **Enhanced CLI Formatter**: The [`CliFormatter`](../src/cli/cli_formatter.py) displays code excerpts with syntax highlighting and line numbers.

### Example Output

Before (without code excerpts):

```
Finding 1:
  File: src/example.py:15
  Severity: Major
  Category: Security
  Message: Potential SQL injection vulnerability
  Suggestion: Use parameterized queries
```

After (with code excerpts):

```
Finding 1:
  File: src/example.py:15
  Severity: Major
  Category: Security
  Message: Potential SQL injection vulnerability
  Suggestion: Use parameterized queries

  Code Context:
  ┌─────────────────────────────────────────
  │  12 | def get_user(user_id):
  │  13 |     connection = get_db_connection()
  │  14 |     cursor = connection.cursor()
  │ >15 |     query = f"SELECT * FROM users WHERE id = {user_id}"
  │  16 |     cursor.execute(query)
  │  17 |     return cursor.fetchone()
  │  18 | 
  └─────────────────────────────────────────
```

## Configuration

The feature can be configured via the [`ReviewConfig`](../src/core/models/review_config.py) model:

```python
class ReviewConfig(BaseModel):
    # Code Excerpt Configuration
    show_code_excerpts: bool = True          # Enable/disable code excerpts
    context_lines_before: int = 3            # Lines to show before the finding
    context_lines_after: int = 3             # Lines to show after the finding
    max_excerpt_lines: int = 20              # Maximum total lines in excerpt
    max_file_size_kb: int = 500              # Skip files larger than this
```

## Features

### Smart Context Extraction

- Automatically extracts 3 lines before and after the finding (configurable)
- Handles file boundaries gracefully
- Limits excerpt size to prevent overwhelming output

### Binary File Detection

- Automatically skips binary files
- Detects files with null bytes or low printable character ratio

### Large File Handling

- Skips files larger than 500KB by default (configurable)
- Prevents memory issues with very large files

### Error Handling

- Graceful degradation when file content is unavailable
- Continues to show findings even if excerpts can't be extracted
- Logs debug information for troubleshooting

### Line Highlighting

- Highlights the specific line(s) mentioned in the finding
- Uses `>` prefix and bold styling for target lines
- Shows line numbers with proper alignment

## Usage

### GitHub PR Review

```bash
# The feature works automatically with GitHub PR reviews
codescout github review-pr --repo-owner myorg --repo-name myproject --pr-number 123
```

### Local Git Review

```bash
# The feature works automatically with local Git reviews
codescout git review --repo-path /path/to/repo --source main --target feature-branch
```

### Staged Files Review

```bash
# The feature works with staged files
codescout git review --repo-path /path/to/repo --staged
```

## Implementation Details

### File Content Fetching

**GitHub Provider**:

- Uses GitHub API `repo.get_contents(file_path, ref=commit_sha)`
- Decodes base64 content from GitHub API
- Handles API rate limits and errors gracefully

**Git Provider**:

- For staged files: Reads from working directory
- For committed files: Reads from Git object database
- Uses GitPython for efficient file access

### Excerpt Extraction Algorithm

1. Parse file content into lines
2. Determine target line(s) from finding
3. Calculate excerpt boundaries with context
4. Respect file boundaries and size limits
5. Format with line numbers and highlighting

### Performance Considerations

- File content is cached during a single review session
- Binary files are detected early to avoid processing
- Large files are skipped to prevent memory issues
- Excerpt extraction is lazy (only when needed)

## Testing

The feature includes comprehensive tests in [`tests/test_code_excerpt_extractor.py`](../tests/test_code_excerpt_extractor.py):

- Context extraction around single lines and ranges
- File boundary handling
- Size limit enforcement
- Binary file detection
- Error handling for invalid inputs

Run tests with:

```bash
task test
```

## Troubleshooting

### No Code Excerpts Shown

1. **Check configuration**: Ensure `show_code_excerpts: true` in ReviewConfig
2. **File access**: Verify the tool can access the source files
3. **File size**: Check if files exceed `max_file_size_kb` limit
4. **Binary files**: Binary files are automatically skipped

### Incomplete Excerpts

1. **Context lines**: Adjust `context_lines_before` and `context_lines_after`
2. **Excerpt limit**: Increase `max_excerpt_lines` if needed
3. **File boundaries**: Excerpts are limited by actual file content

### Performance Issues

1. **Large files**: Reduce `max_file_size_kb` to skip large files
2. **Context size**: Reduce context lines for faster processing
3. **Binary detection**: Ensure binary files are being detected and skipped

## Future Enhancements

Potential improvements for future versions:

1. **Syntax Highlighting**: Add language-specific syntax highlighting
2. **Diff Integration**: Show both old and new code in excerpts
3. **Smart Context**: Expand context to include full functions/classes
4. **Caching**: Persistent caching across review sessions
5. **Configuration UI**: Web interface for configuration management
