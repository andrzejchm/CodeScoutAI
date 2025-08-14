"""CLI interface for Code Scout."""

import os
from typing import Optional

import typer
from dotenv import load_dotenv

# No initial load_dotenv() here.
# It will be handled conditionally inside the main callback.
from cli.cli_context import CliContext
from cli.git_cli import app as git_app
from cli.github_cli import app as github_app

app = typer.Typer(
    help="Code Scout CLI for automated code reviews.",
    no_args_is_help=True,
)


@app.callback()
def main(  # noqa: PLR0913
    ctx: typer.Context,
    model: str = typer.Option(
        default="openrouter/anthropic/claude-sonnet-4",
        envvar="CODESCOUT_MODEL",
        help="""
            Model to use for code review (e.g.,
            'openrouter/anthropic/claude-3.7-sonnet')
        """,
    ),
    # Remove envvar from API key options, as we'll handle them manually
    openrouter_api_key: Optional[str] = typer.Option(
        default=None,
        help="""
            API key for OpenRouter (can be set via CODESCOUT_OPENROUTER_API_KEY
            env variable or .env file)
        """,
    ),
    openai_api_key: Optional[str] = typer.Option(
        default=None,
        help="""
            API key for OpenAI (can be set via CODESCOUT_OPENAI_API_KEY env
            variable or .env file)
        """,
    ),
    claude_api_key: Optional[str] = typer.Option(
        default=None,
        help="""
            API key for Claude (can be set via CODESCOUT_CLAUDE_API_KEY env
            variable or .env file)
        """,
    ),
    env_file: Optional[str] = typer.Option(
        default=None,
        help="Path to the .env file to load environment variables from.",
    ),
):
    """
    Code Scout CLI for automated code reviews.
    """
    # Conditionally load .env file based on whether env_file is provided
    if env_file:
        # If a custom env_file is provided, load it and override existing variables.
        load_dotenv(dotenv_path=env_file, override=True)
    else:
        # If no custom env_file is provided, load the default .env file.
        # This will not override existing system environment variables unless explicitly told to.
        load_dotenv()

    # Manually retrieve API keys from environment variables,
    # prioritizing command-line options if provided.
    # If the command-line option is None, then check the environment variable.
    final_openrouter_api_key = openrouter_api_key or os.getenv("CODESCOUT_OPENROUTER_API_KEY")
    final_openai_api_key = openai_api_key or os.getenv("CODESCOUT_OPENAI_API_KEY")
    final_claude_api_key = claude_api_key or os.getenv("CODESCOUT_CLAUDE_API_KEY")

    ctx.obj = CliContext(
        model=model,
        openrouter_api_key=final_openrouter_api_key,
        openai_api_key=final_openai_api_key,
        claude_api_key=final_claude_api_key,
    )


app.add_typer(
    github_app,
    name="github",
    help="Commands for interacting with GitHub Pull Requests.",
)

app.add_typer(
    git_app,
    name="git",
    help="Commands for reviewing local Git repositories.",
)

if __name__ == "__main__":
    app()
