import logging
from os import environ
from typing import Optional

import typer
from dotenv import load_dotenv

from cli.cli_context import CliContext
from core.diff_providers.github_diff_provider import GitHubDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.models.review_command_args import ReviewCommandArgs
from core.services.code_review_agent import CodeReviewAgent
from core.services.github_service import GitHubService
from src.cli.cli_formatter import CliFormatter
from src.cli.cli_utils import echo_info, select_option

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command("review-pr")
def review_pr(
    ctx: typer.Context,
    repo_owner: str = typer.Option(..., help="GitHub repository owner."),
    repo_name: str = typer.Option(..., help="GitHub repository name."),
    pr_number: int = typer.Option(..., help="Pull request number to review."),
    github_token: Optional[str] = typer.Option(
        default=None,
        envvar="CODESCOUT_GITHUB_API_KEY",
        help="""
        GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY environment variable.
        """,
    ),
):
    """
    Review a specific pull request from a GitHub repository.
    """
    cli_context: CliContext = ctx.obj
    echo_info(f"Attempting to review PR #{pr_number} in {repo_owner}/{repo_name}")

    if not github_token:
        echo_info(
            "Error: GitHub token not provided. Please set CODESCOUT_GITHUB_API_KEY environment "
            "variable or pass --github-token."
        )
        raise typer.Exit(code=1)

    try:
        diff_provider = GitHubDiffProvider(
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            github_token=github_token,
        )

        llm_provider = LangChainProvider()

        review_agent = CodeReviewAgent(
            diff_provider=diff_provider,
            llm_provider=llm_provider,
            formatters=[CliFormatter()],
        )

        review_args = ReviewCommandArgs(
            repo_path="",
            source="",
            target="",
            staged=False,
            model=cli_context.model,
            openrouter_api_key=cli_context.openrouter_api_key,
            openai_api_key=cli_context.openai_api_key,
            claude_api_key=cli_context.claude_api_key,
        )

        review_agent.review_code(review_args)
        echo_info(f"Successfully reviewed PR #{pr_number}.")

    except ValueError as e:
        echo_info(f"Error: {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        echo_info(f"Error reviewing pull request: {e}")
        raise typer.Exit(code=1) from e


@app.command("interactive-review")
def interactive_review(
    ctx: typer.Context,
    repo_owner: str = typer.Option(..., help="GitHub repository owner."),
    repo_name: str = typer.Option(..., help="GitHub repository name."),
    github_token: Optional[str] = typer.Option(
        default=None,
        envvar="CODESCOUT_GITHUB_API_KEY",
        help="GitHub API access token. Can be set via CODESCOUT_GITHUB_API_KEY env variable.",
    ),
):
    """
    List GitHub PRs and allow interactive selection for review.
    """
    echo_info(message=f"Starting interactive review for {repo_owner}/{repo_name}")
    if not github_token:
        echo_info(
            "Error: GitHub token not provided. Please set CODESCOUT_GITHUB_API_KEY environment "
            "variable or pass --github-token."
        )
        raise typer.Exit(code=1)

    try:
        github_service = GitHubService(github_token)
        repo = github_service.get_repository(repo_owner, repo_name)
        pull_requests = github_service.get_open_pull_requests(repo)
        echo_info(f"Fetched {len(pull_requests)} open PRs.")

        if not pull_requests:
            echo_info(message=f"No open pull requests found for {repo_owner}/{repo_name}.")
            return

        pr_choices = [
            f"#{pr.number}: {pr.title} by {pr.user.login} (Branch: {pr.head.ref})"
            for pr in pull_requests
        ]

        selected_pr_display = select_option(
            f"Select a Pull Request to review for {repo_owner}/{repo_name}:",
            pr_choices,
        )

        if selected_pr_display is None:
            echo_info("No PR selected. Exiting interactive review.")
            raise typer.Exit()

        # Extract PR number from the selected string
        selected_pr_number = int(selected_pr_display.split(":")[0].replace("#", ""))
        echo_info(f"User selected PR #{selected_pr_number} for review.")

        action_choices = ["1. Do Code Review", "2. Cancel"]
        selected_action = select_option(
            f"What would you like to do with PR #{selected_pr_number}?",
            action_choices,
        )

        if selected_action is None or selected_action == "2. Cancel":
            raise typer.Exit()
        elif selected_action == "1. Do Code Review":
            review_pr(
                ctx=ctx,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pr_number=selected_pr_number,
                github_token=github_token,
            )
        else:
            echo_info(f"Invalid action selected: {selected_action}")
            raise typer.Exit(code=1)

    except ValueError as e:
        echo_info(f"Error: {e}")
        raise typer.Exit(code=1) from e
    except typer.Exit:
        # This is raised when the user quits, no need to log as an error
        pass
    except Exception as e:
        echo_info(f"Error during interactive review: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    load_dotenv()

    try:
        diff_provider = GitHubDiffProvider(
            repo_owner="glamox-lms",
            repo_name="wireless-radio-dart-sdk",
            pr_number=16,
            github_token=environ.get("CODESCOUT_GITHUB_API_KEY", default=""),
        )

        llm_provider = LangChainProvider()

        review_agent = CodeReviewAgent(
            diff_provider=diff_provider,
            llm_provider=llm_provider,
            formatters=[CliFormatter()],
        )

        review_args = ReviewCommandArgs(
            repo_path="",
            source="",
            target="",
            staged=False,
            model="openrouter/anthropic/claude-sonnet-4",
            openrouter_api_key=environ.get("CODESCOUT_OPENROUTER_API_KEY", default=""),
            openai_api_key="",
            claude_api_key="",
        )

        review_agent.review_code(review_args)
        echo_info("Successfully reviewed PR #16.")

    except ValueError as ex1:
        echo_info(f"Error: {ex1}")
        raise typer.Exit(code=1) from ex1
    except Exception as ex2:
        echo_info(f"Error reviewing pull request: {ex2}")
        raise typer.Exit(code=1) from ex2
