import typer
from questionary import Style, select


def echo_info(message: str):
    """
    Echoes an informational message with grayish color using typer.echo.
    """
    typer.echo(typer.style(message, fg=typer.colors.WHITE))


def select_option(message: str, choices: list) -> str:
    """
    Presents a selection prompt to the user with custom styling.
    """
    custom_style = Style(
        [
            ("qmark", "fg:#673ab7 bold"),
            ("question", "bold"),
            ("selected", "bg:#2ecc71 fg:#ffffff"),
            ("pointer", "fg:#3498db bold"),
            ("highlighted", "bg:#2ecc71 fg:#ffffff"),
            ("answer", "fg:#2ecc71 bold"),
            ("text", "fg:#1a4d73"),
        ]
    )
    return select(
        message,
        choices=choices,
        qmark="?",
        style=custom_style,
    ).ask()
