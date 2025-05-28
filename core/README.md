# Core Module

This module contains the core functionality of the AI Code Reviewer:

- Diff analysis
- AI review capabilities
- Git integration
- Rules processing
- Command execution
- Plugin management

## Components

- `diff_analyzer.py`: Handles parsing and analyzing code diffs
- `ai_reviewer.py`: Integrates with LLMs via LangChain
- `diff_providers/`: Contains different strategies for obtaining diffs
- `rules_loader.py`: Parses Markdown best practices
- `command_runner.py`: Executes linting/testing commands
- `plugin_manager.py`: Manages the plugin system
