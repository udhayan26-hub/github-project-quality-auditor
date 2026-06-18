"""
audit_report.py — Pydantic v2 data contracts for the GitHub Project Quality Auditor.

Design note: Every piece of data that flows between layers is typed here.
Analyzers populate sub-models; ScoreEngine assembles the final AuditReport.
Using Pydantic ensures:
  - Runtime type validation
  - Clear inter-layer contracts
  - JSON serialisability (for future API / export features)
  - Auto-generated schema documentation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Sub-models — raw data from GitHub API
# ---------------------------------------------------------------------------

class RepoMetadata(BaseModel):
    """Raw repository metadata fetched from the GitHub API."""

    name: str
    full_name: str
    description: str | None
    html_url: str
    default_branch: str
    language: str | None = None
    languages: dict[str, int] = Field(default_factory=dict)
    topics: list[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    commit_count: int = 0
    size_kb: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    is_fork: bool = False
    has_wiki: bool = False
    has_issues: bool = False
    license_name: str | None = None


class RepoData(BaseModel):
    """
    Aggregated raw data passed to the analyzer pipeline.
    This is the single object that all analyzers receive.
    """

    metadata: RepoMetadata
    readme_content: str = ""          # decoded README text (empty if absent)
    file_tree: list[str] = Field(default_factory=list)  # full recursive path list
    readme_exists: bool = False
    has_github_actions: bool = False


# ---------------------------------------------------------------------------
# Sub-models — per-analyzer detailed results
# ---------------------------------------------------------------------------

class AnalyzerDetail(BaseModel):
    """Generic per-check result used inside each analyzer result."""

    check: str
    passed: bool
    points_awarded: int
    points_possible: int
    note: str = ""


class ReadmeAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 20
    details: list[AnalyzerDetail] = Field(default_factory=list)


class StructureAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 20
    details: list[AnalyzerDetail] = Field(default_factory=list)
    detected_src_folder: str | None = None
    detected_test_folder: str | None = None
    detected_dependency_file: str | None = None


class TestingAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 20
    details: list[AnalyzerDetail] = Field(default_factory=list)
    test_file_count: int = 0
    detected_framework: str | None = None


class DockerAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 10
    details: list[AnalyzerDetail] = Field(default_factory=list)
    dockerfile_found: bool = False
    compose_found: bool = False


class CICDAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 15
    details: list[AnalyzerDetail] = Field(default_factory=list)
    workflow_files: list[str] = Field(default_factory=list)
    detected_platform: str | None = None


class DocumentationAnalysisResult(BaseModel):
    score: int = 0
    max_score: int = 15
    details: list[AnalyzerDetail] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Recommendation model
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    """A single actionable recommendation with recruiter context."""

    category: str          # e.g. "Testing", "Docker"
    priority: str          # from constants.Priority
    title: str             # short imperative title
    action: str            # what to do
    recruiter_impact: str  # why recruiters care
    code_hint: str = ""    # optional code/command snippet


# ---------------------------------------------------------------------------
# Master audit report
# ---------------------------------------------------------------------------

class AuditReport(BaseModel):
    """
    The final, fully-populated audit report returned by ScoreEngine.
    This is the single object rendered by the Streamlit UI.
    """

    # Input
    repo_url: str
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Raw data
    metadata: RepoMetadata

    # Per-category scores
    readme: ReadmeAnalysisResult = Field(default_factory=ReadmeAnalysisResult)
    structure: StructureAnalysisResult = Field(default_factory=StructureAnalysisResult)
    testing: TestingAnalysisResult = Field(default_factory=TestingAnalysisResult)
    docker: DockerAnalysisResult = Field(default_factory=DockerAnalysisResult)
    cicd: CICDAnalysisResult = Field(default_factory=CICDAnalysisResult)
    documentation: DocumentationAnalysisResult = Field(default_factory=DocumentationAnalysisResult)

    # Aggregated scores
    total_score: int = 0        # 0–100
    resume_impact_score: int = 0  # 0–100

    # Recommendations
    recommendations: list[Recommendation] = Field(default_factory=list)

    # Derived labels (populated by ScoreEngine)
    overall_label: str = ""
    resume_label: str = ""
    resume_emoji: str = ""
    resume_color: str = ""

    def to_markdown(self) -> str:
        """Serialize the audit report to a human-readable Markdown string."""
        lines: list[str] = [
            f"# GitHub Project Audit Report",
            f"",
            f"**Repository**: {self.metadata.full_name}",
            f"**URL**: {self.repo_url}",
            f"**Audited At**: {self.audited_at}",
            f"",
            f"---",
            f"",
            f"## Overall Score: {self.total_score}/100 — {self.overall_label}",
            f"## Resume Impact Score: {self.resume_impact_score}/100 — {self.resume_label}",
            f"",
            f"---",
            f"",
            f"## Score Breakdown",
            f"",
            f"| Category | Score | Max |",
            f"|---|---|---|",
            f"| README Quality | {self.readme.score} | {self.readme.max_score} |",
            f"| Project Structure | {self.structure.score} | {self.structure.max_score} |",
            f"| Testing | {self.testing.score} | {self.testing.max_score} |",
            f"| Docker | {self.docker.score} | {self.docker.max_score} |",
            f"| CI/CD | {self.cicd.score} | {self.cicd.max_score} |",
            f"| Documentation | {self.documentation.score} | {self.documentation.max_score} |",
            f"",
            f"---",
            f"",
            f"## Recommendations",
            f"",
        ]
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"### {i}. [{rec.priority}] {rec.title}")
            lines.append(f"**Action**: {rec.action}")
            lines.append(f"**Recruiter Impact**: {rec.recruiter_impact}")
            if rec.code_hint:
                lines.append(f"```\n{rec.code_hint}\n```")
            lines.append("")

        return "\n".join(lines)
