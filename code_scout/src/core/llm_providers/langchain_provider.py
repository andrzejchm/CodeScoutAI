"""LangChain-based LLM provider implementation."""

import os
from typing import Any, override

import typer
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.interfaces.llm_provider import LLMProvider
from src.cli.cli_utils import echo_info, echo_warning
from src.cli.code_scout_context import CodeScoutContext


class LangChainProvider(LLMProvider):
    """LLM provider that uses LangChain models directly."""

    @override
    def get_llm(
        self,
        code_scout_context: CodeScoutContext,
    ) -> BaseLanguageModel[Any]:
        """Creates and returns a LangChain Language Model."""
        self.validate_cli_context(code_scout_context)

        model = code_scout_context.model
        openrouter_api_key = code_scout_context.openrouter_api_key
        openai_api_key = code_scout_context.openai_api_key
        claude_api_key = code_scout_context.claude_api_key

        if model.startswith("openrouter/"):
            api_key = SecretStr(
                openrouter_api_key or os.getenv("OPENROUTER_API_KEY") or "",
            )
            return ChatOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                model=model.replace("openrouter/", ""),
            )

        elif model.startswith("openai/"):
            api_key = SecretStr(openai_api_key or os.getenv("OPENAI_API_KEY") or "")
            return ChatOpenAI(
                api_key=api_key,
                model=model.split("/")[1],
            )

        elif model.startswith("anthropic/"):
            api_key = SecretStr(claude_api_key or os.getenv("CLAUDE_API_KEY") or "")
            return ChatAnthropic(
                api_key=api_key,
                model_name=model.split("/")[1],
                timeout=60,
                stop=["\n\n"],
            )

        else:
            echo_info(
                (
                    f"Error: Unknown model '{model}'. Supported models are "
                    "'openrouter/{{model-name}}', 'openai/{{model-name}}', 'anthropic/{{model-name}}'."
                )
            )
            raise typer.Exit(code=1)

    def validate_cli_context(self, code_scout_context: CodeScoutContext):
        """
        Validates that the necessary API keys are present in the CliContext
        based on the selected model.
        """
        model = code_scout_context.model
        if model.startswith("openrouter/") and not code_scout_context.openrouter_api_key:
            echo_warning(
                (
                    f"Error: OpenRouter API key not provided for model '{model}'. "
                    f"Use --openrouter-api-key or set CODESCOUT_OPENROUTER_API_KEY env variable."
                )
            )
            raise typer.Exit(code=1)
        elif model.startswith("openai/") and not code_scout_context.openai_api_key:
            echo_warning(
                (
                    f"Error: OpenAI API key not provided for model '{model}'. "
                    f"Use --openai-api-key or set CODESCOUT_OPENAI_API_KEY env variable."
                )
            )
            raise typer.Exit(code=1)
        elif model.startswith("anthropic/") and not code_scout_context.claude_api_key:
            echo_warning(
                (
                    f"Error: Claude API key not provided for model '{model}'. "
                    f"Use --claude-api-key or  set CODESCOUT_CLAUDE_API_KEY env variable."
                )
            )
            raise typer.Exit(code=1)
