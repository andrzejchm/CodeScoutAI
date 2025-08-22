import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from tree_sitter import Language, Parser, Query, QueryCursor
from tree_sitter_language_pack import get_language

from core.code_index.models import CodeSymbol
from core.code_index.queries import QUERIES


def _print_tree(node, indent=""):
    """Pretty-print a Node and its named children."""
    # source should be bytes (as used by tree_sitter)
    start = node.start_point  # (row, col)
    end = node.end_point

    print(f"{indent}{node.type} [{start.row}:{start.column}-{end.row}:{end.column}] - {node.text}")
    for child in node.named_children:
        _print_tree(child, indent + "  ")


class CodeIndexExtractor:
    """
    Extracts code symbols from source files using Tree-sitter parsers and language-specific queries.
    """

    def __init__(self):
        """Initialize the extractor with lazy-loaded parsers and languages."""
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self.extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".dart": "dart",
        }

    def extract_symbols(self, file_path: str, content: str) -> List[CodeSymbol]:  # noqa: PLR0912, PLR0915
        """
        Extract symbols from source code content using Tree-sitter queries.
        """
        try:
            language_name = self.detect_language(file_path)
            if not language_name or language_name not in QUERIES:
                return []

            language = self._get_language(language_name)
            parser = self._get_parser(language_name)
            if not language or not parser:
                return []

            source_bytes = content.encode("utf-8")
            tree = parser.parse(source_bytes)
            # print(
            #     f"\n--- S-expression for {file_path} \n--------------\n\n----------------------------------"
            # )
            _print_tree(tree.root_node)

            query_src = QUERIES[language_name]
            query = Query(language, query_src)
            query_cursor = QueryCursor(query)
            matches = query_cursor.matches(tree.root_node)

            if not matches:
                return []

            file_hash = hashlib.sha256(source_bytes).hexdigest()
            symbols: List[CodeSymbol] = []

            # Minimal span wrapper to combine .start/.end nodes into one range
            class _Span:
                __slots__ = ("end_byte", "end_point", "start_byte", "start_point", "text")

                def __init__(self, a, b):
                    self.start_point = a.start_point
                    self.end_point = b.end_point
                    self.start_byte = a.start_byte
                    self.end_byte = b.end_byte
                    self.text = None  # ensures we slice from source_bytes

            for match in matches:
                captures = match[1]  # dict: {capture_name: [nodes...]}

                definition_node = None
                name_node = None
                start_node = None
                end_node = None
                symbol_type = ""

                for capture_name, nodes in captures.items():
                    if not nodes:
                        continue
                    node = nodes[0]

                    if capture_name.endswith(".definition"):
                        definition_node = node
                        symbol_type = capture_name.split(".")[0]
                    elif capture_name.endswith(".name"):
                        name_node = node
                        symbol_type = capture_name.split(".")[0]
                    elif capture_name.endswith(".start"):
                        start_node = node
                        symbol_type = capture_name.split(".")[0]
                    elif capture_name.endswith(".end"):
                        end_node = node
                        symbol_type = capture_name.split(".")[0]

                # If we only have start/end, synthesize a full span
                if definition_node is None and start_node is not None and end_node is not None:
                    definition_node = _Span(start_node, end_node)

                # If name not captured explicitly, try the 'name' field on the start node
                if name_node is None and start_node is not None:
                    maybe_name = start_node.child_by_field_name("name")
                    if maybe_name is not None:
                        name_node = maybe_name

                if not definition_node or not name_node:
                    continue

                # Decode name text (fallback to slicing if node has no .text)
                name_bytes = getattr(name_node, "text", None)
                if name_bytes is not None:
                    name = name_bytes.decode("utf-8")
                else:
                    name = source_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8")

                # Extract source for the definition span
                def_bytes = getattr(definition_node, "text", None)
                if def_bytes is not None:
                    source_code = def_bytes.decode("utf-8")
                else:
                    source_code = source_bytes[definition_node.start_byte : definition_node.end_byte].decode("utf-8")

                symbol = CodeSymbol(
                    name=name,
                    symbol_type=symbol_type,
                    file_path=file_path,
                    start_line_number=definition_node.start_point[0] + 1,
                    end_line_number=definition_node.end_point[0] + 1,
                    start_column_number=definition_node.start_point[1],
                    end_column_number=definition_node.end_point[1],
                    language=language_name,
                    file_hash=file_hash,
                    source_code=source_code,
                )
                symbols.append(symbol)

            return symbols

        except Exception as e:
            print(f"Error extracting symbols from {file_path}: {e}")
            return []

    def detect_language(self, file_path: str) -> Optional[str]:
        path = Path(file_path)
        return self.extension_map.get(path.suffix.lower())

    def _get_parser(self, language_name: str) -> Optional[Parser]:
        if language_name in self.parsers:
            return self.parsers[language_name]
        try:
            language = self._get_language(language_name)
            if not language:
                return None
            parser = Parser(language)
            self.parsers[language_name] = parser
            return parser
        except Exception as e:
            print(f"Failed to load parser for {language_name}: {e}")
            return None

    def _get_language(self, language_name: str) -> Optional[Language]:
        if language_name in self.languages:
            return self.languages[language_name]
        try:
            # The language pack expects a literal, but our string detection is reliable.
            language = get_language(language_name)  # type: ignore
            self.languages[language_name] = language
            return language
        except Exception:
            return None
