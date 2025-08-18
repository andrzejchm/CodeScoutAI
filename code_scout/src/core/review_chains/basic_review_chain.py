import json
import re
from typing import List, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage

from cli.cli_utils import echo_debug
from core.interfaces.review_chain import ReviewChain
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import Category, ReviewFinding, Severity
from core.utils.code_excerpt_extractor import CodeExcerptExtractor


class BasicReviewChain(ReviewChain):
    """
    A basic review chain that sends code diffs to the LLM for review
    and attempts to parse findings from the LLM's response.
    """

    def __init__(
        self,
        config: ReviewConfig,
    ):
        super().__init__(config)

    def get_chain_name(self) -> str:
        return "Basic review"

    def review(
        self,
        diffs: List[CodeDiff],
        llm: BaseLanguageModel,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        file_path_to_diff = {diff.file_path: diff for diff in diffs}

        try:
            response = self._invoke_llm(diffs, llm)
            if response.content:
                findings = self._process_llm_response(response.content, file_path_to_diff)
            else:
                findings.append(self._create_error_finding("LLM returned no content.", Severity.SUGGESTION))
        except Exception as e:
            findings.append(self._create_error_finding(f"Error during LLM invocation: {e}", Severity.CRITICAL))

        return findings

    def _invoke_llm(self, diffs: List[CodeDiff], llm: BaseLanguageModel):
        """Invoke the LLM with the code diffs."""
        all_diff_content = "\n\n".join([f"File: {d.file_path}\nDiff:\n{d.diff}" for d in diffs])
        system_message_content = self._get_system_message()
        human_message_content = f"Please review the following code diffs:\n\n{all_diff_content}"

        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=human_message_content),
        ]

        echo_debug(f"Sending messages to LLM:\nSystem: {system_message_content}\nHuman: {human_message_content}")

        return llm.invoke(messages)

    def _get_system_message(self) -> str:
        """Get the system message for the LLM."""
        severity_values = ", ".join([s.value for s in Severity])
        category_values = ", ".join([c.value for c in Category])

        # ai! n convert it to multiline f""" """ string
        return f"""
            You are an expert code reviewer with deep expertise across multiple
             programming languages, frameworks, and software engineering best practices.
            Your role is to provide high-quality, actionable code review feedback that helps
            developers write better, more secure, and more maintainable code.

            CRITICAL GUIDELINES:
            - QUALITY OVER QUANTITY: Only report findings you are confident about.
             Avoid speculation or uncertain observations.
            - FOCUS ON IMPACT: Prioritize findings that have real security, performance,
             or maintainability implications.
            - BE SPECIFIC: Provide clear, actionable feedback with concrete suggestions
             when possible.
            - AVOID NOISE: Do not report minor style preferences, subjective opinions,
             or issues that are already handled by automated tools.
            - CONTEXT MATTERS: Consider the broader codebase context when making recommendations.

            ANALYSIS SCOPE:
            Analyze the provided code diffs for:
            • Security vulnerabilities (injection attacks, authentication flaws, data exposure)
            • Logic bugs and error handling issues
            • Performance bottlenecks and inefficient algorithms
            • Architecture and design pattern violations
            • Maintainability and readability concerns
            • Best practice violations with significant impact

            OUTPUT FORMAT:
            Your response must be ONLY a valid JSON array. No explanations, no conversational text.
            Each finding must be a JSON object with these fields:
            • 'severity': One of [{severity_values}]
            • 'category': One of [{category_values}]
            • 'file_path': The file path from the diff
            • 'line_number': Specific line number (optional but preferred)
            • 'message': Clear, concise description of the issue
            • 'suggestion': Actionable recommendation to fix the issue (optional)

            SEVERITY GUIDELINES:
            • critical: Security vulnerabilities, data corruption risks, system crashes
            • major: Significant bugs, performance issues, architectural problems
            • minor: Code quality issues with moderate impact
            • suggestion: Improvements that enhance code quality but aren't urgent

            If no significant issues are found, return an empty array: []

            Example response:
            ```json
            [
              {{"severity": "major",
                "category": "security",
                "file_path": "src/auth.py",
                "line_number": 42,
                "message": "SQL query constructed with string concatenation allows injection attacks",
                "suggestion": "Use parameterized queries or an ORM to prevent SQL injection"
              }}
            ]
            ```
        """

    def _process_llm_response(self, content: str, file_path_to_diff: dict) -> List[ReviewFinding]:
        """Process the LLM response and extract findings."""
        findings = []
        json_str = content.strip()

        try:
            json_str = self._extract_json_from_response(json_str)
            parsed_findings_data = json.loads(json_str)

            if isinstance(parsed_findings_data, list):
                findings = self._create_findings_from_data(parsed_findings_data, file_path_to_diff)
            else:
                findings.append(
                    self._create_error_finding(
                        f"LLM response was not a JSON array. Raw response: {content}",
                        Severity.CRITICAL,
                    )
                )
        except json.JSONDecodeError as e:
            findings.append(
                self._create_error_finding(
                    f"LLM response could not be parsed as JSON: {e}. Raw response: {content}",
                    Severity.CRITICAL,
                )
            )
        except Exception as e:
            findings.append(
                self._create_error_finding(
                    f"An unexpected error occurred during LLM response processing: {e}.Raw response: {content}",
                    Severity.CRITICAL,
                )
            )

        return findings

    def _extract_json_from_response(self, json_str: str) -> str:
        """Extract JSON from LLM response, handling various formats."""
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", json_str)
        if json_match:
            return json_match.group(1).strip()
        elif not json_str.startswith("[") and not json_str.endswith("]"):
            return json_str[json_str.find("[") : json_str.rfind("]") + 1]
        return json_str

    def _create_findings_from_data(self, findings_data: list, file_path_to_diff: dict) -> List[ReviewFinding]:
        """Create ReviewFinding objects from parsed JSON data."""
        findings = []
        for finding_data in findings_data:
            try:
                finding = self._create_single_finding(finding_data, file_path_to_diff)
                findings.append(finding)
            except Exception as e:
                findings.append(
                    self._create_error_finding(
                        f"Failed to parse individual finding from LLM: {e}. Raw data: {finding_data}",
                        Severity.CRITICAL,
                    )
                )
        return findings

    def _create_single_finding(self, finding_data: dict, file_path_to_diff: dict) -> ReviewFinding:
        """Create a single ReviewFinding from finding data."""
        file_path = finding_data.get("file_path", "N/A")
        line_number = finding_data.get("line_number")

        # Extract code excerpt if available
        code_excerpt, excerpt_start_line, excerpt_end_line = self._extract_code_excerpt(
            file_path, line_number, file_path_to_diff
        )

        return ReviewFinding(
            severity=Severity(finding_data.get("severity", "suggestion")),
            category=Category(finding_data.get("category", "best_practices")),
            file_path=file_path,
            line_number=line_number,
            message=finding_data.get("message", "No message provided."),
            suggestion=finding_data.get("suggestion"),
            tool_name=self.get_chain_name(),
            code_excerpt=code_excerpt,
            excerpt_start_line=excerpt_start_line,
            excerpt_end_line=excerpt_end_line,
        )

    def _extract_code_excerpt(self, file_path: str, line_number: Optional[int], file_path_to_diff: dict):
        """Extract code excerpt for a finding."""
        if not (file_path in file_path_to_diff and self.config.show_code_excerpts and line_number):
            return None, None, None

        diff_obj = file_path_to_diff[file_path]
        if not diff_obj.current_file_content:
            return None, None, None

        excerpt = CodeExcerptExtractor.extract_with_context(
            file_content=diff_obj.current_file_content,
            line_number=line_number,
            context_lines=self.config.context_lines_before,
            max_excerpt_lines=self.config.max_excerpt_lines,
        )

        if excerpt:
            return excerpt.content, excerpt.start_line, excerpt.end_line
        return None, None, None

    def _create_error_finding(self, message: str, severity: Severity) -> ReviewFinding:
        """Create an error finding."""
        return ReviewFinding(
            file_path="N/A",
            line_number=0,
            severity=severity,
            category=Category.BUG if severity == Severity.CRITICAL else Category.BEST_PRACTICES,
            message=message,
            tool_name=self.get_chain_name(),
        )
