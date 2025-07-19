from typing import List

import typer

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.llm_provider import LLMProvider
from core.models.code_diff import CodeDiff
from core.models.review_command_args import ReviewCommandArgs  # We'll still use this for LLM args


class CodeReviewService:
    """
    Service responsible for orchestrating the code review process.
    It depends on an IDiffProvider to get code differences and an ILLMProvider
    to get the Language Model for review.
    """

    def __init__(self, diff_provider: DiffProvider, llm_provider: LLMProvider):
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider

    def review_code(self, args: ReviewCommandArgs) -> None:
        """
        Performs a code review by getting diffs and using an LLM.
        """
        llm = self.llm_provider.get_llm(
            model=args.model,
            openrouter_api_key=args.openrouter_api_key,
            openai_api_key=args.openai_api_key,
            claude_api_key=args.claude_api_key,
        )

        typer.echo(message=f"Using LLM: {llm.__class__.__name__}")

        diff: List[CodeDiff] = self.diff_provider.get_diff()
        typer.echo(f"Diff between {args.source} and {args.target} in {args.repo_path}:")
        for code_diff in diff:
            typer.echo(f"File: {code_diff.file_path}, Change Type: {code_diff.change_type}")
        typer.echo(f"Total changes: {len(diff)} files modified.")
