"""
score_engine.py — Aggregates analyzer results into a final AuditReport.

Responsibilities:
  1. Run all 6 analyzers against the RepoData.
  2. Sum category scores into total_score (0–100).
  3. Compute resume_impact_score using the weighted formula.
  4. Attach human-readable labels to scores.
  5. Pass populated report to the Recommender.

Design:
  - Factory Method: ScoreEngine.audit() is the single entry point that
    assembles the complete AuditReport from multiple analyzer strategies.
  - All weights are imported from constants — no magic numbers here.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from analyzers.cicd_analyzer import CICDAnalyzer
from analyzers.docker_analyzer import DockerAnalyzer
from analyzers.documentation_analyzer import DocumentationAnalyzer
from analyzers.readme_analyzer import ReadmeAnalyzer
from analyzers.structure_analyzer import StructureAnalyzer
from analyzers.testing_analyzer import TestingAnalyzer
from models.audit_report import AuditReport, RepoData
from recommendations.recommender import Recommender
from utils.constants import (
    MAX_CICD_SCORE,
    MAX_DOCKER_SCORE,
    MAX_DOCUMENTATION_SCORE,
    MAX_README_SCORE,
    MAX_STRUCTURE_SCORE,
    MAX_TESTING_SCORE,
    OVERALL_SCORE_LABELS,
    RESUME_IMPACT_LABELS,
    RESUME_IMPACT_WEIGHTS,
)

logger = logging.getLogger(__name__)


class ScoreEngine:
    """
    Orchestrates the analyzer pipeline and produces a final AuditReport.

    Usage:
        engine = ScoreEngine()
        report = engine.audit(repo_data)
    """

    def __init__(self) -> None:
        self._readme_analyzer = ReadmeAnalyzer()
        self._structure_analyzer = StructureAnalyzer()
        self._testing_analyzer = TestingAnalyzer()
        self._docker_analyzer = DockerAnalyzer()
        self._cicd_analyzer = CICDAnalyzer()
        self._documentation_analyzer = DocumentationAnalyzer()
        self._recommender = Recommender()

    def audit(self, repo_data: RepoData, repo_url: str) -> AuditReport:
        """
        Run the full analyzer pipeline and return a complete AuditReport.

        Args:
            repo_data: Populated RepoData from GitHubService.
            repo_url:  Original URL as submitted by the user.

        Returns:
            AuditReport with all scores, labels, and recommendations.
        """
        logger.info(f"Starting audit for: {repo_data.metadata.full_name}")

        # ── Run all analyzers ──────────────────────────────────────────────
        readme_result = self._readme_analyzer.analyze(repo_data)
        structure_result = self._structure_analyzer.analyze(repo_data)
        testing_result = self._testing_analyzer.analyze(repo_data)
        docker_result = self._docker_analyzer.analyze(repo_data)
        cicd_result = self._cicd_analyzer.analyze(repo_data)
        documentation_result = self._documentation_analyzer.analyze(repo_data)

        # ── Aggregate total score ─────────────────────────────────────────
        total_score = (
            readme_result.score
            + structure_result.score
            + testing_result.score
            + docker_result.score
            + cicd_result.score
            + documentation_result.score
        )

        # ── Compute Resume Impact Score ───────────────────────────────────
        resume_impact_score = self._compute_resume_impact(
            readme=readme_result.score,
            structure=structure_result.score,
            testing=testing_result.score,
            docker=docker_result.score,
            cicd=cicd_result.score,
            documentation=documentation_result.score,
        )

        # ── Resolve labels ────────────────────────────────────────────────
        overall_label, overall_color = self._get_label(total_score, OVERALL_SCORE_LABELS)
        resume_label, resume_emoji, resume_color = self._get_resume_label(resume_impact_score)

        # ── Assemble report skeleton ──────────────────────────────────────
        report = AuditReport(
            repo_url=repo_url,
            audited_at=datetime.now(timezone.utc).isoformat(),
            metadata=repo_data.metadata,
            readme=readme_result,
            structure=structure_result,
            testing=testing_result,
            docker=docker_result,
            cicd=cicd_result,
            documentation=documentation_result,
            total_score=total_score,
            resume_impact_score=resume_impact_score,
            overall_label=overall_label,
            resume_label=resume_label,
            resume_emoji=resume_emoji,
            resume_color=resume_color,
        )

        # ── Generate recommendations ──────────────────────────────────────
        report.recommendations = self._recommender.generate(report)

        logger.info(
            f"Audit complete: total={total_score}/100, "
            f"resume_impact={resume_impact_score}/100, "
            f"recommendations={len(report.recommendations)}"
        )

        return report

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_resume_impact(
        readme: int,
        structure: int,
        testing: int,
        docker: int,
        cicd: int,
        documentation: int,
    ) -> int:
        """
        Compute the Resume Impact Score using weighted normalization.

        Each category is normalized to a 0–1 scale before weighting,
        ensuring that categories with different max points are comparable.

        Formula:
            raw = Σ (weight × (score / max_score))
            resume_impact = round(raw × 100)
        """
        weights = RESUME_IMPACT_WEIGHTS
        raw = (
            weights["readme"]        * (readme        / MAX_README_SCORE)
            + weights["structure"]   * (structure      / MAX_STRUCTURE_SCORE)
            + weights["testing"]     * (testing        / MAX_TESTING_SCORE)
            + weights["docker"]      * (docker         / MAX_DOCKER_SCORE)
            + weights["cicd"]        * (cicd           / MAX_CICD_SCORE)
            + weights["documentation"] * (documentation / MAX_DOCUMENTATION_SCORE)
        )
        return round(raw * 100)

    @staticmethod
    def _get_label(score: int, label_map: dict) -> tuple[str, str]:
        """Resolve a score to its (label, color) from a range-keyed dict."""
        for (low, high), (label, color) in label_map.items():
            if low <= score < high:
                return label, color
        return "Unknown", "#888888"

    @staticmethod
    def _get_resume_label(score: int) -> tuple[str, str, str]:
        """Resolve a resume impact score to its (label, emoji, color)."""
        for (low, high), (label, emoji, color) in RESUME_IMPACT_LABELS.items():
            if low <= score < high:
                return label, emoji, color
        return "Unknown", "❓", "#888888"
