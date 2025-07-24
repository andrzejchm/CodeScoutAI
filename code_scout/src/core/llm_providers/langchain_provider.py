"""LangChain-based LLM provider implementation."""

import os
from typing import Optional

import typer
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.interfaces.llm_provider import LLMProvider


class LangChainProvider(LLMProvider):
    """LLM provider that uses LangChain models directly."""

    def get_llm(
        self,
        model: str,
        openrouter_api_key: Optional[str],
        openai_api_key: Optional[str],
        claude_api_key: Optional[str],
    ) -> BaseLanguageModel:
        """Creates and returns a LangChain Language Model."""
        if model.startswith("openrouter/"):
            api_key = SecretStr(
                openrouter_api_key or os.getenv("OPENROUTER_API_KEY") or "",
            )
            if not api_key.get_secret_value():
                typer.echo(
                    "Error: OpenRouter API key not provided. Use --openrouter-api-key or set "
                    "OPENROUTER_API_KEY environment variable."
                )
                raise typer.Exit(code=1)

            return ChatOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                model=model.split(sep="/")[1],
            )

        elif model.startswith("openai/"):
            api_key = SecretStr(openai_api_key or os.getenv("OPENAI_API_KEY") or "")
            if not api_key.get_secret_value():
                typer.echo(
                    "Error: OpenAI API key not provided. Use --openai-api-key or set "
                    "OPENAI_API_KEY environment variable."
                )
                raise typer.Exit(code=1)

            return ChatOpenAI(
                api_key=api_key,
                model=model.split("/")[1],
            )

        elif model.startswith("anthropic/"):
            api_key = SecretStr(claude_api_key or os.getenv("CLAUDE_API_KEY") or "")
            if not api_key.get_secret_value():
                typer.echo(
                    "Error: Claude API key not provided. Use --claude-api-key or"
                    " set CLAUDE_API_KEY environment variable."
                )
                raise typer.Exit(code=1)

            return ChatAnthropic(
                api_key=api_key,
                model_name=model.split("/")[1],
                timeout=60,  # Set a reasonable timeout for API calls
                stop=["\n\n"],  # Stop generation on double newlines
            )

        else:
            typer.echo(
                f"Error: Unknown model '{model}'. Supported models are "
                "'openrouter/{{model-name}}', 'openai/{{model-name}}', 'anthropic/{{model-name}}'."
            )
            raise typer.Exit(code=1)
