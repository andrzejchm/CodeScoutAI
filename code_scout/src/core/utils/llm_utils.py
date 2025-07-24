"""Utility functions for working with LangChain LLM responses and models."""

from langchain_core.language_models import BaseLanguageModel


def extract_content(response) -> str:
    """Extract content from LangChain response."""
    if hasattr(response, "content"):
        content = response.content
        return str(content) if content is not None else ""
    return str(response)


def get_model_info(llm: BaseLanguageModel) -> dict:
    """Extract model metadata from LangChain model instance."""
    return {
        "name": getattr(llm, "model_name", getattr(llm, "model", "unknown")),
        "provider": llm.__class__.__name__,
        "class": llm.__class__.__module__ + "." + llm.__class__.__name__,
    }
