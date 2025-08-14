from typing import Optional


class CliContext:
    """
    A custom class to hold common CLI options for Typer context.
    """

    def __init__(
        self,
        model: str,
        openrouter_api_key: Optional[str],
        openai_api_key: Optional[str],
        claude_api_key: Optional[str],
    ):
        self.model = model
        self.openrouter_api_key = openrouter_api_key
        self.openai_api_key = openai_api_key
        self.claude_api_key = claude_api_key

    def __str__(self):
        return f"""
CliContext(
    model={self.model},
    openrouter_api_key={self.openrouter_api_key},
    openai_api_key={self.openai_api_key},
    claude_api_key={self.claude_api_key},
)"""
