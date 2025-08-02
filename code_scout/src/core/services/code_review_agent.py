import time
from typing import Dict, List, Optional

import typer
from langchain_core.language_models import BaseLanguageModel

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.llm_provider import LLMProvider
from core.interfaces.review_chain import ReviewChain
from core.interfaces.review_formatter import ReviewFormatter
from core.interfaces.review_tool import ReviewTool
from core.models.code_diff import CodeDiff
from core.models.review_command_args import ReviewCommandArgs
from core.models.review_config import ReviewConfig
from core.models.review_finding import ReviewFinding
from core.models.review_result import ReviewResult
from core.utils.llm_utils import get_model_info


class CodeReviewAgent:
    """
    Comprehensive code review agent with pluggable architecture.
    Orchestrates the entire review pipeline with configurable components.
    """

    def __init__(
        self,
        diff_provider: DiffProvider,
        llm_provider: LLMProvider,
        config: Optional[ReviewConfig] = None,
    ):
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider
        self.config = config or ReviewConfig()

        # Pluggable components
        self._review_chains: List[ReviewChain] = []
        self._formatters: Dict[str, ReviewFormatter] = {}
        self._tools: Dict[str, ReviewTool] = {}

        # Initialize default components
        self._initialize_default_components()

    def _initialize_default_components(self):
        """Initialize default review chains, filters, and formatters."""
        # Register and add default chains (e.g., HolisticReviewChain)
        # Register and add default formatters (e.g., CliFormatter)
        pass

    def add_review_chain(self, chain: ReviewChain) -> "CodeReviewAgent":
        """Add a review chain to the pipeline."""
        self._review_chains.append(chain)
        return self

    def add_formatter(self, name: str, formatter: ReviewFormatter) -> "CodeReviewAgent":
        """Add a formatter for output generation."""
        self._formatters[name] = formatter
        return self

    def add_tool(self, name: str, tool: ReviewTool) -> "CodeReviewAgent":
        """Add an external tool for analysis."""
        self._tools[name] = tool
        return self

    def review_code(self, args: ReviewCommandArgs) -> ReviewResult:
        """
        Execute the complete review pipeline.
        """
        start_time = time.time()

        # 1. Initialize LLM
        llm: BaseLanguageModel = self.llm_provider.get_llm(args=args)
        model_info = get_model_info(llm)
        typer.echo(f"Using LLM: {model_info['name']} ({model_info['provider']}) - {args.model}")

        # 2. Get diffs
        diffs: List[CodeDiff] = self.diff_provider.get_diff()
        typer.echo(f"Diff between {args.source} and {args.target} in {args.repo_path}:")
        typer.echo(f"Total changes: {len(diffs)} files modified.")

        # 3. Execute review chains
        all_findings = self._execute_review_chains(diffs, llm)

        # 4. Aggregate results
        end_time = time.time()
        duration = end_time - start_time

        result = ReviewResult.aggregate(all_findings)
        result.review_duration = duration
        result.total_files_reviewed = len(set(d.file_path for d in diffs))
        # total_lines_reviewed would require more detailed diff parsing

        # 5. Format and display output
        self._output_results(result)

        return result

    def _execute_review_chains(
        self, diffs: List[CodeDiff], llm: BaseLanguageModel
    ) -> List[ReviewFinding]:
        """Execute all enabled review chains."""
        all_findings = []
        for chain in self._review_chains:
            if chain.is_enabled():
                try:
                    findings = chain.review(diffs, llm)
                    all_findings.extend(findings)
                    typer.echo(f"Completed review: {chain.get_chain_name()}")
                except Exception as e:
                    typer.echo(f"Warning: Chain {chain.get_chain_name()} failed: {e}")
        return all_findings

    def _output_results(self, result: ReviewResult):
        """Format and output the review results."""
        formatter_name = self.config.output_format
        if formatter_name in self._formatters:
            formatter = self._formatters[formatter_name]
            output = formatter.format(result)
            typer.echo(output)
        else:
            # Fallback to simple output
            typer.echo(f"Review completed: {len(result.findings)} findings")
