"""CLI interface for Code Scout."""

import os
from typing import Optional

import typer
from dotenv import load_dotenv

from cli.cli_config import cli_config
from cli.cli_context import CliContext
from cli.git_cli import app as git_app
from cli.github_cli import app as github_app
from core.llm_providers.langchain_provider import LangChainProvider
from src.cli.cli_utils import cli_option

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
    openrouter_api_key: Optional[str] = cli_option(
        env_var_name="CODESCOUT_OPENROUTER_API_KEY",
        help="""
            API key for OpenRouter (can be set via CODESCOUT_OPENROUTER_API_KEY
            env variable or .env file)
        """,
    ),
    openai_api_key: Optional[str] = cli_option(
        env_var_name="CODESCOUT_OPENAI_API_KEY",
        help="""
            API key for OpenAI (can be set via CODESCOUT_OPENAI_API_KEY env
            variable or .env file)
        """,
    ),
    claude_api_key: Optional[str] = cli_option(
        env_var_name="CODESCOUT_CLAUDE_API_KEY",
        help="""
            API key for Claude (can be set via CODESCOUT_CLAUDE_API_KEY env
            variable or .env file)
        """,
    ),
    env_file: Optional[str] = typer.Option(
        default=None,
        envvar="CODESCOUT_ENV_FILE",
        help="Path to the .env file to load environment variables from.",
    ),
    debug: bool = typer.Option(
        default=False,
        envvar="CODESCOUT_DEBUG",
        help="""
        Enable debug mode and verbose output.
        (Can be set via CODESCOUT_DEBUG env variable or --debug flag)
        """,
    ),
):
    """
    Code Scout CLI for automated code reviews.
    """
    if env_file:
        # If a custom env_file is provided, load it and override existing variables.
        load_dotenv(dotenv_path=env_file, override=True)
    else:
        # If no custom env_file is provided, load the default .env file.
        # This will not override existing system environment variables unless explicitly told to.
        load_dotenv()

    # Set the debug flag in the centralized config
    cli_config.is_debug = (
        debug if debug is not None else os.getenv("CODESCOUT_DEBUG", "false").lower() == "true"
    )

    ctx.obj = CliContext(
        model=model,
        openrouter_api_key=openrouter_api_key,
        openai_api_key=openai_api_key,
        claude_api_key=claude_api_key,
    )

    LangChainProvider().validate_cli_context(ctx.obj)


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
