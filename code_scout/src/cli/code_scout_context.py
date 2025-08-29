class CodeScoutContext:
    """
    A custom class to hold common CLI options for Typer context.
    """

    model: str
    openrouter_api_key: str | None
    openai_api_key: str | None
    claude_api_key: str | None

    def __init__(
        self,
        model: str,
        openrouter_api_key: str | None,
        openai_api_key: str | None,
        claude_api_key: str | None,
    ):
        self.model = model
        self.openrouter_api_key = openrouter_api_key
        self.openai_api_key = openai_api_key
        self.claude_api_key = claude_api_key
