"""CLI interface for Code Scout."""

import os
from typing import Optional

import typer
from dotenv import load_dotenv

from cli.cli_config import cli_config
from cli.code_scout_context import CodeScoutContext
from cli.git_cli import app as git_app
from cli.github_cli import app as github_app
from core.llm_providers.langchain_provider import LangChainProvider
from src.cli.cli_options import (
    claude_api_key_option,
    env_file_option,
    model_option,
    openai_api_key_option,
    openrouter_api_key_option,
)
from src.cli.cli_utils import handle_cli_exception  # Import the new utility function

# Load default .env file at module import time
load_dotenv()

app = typer.Typer(
    help="Code Scout CLI for automated code reviews.",
    no_args_is_help=True,
)


@app.callback()
def main(  # noqa: PLR0913
    ctx: typer.Context,
    # env_file param is required and needs to be first in order to first process the .env file
    # and only then load other parameters
    _env_file: Optional[str] = env_file_option(),
    model: str = model_option(),
    openrouter_api_key: Optional[str] = openrouter_api_key_option(),
    openai_api_key: Optional[str] = openai_api_key_option(),
    claude_api_key: Optional[str] = claude_api_key_option(),
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

    # Set the debug flag in the centralized config
    cli_config.is_debug = debug if debug is not None else os.getenv("CODESCOUT_DEBUG", "false").lower() == "true"

    ctx.obj = CodeScoutContext(
        model=model,
        openrouter_api_key=openrouter_api_key,
        openai_api_key=openai_api_key,
        claude_api_key=claude_api_key,
    )

    try:
        LangChainProvider().validate_cli_context(ctx.obj)
    except Exception as e:
        handle_cli_exception(e, message="Error validating LLM configuration")


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
