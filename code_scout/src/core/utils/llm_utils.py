"""Utility functions for working with LangChain LLM responses and models."""

from typing import Any

from langchain_core.language_models import BaseLanguageModel


def get_model_info(llm: BaseLanguageModel[Any]) -> dict[str, str]:
    """Extract model metadata from LangChain model instance."""
    return {
        "name": getattr(llm, "model_name", getattr(llm, "model", "unknown")),
        "provider": llm.__class__.__name__,
        "class": llm.__class__.__module__ + "." + llm.__class__.__name__,
    }
