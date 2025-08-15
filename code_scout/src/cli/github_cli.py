import os

import typer
from dotenv import load_dotenv

from cli.cli_context import CliContext
from core.diff_providers.github_diff_provider import GitHubDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.services.code_review_agent import CodeReviewAgent
from src.cli.cli_formatter import CliFormatter
from src.cli.cli_utils import (
    cli_option,
    echo_info,
    echo_warning,
    select_option,
    show_spinner,
)
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
):
    """
    Private method to perform the actual code review logic.
    """
    cli_context: CliContext = ctx.obj
    echo_info(f"Attempting to review PR #{pr_number} in {repo_owner}/{repo_name}")

    try:
        diff_provider = GitHubDiffProvider(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            github_token=github_token,
        )

        review_agent = CodeReviewAgent(
            diff_provider=diff_provider,
            llm_provider=LangChainProvider(),
            formatters=[CliFormatter()],
            cli_context=cli_context,
        )

        review_agent.review_code()

    except typer.Exit:
        pass
    except Exception as e:
        echo_warning(f"Error reviewing pull request: {e}")
        raise typer.Exit(code=1) from e


@app.command("review-pr")
def review_pr(
    ctx: typer.Context,
    repo_owner: str = cli_option(
        env_var_name="CODESCOUT_REPO_OWNER",
        prompt_message="Enter GitHub repository owner",
        required=True,
        help="GitHub repository owner.",
    ),
    repo_name: str = cli_option(
        env_var_name="CODESCOUT_REPO_NAME",
        prompt_message="Enter GitHub repository name",
        required=True,
        help="GitHub repository name.",
    ),
    pr_number: int = typer.Option(
        help="Pull request number to review.",
        envvar="CODESCOUT_PR_NUMBER",
    ),
    github_token: str = cli_option(
        env_var_name="CODESCOUT_GITHUB_API_KEY",
        prompt_message="Enter GitHub API key",
        required=True,
        secure_input=True,
        help="""
        GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY environment variable.
        """,
    ),
):
    """
    Review a specific pull request from a GitHub repository.
    """
    _perform_review(ctx, repo_owner, repo_name, pr_number, github_token)


@app.command("interactive-review")
def interactive_review(
    ctx: typer.Context,
    repo_owner: str = cli_option(
        env_var_name="CODESCOUT_REPO_OWNER",
        prompt_message="Enter GitHub repository owner",
        required=True,
        help="GitHub repository owner.",
    ),
    repo_name: str = cli_option(
        env_var_name="CODESCOUT_REPO_NAME",
        prompt_message="Enter GitHub repository name",
        required=True,
        help="GitHub repository name.",
    ),
    github_token: str = cli_option(
        env_var_name="CODESCOUT_GITHUB_API_KEY",
        prompt_message="Enter GitHub API key",
        required=True,
        secure_input=True,
        help="GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY env variable.",
    ),
):
    echo_info(message=f"Starting github interactive review for {repo_owner}/{repo_name}")
    try:
        github_service = GitHubService(github_token, repo_owner, repo_name)
        with show_spinner(label="Fetching open pull requests"):
            pull_requests = github_service.get_open_pull_requests()

        if not pull_requests:
            echo_info(message=f"No open pull requests found for {repo_owner}/{repo_name}.")
            return

        pr_choices = [
            (f"#{pr.number}: {pr.title} by {pr.user.login} (Branch: {pr.head.ref})", pr.number)
            for pr in pull_requests
        ]

        selected_pr_number = select_option(
            "Select a Pull Request to review",
            pr_choices,
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
            )
        else:
            echo_warning(f"Invalid action selected: {selected_action}")
            raise typer.Exit(code=1)

    except typer.Exit:
        pass
    except Exception as e:
        echo_warning(f"Error during interactive review: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    load_dotenv()

    try:
        diff_provider = GitHubDiffProvider(
            repo_owner="glamox-lms",
            repo_name="wireless-radio-dart-sdk",
            pr_number=82,
            github_token=os.getenv("CODESCOUT_GITHUB_API_KEY", default=""),
        )

        llm_provider = LangChainProvider()
        # Create a dummy CliContext for standalone execution
        cli_context = CliContext(
            model="openrouter/anthropic/claude-sonnet-4",
            openrouter_api_key=os.getenv("CODESCOUT_OPENROUTER_API_KEY", default=""),
            openai_api_key="",
            claude_api_key="",
        )

        review_agent = CodeReviewAgent(
            diff_provider=diff_provider,
            llm_provider=llm_provider,
            formatters=[CliFormatter()],
            cli_context=cli_context,
        )

        echo_info(f"\nUsing LLM: {cli_context.model}")
        with show_spinner(label="Performing code review"):
            review_agent.review_code()
        echo_info("Successfully reviewed PR #16.")

    except ValueError as ex1:
        echo_warning(f"Error: {ex1}")
        raise typer.Exit(code=1) from ex1
    except Exception as ex2:
        echo_warning(f"Error reviewing pull request: {ex2}")
        raise typer.Exit(code=1) from ex2
