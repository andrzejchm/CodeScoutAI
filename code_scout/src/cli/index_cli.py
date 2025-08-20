"""CLI commands for managing the code index."""

import json
from pathlib import Path
from typing import Optional

import typer

from core.code_index.code_index_config import CodeIndexConfig
from core.code_index.code_index_manager import CodeIndexManager
from core.code_index.models import CodeIndexQuery
from src.cli.cli_utils import echo_info, echo_warning, handle_cli_exception

app = typer.Typer(
    no_args_is_help=True,
    help="Commands for managing the code index.",
)


def _get_default_db_path() -> str:
    """Get default database path relative to current directory."""
    return "./.codescout/code_index.db"


@app.command("build")
def build_index(
    repo_path: str = typer.Option(".", "--repo-path", help="Path to the repository root"),
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the code index database file"),
) -> None:
    """Build code index for the repository."""
    try:
        db_path = db_path or _get_default_db_path()

        # Ensure .codescout directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        echo_info("Building code index...")
        echo_info(f"Repository: {repo_path}")
        echo_info(f"Database: {db_path}")

        result = manager.build_index(repo_path)

        if result.success:
            echo_info(f"✓ Indexed {result.symbols_indexed} symbols from {result.files_processed} files")
            if result.errors:
                echo_warning(f"⚠ {len(result.errors)} files had parsing errors")
        else:
            echo_warning(f"✗ Failed to build index: {result.message}")

    except Exception as e:
        handle_cli_exception(e, message="Error building code index")


@app.command("update")
def update_file(
    file_path: str = typer.Argument(..., help="Path to the file to update"),
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the code index database file"),
) -> None:
    """Update code index for a specific file."""
    try:
        db_path = db_path or _get_default_db_path()

        if not Path(db_path).exists():
            echo_warning(f"Code index not found at {db_path}")
            echo_info("Run 'codescout index build' to create the index")
            return

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        result = manager.update_file(file_path)

        if result.success:
            if result.symbols_added > 0 or result.symbols_removed > 0:
                echo_info(f"✓ Updated {file_path}: +{result.symbols_added} symbols, -{result.symbols_removed} symbols")
            else:
                echo_info(f"→ No changes detected in {file_path}")
        else:
            echo_warning(f"✗ Failed to update file: {result.message}")

    except Exception as e:
        handle_cli_exception(e, message="Error updating file in code index")


@app.command("rebuild")
def rebuild_index(
    repo_path: str = typer.Option(".", "--repo-path", help="Path to the repository root"),
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the code index database file"),
) -> None:
    """Rebuild the entire code index from scratch."""
    try:
        db_path = db_path or _get_default_db_path()

        # Ensure .codescout directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        echo_info("Rebuilding code index...")
        echo_info(f"Repository: {repo_path}")
        echo_info(f"Database: {db_path}")

        result = manager.rebuild_index(repo_path)

        if result.success:
            echo_info(f"✓ Rebuilt index with {result.symbols_indexed} symbols from {result.files_processed} files")
            if result.errors:
                echo_warning(f"⚠ {len(result.errors)} files had parsing errors")
        else:
            echo_warning(f"✗ Failed to rebuild index: {result.message}")

    except Exception as e:
        handle_cli_exception(e, message="Error rebuilding code index")


@app.command("search")
def search_symbols(
    query: str = typer.Argument(..., help="Search query for symbols"),
    symbol_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by symbol type (function, class, method, variable)"
    ),
    file_pattern: Optional[str] = typer.Option(None, "--file", help="Filter by file path pattern"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
) -> None:
    """Search for code symbols."""
    try:
        db_path = _get_default_db_path()

        if not Path(db_path).exists():
            echo_warning(f"Code index not found at {db_path}")
            echo_info("Run 'codescout index build' to create the index")
            return

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        query_obj = CodeIndexQuery(text=query, symbol_type=symbol_type, file_pattern=file_pattern, limit=20)

        results = manager.search_symbols(query_obj)

        if json_output:
            output = [
                {
                    "id": symbol.id,
                    "name": symbol.name,
                    "symbol_type": symbol.symbol_type,
                    "language": symbol.language,
                    "file_path": symbol.file_path,
                    "line": symbol.line_number,
                    "signature": symbol.signature,
                    "docstring": symbol.docstring,
                    "score": getattr(symbol, "score", 0),
                    "reasons": getattr(symbol, "reasons", []),
                }
                for symbol in results
            ]
            echo_info(json.dumps(output, indent=2))
        else:
            if not results:
                echo_warning("No symbols found matching the query")
                return

            echo_info(f"Found {len(results)} symbols:")
            for symbol in results:
                echo_info(f"  {symbol.symbol_type}: {symbol.name} ({symbol.file_path}:{symbol.line_number})")
                if symbol.signature:
                    echo_info(f"    Signature: {symbol.signature}")
                score = getattr(symbol, "score", None)
                if score is not None:
                    echo_info(f"    Score: {score:.2f}")

    except Exception as e:
        handle_cli_exception(e, message="Error searching code index")


@app.command("stats")
def show_stats(
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the code index database file"),
) -> None:
    """Show code index statistics."""
    try:
        db_path = db_path or _get_default_db_path()

        if not Path(db_path).exists():
            echo_warning(f"Code index not found at {db_path}")
            echo_info("Run 'codescout index build' to create the index")
            return

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        stats = manager.get_index_stats()

        echo_info("Code Index Statistics:")
        echo_info(f"  Database: {db_path}")
        echo_info(f"  Total symbols: {stats.total_symbols}")
        echo_info(f"  Total files: {stats.total_files}")

        # Show languages
        if stats.symbols_by_language:
            languages = list(stats.symbols_by_language.keys())
            echo_info(f"  Languages: {', '.join(languages)}")

        if stats.last_updated:
            echo_info(f"  Last updated: {stats.last_updated}")

        echo_info("\nSymbol types:")
        if stats.symbols_by_type:
            for symbol_type, count in stats.symbols_by_type.items():
                echo_info(f"  {symbol_type}: {count}")
        else:
            echo_info("  No symbols found")

    except Exception as e:
        handle_cli_exception(e, message="Error retrieving code index statistics")


@app.command("types")
def list_symbol_types(
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the code index database file"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
) -> None:
    """List available symbol types in the code index."""
    try:
        db_path = db_path or _get_default_db_path()

        if not Path(db_path).exists():
            echo_warning(f"Code index not found at {db_path}")
            echo_info("Run 'codescout index build' to create the index")
            return

        config = CodeIndexConfig(db_path=db_path)
        manager = CodeIndexManager(config)

        # Get distinct symbol types from the database
        symbol_types = manager.get_symbol_types()

        if json_output:
            print(json.dumps({"symbol_types": symbol_types}, indent=2))
        elif symbol_types:
            echo_info("Available symbol types:")
            for symbol_type in sorted(symbol_types):
                echo_info(f"  {symbol_type}")
        else:
            echo_info("No symbol types found")

    except Exception as e:
        handle_cli_exception(e, message="Error retrieving symbol types")
