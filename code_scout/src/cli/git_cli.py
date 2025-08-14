import typer

from cli.cli_context import CliContext
from cli.cli_formatter import CliFormatter
from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.models.review_command_args import ReviewCommandArgs
from core.services.code_review_agent import CodeReviewAgent

app = typer.Typer()


@app.command()
def review(
    ctx: typer.Context,
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
) -> None:
    """
    Reviews code changes in a Git repository.
    """
    # Access common options from ctx.obj with type hinting
    cli_context: CliContext = ctx.obj

    git_diff_provider = GitDiffProvider(
        repo_path=repo_path,
        source=source,
        target=target,
        staged=staged,
    )

    llm_provider = LangChainProvider()

    review_agent = CodeReviewAgent(
        diff_provider=git_diff_provider,
        llm_provider=llm_provider,
        formatters=[CliFormatter()],
    )

    review_agent.review_code(
        args=ReviewCommandArgs(
            repo_path=repo_path,
            source=source,
            target=target,
            staged=staged,
            model=cli_context.model,
            openrouter_api_key=cli_context.openrouter_api_key,
            openai_api_key=cli_context.openai_api_key,
            claude_api_key=cli_context.claude_api_key,
        ),
    )
