"""
test_score_engine.py — Unit tests for ScoreEngine.

Tests scoring math, resume impact formula, and label resolution.
"""

import pytest
from unittest.mock import MagicMock, patch

from scoring.score_engine import ScoreEngine
from models.audit_report import (
    AuditReport, RepoData, RepoMetadata,
    ReadmeAnalysisResult, StructureAnalysisResult, TestingAnalysisResult,
    DockerAnalysisResult, CICDAnalysisResult, DocumentationAnalysisResult,
)


def _make_repo_data() -> RepoData:
    meta = RepoMetadata(
        name="test",
        full_name="user/test",
        description="Test",
        html_url="https://github.com/user/test",
        default_branch="main",
    )
    return RepoData(metadata=meta, file_tree=[], readme_content="", readme_exists=False)


class TestScoreEngine:

    def setup_method(self):
        self.engine = ScoreEngine()

    def test_resume_impact_formula_perfect_score(self):
        score = ScoreEngine._compute_resume_impact(
            readme=20, structure=20, testing=20,
            docker=10, cicd=15, documentation=15
        )
        assert score == 100

    def test_resume_impact_formula_zero_score(self):
        score = ScoreEngine._compute_resume_impact(
            readme=0, structure=0, testing=0,
            docker=0, cicd=0, documentation=0
        )
        assert score == 0

    def test_resume_impact_testing_weighted_heavily(self):
        """Testing has 30% weight — a project with only tests should score 30."""
        score = ScoreEngine._compute_resume_impact(
            readme=0, structure=0, testing=20,
            docker=0, cicd=0, documentation=0
        )
        assert score == 30

    def test_resume_impact_cicd_weighted_second(self):
        """CI/CD has 20% weight."""
        score = ScoreEngine._compute_resume_impact(
            readme=0, structure=0, testing=0,
            docker=0, cicd=15, documentation=0
        )
        assert score == 20

    def test_overall_label_production_ready(self):
        from utils.constants import OVERALL_SCORE_LABELS
        label, _ = ScoreEngine._get_label(90, OVERALL_SCORE_LABELS)
        assert label == "Production Ready"

    def test_overall_label_needs_major_work(self):
        from utils.constants import OVERALL_SCORE_LABELS
        label, _ = ScoreEngine._get_label(15, OVERALL_SCORE_LABELS)
        assert label == "Needs Major Work"

    def test_resume_label_exceptional(self):
        label, emoji, color = ScoreEngine._get_resume_label(95)
        assert label == "Exceptional"
        assert emoji == "🏆"

    def test_resume_label_weak(self):
        label, emoji, color = ScoreEngine._get_resume_label(10)
        assert label == "Weak"
        assert emoji == "❌"

    def test_audit_returns_valid_report(self):
        """Full integration test — audit() should return a complete AuditReport."""
        repo_data = _make_repo_data()
        report = self.engine.audit(repo_data, "https://github.com/user/test")

        assert isinstance(report, AuditReport)
        assert 0 <= report.total_score <= 100
        assert 0 <= report.resume_impact_score <= 100
        assert report.total_score == (
            report.readme.score
            + report.structure.score
            + report.testing.score
            + report.docker.score
            + report.cicd.score
            + report.documentation.score
        )
        assert isinstance(report.recommendations, list)
        assert report.overall_label != ""

    def test_total_score_equals_sum_of_categories(self):
        repo_data = _make_repo_data()
        # Inject a richer file tree
        repo_data.file_tree = [
            "src/app.py", "tests/test_app.py",
            "requirements.txt", "Dockerfile",
            ".github/workflows/ci.yml", "docs/index.md",
        ]
        repo_data.has_github_actions = True
        report = self.engine.audit(repo_data, "https://github.com/user/test")
        expected = (
            report.readme.score + report.structure.score + report.testing.score
            + report.docker.score + report.cicd.score + report.documentation.score
        )
        assert report.total_score == expected
