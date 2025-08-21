from typing import Any, Optional

import typer

from cli.cli_utils import cli_option, echo_debug


def repo_owner_option() -> Any:
    return cli_option(
        param_decls=["--repo-owner"],
        env_var_name="CODESCOUT_REPO_OWNER",
        prompt_message="Enter GitHub repository owner",
        required=True,
        help="GitHub repository owner.",
    )


def repo_name_option() -> Any:
    return cli_option(
        param_decls=["--repo-name"],
        env_var_name="CODESCOUT_REPO_NAME",
        prompt_message="Enter GitHub repository name",
        required=True,
        help="GitHub repository name.",
    )


def pr_number_option() -> Any:
    return cli_option(
        param_decls=["--pr-number"],
        env_var_name="CODESCOUT_PR_NUMBER",
        prompt_message="Enter Pull Request number",
        required=True,
        help="Pull request number to review.",
    )


def github_token_option() -> Any:
    return cli_option(
        param_decls=["--github-token"],
        env_var_name="CODESCOUT_GITHUB_API_KEY",
        prompt_message="Enter GitHub API key",
        required=True,
        secure_input=True,
        help="""
        GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY environment variable.
        """,
    )


def env_file_option() -> Any:
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
    return typer.Option(
        default="openrouter/anthropic/claude-sonnet-4",
        envvar="CODESCOUT_MODEL",
        help="""
            Model to use for code review (e.g.,
            'openrouter/anthropic/claude-3.7-sonnet')
        """,
    )


def openrouter_api_key_option() -> Any:
    return cli_option(
        param_decls=["--openrouter-api-key"],
        env_var_name="CODESCOUT_OPENROUTER_API_KEY",
        help="""
            API key for OpenRouter (can be set via CODESCOUT_OPENROUTER_API_KEY
            env variable or .env file)
        """,
    )


def openai_api_key_option() -> Any:
    return cli_option(
        param_decls=["--openai-api-key"],
        env_var_name="CODESCOUT_OPENAI_API_KEY",
        help="""
            API key for OpenAI (can be set via CODESCOUT_OPENAI_API_KEY env
            variable or .env file)
        """,
    )


def claude_api_key_option() -> Any:
    return cli_option(
        param_decls=["--claude-api-key"],
        env_var_name="CODESCOUT_CLAUDE_API_KEY",
        help="""
            API key for Claude (can be set via CODESCOUT_CLAUDE_API_KEY env
            variable or .env file)
        """,
    )


def repo_path_option(required: bool = False) -> Any:
    return cli_option(
        param_decls=["--repo-path"],
        env_var_name="CODESCOUT_REPO_PATH",
        prompt_message="Enter path to the Git repository",
        required=required,
        help="Path to the Git repository",
        default=".",
    )


def code_paths_option() -> Any:
    return cli_option(
        param_decls=["--code-path", "-p"],
        env_var_name="CODESCOUT_INDEX_CODE_PATHS",
        help="Path(s) to the code repository or directories to index. Can be specified multiple times.",
        required=True,
        is_list=True,
    )


def print_file_paths_option() -> Any:
    return cli_option(
        param_decls=["--print-file-paths"],
        env_var_name="CODESCOUT_PRINT_FILE_PATHS",
        prompt_message="Print file paths being indexed",
    )


def file_extensions_option() -> Any:
    return cli_option(
        param_decls=["--file-extensions", "-e"],
        env_var_name="CODESCOUT_INDEX_FILE_EXTENSIONS",
        help="""Comma-separated list of file extensions to include (e.g., py,js,ts).
        If empty, all supported files are indexed.""",
        is_list=True,
    )


def source_option() -> Any:
    return cli_option(
        param_decls=["--source"],
        env_var_name="CODESCOUT_SOURCE",
        help="Source branch, commit, or tag to compare from (e.g., 'main', 'HEAD~1')",
    )


def target_option() -> Any:
    return cli_option(
        param_decls=["--target"],
        env_var_name="CODESCOUT_TARGET",
        help="Target branch, commit, or tag to compare to (e.g., 'HEAD')",
    )


def staged_option() -> Any:
    return typer.Option(
        default=False,
        envvar="CODESCOUT_STAGED",
        help="Review only staged files",
    )


def db_path_option() -> Any:
    return cli_option(
        param_decls=["--db-path"],
        env_var_name="CODESCOUT_DB_PATH",
        help="Path to the code index database file.",
    )
