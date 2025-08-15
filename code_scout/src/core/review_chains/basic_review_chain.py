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
                findings.append(
                    self._create_error_finding("LLM returned no content.", Severity.SUGGESTION)
                )
        except Exception as e:
            findings.append(
                self._create_error_finding(f"Error during LLM invocation: {e}", Severity.CRITICAL)
            )

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

        echo_debug(
            f"Sending messages to LLM:\nSystem: {system_message_content}"
            f"\nHuman: {human_message_content}"
        )

        return llm.invoke(messages)

    def _get_system_message(self) -> str:
        """Get the system message for the LLM."""
        return (
            "You are an expert code reviewer. Analyze the provided code diffs "
            "and identify potential issues, bugs, security vulnerabilities, "
            "performance bottlenecks, or areas for improvement. "
            "Provide your findings in a clear and concise JSON array format. "
            "Each finding should be an object with 'severity', 'category', 'file_path', "
            "Your *only* response must be a JSON array. Do not include any other text, "
            "explanations, or conversational elements outside the JSON."
            "'line_number' (optional), 'message', and 'suggestion' (optional) fields. "
            "Use the following enums for severity: critical, major, minor, suggestion. "
            "Use the following enums for category: bug, security, performance, style, "
            "architecture, best_practices, maintainability, readability. "
            "If no issues are found, return an empty JSON array: [].\n\n"
            "Example of a single finding:\n"
            "```json\n"
            "[\n"
            "  {\n"
            '    "severity": "major",\n'
            '    "category": "security",\n'
            '    "file_path": "src/main.py",\n'
            '    "line_number": 15,\n'
            '    "message": "Potential SQL injection vulnerability.",\n'
            '    "suggestion": "Use parameterized queries."\n'
            "  }\n"
            "]\n"
            "```"
        )

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
                    (
                        f"An unexpected error occurred during LLM response processing: {e}."
                        f"Raw response: {content}"
                    ),
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

    def _create_findings_from_data(
        self, findings_data: list, file_path_to_diff: dict
    ) -> List[ReviewFinding]:
        """Create ReviewFinding objects from parsed JSON data."""
        findings = []
        for finding_data in findings_data:
            try:
                finding = self._create_single_finding(finding_data, file_path_to_diff)
                findings.append(finding)
            except Exception as e:
                findings.append(
                    self._create_error_finding(
                        (
                            f"Failed to parse individual finding from LLM: {e}."
                            f" Raw data: {finding_data}"
                        ),
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

    def _extract_code_excerpt(
        self, file_path: str, line_number: Optional[int], file_path_to_diff: dict
    ):
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
