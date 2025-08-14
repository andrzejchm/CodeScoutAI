import time
from typing import List, Optional

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
from core.review_chains.basic_review_chain import BasicReviewChain
from core.utils.llm_utils import get_model_info
from src.cli.cli_utils import echo_info


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
        config: Optional[ReviewConfig] = None,
    ):
        self.config = config or ReviewConfig()
        self._tools: List[ReviewTool] = []
        self._review_chains: List[ReviewChain] = [
            BasicReviewChain(
                llm_provider=llm_provider,
                config=self.config,
            ),
        ]
        self.diff_provider = diff_provider
        self.llm_provider = llm_provider

        # Pluggable components

        self._formatters = formatters

        # Initialize default components (if any, though with immutability,
        # these would ideally be passed in)self._initialize_default_components()
        # # This method would likely be removed or its
        #  logic moved to where components are assembled.

    def review_code(self, args: ReviewCommandArgs) -> ReviewResult:
        start_time = time.time()

        # 1. Initialize LLM
        llm: BaseLanguageModel = self.llm_provider.get_llm(args=args)
        model_info = get_model_info(llm)
        echo_info(f"Using LLM: {model_info['name']} ({model_info['provider']}) - {args.model}")

        # 2. Get diffs
        diffs: List[CodeDiff] = self.diff_provider.get_diff()
        echo_info(f"Total changes: {len(diffs)} files modified.")

        # 3. Execute review chains
        all_findings = self._execute_review_chains(diffs, llm)

        # 4. Aggregate results
        end_time = time.time()
        duration = end_time - start_time

        result = ReviewResult.aggregate(all_findings)
        result.review_duration = duration
        result.total_files_reviewed = len({d.file_path for d in diffs})
        # total_lines_reviewed would require more detailed diff parsing

        # 5. Format and display output
        self._output_results(result)

        return result

    def _execute_review_chains(
        self,
        diffs: List[CodeDiff],
        llm: BaseLanguageModel,
    ) -> List[ReviewFinding]:
        """Execute all enabled review chains."""
        all_findings = []
        for chain in self._review_chains:
            try:
                findings = chain.review(diffs, llm)
                all_findings.extend(findings)
                echo_info(f"Completed review: {chain.get_chain_name()}")
            except Exception as e:
                echo_info(f"Warning: Chain {chain.get_chain_name()} failed: {e}")
        return all_findings

    def _output_results(self, result: ReviewResult):
        """Format and output the review results."""
        found_formatter = False
        for formatter in self._formatters:
            output = formatter.format(result)
            echo_info(output)
            found_formatter = True
            break
        if not found_formatter:
            # Fallback to simple output
            echo_info(f"Review completed: {len(result.findings)} findings")
