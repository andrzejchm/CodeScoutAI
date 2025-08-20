import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from tree_sitter import Language, Node, Parser

from .models import CodeSymbol


class CodeIndexExtractor:
    """
    Extracts code symbols from source files using Tree-sitter parsers.

    This class provides language-agnostic parsing through Tree-sitter with
    lazy-loaded language grammars for performance. It extracts symbols like
    functions, classes, methods, and variables with their metadata.
    """

    def __init__(self):
        """Initialize the extractor with lazy-loaded parsers."""
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}

        # Comprehensive file extension to language mapping
        self.extension_map = {
            # Python
            ".py": "python",
            ".pyw": "python",
            ".pyi": "python",
            ".pyx": "python",
            # JavaScript/TypeScript
            ".js": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".mts": "typescript",
            ".cts": "typescript",
            # Java/JVM Languages
            ".java": "java",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".scala": "scala",
            ".sc": "scala",
            ".groovy": "groovy",
            ".gradle": "groovy",
            ".clj": "clojure",
            ".cljs": "clojure",
            ".cljc": "clojure",
            # C/C++
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".c++": "cpp",
            ".hpp": "cpp",
            ".hxx": "cpp",
            ".hh": "cpp",
            ".h++": "cpp",
            # C#/.NET
            ".cs": "c_sharp",
            ".csx": "c_sharp",
            ".vb": "vb_net",
            ".fs": "f_sharp",
            ".fsx": "f_sharp",
            ".fsi": "f_sharp",
            # Go
            ".go": "go",
            # Rust
            ".rs": "rust",
            # Ruby
            ".rb": "ruby",
            ".rbw": "ruby",
            ".rake": "ruby",
            ".gemspec": "ruby",
            # PHP
            ".php": "php",
            ".php3": "php",
            ".php4": "php",
            ".php5": "php",
            ".phtml": "php",
            # Swift
            ".swift": "swift",
            # Objective-C
            ".m": "objc",
            ".mm": "objcpp",
            # Shell Scripts
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "fish",
            ".ksh": "bash",
            ".csh": "bash",
            ".tcsh": "bash",
            # Web Technologies
            ".html": "html",
            ".htm": "html",
            ".xhtml": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".styl": "stylus",
            # Data/Config
            ".json": "json",
            ".jsonc": "json",
            ".json5": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
            ".xsl": "xml",
            ".xslt": "xml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            # Database
            ".sql": "sql",
            ".mysql": "sql",
            ".pgsql": "sql",
            ".sqlite": "sql",
            # R
            ".r": "r",
            ".R": "r",
            ".rmd": "r",
            ".Rmd": "r",
            # MATLAB/Octave
            ".m": "matlab",
            ".mat": "matlab",
            # Lua
            ".lua": "lua",
            # Perl
            ".pl": "perl",
            ".pm": "perl",
            ".pod": "perl",
            ".t": "perl",
            # Vim
            ".vim": "vim",
            ".vimrc": "vim",
            # Haskell
            ".hs": "haskell",
            ".lhs": "haskell",
            # Erlang/Elixir
            ".erl": "erlang",
            ".hrl": "erlang",
            ".ex": "elixir",
            ".exs": "elixir",
            # OCaml
            ".ml": "ocaml",
            ".mli": "ocaml",
            # Dart
            ".dart": "dart",
            # Julia
            ".jl": "julia",
            # Zig
            ".zig": "zig",
            # Nim
            ".nim": "nim",
            ".nims": "nim",
            # Crystal
            ".cr": "crystal",
            # D
            ".d": "d",
            # Pascal
            ".pas": "pascal",
            ".pp": "pascal",
            # Fortran
            ".f": "fortran",
            ".f90": "fortran",
            ".f95": "fortran",
            ".f03": "fortran",
            ".f08": "fortran",
            # COBOL
            ".cob": "cobol",
            ".cbl": "cobol",
            # Assembly
            ".asm": "assembly",
            ".s": "assembly",
            ".S": "assembly",
            # Lisp
            ".lisp": "lisp",
            ".lsp": "lisp",
            ".cl": "lisp",
            # Scheme
            ".scm": "scheme",
            ".ss": "scheme",
            # Prolog
            ".pl": "prolog",
            ".pro": "prolog",
            # Dockerfile
            ".dockerfile": "dockerfile",
            # Makefile
            ".mk": "make",
            # CMake
            ".cmake": "cmake",
            # Terraform
            ".tf": "terraform",
            ".tfvars": "terraform",
            # GraphQL
            ".graphql": "graphql",
            ".gql": "graphql",
            # Protocol Buffers
            ".proto": "protobuf",
            # Thrift
            ".thrift": "thrift",
            # ANTLR
            ".g4": "antlr",
            # Regex
            ".regex": "regex",
            # Markdown
            ".md": "markdown",
            ".markdown": "markdown",
            ".mdown": "markdown",
            ".mkd": "markdown",
            # LaTeX
            ".tex": "latex",
            ".sty": "latex",
            ".cls": "latex",
            # Org Mode
            ".org": "org",
            # reStructuredText
            ".rst": "rst",
            ".rest": "rst",
            # AsciiDoc
            ".adoc": "asciidoc",
            ".asciidoc": "asciidoc",
        }

    def extract_symbols(self, file_path: str, content: str) -> List[CodeSymbol]:
        """
        Extract symbols from source code content.

        Args:
            file_path: Path to the source file
            content: Source code content

        Returns:
            List of CodeSymbol objects extracted from the content
        """
        try:
            # Detect language from file extension
            language = self._detect_language(file_path)
            if not language:
                return []

            # Get parser for the language
            parser = self._get_parser(language)
            if not parser:
                return []

            # Calculate file hash for change detection
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Parse content and extract symbols
            return self._parse_and_extract(content, parser, file_path, language, file_hash)

        except Exception as e:
            # Log error but don't fail the entire operation
            print(f"Error extracting symbols from {file_path}: {e}")
            return []

    def _detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the source file

        Returns:
            Language identifier or None if not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Handle special cases for files without extensions
        filename_lower = path.name.lower()
        if filename_lower in ["dockerfile", "makefile", "rakefile", "gemfile", "vagrantfile", "cmakelists.txt"]:
            special_map = {
                "dockerfile": "dockerfile",
                "makefile": "make",
                "rakefile": "ruby",
                "gemfile": "ruby",
                "vagrantfile": "ruby",
                "cmakelists.txt": "cmake",
            }
            return special_map.get(filename_lower)

        return self.extension_map.get(extension)

    def _get_parser(self, language: str) -> Optional[Parser]:
        """
        Get or create a Tree-sitter parser for the specified language.

        Args:
            language: Language identifier

        Returns:
            Parser instance or None if language not supported
        """
        if language in self.parsers:
            return self.parsers[language]

        try:
            # Try to load the language library
            lang_lib = self._load_language_library(language)
            if not lang_lib:
                return None

            # Create parser and set language
            parser = Parser()
            parser.set_language(lang_lib)

            # Cache the parser and language
            self.parsers[language] = parser
            self.languages[language] = lang_lib

            return parser

        except Exception as e:
            print(f"Failed to load parser for {language}: {e}")
            return None

    def _load_language_library(self, language: str) -> Optional[Language]:
        """
        Load Tree-sitter language library.

        For now, this assumes pre-built language libraries are available.
        In a production setup, this would handle building grammars from source.

        Args:
            language: Language identifier

        Returns:
            Language instance or None if not available
        """
        try:
            # Try to import the language directly from tree_sitter_languages if available
            # This is a common package that provides pre-built languages
            try:
                import tree_sitter_languages  # type: ignore

                return tree_sitter_languages.get_language(language)
            except ImportError:
                pass

            # Fallback: try to load from build directory
            build_path = Path("build") / f"tree-sitter-{language}.so"
            if build_path.exists():
                return Language(str(build_path), language)

            # Another common location
            build_path = Path("build") / "my-languages.so"
            if build_path.exists():
                return Language(str(build_path), language)

            return None

        except Exception as e:
            print(f"Failed to load language library for {language}: {e}")
            return None

    def _parse_and_extract(
        self, content: str, parser: Parser, file_path: str, language: str, file_hash: str
    ) -> List[CodeSymbol]:
        """
        Parse content and extract symbols from the AST.

        Args:
            content: Source code content
            parser: Tree-sitter parser
            file_path: Path to the source file
            language: Language identifier
            file_hash: Hash of the file content

        Returns:
            List of extracted CodeSymbol objects
        """
        try:
            # Parse the content
            tree = parser.parse(content.encode("utf-8"))
            root_node = tree.root_node

            symbols = []
            source_bytes = content.encode("utf-8")

            # Extract symbols based on language
            if language == "python":
                symbols.extend(self._extract_python_symbols(root_node, source_bytes, file_path, file_hash))
            elif language in ["javascript", "typescript"]:
                symbols.extend(self._extract_js_symbols(root_node, source_bytes, file_path, file_hash))
            else:
                # Generic extraction for other languages
                symbols.extend(self._extract_generic_symbols(root_node, source_bytes, file_path, language, file_hash))

            return symbols

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def _extract_python_symbols(self, node: Node, source: bytes, file_path: str, file_hash: str) -> List[CodeSymbol]:
        """Extract symbols from Python AST."""
        symbols = []

        def traverse(node: Node, parent_symbol: Optional[str] = None):
            # Function definitions
            if node.type == "function_definition":
                symbol = self._create_python_function_symbol(node, source, file_path, file_hash, parent_symbol)
                if symbol:
                    symbols.append(symbol)
                    # Recursively process nested functions
                    for child in node.children:
                        traverse(child, symbol.name)

            # Class definitions
            elif node.type == "class_definition":
                symbol = self._create_python_class_symbol(node, source, file_path, file_hash, parent_symbol)
                if symbol:
                    symbols.append(symbol)
                    # Process class methods
                    for child in node.children:
                        traverse(child, symbol.name)

            # Import statements
            elif node.type in ["import_statement", "import_from_statement"]:
                import_symbols = self._create_python_import_symbols(node, source, file_path, file_hash)
                symbols.extend(import_symbols)

            # Variable assignments (top-level only)
            elif node.type == "assignment" and parent_symbol is None:
                var_symbols = self._create_python_variable_symbols(node, source, file_path, file_hash)
                symbols.extend(var_symbols)

            else:
                # Continue traversing for other node types
                for child in node.children:
                    traverse(child, parent_symbol)

        traverse(node)
        return symbols

    def _create_python_function_symbol(
        self, node: Node, source: bytes, file_path: str, file_hash: str, parent_symbol: Optional[str]
    ) -> Optional[CodeSymbol]:
        """Create a CodeSymbol for a Python function."""
        try:
            # Find function name
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break

            if not name_node:
                return None

            name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")

            # Get function signature
            signature = source[node.start_byte : node.end_byte].decode("utf-8").split("\n")[0].strip()

            # Extract docstring
            docstring = self._extract_python_docstring(node, source)

            # Determine scope
            scope = "private" if name.startswith("_") else "public"

            # Extract parameters
            parameters = self._extract_python_parameters(node, source)

            return CodeSymbol(
                name=name,
                symbol_type="method" if parent_symbol else "function",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language="python",
                signature=signature,
                docstring=docstring,
                parent_symbol=parent_symbol,
                scope=scope,
                parameters=parameters,
                file_hash=file_hash,
            )

        except Exception as e:
            print(f"Error creating function symbol: {e}")
            return None

    def _create_python_class_symbol(
        self, node: Node, source: bytes, file_path: str, file_hash: str, parent_symbol: Optional[str]
    ) -> Optional[CodeSymbol]:
        """Create a CodeSymbol for a Python class."""
        try:
            # Find class name
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break

            if not name_node:
                return None

            name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")

            # Get class signature (class definition line)
            signature = source[node.start_byte : node.end_byte].decode("utf-8").split("\n")[0].strip()

            # Extract docstring
            docstring = self._extract_python_docstring(node, source)

            return CodeSymbol(
                name=name,
                symbol_type="class",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language="python",
                signature=signature,
                docstring=docstring,
                parent_symbol=parent_symbol,
                scope="public",
                file_hash=file_hash,
            )

        except Exception as e:
            print(f"Error creating class symbol: {e}")
            return None

    def _create_python_import_symbols(
        self, node: Node, source: bytes, file_path: str, file_hash: str
    ) -> List[CodeSymbol]:
        """Create CodeSymbol objects for Python imports."""
        symbols = []
        try:
            import_text = source[node.start_byte : node.end_byte].decode("utf-8").strip()

            # Create a single import symbol for the entire import statement
            symbol = CodeSymbol(
                name=import_text,
                symbol_type="import",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language="python",
                signature=import_text,
                scope="public",
                file_hash=file_hash,
            )
            symbols.append(symbol)

        except Exception as e:
            print(f"Error creating import symbol: {e}")

        return symbols

    def _create_python_variable_symbols(
        self, node: Node, source: bytes, file_path: str, file_hash: str
    ) -> List[CodeSymbol]:
        """Create CodeSymbol objects for Python variable assignments."""
        symbols = []
        try:
            # Extract variable names from assignment
            for child in node.children:
                if child.type == "identifier":
                    name = source[child.start_byte : child.end_byte].decode("utf-8")

                    # Skip private variables (starting with _) for top-level variables
                    if name.startswith("_"):
                        continue

                    assignment_text = source[node.start_byte : node.end_byte].decode("utf-8").strip()

                    symbol = CodeSymbol(
                        name=name,
                        symbol_type="variable",
                        file_path=file_path,
                        line_number=node.start_point[0] + 1,
                        column_number=node.start_point[1],
                        end_line_number=node.end_point[0] + 1,
                        end_column_number=node.end_point[1],
                        language="python",
                        signature=assignment_text,
                        scope="public",
                        file_hash=file_hash,
                    )
                    symbols.append(symbol)

        except Exception as e:
            print(f"Error creating variable symbol: {e}")

        return symbols

    def _extract_python_docstring(self, node: Node, source: bytes) -> Optional[str]:
        """Extract docstring from a Python function or class."""
        try:
            # Look for the first string literal in the body
            for child in node.children:
                if child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            for expr_child in stmt.children:
                                if expr_child.type == "string":
                                    docstring = source[expr_child.start_byte : expr_child.end_byte].decode("utf-8")
                                    # Remove quotes and clean up
                                    if docstring.startswith('"""') or docstring.startswith("'''"):
                                        return docstring[3:-3].strip()
                                    elif docstring.startswith('"') or docstring.startswith("'"):
                                        return docstring[1:-1].strip()
                                    return docstring.strip()
            return None
        except Exception:
            return None

    def _extract_python_parameters(self, node: Node, source: bytes) -> Optional[str]:
        """Extract parameter information from a Python function."""
        try:
            # Find parameters node
            for child in node.children:
                if child.type == "parameters":
                    params_text = source[child.start_byte : child.end_byte].decode("utf-8")
                    return params_text
            return None
        except Exception:
            return None

    def _extract_js_symbols(self, node: Node, source: bytes, file_path: str, file_hash: str) -> List[CodeSymbol]:
        """Extract symbols from JavaScript/TypeScript AST."""
        symbols = []

        def traverse(node: Node, parent_symbol: Optional[str] = None):
            # Function declarations
            if node.type in ["function_declaration", "method_definition", "arrow_function"]:
                symbol = self._create_js_function_symbol(node, source, file_path, file_hash, parent_symbol)
                if symbol:
                    symbols.append(symbol)

            # Class declarations
            elif node.type == "class_declaration":
                symbol = self._create_js_class_symbol(node, source, file_path, file_hash, parent_symbol)
                if symbol:
                    symbols.append(symbol)
                    # Process class methods
                    for child in node.children:
                        traverse(child, symbol.name)

            # Variable declarations
            elif node.type in ["variable_declaration", "lexical_declaration"]:
                var_symbols = self._create_js_variable_symbols(node, source, file_path, file_hash)
                symbols.extend(var_symbols)

            else:
                # Continue traversing
                for child in node.children:
                    traverse(child, parent_symbol)

        traverse(node)
        return symbols

    def _create_js_function_symbol(
        self, node: Node, source: bytes, file_path: str, file_hash: str, parent_symbol: Optional[str]
    ) -> Optional[CodeSymbol]:
        """Create a CodeSymbol for a JavaScript/TypeScript function."""
        try:
            # Extract function name
            name = "anonymous"
            for child in node.children:
                if child.type == "identifier":
                    name = source[child.start_byte : child.end_byte].decode("utf-8")
                    break

            # Get function signature
            signature = source[node.start_byte : node.end_byte].decode("utf-8").split("\n")[0].strip()

            return CodeSymbol(
                name=name,
                symbol_type="method" if parent_symbol else "function",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language="javascript",
                signature=signature,
                parent_symbol=parent_symbol,
                scope="public",
                file_hash=file_hash,
            )

        except Exception as e:
            print(f"Error creating JS function symbol: {e}")
            return None

    def _create_js_class_symbol(
        self, node: Node, source: bytes, file_path: str, file_hash: str, parent_symbol: Optional[str]
    ) -> Optional[CodeSymbol]:
        """Create a CodeSymbol for a JavaScript/TypeScript class."""
        try:
            # Find class name
            name = "anonymous"
            for child in node.children:
                if child.type == "identifier":
                    name = source[child.start_byte : child.end_byte].decode("utf-8")
                    break

            # Get class signature
            signature = source[node.start_byte : node.end_byte].decode("utf-8").split("\n")[0].strip()

            return CodeSymbol(
                name=name,
                symbol_type="class",
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language="javascript",
                signature=signature,
                parent_symbol=parent_symbol,
                scope="public",
                file_hash=file_hash,
            )

        except Exception as e:
            print(f"Error creating JS class symbol: {e}")
            return None

    def _create_js_variable_symbols(
        self, node: Node, source: bytes, file_path: str, file_hash: str
    ) -> List[CodeSymbol]:
        """Create CodeSymbol objects for JavaScript/TypeScript variables."""
        symbols = []
        try:
            # Extract variable names from declaration
            for child in node.children:
                if child.type == "variable_declarator":
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            name = source[subchild.start_byte : subchild.end_byte].decode("utf-8")

                            declaration_text = source[node.start_byte : node.end_byte].decode("utf-8").strip()

                            symbol = CodeSymbol(
                                name=name,
                                symbol_type="variable",
                                file_path=file_path,
                                line_number=node.start_point[0] + 1,
                                column_number=node.start_point[1],
                                end_line_number=node.end_point[0] + 1,
                                end_column_number=node.end_point[1],
                                language="javascript",
                                signature=declaration_text,
                                scope="public",
                                file_hash=file_hash,
                            )
                            symbols.append(symbol)

        except Exception as e:
            print(f"Error creating JS variable symbol: {e}")

        return symbols

    def _extract_generic_symbols(
        self, node: Node, source: bytes, file_path: str, language: str, file_hash: str
    ) -> List[CodeSymbol]:
        """Generic symbol extraction for unsupported languages."""
        symbols = []

        # This is a basic implementation that looks for common patterns
        # In a production system, this would be expanded with language-specific rules

        def traverse(node: Node):
            # Look for function-like patterns
            if "function" in node.type or "method" in node.type:
                symbol = self._create_generic_symbol(node, source, file_path, language, file_hash, "function")
                if symbol:
                    symbols.append(symbol)

            # Look for class-like patterns
            elif "class" in node.type or "struct" in node.type:
                symbol = self._create_generic_symbol(node, source, file_path, language, file_hash, "class")
                if symbol:
                    symbols.append(symbol)

            # Continue traversing
            for child in node.children:
                traverse(child)

        traverse(node)
        return symbols

    def _create_generic_symbol(
        self, node: Node, source: bytes, file_path: str, language: str, file_hash: str, symbol_type: str
    ) -> Optional[CodeSymbol]:
        """Create a generic CodeSymbol for unsupported languages."""
        try:
            # Try to extract a name (this is very basic)
            name = f"{symbol_type}_at_line_{node.start_point[0] + 1}"

            # Get the first line as signature
            signature = source[node.start_byte : node.end_byte].decode("utf-8").split("\n")[0].strip()

            return CodeSymbol(
                name=name,
                symbol_type=symbol_type,
                file_path=file_path,
                line_number=node.start_point[0] + 1,
                column_number=node.start_point[1],
                end_line_number=node.end_point[0] + 1,
                end_column_number=node.end_point[1],
                language=language,
                signature=signature,
                scope="public",
                file_hash=file_hash,
            )

        except Exception as e:
            print(f"Error creating generic symbol: {e}")
            return None
