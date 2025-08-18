import time
from typing import List, Optional

from langchain_core.language_models import BaseLanguageModel

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.llm_provider import LLMProvider
from core.interfaces.review_chain import ReviewChain
from core.interfaces.review_formatter import ReviewFormatter
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import ReviewFinding
from core.models.review_result import ReviewResult
from core.review_chains.basic_review_chain import BasicReviewChain
from src.cli.cli_utils import echo_info, show_spinner
from src.cli.code_scout_context import CodeScoutContext


class CodeReviewAgent:
    """
    Comprehensive code review agent with pluggable architecture.
    Orchestrates the entire review pipeline with configurable components.
    """

    def __init__(
        self,
        diff_provider: DiffProvider,
        llm_provider: LLMProvider,
        formatters: List[ReviewFormatter],
        cli_context: CodeScoutContext,
        config: Optional[ReviewConfig] = None,
    ):
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider
        self.formatters = formatters
        self.cli_context = cli_context
        self.config = config or ReviewConfig()

        self.llm: BaseLanguageModel = self.llm_provider.get_llm(self.cli_context)

        self.review_chains: List[ReviewChain] = [BasicReviewChain(config=self.config)]

    def review_code(self) -> ReviewResult:
        """
        Executes the code review process.

        Returns:
            ReviewResult: The aggregated results of the code review.
        """
        start_time = time.time()

        with show_spinner(label="Initializing code diffs..."):
            diffs: List[CodeDiff] = self.diff_provider.get_diff()

        if not diffs:
            echo_info("No code differences found to review.")
            return ReviewResult.aggregate([])

        echo_info(f"\nTotal changes: {len(diffs)} files modified.")

        all_findings = self._execute_review_chains(diffs)

        end_time = time.time()
        duration = end_time - start_time

        result = ReviewResult.aggregate(all_findings)
        result.review_duration = duration
        result.total_files_reviewed = len({d.file_path for d in diffs})

        self._output_results(result)

        return result

    def _execute_review_chains(
        self,
        diffs: List[CodeDiff],
    ) -> List[ReviewFinding]:
        """Execute all enabled review chains."""
        all_findings = []
        for chain in self.review_chains:
            try:
                with show_spinner(label=f"Running {chain.get_chain_name()}..."):
                    findings = chain.review(diffs, self.llm)
                all_findings.extend(findings)
                echo_info(f"Completed review: {chain.get_chain_name()}")
            except Exception as e:
                echo_info(f"Warning: Chain {chain.get_chain_name()} failed: {e}")
        return all_findings

    def _output_results(self, result: ReviewResult):
        """Format and output the review results."""
        found_formatter = False
        for formatter in self.formatters:
            output = formatter.format(result)
            echo_info(output)
            found_formatter = True
            break
        if not found_formatter:
            echo_info(f"Review completed: {len(result.findings)} findings")
