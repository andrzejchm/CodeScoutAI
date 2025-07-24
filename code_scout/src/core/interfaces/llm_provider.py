from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.language_models import BaseLanguageModel


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    Defines the interface for any class that provides a Language Model instance.
    """

    @abstractmethod
    def get_llm(
        self,
        model: str,
        openrouter_api_key: Optional[str],
        openai_api_key: Optional[str],
        claude_api_key: Optional[str],
    ) -> BaseLanguageModel:
        """
        Retrieves a Language Model instance based on the provided model string and API keys.
        """
        pass
