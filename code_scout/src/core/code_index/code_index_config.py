class CodeIndexConfig:
    """Simplified configuration class for the code index service."""

    def __init__(self, db_path: str = "./.codescout/code_index.db"):
        self.db_path = db_path
