import hashlib
from pathlib import Path
from typing import Dict, List, Optional

from tree_sitter import Language, Parser, Query, QueryCursor
from tree_sitter_language_pack import get_language

from core.code_index.models import CodeSymbol
from core.code_index.queries import QUERIES


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

    def extract_symbols(self, file_path: str, content: str) -> List[CodeSymbol]:
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

            query_src = QUERIES[language_name]
            query = Query(language, query_src)
            query_cursor = QueryCursor(query)
            matches = query_cursor.matches(tree.root_node)

            if not matches:
                return []

            file_hash = hashlib.sha256(source_bytes).hexdigest()
            symbols: List[CodeSymbol] = []

            for match in matches:
                captures = match[1]

                definition_node = None
                name_node = None
                symbol_type = ""

                for capture_name, nodes in captures.items():
                    if not nodes:
                        continue
                    node = nodes[0]
                    if ".definition" in capture_name:
                        definition_node = node
                        symbol_type = capture_name.split(".")[0]
                    elif ".name" in capture_name:
                        name_node = node

                if not definition_node or not name_node:
                    continue

                name = name_node.text.decode("utf-8") if name_node.text else ""
                source_code = definition_node.text.decode("utf-8") if definition_node.text else ""

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
