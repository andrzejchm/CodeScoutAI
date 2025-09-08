import typer
from dotenv import load_dotenv
from typer.testing import CliRunner

from cli.cli_config import cli_config
from cli.cli_formatter import CliFormatter
from cli.code_scout_context import CodeScoutContext
from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.services.code_review_agent import CodeReviewAgent
from core.tools.file_content_tool import FileContentTool
from core.tools.search_code_index_tool import SearchCodeIndexTool
from src.cli.cli_options import (
    allowed_categories_option,
    allowed_severities_option,
    banned_categories_option,
    banned_severities_option,
    repo_path_option,
    source_option,
    staged_option,
    target_option,
)
from src.cli.cli_utils import echo_debug, handle_cli_exception
from src.core.models.review_config import ReviewConfig

git_app = typer.Typer(
    no_args_is_help=True,
    help="Commands for reviewing local Git repositories.",
)


@git_app.command()
def review(
    ctx: typer.Context,
    repo_path: str = repo_path_option(),
    source: str = source_option(),
    target: str = target_option(),
    staged: bool = staged_option(),
    allowed_severities: list[str] = allowed_severities_option(),
    banned_severities: list[str] = banned_severities_option(),
    allowed_categories: list[str] = allowed_categories_option(),
    banned_categories: list[str] = banned_categories_option(),
) -> None:
    """
    Reviews code changes in a Git repository.
    """
    code_scout_context: CodeScoutContext = ctx.obj
    echo_debug(
        f"""
        Reviewing Git repository.
        repo_path:\t{repo_path}
        source:\t\t{source}
        target:\t\t{target}
        staged:\t\t{staged}
""",
    )
    try:
        git_diff_provider = GitDiffProvider(
            repo_path=repo_path,
            source=source,
            target=target,
            staged=staged,
        )

        llm_provider = LangChainProvider()

        review_config = ReviewConfig(
            langchain_tools=[
                FileContentTool(),
                SearchCodeIndexTool(),
            ],
            allowed_severities=allowed_severities,
            banned_severities=banned_severities,
            allowed_categories=allowed_categories,
            banned_categories=banned_categories,
        )

        review_agent = CodeReviewAgent(
            diff_provider=git_diff_provider,
            llm_provider=llm_provider,
            formatters=[CliFormatter()],
            cli_context=code_scout_context,
            config=review_config,
        )

        _ = review_agent.review_code()
    except Exception as e:
        handle_cli_exception(e, message="Error reviewing Git repository")


if __name__ == "__main__":
    # The load_dotenv call here is for testing purposes when running github_cli.py directly.
    # In a real CLI execution via main.py, dotenv is loaded by main.py's callback.
    _ = load_dotenv("../../.codescout.env")  # Assign to _ to explicitly ignore the result
    cli_config.is_debug = True
    runner = CliRunner()
    from cli.main import app

    # Example usage of review-pr command
    result = runner.invoke(
        app,
        ["git", "review"],
        catch_exceptions=False,
        color=True,
    )
    print(f"Err: {result.stderr}")
    print(f"stdout: {result.stdout}")
