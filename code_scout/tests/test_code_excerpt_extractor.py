from core.utils.code_excerpt_extractor import CodeExcerptExtractor


class TestCodeExcerptExtractor:
    """Test cases for the CodeExcerptExtractor utility."""

    def test_extract_with_context_single_line(self):
        """Test extracting context around a single line."""
        file_content = """def hello_world():
    print("Hello, World!")
    return "success"

def another_function():
    x = 1
    y = 2
    return x + y"""

        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content,
            line_number=2,  # print("Hello, World!")
            context_lines=1,
        )

        assert excerpt is not None
        assert excerpt.start_line == 1
        assert excerpt.end_line == 3
        assert excerpt.target_line == 2
        assert "def hello_world():" in excerpt.content
        assert 'print("Hello, World!")' in excerpt.content
        assert 'return "success"' in excerpt.content

    def test_extract_with_context_line_range(self):
        """Test extracting context around a line range."""
        file_content = """class MyClass:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self.value"""

        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content,
            line_range=(5, 6),  # increment method
            context_lines=2,
        )

        assert excerpt is not None
        assert excerpt.start_line == 3
        assert excerpt.end_line == 7
        assert excerpt.target_range == (5, 6)
        assert "self.value = 0" in excerpt.content
        assert "def increment(self):" in excerpt.content
        assert "return self.value" in excerpt.content

    def test_extract_with_context_file_boundaries(self):
        """Test that extraction respects file boundaries."""
        file_content = """line 1
line 2
line 3"""

        # Test beginning of file
        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content,
            line_number=1,
            context_lines=5,  # More than available
        )

        assert excerpt is not None
        assert excerpt.start_line == 1
        assert excerpt.end_line == 3

        # Test end of file
        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content,
            line_number=3,
            context_lines=5,  # More than available
        )

        assert excerpt is not None
        assert excerpt.start_line == 1
        assert excerpt.end_line == 3

    def test_extract_with_max_excerpt_lines(self):
        """Test that max_excerpt_lines is respected."""
        file_content = "\n".join([f"line {i}" for i in range(1, 21)])  # 20 lines

        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content,
            line_number=10,
            context_lines=10,
            max_excerpt_lines=5,
        )

        assert excerpt is not None
        # Should center around line 10 with max 5 lines
        lines_in_excerpt = len(excerpt.content.split("\n"))
        assert lines_in_excerpt <= 5

    def test_extract_invalid_inputs(self):
        """Test handling of invalid inputs."""
        file_content = "line 1\nline 2\nline 3"

        # No line number or range
        excerpt = CodeExcerptExtractor.extract_with_context(file_content=file_content)
        assert excerpt is None

        # Empty file content
        excerpt = CodeExcerptExtractor.extract_with_context(file_content="", line_number=1)
        assert excerpt is None

        # Line number out of range
        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=file_content, line_number=100
        )
        assert excerpt is None

    def test_is_binary_content(self):
        """Test binary content detection."""
        # Text content
        assert not CodeExcerptExtractor.is_binary_content("Hello, World!")
        assert not CodeExcerptExtractor.is_binary_content("def func():\n    pass")

        # Binary content (with null bytes)
        assert CodeExcerptExtractor.is_binary_content("Hello\x00World")

        # Content with low printable ratio
        non_printable = "".join([chr(i) for i in range(0, 32)] * 10)
        assert CodeExcerptExtractor.is_binary_content(non_printable)

    def test_is_file_too_large(self):
        """Test file size checking."""
        small_content = "Hello, World!"
        assert not CodeExcerptExtractor.is_file_too_large(small_content, max_size_kb=1)

        # Create content larger than 1KB
        large_content = "x" * 2000  # 2KB
        assert CodeExcerptExtractor.is_file_too_large(large_content, max_size_kb=1)

        # Empty content
        assert not CodeExcerptExtractor.is_file_too_large("", max_size_kb=1)
