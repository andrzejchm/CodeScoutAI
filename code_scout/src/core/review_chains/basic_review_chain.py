import json
import re
from typing import List

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage

from core.interfaces.llm_provider import LLMProvider
from core.interfaces.review_chain import ReviewChain
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import Category, ReviewFinding, Severity


class BasicReviewChain(ReviewChain):
    """
    A basic review chain that sends code diffs to the LLM for review
    and attempts to parse findings from the LLM's response.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        config: ReviewConfig,
    ):
        super().__init__(llm_provider, config)

    def get_chain_name(self) -> str:
        return "basic_review_chain"

    def review(
        self,
        diffs: List[CodeDiff],
        llm: BaseLanguageModel,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        # For simplicity, join all diffs into a single string.
        # In a real-world scenario, you'd need to manage context windows
        # and potentially split diffs or process them in chunks.
        # This is a placeholder for more sophisticated context management.
        all_diff_content = "\n\n".join([f"File: {d.file_path}\nDiff:\n{d.diff}" for d in diffs])

        system_message_content = (
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

        human_message_content = f"Please review the following code diffs:\n\n{all_diff_content}"

        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=human_message_content),
        ]

        try:
            response = llm.invoke(messages)
            if response.content:
                json_str = response.content.strip()
                try:
                    # Use regex to extract JSON block, handling cases where LLM might add extra text
                    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", json_str)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    elif not json_str.startswith("[") and not json_str.endswith("]"):
                        # If no ```json block, but it's not a direct JSON array,
                        # it might be malformed or contain leading/trailing text.
                        # Attempt to find the first and last bracket.
                        json_str = json_str[json_str.find("[") : json_str.rfind("]") + 1]

                    parsed_findings_data = json.loads(json_str)

                    if isinstance(parsed_findings_data, list):
                        for finding_data in parsed_findings_data:
                            try:
                                # Validate and create ReviewFinding objects
                                finding = ReviewFinding(
                                    severity=Severity(finding_data.get("severity", "suggestion")),
                                    category=Category(
                                        finding_data.get("category", "best_practices")
                                    ),
                                    file_path=finding_data.get("file_path", "N/A"),
                                    line_number=finding_data.get("line_number"),
                                    message=finding_data.get("message", "No message provided."),
                                    suggestion=finding_data.get("suggestion"),
                                    tool_name=self.get_chain_name(),
                                )
                                findings.append(finding)
                            except Exception as e:
                                findings.append(
                                    ReviewFinding(
                                        file_path="N/A",
                                        line_number=0,
                                        severity=Severity.CRITICAL,
                                        category=Category.BUG,
                                        message=(
                                            f"Failed to parse individual finding from LLM: {e}."
                                            f" Raw data: {finding_data}"
                                        ),
                                        tool_name=self.get_chain_name(),
                                    )
                                )
                    else:
                        findings.append(
                            ReviewFinding(
                                file_path="N/A",
                                line_number=0,
                                severity=Severity.CRITICAL,
                                category=Category.BUG,
                                message=(
                                    f"LLM response was not a JSON array. "
                                    f"Raw response: {response.content}"
                                ),
                                tool_name=self.get_chain_name(),
                            )
                        )
                except json.JSONDecodeError as e:
                    findings.append(
                        ReviewFinding(
                            file_path="N/A",
                            line_number=0,
                            severity=Severity.CRITICAL,
                            category=Category.BUG,
                            message=(
                                f"LLM response could not be parsed as JSON:"
                                f" {e}."
                                f" Raw response: {response.content}"
                            ),
                            tool_name=self.get_chain_name(),
                        )
                    )
                except Exception as e:
                    findings.append(
                        ReviewFinding(
                            file_path="N/A",
                            line_number=0,
                            severity=Severity.CRITICAL,
                            category=Category.BUG,
                            message=(
                                f"An unexpected error occurred during LLM"
                                f" response processing: {e}. "
                                f"Raw response: {response.content}"
                            ),
                            tool_name=self.get_chain_name(),
                        )
                    )
            else:
                findings.append(
                    ReviewFinding(
                        file_path="N/A",
                        line_number=0,
                        severity=Severity.SUGGESTION,
                        # Changed from INFO to SUGGESTION
                        category=Category.BEST_PRACTICES,
                        message="LLM returned no content.",
                        tool_name=self.get_chain_name(),
                    )
                )

        except Exception as e:
            findings.append(
                ReviewFinding(
                    file_path="N/A",
                    line_number=0,
                    severity=Severity.CRITICAL,
                    category=Category.BUG,
                    message=f"Error during LLM invocation: {e}",
                    tool_name=self.get_chain_name(),
                )
            )

        return findings
