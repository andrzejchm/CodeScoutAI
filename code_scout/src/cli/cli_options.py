from typing import Any, Optional

import typer

from cli.cli_utils import echo_debug
from src.cli.cli_utils import cli_option


def repo_owner_option() -> Any:
    """Typer option for GitHub repository owner."""
    return cli_option(
        env_var_name="CODESCOUT_REPO_OWNER",
        prompt_message="Enter GitHub repository owner",
        required=True,
        help="GitHub repository owner.",
    )


def repo_name_option() -> Any:
    """Typer option for GitHub repository name."""
    return cli_option(
        env_var_name="CODESCOUT_REPO_NAME",
        prompt_message="Enter GitHub repository name",
        required=True,
        help="GitHub repository name.",
    )


def pr_number_option() -> Any:
    """Typer option for GitHub Pull Request number."""
    return cli_option(
        env_var_name="CODESCOUT_PR_NUMBER",
        prompt_message="Enter Pull Request number",
        required=True,
        help="Pull request number to review.",
    )


def github_token_option() -> Any:
    """Typer option for GitHub API token."""
    return cli_option(
        env_var_name="CODESCOUT_GITHUB_API_KEY",
        prompt_message="Enter GitHub API key",
        required=True,
        secure_input=True,
        help="""
        GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY environment variable.
        """,
    )


def env_file_option() -> Any:
    """Typer option for specifying an environment file."""

    def _env_file_callback(env_file_path: Optional[str]) -> Optional[str]:
        """Callback to reload dotenv when custom env file is specified."""
        if env_file_path:
            echo_debug(f"Loading environment variables from {env_file_path}")
            from dotenv import load_dotenv

            load_dotenv(dotenv_path=env_file_path, override=True)
        return env_file_path

    return typer.Option(
        "",
        "--env-file",
        envvar="CODESCOUT_ENV_FILE",
        callback=_env_file_callback,
        help="Path to the .env file to load environment variables from.",
    )


def model_option() -> Any:
    """Typer option for the LLM model to use."""
    return typer.Option(
        default="openrouter/anthropic/claude-sonnet-4",
        envvar="CODESCOUT_MODEL",
        help="""
            Model to use for code review (e.g.,
            'openrouter/anthropic/claude-3.7-sonnet')
        """,
    )


def openrouter_api_key_option() -> Any:
    """Typer option for OpenRouter API key."""
    return cli_option(
        env_var_name="CODESCOUT_OPENROUTER_API_KEY",
        help="""
            API key for OpenRouter (can be set via CODESCOUT_OPENROUTER_API_KEY
            env variable or .env file)
        """,
    )


def openai_api_key_option() -> Any:
    """Typer option for OpenAI API key."""
    return cli_option(
        env_var_name="CODESCOUT_OPENAI_API_KEY",
        help="""
            API key for OpenAI (can be set via CODESCOUT_OPENAI_API_KEY env
            variable or .env file)
        """,
    )


def claude_api_key_option() -> Any:
    """Typer option for Claude API key."""
    return cli_option(
        env_var_name="CODESCOUT_CLAUDE_API_KEY",
        help="""
            API key for Claude (can be set via CODESCOUT_CLAUDE_API_KEY env
            variable or .env file)
        """,
    )


def repo_path_option() -> Any:
    """Typer option for the Git repository path."""
    return cli_option(
        env_var_name="CODESCOUT_REPO_PATH",
        prompt_message="Enter path to the Git repository",
        required=True,
        help="Path to the Git repository",
    )


def source_option() -> Any:
    """Typer option for the source reference in Git."""
    return cli_option(
        env_var_name="CODESCOUT_SOURCE",
        help="Source branch, commit, or tag to compare from (e.g., 'main', 'HEAD~1')",
    )


def target_option() -> Any:
    """Typer option for the target reference in Git."""
    return cli_option(
        env_var_name="CODESCOUT_TARGET",
        help="Target branch, commit, or tag to compare to (e.g., 'HEAD')",
    )


def staged_option() -> Any:
    """Typer option for reviewing only staged files in Git."""
    return typer.Option(
        default=False,
        envvar="CODESCOUT_STAGED",
        help="Review only staged files",
    )
