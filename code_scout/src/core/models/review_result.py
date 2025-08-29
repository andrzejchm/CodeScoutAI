from collections import defaultdict
from typing import Any

from langchain_core.messages.ai import UsageMetadata
from pydantic import BaseModel

from core.models.review_finding import Category, ReviewFinding, Severity


class ReviewSummary(BaseModel):
    severity: dict[Severity, int] = defaultdict(int)
    category: dict[Category, int] = defaultdict(int)


class ReviewResult(BaseModel):
    """Aggregated results of a code review."""

    findings: list[ReviewFinding]
    summary: ReviewSummary
    total_files_reviewed: int
    total_lines_reviewed: int
    review_duration: float  # in seconds
    metadata: dict[str, Any] = {}
    usage_metadata: UsageMetadata | None = None

    @classmethod
    def aggregate(
        cls,
        findings: list[ReviewFinding],
        usage_metadata: UsageMetadata | None,
    ) -> "ReviewResult":
        """
        Aggregates findings, deduplicates, and generates a summary.
        """
        # Simple deduplication for now (can be enhanced later)
        unique_findings: list[ReviewFinding] = []
        seen_findings: set[tuple[str, int | None, str, str, str]] = set()
        for finding in findings:
            finding_tuple = (
                finding.file_path,
                finding.line_number,
                finding.message,
                finding.category.value,
                finding.severity.value,
            )
            if finding_tuple not in seen_findings:
                unique_findings.append(finding)
                seen_findings.add(finding_tuple)

        # Generate summary
        summary_by_severity: dict[Severity, int] = defaultdict(int)
        summary_by_category: dict[Category, int] = defaultdict(int)

        for finding in unique_findings:
            summary_by_severity[finding.severity] += 1
            summary_by_category[finding.category] += 1

        summary = ReviewSummary(
            severity=summary_by_severity,
            category=summary_by_category,
        )

        # Placeholder for actual counts and duration
        total_files = len({f.file_path for f in unique_findings})
        total_lines = 0  # This would require more context from diffs
        duration = 0.0  # This would be calculated during the review process

        return cls(
            findings=unique_findings,
            summary=summary,
            total_files_reviewed=total_files,
            total_lines_reviewed=total_lines,
            review_duration=duration,
            usage_metadata=usage_metadata,
        )
