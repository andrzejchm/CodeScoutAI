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
/code-reviewer
/core
    diff_analyzer.py                # Diff and file change detection
    ai_reviewer.py                  # LangChain-powered AI module
    diff_providers/
        git_diff_provider.py        # Interface/abstract class for diff providers (strategy pattern)
        local_git_diff_provider.py      # Local Git diff implementation
        github_diff_provider.py     # GitHub PR diff implementation
        bitbucket_diff_provider.py  # (Planned) Bitbucket diff implementation
    rules_loader.py                 # Parses Markdown best practices
    command_runner.py               # Executes linting/testing commands
    plugin_manager.py               # Plugin system for additional steps
/cli
    main.py                         # CLI entry point (click)
/plugins
    example_plugin.py               # Example plugin for custom checks
/tests
    ...                             # Unit tests
/examples
    best_practices.md               # Sample Markdown rules file
README.md
pyproject.toml                      # Project dependencies
requirements.txt
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

## 📥 Get Started (Coming Soon)

```bash
git clone https://github.com/yourusername/ai-code-reviewer
cd ai-code-reviewer
pip install -r requirements.txt

# Run on local diffs
python cli/main.py --diff HEAD~1 HEAD --rules examples/best_practices.md --run-commands

# Run on GitHub PR
python cli/main.py --github-pr owner/repo/123 --rules examples/best_practices.md --run-commands
```
