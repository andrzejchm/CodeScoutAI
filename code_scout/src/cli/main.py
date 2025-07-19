"""CLI interface for Code Scout."""

import typer
from dotenv import load_dotenv

from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.default_llm_provider import DefaultLLMProvider
from core.models.review_command_args import ReviewCommandArgs
from core.services.code_review_service import CodeReviewService

app = typer.Typer()


@app.command()
def review(  # noqa: PLR0913
    repo_path: str = typer.Argument(
        "/Users/andrzejchm/Developer/andrzejchm/CodeScoutAI",
        help="Path to the Git repository",
    ),
    source: str = typer.Option(
        "HEAD",
        help="Source branch or commit",
    ),
    target: str = typer.Option(
        "HEAD~1",
        help="Target branch or commit",
    ),
    model: str = typer.Option(
        "openrouter/anthropic/claude-3.7-sonnet",
        prompt=True,
        help="Model to use for code review (e.g., 'openrouter/anthropic/claude-3.7-sonnet')",
    ),
    openrouter_api_key: str = typer.Option(
        None,
        envvar="OPENROUTER_API_KEY",
        help="API key for OpenRouter (can be set via OPENROUTER_API_KEY environment variable)",
    ),
    openai_api_key: str = typer.Option(
        None,
        envvar="OPENAI_API_KEY",
        help="API key for OpenAI (can be set via OPENAI_API_KEY environment variable)",
    ),
    claude_api_key: str = typer.Option(
        None,
        envvar="CLAUDE_API_KEY",
        help="API key for Claude (can be set via CLAUDE_API_KEY environment variable)",
    ),
) -> None:
    """
    Shows the number of lines changed in the diff between two branches or commits.
    """
    load_dotenv()

    git_diff_provider = GitDiffProvider(
        repo_path=repo_path,
        source=source,
        target=target,
    )

    default_llm_provider = DefaultLLMProvider()

    review_service = CodeReviewService(
        diff_provider=git_diff_provider,
        llm_provider=default_llm_provider,
    )

    review_service.review_code(
        ReviewCommandArgs(
            repo_path=repo_path,
            source=source,
            target=target,
            model=model,
            openrouter_api_key=openrouter_api_key,
            openai_api_key=openai_api_key,
            claude_api_key=claude_api_key,
        ),
    )


if __name__ == "__main__":
    app()
