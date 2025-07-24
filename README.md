# AI Code Reviewer

A modular, AI-assisted code review tool that integrates with GitHub or works offline. It analyzes pull requests, diffs between branches, or local changes, and generates insightful code review comments by combining AI, best practices, and results from linters, tests, and custom checks.

---

## 🚀 Purpose

Modern codebases are complex, and automated checks like linters and tests only scratch the surface. This project aims to bridge the gap between static analysis and human insight by:

- Providing an **AI-powered code review assistant** that suggests improvements, identifies issues, and enforces best practices.
- Allowing **customizable review criteria** through Markdown-defined best practices.
- Supporting **any language** and codebase by integrating external tools (linters, tests, formatters) via a plugin-style architecture.
- Working both **offline (local Git)** and **online (GitHub)** for maximum flexibility.

---

## ✨ Features / User Stories

✅ Review pull requests on GitHub, adding draft comments automatically.  
✅ Perform code reviews locally by comparing branches or commits (`git diff`).  
✅ Accept list of best practices as a guide for the AI.  
✅ Allow for running plugins augmenting the review process (by running lints, tests etc).
✅ Output review findings to:

- The CLI (with colorized diffs and comments),
- Draft PR comments on GitHub,
- JSON/Markdown files for later processing.

✅ Fully **extensible**:  

- Add new **review steps** as plugins (e.g., security scans, static analysis, formatting checks).
- Add new **AI models** via LangChain integrations (OpenAI, Claude, Ollama, etc.).

---

## 🏗️ Tech Stack

| Component          | Technology                                         |
|--------------------|----------------------------------------------------|
| CLI                | Python, `click`, `rich`                             |
| Git integration    | `GitPython`                                        |
| AI layer           | `LangChain`, OpenAI/Claude/Custom LLMs             |
| Diff parsing       | `unidiff`, `difflib`                               |
| Commands execution | `subprocess` (for lint/test commands)              |
| Output formats     | CLI, GitHub API (via `PyGithub`), JSON/Markdown    |
| Future UI (web)    | React + Tailwind (planned)                         |

---

## 📂 Folder Structure

```
/code_scout                         # Main Python package
    /src
        /core                       # Core functionality
        /cli                        # Command-line interface
        /plugins                    # Plugin system for extensibility
    /tests                          # Unit and integration tests
README.md
Taskfile.yml                        # Task runner configuration
```

---

## 🔌 Extensibility: Plugin Architecture

This project is built with **extensibility in mind**. You can add custom **review steps** as plugins:

- Each plugin is a Python module in the `/plugins` folder.
- A plugin must implement a `run(diff, context) -> findings` function.
- Plugins can:
  - Analyze diffs (e.g., static analysis, security checks),
  - Run external tools (e.g., security scanners),
  - Enrich the AI prompt with additional context.

The core review pipeline:

```

\[Diff] + \[Best Practices] + \[Command Outputs] + \[Plugin Findings] --> AI Reviewer --> Output

````

---

## 🚀 Installation & Usage

This tool uses [Poetry](https://python-poetry.org/) for dependency management and [Typer](https://typer.tiangolo.com/) for building the command-line interface.

### Prerequisites

- Python 3.13 or higher
- Poetry (for dependency management)

### Installation

1. **Install Poetry (if you haven't already):**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone and install the project:**

   ```bash
   git clone <repository-url>
   cd CodeScoutAI/code_scout
   poetry install
   ```

   This installs all dependencies and makes the `codescout` command available within the Poetry virtual environment.

### Running the CLI

You have two options to run the `codescout` command:

#### Option 1: Using Poetry (Recommended)

Run commands through Poetry's virtual environment:

```bash
cd code_scout
poetry run codescout --help
poetry run codescout review --repo-path . --source HEAD~1 --target HEAD
```

#### Option 2: Activate the Virtual Environment

Activate Poetry's virtual environment to run `codescout` directly:

```bash
cd code_scout
poetry shell
codescout --help
codescout review --repo-path . --source HEAD~1 --target HEAD
```

### Basic Usage Examples

```bash
# Show help
poetry run codescout --help

# Review changes between commits
poetry run codescout review --repo-path /path/to/repo --source HEAD~1 --target HEAD

# Review current working directory changes
poetry run codescout review --repo-path . --source HEAD~1 --target HEAD
```

### Configuration

The CLI supports various options for customizing the review process. Use `poetry run codescout review --help` to see all available options including:

- Repository path configuration
- Source and target branch/commit specification
- AI model selection
- API keys (e.g., `CODESCOUT_OPENROUTER_API_KEY`, `CODESCOUT_OPENAI_API_KEY`, `CODESCOUT_CLAUDE_API_KEY`)
- Output format options
