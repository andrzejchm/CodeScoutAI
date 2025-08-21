from typing import List, Optional


class CodeIndexConfig:
    """Simplified configuration class for the code index service."""

    def __init__(
        self,
        db_path: str = "./.codescout/code_index.db",
        file_extensions: Optional[List[str]] = None,
    ):
        self.db_path = db_path
        self.file_extensions = (
            [extension.replace(".", "").strip() for extension in file_extensions] if file_extensions else [],
        )
