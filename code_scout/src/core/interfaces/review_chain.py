from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.language_models import BaseLanguageModel

from core.interfaces.llm_provider import LLMProvider
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import ReviewFinding


class ReviewChain(ABC):
    """Abstract base class for review chain components."""

    def __init__(self, llm_provider: LLMProvider, config: ReviewConfig):
        self.llm_provider = llm_provider
        self.config = config

    @abstractmethod
    def review(
        self,
        diffs: List[CodeDiff],
        llm: BaseLanguageModel,
    ) -> List[ReviewFinding]:
        """Execute the review chain and return findings."""
        pass

    @abstractmethod
    def get_chain_name(self) -> str:
        """Return the name of this review chain."""
        pass

    def is_enabled(self) -> bool:
        """Check if this chain is enabled in the configuration."""
        return True  # Override in subclasses
