class CodeIndexConfig:
    """Simplified configuration class for the code index service."""

    db_path: str
    file_extensions: list[str]

    def __init__(
        self,
        db_path: str = "./.codescout/code_index.db",
        file_extensions: list[str] | None = None,
    ):
        self.db_path = db_path
        self.file_extensions = (
            [extension.replace(".", "").strip() for extension in file_extensions] if file_extensions else []
        )
