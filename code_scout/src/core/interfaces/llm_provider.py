from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLanguageModel

from core.models.review_command_args import ReviewCommandArgs


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    Defines the interface for any class that provides a Language Model instance.
    """

    @abstractmethod
    def get_llm(
        self,
        args: ReviewCommandArgs,
    ) -> BaseLanguageModel:
        """
        Retrieves a Language Model instance based on the provided model string and API keys.
        """
        pass
