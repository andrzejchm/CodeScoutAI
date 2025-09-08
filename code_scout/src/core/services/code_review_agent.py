import time
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from core.interfaces.diff_provider import DiffProvider
from core.interfaces.llm_provider import LLMProvider
from core.interfaces.review_formatter import ReviewFormatter
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import ReviewFinding
from core.models.review_result import ReviewResult
from core.review_chains.basic_review_chain import BasicReviewChain
from core.tools.file_content_tool import FileContentTool
from core.tools.search_code_index_tool import SearchCodeIndexTool
from src.cli.cli_utils import echo_error, echo_info, show_spinner
from src.cli.code_scout_context import CodeScoutContext


class CodeReviewAgent:
    """
    Comprehensive code review agent with pluggable architecture.
    Orchestrates the entire review pipeline with configurable components.
    """

    diff_provider: DiffProvider
    llm_provider: LLMProvider
    formatters: list[ReviewFormatter]
    cli_context: CodeScoutContext
    config: ReviewConfig
    llm: BaseLanguageModel[Any]

    def __init__(
        self,
        diff_provider: DiffProvider,
        llm_provider: LLMProvider,
        formatters: list[ReviewFormatter],
        cli_context: CodeScoutContext,
        config: ReviewConfig | None = None,
    ):
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider
        self.formatters = formatters
        self.cli_context = cli_context
        self.config = config or ReviewConfig(
            langchain_tools=[
                FileContentTool(),
                SearchCodeIndexTool(),
            ],
            show_code_excerpts=True,
            context_lines_before=3,
            context_lines_after=3,
            max_excerpt_lines=20,
        )

        self.llm = self.llm_provider.get_llm(self.cli_context)

    def review_code(self) -> ReviewResult | None:
        """
        Executes the code review process.

        Returns:
            ReviewResult: The aggregated results of the code review.
        """
        start_time = time.time()

        with show_spinner(label="Initializing code diffs..."):
            diffs: list[CodeDiff] = self.diff_provider.get_diff()

        if not diffs:
            echo_info("No code differences found to review.")
            return ReviewResult.aggregate([], usage_metadata=None)

        echo_info(f"\nTotal changes: {len(diffs)} files modified.")

        result = self._execute_review_chain(diffs)

        end_time = time.time()
        duration = end_time - start_time
        if result:
            result.review_duration = duration
            result.total_files_reviewed = len({d.file_path for d in diffs})
            self._output_results(result)

        return result

    def _execute_review_chain(
        self,
        diffs: list[CodeDiff],
    ) -> ReviewResult | None:
        """Execute all enabled review chains."""
        chain = BasicReviewChain(config=self.config)
        try:
            with show_spinner(label=f"Running {chain.get_chain_name()}..."):
                review_result = chain.review(diffs, self.llm)
                if review_result and review_result.findings:
                    review_result.findings = self._filter_findings(review_result.findings)
                echo_info(f"Completed review: {chain.get_chain_name()}")
                return review_result

        except Exception as e:
            echo_error(f"Warning: Chain {chain.get_chain_name()} failed: {e}")
            return None  # Explicitly return None on error

    def _output_results(self, result: ReviewResult) -> None:
        """Format and output the review results."""
        found_formatter = False
        for formatter in self.formatters:
            output = formatter.format(result)
            echo_info(output)
            found_formatter = True
            break
        if not found_formatter:
            echo_info(f"Review completed: {len(result.findings)} findings")

    def _filter_findings(self, findings: list[ReviewFinding]) -> list[ReviewFinding]:
        """
        Filters review findings based on configured allowed/banned severities and categories.
        """
        filtered_findings = []
        for finding in findings:
            # Filter by severity
            if self.config.allowed_severities:
                allowed_severities_lower = [s.lower() for s in self.config.allowed_severities]
                if finding.severity.value.lower() not in allowed_severities_lower:
                    continue
            if self.config.banned_severities:
                banned_severities_lower = [s.lower() for s in self.config.banned_severities]
                if finding.severity.value.lower() in banned_severities_lower:
                    continue

            # Filter by category
            if self.config.allowed_categories:
                allowed_categories_lower = [c.lower() for c in self.config.allowed_categories]
                if finding.category.value.lower() not in allowed_categories_lower:
                    continue
            if self.config.banned_categories:
                banned_categories_lower = [c.lower() for c in self.config.banned_categories]
                if finding.category.value.lower() in banned_categories_lower:
                    continue

            filtered_findings.append(finding)
        return filtered_findings
