import typer
from dotenv import load_dotenv
from typer.testing import CliRunner

from cli.cli_config import cli_config
from cli.code_scout_context import CodeScoutContext
from core.diff_providers.github_diff_provider import GitHubDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.services.code_review_agent import CodeReviewAgent
from core.tools.file_content_tool import FileContentTool
from core.tools.search_code_index_tool import SearchCodeIndexTool
from src.cli.cli_formatter import CliFormatter
from src.cli.cli_options import (
    allowed_categories_option,
    allowed_severities_option,
    banned_categories_option,
    banned_severities_option,
    github_token_option,
    pr_number_option,
    repo_name_option,
    repo_owner_option,
)
from src.cli.cli_utils import (
    echo_info,
    echo_warning,
    handle_cli_exception,
    select_from_paginated_options,
    select_option,
)
from src.core.models.review_config import ReviewConfig
from src.core.services.github_service import GitHubService

app = typer.Typer(
    no_args_is_help=True,
    help="Commands for interacting with GitHub Pull Requests.",
)


def _perform_review(
    ctx: typer.Context,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    github_token: str,
    allowed_severities: list[str],
    banned_severities: list[str],
    allowed_categories: list[str],
    banned_categories: list[str],
) -> None:
    """
    Private method to perform the actual code review logic.
    """
    code_scout_context: CodeScoutContext = ctx.obj
    echo_info(f"Attempting to review PR #{pr_number} in {repo_owner}/{repo_name}")

    try:
        diff_provider = GitHubDiffProvider(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            github_token=github_token,
        )

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
            diff_provider=diff_provider,
            llm_provider=LangChainProvider(),
            formatters=[CliFormatter()],
            cli_context=code_scout_context,
            config=review_config,
        )

        _ = review_agent.review_code()  # Assign to _ to explicitly ignore the result

    except typer.Exit:
        pass
    except Exception as e:
        handle_cli_exception(e, message="Error reviewing pull request")


@app.command("review-pr")
def review_pr(
    ctx: typer.Context,
    repo_owner: str = repo_owner_option(),
    repo_name: str = repo_name_option(),
    pr_number: int = pr_number_option(),
    github_token: str = github_token_option(),
    allowed_severities: list[str] = allowed_severities_option(),
    banned_severities: list[str] = banned_severities_option(),
    allowed_categories: list[str] = allowed_categories_option(),
    banned_categories: list[str] = banned_categories_option(),
) -> None:
    """
    Review a specific pull request from a GitHub repository.
    """
    _perform_review(
        ctx,
        repo_owner,
        repo_name,
        pr_number,
        github_token,
        allowed_severities,
        banned_severities,
        allowed_categories,
        banned_categories,
    )


@app.command("interactive-review")
def interactive_review(
    ctx: typer.Context,
    repo_owner: str = repo_owner_option(),
    repo_name: str = repo_name_option(),
    github_token: str = github_token_option(),
    allowed_severities: list[str] = allowed_severities_option(),
    banned_severities: list[str] = banned_severities_option(),
    allowed_categories: list[str] = allowed_categories_option(),
    banned_categories: list[str] = banned_categories_option(),
) -> None:
    echo_info(message=f"Starting github interactive review for {repo_owner}/{repo_name}")
    try:
        github_service = GitHubService(github_token, repo_owner, repo_name)

        def fetch_pull_requests_page(page: int, _per_page: int) -> list[tuple[str, int]]:
            pull_requests = github_service.get_open_pull_requests(page=page)
            return [
                (f"#{pr.number}: {pr.title} by {pr.user.login} (Branch: {pr.head.ref})", pr.number)
                for pr in pull_requests
            ]

        selected_pr_number = select_from_paginated_options(
            "Select a Pull Request to review",
            fetch_pull_requests_page,
            per_page=10,
        )

        if selected_pr_number is None:
            echo_info("No PR selected. Exiting interactive review.")
            raise typer.Exit()

        action_choices = [("Do Code Review", "review"), ("Cancel", "cancel")]
        selected_action = select_option(
            "What would you like to do?",
            action_choices,
        )

        if selected_action is None or selected_action == "cancel":
            raise typer.Exit()
        elif selected_action == "review":
            _perform_review(
                ctx=ctx,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pr_number=selected_pr_number,
                github_token=github_token,
                allowed_severities=allowed_severities,
                banned_severities=banned_severities,
                allowed_categories=allowed_categories,
                banned_categories=banned_categories,
            )
        else:
            echo_warning(f"Invalid action selected: {selected_action}")
            raise typer.Exit(code=1)

    except typer.Exit:
        pass
    except Exception as e:
        handle_cli_exception(e, message="Error during interactive review")


if __name__ == "__main__":
    # The load_dotenv call here is for testing purposes when running github_cli.py directly.
    # In a real CLI execution via main.py, dotenv is loaded by main.py's callback.
    _ = load_dotenv(".codescout.env")  # Assign to _ to explicitly ignore the result
    cli_config.is_debug = True
    runner = CliRunner()

    # Example usage of review-pr command
    result = runner.invoke(
        app,
        ["review-pr", "--pr-number", "257"],
        catch_exceptions=False,
        color=True,
    )
    print(f"Err: {result.stderr}")
    print(f"stdout: {result.stdout}")
