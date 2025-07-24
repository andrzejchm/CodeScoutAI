import os
from typing import Optional

import typer
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.interfaces.llm_provider import LLMProvider
from core.models.llm_wrapper import LLMWrapper


class DefaultLLMProvider(LLMProvider):
    """
    Default implementation of ILLMProvider that provides Language Models
    based on the model string and API keys, supporting OpenRouter, OpenAI, and Anthropic.
    """

    def get_llm(
        self,
        model: str,
        openrouter_api_key: Optional[str],
        openai_api_key: Optional[str],
        claude_api_key: Optional[str],
    ) -> LLMWrapper:
        """
        Initializes and returns a Language Model based on the provided model string and API keys.
        """
        if model.startswith("openrouter/"):
            api_key = SecretStr(
                openrouter_api_key or os.getenv("OPENROUTER_API_KEY") or "",
            )
            if not api_key:
                typer.echo(
                    "Error: OpenRouter API key not provided. Use --openrouter-api-key or set "
                    "OPENROUTER_API_KEY environment variable."
                )
                raise typer.Exit(code=1)
            return LLMWrapper(
                model=ChatOpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    model=model.split(sep="/")[1],
                ),
                context_length=8192,  # Common context length for many models
                model_name=model,
            )
        elif model.startswith("openai/"):
            api_key = SecretStr(openai_api_key or os.getenv("OPENAI_API_KEY") or "")
            if not api_key:
                typer.echo(
                    "Error: OpenAI API key not provided. Use --openai-api-key or set "
                    "OPENAI_API_KEY environment variable."
                )
                raise typer.Exit(code=1)
            return LLMWrapper(
                model=ChatOpenAI(api_key=api_key, model=model.split("/")[1]),
                context_length=8192,  # Common context length for many models
                model_name=model,
            )
        elif model.startswith("anthropic/"):
            api_key = SecretStr(claude_api_key or os.getenv("CLAUDE_API_KEY") or "")
            if not api_key:
                typer.echo(
                    "Error: Claude API key not provided. Use --claude-api-key or"
                    " set CLAUDE_API_KEY environment variable."
                )
                raise typer.Exit(code=1)
            return LLMWrapper(
                model=ChatAnthropic(
                    api_key=api_key,
                    model_name=model.split("/")[1],
                    timeout=60,  # Set a reasonable timeout for API calls
                    stop=["\n\n"],  # Stop generation on double newlines
                ),
                context_length=8192,  # Common context length for many models
                model_name=model,
            )
        else:
            typer.echo(
                f"Error: Unknown model '{model}'. Supported models are "
                "'openrouter/{{model-name}}', 'openai/{{model-name}}', 'anthropic/{{model-name}}'."
            )
            raise typer.Exit(code=1)
