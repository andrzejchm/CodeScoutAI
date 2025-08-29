import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Callable, Never, TypeVar

import typer
from questionary import Choice, Style, select
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.cli_config import cli_config

T = TypeVar("T")

err_console = Console(stderr=True, soft_wrap=True)


def echo_debug(message: str) -> None:
    """
    Echoes a debug message with a grayish color using typer.echo, only if debug mode is enabled.
    """
    if cli_config.is_debug:
        typer.echo(typer.style(f"[DEBUG] {message}", fg=typer.colors.BRIGHT_BLACK))


def echo_info(message: str) -> None:
    """
    Echoes an informational message with grayish color using typer.echo.
    """
    typer.echo(typer.style(message, fg=typer.colors.WHITE))


def echo_warning(message: str) -> None:
    """
    Echoes a warning message with a yellow color using typer.echo.
    """
    typer.echo(typer.style(message, fg=typer.colors.YELLOW))


def echo_error(message: str) -> None:
    """
    Echoes an error message with a red color using typer.echo.
    """
    err_console.print(message)


def select_option(message: str, choices: list[tuple[str, T]]) -> T | None:
    """
    Presents a selection prompt to the user with custom styling.
    Choices are provided as a list of (display_string, value) tuples.
    Returns the selected value.
    """
    custom_style = Style(
        [
            ("qmark", "fg:#673ab7 bold"),
            ("question", "bold"),
            ("selected", "bg:#2ecc71 fg:#000000"),
            ("pointer", "fg:#3498db bold"),
            ("highlighted", "bg:#2ecc71 fg:#000000"),
            ("answer", "fg:#2ecc71 bold"),
            ("text", "fg:#2ecc71"),
        ]
    )
    # questionary's select expects a list of strings or Choice objects.
    # When given (display, value) tuples, it displays 'display' and returns 'value'.
    # To satisfy type checkers, we convert the tuples to Choice objects.
    questionary_choices = [Choice(title=display, value=value) for display, value in choices]
    if not questionary_choices:
        return None

    return select(
        message,
        choices=questionary_choices,
        qmark="?",
        style=custom_style,
    ).ask()


def select_from_paginated_options(
    message: str,
    fetch_page_func: Callable[[int, int], list[tuple[str, T]]],
    per_page: int = 10,
) -> T | None:
    """
    Presents a list of choices to the user with pagination, allowing them to load more.

    Args:
        message: The message to display to the user.
        fetch_page_func: A callable that takes (page_number, per_page) and returns
                         a list of (display_text, value) tuples for that page.
        per_page: The number of items to display per page.

    Returns:
        The value of the selected option, or None if the user cancels.
    """
    page = 0
    all_options_loaded = False
    all_fetched_options: list[tuple[str, Any]] = []

    while True:
        with show_spinner(label=f"Fetching options (page {page + 1})"):
            current_page_options = fetch_page_func(page, per_page)
            all_fetched_options.extend(current_page_options)

        if not current_page_options and page == 0:
            echo_info("No options available.")
            return None
        elif not current_page_options:
            all_options_loaded = True

        # Ensure display_choices can hold both T and "show_more"
        display_choices: list[tuple[str, Any]] = list(current_page_options)

        if not all_options_loaded:
            display_choices.append(("Show more...", "show_more"))

        if not display_choices:
            echo_info("No more options available.")
            return None
        selected_option = select_option(message, display_choices)

        if selected_option == "show_more":
            page += 1
        elif selected_option is None:
            return None
        else:
            return selected_option


@contextmanager
def show_spinner(label: str) -> Generator[None, Any, None]:
    """
    Displays a spinner while a block of code is executing.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task_id = progress.add_task(description=f"{label.strip()}\n", total=None)
        yield
        progress.remove_task(task_id)


def get_option_or_env_var(  # noqa PLR013
    param_decls: list[str],
    option_value: Any | None,
    env_var_name: str,
    prompt_message: str | None = None,
    required: bool = False,
    secure_input: bool = False,
    is_list: bool = False,
) -> Any | None:
    """
    Retrieves a value from a Typer option or an environment variable.
    If the value is missing and `required` is True, it prompts the user for input.

    Args:
        param_decls: The parameter name declared in a Typer option.
        option_value: The value passed via the Typer option.
        env_var_name: The name of the environment variable to check.
        prompt_message: The message to display if prompting the user for input.
        required: If True, the user will be prompted if the value is missing.
                  If False, None is returned if the value is not found.
        secure_input: If True, the user's input will be hidden (e.g., for API keys).
        is_list: If True, the environment variable value will be split by comma.

    Returns:
        The retrieved value, or None if not found and not required.

    Raises:
        typer.Exit: If the value is required but not provided by the user.
    """
    if is_list and isinstance(option_value, list) and len(option_value) > 0:
        return option_value  # pyright: ignore[reportUnknownVariableType]
    if not is_list and option_value:
        return option_value  # pyright: ignore[reportUnknownVariableType]
    env_value = os.getenv(env_var_name)

    if env_value is not None:
        if is_list:
            return [item.strip() for item in env_value.split(",") if item.strip()]
        return env_value

    if required:
        if prompt_message:
            value = typer.prompt(prompt_message, hide_input=secure_input)
            if value:
                if is_list:
                    return [item.strip() for item in value.split(",") if item.strip()]
                return value
            else:
                echo_error(
                    f"Error: {param_decls} or {env_var_name.strip()} env variable is required but was not provided."
                )
                raise typer.Exit(code=1)
        else:
            echo_error(f"Error: {param_decls} or {env_var_name.strip()} env variable is required but was not provided.")
            raise typer.Exit(code=1)
    elif is_list:
        return []
    return None


def cli_option(  # noqa PLR013
    param_decls: list[str],
    env_var_name: str = "",
    prompt_message: str | None = None,
    required: bool = False,
    secure_input: bool = False,
    help: str | None = None,
    default: Any | None = None,
    is_list: bool = False,
) -> Any:
    """
    A custom Typer Option factory that integrates environment variable lookup
    and interactive prompting.

    Args:
        param_decls: List of parameter declaration strings (e.g., ["--name", "-n"]).
        env_var_name: The name of the environment variable to check.
        prompt_message: The message to display if prompting the user for input.
        required: If True, the user will be prompted if the value is missing.
        secure_input: If True, the user's input will be hidden (e.g., for API keys).
        help: The help message for the CLI option.
        default: The default value for the option.
        is_list: If True, the option expects a list of values (e.g., multiple --code-path).

    Returns:
        A typer.Option object configured with the custom callback.
    """

    def callback(value: Any | None) -> Any:
        return get_option_or_env_var(
            param_decls=param_decls,
            option_value=value,
            env_var_name=env_var_name,
            prompt_message=prompt_message,
            required=required,
            secure_input=secure_input,
            is_list=is_list,
        )

    return typer.Option(
        default if default is not None else [] if is_list else None,
        *param_decls,
        callback=callback,
        help=help,
    )


def handle_cli_exception(e: Exception, message: str = "An error occurred") -> Never:
    """
    Handles exceptions in CLI commands, raising the original exception if debug is enabled,
    otherwise exiting gracefully with a warning message, chaining the original exception.
    """
    if cli_config.is_debug:
        raise e  # Re-raises the original exception, preserving its full stack trace
    else:
        echo_error(f"{message}: {e}")
        # Raise a new typer.Exit, but chain the original exception 'e'
        raise typer.Exit(code=1) from e
