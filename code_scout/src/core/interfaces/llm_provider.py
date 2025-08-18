from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLanguageModel

from src.cli.code_scout_context import CodeScoutContext


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    Defines the interface for any class that provides a Language Model instance.
    """

    @abstractmethod
    def get_llm(
        self,
        code_scout_context: CodeScoutContext,
    ) -> BaseLanguageModel:
        """
        Retrieves a Language Model instance based on the provided model string and API keys.
        """
        pass
