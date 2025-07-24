"""CLI interface for Code Scout."""

import typer
from dotenv import load_dotenv

from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.default_llm_provider import DefaultLLMProvider
from core.models.review_command_args import ReviewCommandArgs
from core.services.code_review_service import CodeReviewService

app = typer.Typer()


load_dotenv()


@app.command()
def review(  # noqa: PLR0913
    repo_path: str = typer.Argument(
        default="/Users/andrzejchm/Developer/andrzejchm/CodeScoutAI",
        envvar="CODESCOUT_REPO_PATH",
        help="Path to the Git repository",
    ),
    source: str = typer.Option(
        default="HEAD",
        envvar="CODESCOUT_SOURCE",
        help="Source branch or commit",
    ),
    target: str = typer.Option(
        default="HEAD~1",
        envvar="CODESCOUT_TARGET",
        help="Target branch or commit",
    ),
    staged: bool = typer.Option(
        default=False,
        envvar="CODESCOUT_STAGED",
        help="Review only staged files",
    ),
    model: str = typer.Option(
        default="openrouter/anthropic/claude-sonnet-4",
        prompt=True,
        envvar="CODESCOUT_MODEL",
        help="Model to use for code review (e.g., 'openrouter/anthropic/claude-3.7-sonnet')",
    ),
    openrouter_api_key: str = typer.Option(
        default=None,
        envvar="CODESCOUT_OPENROUTER_API_KEY",
        help="API key for OpenRouter (can be set via CODESCOUT_OPENROUTER_API_KEY env variable)",
    ),
    openai_api_key: str = typer.Option(
        default=None,
        envvar="CODESCOUT_OPENAI_API_KEY",
        help="API key for OpenAI (can be set via CODESCOUT_OPENAI_API_KEY env variable)",
    ),
    claude_api_key: str = typer.Option(
        default=None,
        envvar="CODESCOUT_CLAUDE_API_KEY",
        help="API key for Claude (can be set via CODESCOUT_CLAUDE_API_KEY env variable)",
    ),
) -> None:
    """
    Shows the number of lines changed in the diff between two branches or commits.
    """

    git_diff_provider = GitDiffProvider(
        repo_path=repo_path,
        source=source,
        target=target,
        staged=staged,
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
            staged=staged,
            model=model,
            openrouter_api_key=openrouter_api_key,
            openai_api_key=openai_api_key,
            claude_api_key=claude_api_key,
        ),
    )


if __name__ == "__main__":
    app()
