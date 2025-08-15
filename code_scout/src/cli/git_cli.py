import typer

from cli.cli_context import CliContext
from cli.cli_formatter import CliFormatter
from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.services.code_review_agent import CodeReviewAgent
from src.cli.cli_utils import cli_option

app = typer.Typer(
    no_args_is_help=True,
    help="Commands for reviewing local Git repositories.",
)


@app.command()
def review(
    ctx: typer.Context,
    repo_path: str = cli_option(
        env_var_name="CODESCOUT_REPO_PATH",
        prompt_message="Enter path to the Git repository",
        required=True,
        help="Path to the Git repository",
    ),
    source: str = cli_option(
        env_var_name="CODESCOUT_SOURCE",
        help="Source branch, commit, or tag to compare from (e.g., 'main', 'HEAD~1')",
    ),
    target: str = cli_option(
        env_var_name="CODESCOUT_TARGET",
        help="Target branch, commit, or tag to compare to (e.g., 'HEAD')",
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
        cli_context=cli_context,
    )

    review_agent.review_code()
