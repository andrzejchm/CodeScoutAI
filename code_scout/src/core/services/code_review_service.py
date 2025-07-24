from typing import List

import typer
from langchain_core.language_models import BaseLanguageModel

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.llm_provider import LLMProvider
from core.models.code_diff import CodeDiff
from core.models.review_command_args import ReviewCommandArgs
from core.utils.llm_utils import get_model_info


class CodeReviewService:
    """Service responsible for orchestrating the code review process."""

    def __init__(self, diff_provider: DiffProvider, llm_provider: LLMProvider):
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider

    def review_code(self, args: ReviewCommandArgs) -> None:
        """
        Performs a code review by getting diffs and using an LLM.
        """
        llm: BaseLanguageModel = self.llm_provider.get_llm(
            model=args.model,
            openrouter_api_key=args.openrouter_api_key,
            openai_api_key=args.openai_api_key,
            claude_api_key=args.claude_api_key,
        )

        model_info = get_model_info(llm)
        typer.echo(message=f"Using LLM: {model_info['name']} ({model_info['provider']})")

        diff: List[CodeDiff] = self.diff_provider.get_diff()
        typer.echo(f"Diff between {args.source} and {args.target} in {args.repo_path}:")
        for code_diff in diff:
            # ai first, print the type change, then the file, then the old file
            typer.echo(
                f"Change Type: {code_diff.change_type}\tFile: {code_diff.file_path} \
                \tOld File: {code_diff.old_file_path}",
            )
        typer.echo(f"Total changes: {len(diff)} files modified.")
        
        # TODO: Implement actual LLM-based code review logic here
        # Example: response = llm.invoke("Review this code diff: ...")
        # content = extract_content(response)
