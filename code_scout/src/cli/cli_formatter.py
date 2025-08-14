import typer

from core.interfaces.review_formatter import ReviewFormatter
from core.models.review_finding import Severity
from core.models.review_result import ReviewResult


class CliFormatter(ReviewFormatter):
    """
    A formatter for displaying review results in the command line interface.
    """

    def format(self, result: ReviewResult) -> str:
        """
        Formats the review result into a human-readable string for CLI output.
        """
        output = [
            typer.style(
                "--- Code Review Results ---",
                fg=typer.colors.BRIGHT_BLUE,
                bold=True,
            ),
            "\nTotal Files Reviewed: "
            f"{typer.style(str(result.total_files_reviewed), fg=typer.colors.CYAN)}",
            "\nTotal Lines Reviewed: ",
            typer.style(
                str(result.total_lines_reviewed),
                fg=typer.colors.CYAN,
            ),
            "\nReview Duration: ",
            f"{typer.style(f'{result.review_duration:.2f}', fg=typer.colors.CYAN)} seconds",
            typer.style("\n\n--- Summary ---", fg=typer.colors.BRIGHT_BLUE, bold=True),
            typer.style("\nSeverity:", fg=typer.colors.BLUE, bold=True),
        ]

        for severity, count in result.summary.severity.items():
            color = self._get_severity_color(severity)
            output.append(
                f"\n  - {typer.style(severity.value.capitalize(), fg=color)}: "
                f"{typer.style(str(count), fg=typer.colors.CYAN)}",
            )

        output.append(typer.style("\nCategory:", fg=typer.colors.BLUE, bold=True))
        for category, count in result.summary.category.items():
            output.append(
                f"\n  - {typer.style(category.value.capitalize(), fg=typer.colors.GREEN)}: "
                f"{typer.style(str(count), fg=typer.colors.CYAN)}",
            )

        if result.findings:
            output.append(
                typer.style(
                    "\n\n--- Findings ---",
                    fg=typer.colors.BRIGHT_BLUE,
                    bold=True,
                ),
            )
            for i, finding in enumerate(result.findings):
                output.append(
                    typer.style(
                        f"\n\nFinding {i + 1}:",
                        fg=typer.colors.BRIGHT_YELLOW,
                        bold=True,
                    ),
                )
                output.append("\n  File: ")
                output.append(
                    typer.style(
                        finding.file_path,
                        fg=typer.colors.BRIGHT_WHITE,
                    )
                )
                if finding.line_number:
                    output.append(":")
                    output.append(
                        typer.style(
                            str(finding.line_number),
                            fg=typer.colors.BRIGHT_WHITE,
                        )
                    )
                if finding.line_range:
                    output.append(":")
                    output.append(
                        typer.style(
                            f"{finding.line_range[0]}-{finding.line_range[1]}",
                            fg=typer.colors.BRIGHT_WHITE,
                        )
                    )

                severity_color = self._get_severity_color(finding.severity)
                output.append("\n  Severity: ")
                output.append(
                    typer.style(
                        finding.severity.value.capitalize(),
                        fg=severity_color,
                        bold=True,
                    ),
                )
                output.append(f"\n  Category: {finding.category.value.capitalize()}")
                output.append(
                    f"\n  Message: {typer.style(finding.message, fg=typer.colors.WHITE)}",
                )
                if finding.suggestion:
                    output.append(
                        f"\n  Suggestion: {typer.style(finding.suggestion, fg=typer.colors.YELLOW)}",
                    )
                if finding.code_example:
                    output.append(
                        typer.style(
                            "\n  Code Example:",
                            fg=typer.colors.BLUE,
                        )
                    )
                    output.append(
                        typer.style(
                            f"```\n{finding.code_example}\n```",
                            fg=typer.colors.BRIGHT_BLACK,
                        ),
                    )
                if finding.tool_name:
                    output.append(
                        typer.style(f"Tool: {finding.tool_name}", fg=typer.colors.BRIGHT_BLACK),
                    )
        else:
            output.append(
                typer.style(
                    "\nNo findings to report. Great job!", fg=typer.colors.GREEN, bold=True
                ),
            )

        output.append("\n==========================================\n\n")
        return "".join(output)

    @staticmethod
    def _get_severity_color(severity: Severity) -> str:
        """
        Helper to get color based on severity.
        """
        if severity == Severity.CRITICAL:
            return typer.colors.RED
        elif severity == Severity.MAJOR:
            return typer.colors.YELLOW
        elif severity == Severity.MINOR:
            return typer.colors.GREEN
        elif severity == Severity.SUGGESTION:
            return typer.colors.BLUE

    def get_formatter_name(self) -> str:
        """
        Returns the name of this formatter.
        """
        return "cli_formatter"
