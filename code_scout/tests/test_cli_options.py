import os
from collections.abc import Generator
from typing import Any

import pytest
import typer
from click.testing import Result
from typer.testing import CliRunner

from cli.cli_options import code_paths_option, file_extensions_option


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, Any, None]:
    """Fixture to clean up environment variables before each test."""
    yield
    if "CODESCOUT_INDEX_CODE_PATHS" in os.environ:
        del os.environ["CODESCOUT_INDEX_CODE_PATHS"]
    if "CODESCOUT_INDEX_FILE_EXTENSIONS" in os.environ:
        del os.environ["CODESCOUT_INDEX_FILE_EXTENSIONS"]


def _assert_success(result: Result) -> None:
    """Asserts that the Typer command executed successfully, printing output on failure."""
    if result.exit_code != 0:
        print(f"\nSTDOUT:\n{result.stdout}")
        print(f"\nSTDERR:\n{result.stderr}")
    assert result.exit_code == 0


def test_code_paths_option_from_env_multiple() -> None:
    """Test code_paths_option with multiple paths from environment variable."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        code_paths: list[str] = code_paths_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {' --- '.join(code_paths)}")

    runner = CliRunner()
    result = runner.invoke(app, [], env={"CODESCOUT_INDEX_CODE_PATHS": "/path/to/repo1,/path/to/repo2"})
    _assert_success(result)
    assert "Code Paths: /path/to/repo1 --- /path/to/repo2" in result.stdout


def test_code_paths_option_from_env_single() -> None:
    """Test code_paths_option with a single path from environment variable."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        code_paths: list[str] = code_paths_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {','.join(code_paths)}")

    runner = CliRunner()
    result = runner.invoke(app, [], env={"CODESCOUT_INDEX_CODE_PATHS": "/path/to/single_repo"})
    _assert_success(result)
    assert "Code Paths: /path/to/single_repo" in result.stdout


def test_code_paths_option_from_cli_multiple() -> None:
    """Test code_paths_option with multiple paths from CLI arguments."""
    app = typer.Typer()

    def test_command(
        code_paths: list[str] = code_paths_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {','.join(code_paths)}")

    _ = app.command()(test_command)

    runner = CliRunner()
    result = runner.invoke(app, ["--code-path", "path/a", "-p", "path/b"])
    _assert_success(result)
    assert "Code Paths: path/a,path/b" in result.stdout


def test_code_paths_option_from_cli_single() -> None:
    """Test code_paths_option with a single path from CLI argument."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        code_paths: list[str] = code_paths_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {','.join(code_paths)}")

    runner = CliRunner()
    result = runner.invoke(app, ["--code-path", "path/c"])
    _assert_success(result)
    assert "Code Paths: path/c" in result.stdout


def test_code_paths_option_no_value_required_true() -> None:
    """Test code_paths_option when no value is provided & it's required."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        code_paths: list[str] = code_paths_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {','.join(code_paths)}")

    runner = CliRunner()
    # Since code_paths_option is defined with required=True, it should prompt or exit
    result = runner.invoke(app, [], input="\n")  # Provide empty input to prompt
    assert result.exit_code == 1
    assert (
        "Error: ['--code-path', '-p'] or CODESCOUT_INDEX_CODE_PATHS env variable is required but was not provided."
        in result.stderr
    )


def test_file_extensions_option_from_env_multiple() -> None:
    """Test file_extensions_option with multiple extensions from environment variable."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(app, [], env={"CODESCOUT_INDEX_FILE_EXTENSIONS": "py,js,ts"})
    _assert_success(result)
    assert "File Extensions: py,js,ts" in result.stdout


def test_file_extensions_option_from_env_single() -> None:
    """Test file_extensions_option with a single extension from environment variable."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(app, [], env={"CODESCOUT_INDEX_FILE_EXTENSIONS": "py"})
    _assert_success(result)
    assert "File Extensions: py" in result.stdout


def test_file_extensions_option_from_cli_multiple() -> None:
    """Test file_extensions_option with multiple extensions from CLI arguments."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(app, ["--file-extensions", "py", "-e", "js"])
    _assert_success(result)
    assert "File Extensions: py,js" in result.stdout


def test_file_extensions_option_from_cli_single() -> None:
    """Test file_extensions_option with a single extension from CLI argument."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(app, ["--file-extensions", "ts"])
    _assert_success(result)
    assert "File Extensions: ts" in result.stdout


def test_file_extensions_option_no_value() -> None:
    """Test file_extensions_option when no value is provided (not required)."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(app, [])
    _assert_success(result)
    assert "File Extensions: " in result.stdout  # Should be empty list


def test_cli_option_precedence_cli_over_env() -> None:
    """Test that CLI arguments take precedence over environment variables."""
    app = typer.Typer()

    @app.command("test")
    def test_command(  # pyright: ignore[reportUnusedFunction]
        code_paths: list[str] = code_paths_option(),  # noqa B008
        file_extensions: list[str] = file_extensions_option(),  # noqa B008
    ) -> None:
        typer.echo(f"Code Paths: {','.join(code_paths)}")
        typer.echo(f"File Extensions: {','.join(file_extensions)}")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--code-path",
            "cli/path1",
            "-e",
            "cli_ext1",
        ],
        env={
            "CODESCOUT_INDEX_CODE_PATHS": "env/path1,env/path2",
            "CODESCOUT_INDEX_FILE_EXTENSIONS": "env_ext1,env_ext2",
        },
    )
    _assert_success(result)
    assert "Code Paths: cli/path1" in result.stdout
    assert "File Extensions: cli_ext1" in result.stdout
