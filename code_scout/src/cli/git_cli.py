import typer

from cli.cli_formatter import CliFormatter
from cli.code_scout_context import CodeScoutContext
from core.diff_providers.git_diff_provider import GitDiffProvider
from core.llm_providers.langchain_provider import LangChainProvider
from core.services.code_review_agent import CodeReviewAgent
from src.cli.cli_options import repo_path_option, source_option, staged_option, target_option
from src.cli.cli_utils import handle_cli_exception  # Import the new utility function

app = typer.Typer(
    no_args_is_help=True,
    help="Commands for reviewing local Git repositories.",
)


@app.command()
def review(
    ctx: typer.Context,
    repo_path: str = repo_path_option(),
    source: str = source_option(),
    target: str = target_option(),
    staged: bool = staged_option(),
) -> None:
    """
    Reviews code changes in a Git repository.
    """
    code_scout_context: CodeScoutContext = ctx.obj

    try:
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
            cli_context=code_scout_context,
        )

        review_agent.review_code()
    except Exception as e:
        handle_cli_exception(e, message="Error reviewing Git repository")
