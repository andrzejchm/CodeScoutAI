from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLanguageModel

from src.cli.cli_context import CliContext


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    Defines the interface for any class that provides a Language Model instance.
    """

    @abstractmethod
    def get_llm(
        self,
        cli_context: CliContext,
    ) -> BaseLanguageModel:
        """
        Retrieves a Language Model instance based on the provided model string and API keys.
        """
        pass
