from typing import override

import typer

from core.interfaces.review_formatter import ReviewFormatter
from core.models.review_finding import ReviewFinding, Severity
from core.models.review_result import ReviewResult


class CliFormatter(ReviewFormatter):
    """
    A formatter for displaying review results in the command line interface.
    """

    @override
    def format(self, result: ReviewResult) -> str:
        """
        Formats the review result into a human-readable string for CLI output.
        """
        output: list[str] = []
        output.extend(self._format_header(result))
        output.extend(self._format_summary(result))
        output.extend(self._format_findings(result))
        output.extend(self._format_usage_metadata(result))
        output.append("\n==========================================\n\n")
        return "".join(output)

    def _format_header(self, result: ReviewResult) -> list[str]:
        """Formats the header section of the review results."""
        return [
            typer.style(
                "--- Code Review Results ---",
                fg=typer.colors.BRIGHT_BLUE,
                bold=True,
            ),
            f"\nTotal Files Reviewed: {typer.style(str(result.total_files_reviewed), fg=typer.colors.CYAN)}",
            f"\nTotal Lines Reviewed: {typer.style(str(result.total_lines_reviewed), fg=typer.colors.CYAN)}",
            f"\nReview Duration: {typer.style(f'{result.review_duration:.2f}', fg=typer.colors.CYAN)} seconds",
        ]

    def _format_summary(self, result: ReviewResult) -> list[str]:
        """Formats the summary section of the review results."""
        output = [
            typer.style("\n\n--- Summary ---", fg=typer.colors.BRIGHT_BLUE, bold=True),
            typer.style("\nSeverity:", fg=typer.colors.BLUE, bold=True),
        ]

        for severity, count in result.summary.severity.items():
            color = self._get_severity_color(severity)
            output.append(
                (
                    f"\n  - {typer.style(severity.value.capitalize(), fg=color)}: "
                    f"{typer.style(str(count), fg=typer.colors.CYAN)}"
                )
            )

        output.append(typer.style("\nCategory:", fg=typer.colors.BLUE, bold=True))
        for category, count in result.summary.category.items():
            output.append(
                (
                    f"\n  - {typer.style(category.value.capitalize(), fg=typer.colors.GREEN)}: "
                    f"{typer.style(str(count), fg=typer.colors.CYAN)}"
                )
            )
        return output

    def _format_findings(self, result: ReviewResult) -> list[str]:
        """Formats the findings section of the review results."""
        output: list[str] = []
        if result.findings:
            output.append(
                typer.style(
                    "\n\n--- Findings ---",
                    fg=typer.colors.BRIGHT_BLUE,
                    bold=True,
                ),
            )
            for i, finding in enumerate(result.findings):
                output.extend(self._format_single_finding(i, finding))
        else:
            output.append(
                typer.style("\nNo findings to report. Great job!", fg=typer.colors.GREEN, bold=True),
            )
        return output

    def _format_single_finding(self, index: int, finding: ReviewFinding) -> list[str]:
        """Formats a single review finding."""
        output = [
            typer.style(
                f"\n\nFinding {index + 1}:",
                fg=typer.colors.BRIGHT_YELLOW,
                bold=True,
            ),
            "\n  File: ",
            typer.style(
                finding.file_path,
                fg=typer.colors.BRIGHT_WHITE,
            ),
        ]

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
            suggestion_text = typer.style(finding.suggestion, fg=typer.colors.YELLOW)
            output.append(f"\n  Suggestion: {suggestion_text}")
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

        # Display code excerpt with context if available
        if finding.code_excerpt:
            output.append(
                typer.style(
                    "\n  Code Context:",
                    fg=typer.colors.BLUE,
                    bold=True,
                )
            )
            output.append(self._format_code_excerpt(finding))
        if finding.tool_name:
            output.append(
                typer.style(f"\nTool: {finding.tool_name}", fg=typer.colors.BRIGHT_BLACK),
            )
        return output

    def _format_usage_metadata(self, result: ReviewResult) -> list[str]:
        """Formats the usage metadata section of the review results."""
        output: list[str] = []
        usage_metadata = result.usage_metadata
        if usage_metadata:
            output.append(typer.style("\n\n--- Usage Metadata ---", fg=typer.colors.BRIGHT_BLUE, bold=True))
            output.append(
                f"\nInput Tokens: {typer.style(str(usage_metadata.get('input_tokens')), fg=typer.colors.CYAN)}"
            )
            output.append(
                f"\nOutput Tokens: {typer.style(str(usage_metadata.get('output_tokens')), fg=typer.colors.CYAN)}"
            )
            output.append(
                f"\nTotal Tokens: {typer.style(str(usage_metadata.get('total_tokens')), fg=typer.colors.CYAN)}"
            )

            input_token_details = usage_metadata.get("input_token_details")
            if input_token_details:
                output.append(typer.style("\nInput Token Details:", fg=typer.colors.BLUE, bold=True))
                output.append(f"{input_token_details}")

            output_token_details = usage_metadata.get("output_token_details")
            if output_token_details:
                output.append(typer.style("\nOutput Token Details:", fg=typer.colors.BLUE, bold=True))
                for key, value in output_token_details.items():
                    output.append(
                        f"\n  {key.replace('_', ' ').title()}: {typer.style(str(value), fg=typer.colors.CYAN)}"
                    )
        return output

    def _format_code_excerpt(self, finding: ReviewFinding) -> str:
        """
        Format code excerpt with line numbers and highlighting.
        """
        if not finding.code_excerpt or not finding.excerpt_start_line:
            return ""

        lines = finding.code_excerpt.split("\n")
        formatted_lines: list[str] = [
            typer.style(
                "\n  ┌─────────────────────────────────────────",
                fg=typer.colors.BRIGHT_BLACK,
            )
        ]

        # Add top border

        current_line = finding.excerpt_start_line
        for line in lines:
            # Determine if this is the target line
            is_target_line = (finding.line_number and current_line == finding.line_number) or (
                finding.line_range and finding.line_range[0] <= current_line <= finding.line_range[1]
            )

            # Format line number with padding
            line_num_str = f"{current_line:>3}"

            if is_target_line:
                # Highlight the target line
                formatted_line = typer.style(
                    f"  │ >{line_num_str} | {line}",
                    fg=typer.colors.BRIGHT_YELLOW,
                    bold=True,
                )
            else:
                # Regular context line
                formatted_line = typer.style(
                    f"  │  {line_num_str} | {line}",
                    fg=typer.colors.WHITE,
                )

            formatted_lines.append(formatted_line)
            current_line += 1

        # Add bottom border
        formatted_lines.append(
            typer.style(
                "  └─────────────────────────────────────────",
                fg=typer.colors.BRIGHT_BLACK,
            )
        )

        return "\n".join(formatted_lines)

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

    @override
    def get_formatter_name(self) -> str:
        """
        Returns the name of this formatter.
        """
        return "cli_formatter"
