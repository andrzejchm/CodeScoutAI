import json
import re
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent  # pyright: ignore[reportUnknownVariableType]

from cli.cli_utils import echo_debug
from core.models.code_diff import CodeDiff
from core.models.review_config import ReviewConfig
from core.models.review_finding import Category, ReviewFinding, Severity
from core.models.review_result import ReviewResult
from core.utils.code_excerpt_extractor import CodeExcerptExtractor


class BasicReviewChain:
    """
    A basic review chain that sends structured code diffs to the LLM for review
    and parses findings from the LLM's response.
    """

    def __init__(
        self,
        config: ReviewConfig,
    ):
        self.config: ReviewConfig = config

    def get_chain_name(self) -> str:
        return "Basic review"

    def review(
        self,
        diffs: list[CodeDiff],
        llm: BaseLanguageModel[Any],
    ) -> ReviewResult:
        findings: list[ReviewFinding] = []
        file_path_to_diff: dict[str, CodeDiff] = {diff.file_path: diff for diff in diffs}

        response = self._invoke_llm(diffs, llm)
        if response:
            findings = self._process_llm_response(response, file_path_to_diff)
        else:
            findings.append(self._create_error_finding("LLM returned no content.", Severity.SUGGESTION))
        return ReviewResult.aggregate(
            findings=findings,
            usage_metadata=response.usage_metadata if response else None,
        )

    def _invoke_llm(self, diffs: list[CodeDiff], llm: BaseLanguageModel[Any]) -> AIMessage | None:
        """Invoke the LLM with the structured code diffs using an agent executor."""

        tools = self._get_tools(diffs)
        system_message_content = self._get_system_message()

        agent: CompiledStateGraph = create_react_agent(model=llm, tools=tools)  # pyright: ignore[reportMissingTypeArgument, reportUnknownVariableType]

        echo_debug(f"Executing agent with tools: {[tool.name for tool in tools]}")

        diff_contents = f"{'\n'.join([d.llm_repr for d in diffs])}"
        echo_debug(f"system message:\n{system_message_content}")
        echo_debug("======================================")
        echo_debug(f"\ndiff message:\n{diff_contents}")
        echo_debug("======================================")
        # noinspection PyTypeChecker
        result: dict[str, Any] = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=system_message_content),
                    HumanMessage(content=diff_contents),
                ],
            }
        )

        last_response = self._extract_content_from_result(result)
        echo_debug(f"Agent response: {last_response}")
        return last_response

    def _get_tools(self, diffs: list[CodeDiff]) -> list[BaseTool]:
        tools: list[BaseTool] = []
        for tool_instance in self.config.langchain_tools:
            tool = tool_instance.get_tool(diffs)
            if tool:
                tools.append(tool)
        return tools

    def _extract_content_from_result(self, result: dict[str, Any]) -> AIMessage | None:
        result_messages: list[BaseMessage] | None = result.get("messages")
        if isinstance(result_messages, list) and result_messages:
            last_message = result_messages[-1]
            if isinstance(last_message, AIMessage):
                return last_message
        return None

    def _process_llm_response(
        self,
        response_message: AIMessage,
        file_path_to_diff: dict[str, CodeDiff],
    ) -> list[ReviewFinding]:
        """Process the LLM response and extract findings."""
        findings: list[ReviewFinding] = []
        try:
            json_str = self._extract_json_from_response(response_message.content)
            parsed_findings_data: Any = json.loads(json_str)

            if isinstance(parsed_findings_data, list):
                findings = self._create_findings_from_data(parsed_findings_data, file_path_to_diff)
            else:
                findings.append(self._create_error_finding("LLM response was not a JSON array.", Severity.CRITICAL))
        except json.JSONDecodeError:
            findings.append(
                self._create_error_finding(
                    "LLM response could not be parsed as JSON.", Severity.CRITICAL, f"{response_message}"
                )
            )
        except Exception as e:
            findings.append(
                self._create_error_finding(
                    f"An unexpected error occurred: {e}", Severity.CRITICAL, f"{response_message}"
                )
            )

        return findings

    def _extract_json_from_response(self, content: str | list[str | dict[Any, Any]]) -> str:
        """Extracts a JSON object or array from a string, stripping makrdown code blocks."""
        text = str(content) if isinstance(content, str) else json.dumps(content)
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        # Fallback for responses that might not be in a markdown block
        json_start = text.find("[")
        json_end = text.rfind("]")
        if json_start != -1 and json_end != -1:
            return text[json_start : json_end + 1]
        return text

    def _create_findings_from_data(
        self, findings_data: list[dict[str, Any]], file_path_to_diff: dict[str, CodeDiff]
    ) -> list[ReviewFinding]:
        """Create ReviewFinding objects from parsed JSON data."""
        findings: list[ReviewFinding] = []
        for finding_data in findings_data:
            try:
                finding = self._create_single_finding(finding_data, file_path_to_diff)
                findings.append(finding)
            except Exception as e:
                findings.append(
                    self._create_error_finding(f"Failed to parse a finding: {e}", Severity.CRITICAL, str(finding_data))
                )
        return findings

    def _create_single_finding(
        self, finding_data: dict[str, Any], file_path_to_diff: dict[str, CodeDiff]
    ) -> ReviewFinding:
        """Create a single ReviewFinding from finding data."""
        file_path: str = finding_data.get("file_path", "N/A") or ""
        line_number: int | None = finding_data.get("line_number")

        code_excerpt, start_line, end_line = self._extract_code_excerpt(file_path, line_number, file_path_to_diff)

        return ReviewFinding(
            severity=Severity(finding_data.get("severity", "suggestion")),
            category=Category(finding_data.get("category", "best_practices")),
            file_path=file_path,
            line_number=line_number,
            message=finding_data.get("message", "No message provided.") or "",
            suggestion=finding_data.get("suggestion"),
            tool_name=self.get_chain_name(),
            code_excerpt=code_excerpt,
            excerpt_start_line=start_line,
            excerpt_end_line=end_line,
        )

    def _extract_code_excerpt(self, file_path: str, line_number: int | None, file_path_to_diff: dict[str, CodeDiff]):
        if not (file_path in file_path_to_diff and self.config.show_code_excerpts and line_number):
            return None, None, None

        diff_obj: CodeDiff = file_path_to_diff[file_path]
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

    def _create_error_finding(self, message: str, severity: Severity, raw_content: str = "") -> ReviewFinding:
        """Create an error finding."""
        full_message = f"{message} Raw content: {raw_content}" if raw_content else message
        return ReviewFinding(
            file_path="N/A",
            line_number=0,
            severity=severity,
            category=Category.BUG,
            message=full_message,
            tool_name=self.get_chain_name(),
        )

    def _get_system_message(self) -> str:
        """Get the system message for the LLM, updated for structured diffs."""
        severity_values = ", ".join([s.value for s in Severity])
        category_values = ", ".join([c.value for c in Category])

        return f"""
You are an expert code reviewer. Your role is to provide high-quality, actionable feedback.
Analyze the provided code changes, which are given as a JSON array of file diffs.
Each file diff contains a list of 'hunks', representing a block of changes.
For each hunk, you will see the line numbers and the content of the changes.

CRITICAL GUIDELINES:
- Your response MUST be ONLY a valid JSON array of finding objects.
- Each finding must correlate to a specific hunk.
- For `line_number`, use the `target_line_no` of the first relevant line in the hunk.

OUTPUT FORMAT:
Each finding must be a JSON object with these fields:
- severity: One of [{severity_values}]
- category: One of [{category_values}]
- file_path: The file path from the diff
- line_number: The starting line number of the issue in the new file.
- message: Clear, concise description of the issue.
- suggestion: Actionable recommendation to fix the issue (optional).

Example response:
```json
[
  {{
    "severity": "major",
    "category": "security",
    "file_path": "src/auth.py",
    "line_number": 42,
    "message": "SQL query constructed with string concatenation allows injection attacks.",
    "suggestion": "Use parameterized queries or an ORM to prevent SQL injection."
  }}
]
```
        """
