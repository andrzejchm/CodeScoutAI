from typing import Any

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel


class LLMWrapper(BaseModel):
    """
    Wrapper class for Language Models that exposes interaction interface
    and model constraints like context length.
    """

    model: BaseLanguageModel
    context_length: int
    model_name: str

    class Config:
        arbitrary_types_allowed = True

    def invoke(self, prompt: str) -> str:
        """
        Invoke the language model with a prompt.
        """
        result = self.model.invoke(prompt)
        if hasattr(result, 'content'):
            content = result.content
            return str(content) if content is not None else ""
        return str(result)

    def get_context_length(self) -> int:
        """
        Get the maximum context length for this model.
        """
        return self.context_length

    def get_model_name(self) -> str:
        """
        Get the name of the model.
        """
        return self.model_name
