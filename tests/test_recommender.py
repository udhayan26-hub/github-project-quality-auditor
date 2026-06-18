"""
test_recommender.py — Unit tests for the Recommender engine.
"""

import pytest

from recommendations.recommender import Recommender
from models.audit_report import (
    AuditReport, RepoMetadata,
    ReadmeAnalysisResult, StructureAnalysisResult, TestingAnalysisResult,
    DockerAnalysisResult, CICDAnalysisResult, DocumentationAnalysisResult,
    AnalyzerDetail,
)
from utils.constants import Priority


def _make_report(
    readme_score: int = 20,
    structure_score: int = 20,
    testing_score: int = 20,
    docker_score: int = 10,
    cicd_score: int = 15,
    documentation_score: int = 15,
    readme_details: list | None = None,
    structure_details: list | None = None,
    testing_details: list | None = None,
    docker_details: list | None = None,
    cicd_details: list | None = None,
    doc_details: list | None = None,
    test_file_count: int = 5,
    dockerfile_found: bool = True,
    compose_found: bool = True,
    workflow_files: list | None = None,
    detected_framework: str | None = "pytest",
) -> AuditReport:
    meta = RepoMetadata(
        name="test", full_name="user/test",
        description="Test", html_url="https://github.com/user/test",
        default_branch="main",
    )
    return AuditReport(
        repo_url="https://github.com/user/test",
        metadata=meta,
        readme=ReadmeAnalysisResult(
            score=readme_score, details=readme_details or []
        ),
        structure=StructureAnalysisResult(
            score=structure_score, details=structure_details or []
        ),
        testing=TestingAnalysisResult(
            score=testing_score, details=testing_details or [],
            test_file_count=test_file_count,
            detected_framework=detected_framework,
        ),
        docker=DockerAnalysisResult(
            score=docker_score, details=docker_details or [],
            dockerfile_found=dockerfile_found,
            compose_found=compose_found,
        ),
        cicd=CICDAnalysisResult(
            score=cicd_score, details=cicd_details or [],
            workflow_files=workflow_files or [],
        ),
        documentation=DocumentationAnalysisResult(
            score=documentation_score, details=doc_details or [],
        ),
        total_score=readme_score + structure_score + testing_score + docker_score + cicd_score + documentation_score,
        resume_impact_score=50,
    )


class TestRecommender:

    def setup_method(self):
        self.recommender = Recommender()

    def test_no_readme_generates_critical_rec(self):
        readme_details = [
            AnalyzerDetail(
                check="README exists and is meaningful",
                passed=False,
                points_awarded=0,
                points_possible=4,
            )
        ]
        report = _make_report(readme_score=0, readme_details=readme_details)
        recs = self.recommender.generate(report)
        categories = [r.category for r in recs]
        assert "README" in categories
        critical_recs = [r for r in recs if r.priority == Priority.CRITICAL]
        assert len(critical_recs) > 0

    def test_no_testing_generates_critical_rec(self):
        report = _make_report(testing_score=0, test_file_count=0)
        recs = self.recommender.generate(report)
        testing_recs = [r for r in recs if r.category == "Testing"]
        assert any(r.priority == Priority.CRITICAL for r in testing_recs)

    def test_no_dockerfile_generates_rec(self):
        report = _make_report(docker_score=0, dockerfile_found=False, compose_found=False)
        recs = self.recommender.generate(report)
        docker_recs = [r for r in recs if r.category == "Docker"]
        assert len(docker_recs) > 0

    def test_no_cicd_generates_rec(self):
        report = _make_report(cicd_score=0, workflow_files=[])
        recs = self.recommender.generate(report)
        cicd_recs = [r for r in recs if r.category == "CI/CD"]
        assert len(cicd_recs) > 0

    def test_all_perfect_generates_no_recs(self):
        report = _make_report(
            readme_score=20, structure_score=20, testing_score=20,
            docker_score=10, cicd_score=15, documentation_score=15,
            readme_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=p, points_possible=p)
                for c, p in [
                    ("README exists and is meaningful", 4),
                    ("Has project description / introduction", 3),
                    ("Has installation / setup instructions", 3),
                    ("Has usage examples or demo", 3),
                    ("Has tech stack / built-with section", 2),
                    ("Has screenshots, badges, or visual assets", 3),
                    ("Has contribution guide", 2),
                ]
            ],
            structure_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=4, points_possible=4)
                for c in [
                    "Has dedicated source code folder (src/, app/, etc.)",
                    "Has dedicated tests folder (tests/, test/, spec/)",
                    "Has dependency manifest (requirements.txt, package.json, etc.)",
                    "Has configuration / environment template (.env.example, config.yml, etc.)",
                    "Has documentation folder (docs/, wiki/, guides/)",
                ]
            ],
            testing_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=5, points_possible=5)
                for c in [
                    "Dedicated tests folder exists",
                    "Test files detected (test_*.py, *.test.js, etc.)",
                    "Testing framework configuration file present",
                    "Substantial test suite (≥3 test files)",
                ]
            ],
            docker_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=p, points_possible=p)
                for c, p in [("Dockerfile present", 5), ("docker-compose.yml present", 3), (".dockerignore present", 2)]
            ],
            cicd_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=5, points_possible=5)
                for c in ["CI/CD configuration directory or file detected",
                           "Workflow/pipeline files present",
                           "Workflow contains CI steps (build, test, lint, deploy)"]
            ],
            doc_details=[
                AnalyzerDetail(check=c, passed=True, points_awarded=p, points_possible=p)
                for c, p in [
                    ("Dedicated documentation folder or GitHub Wiki", 4),
                    ("API documentation or structured docs files present", 4),
                    ("License file present", 3),
                    ("CHANGELOG or release notes present", 2),
                    ("README is detailed (≥150 words, found 200)", 2),
                ]
            ],
            workflow_files=[".github/workflows/ci.yml", ".github/workflows/deploy.yml"],
        )
        recs = self.recommender.generate(report)
        assert len(recs) == 0

    def test_recommendations_sorted_critical_first(self):
        readme_details = [
            AnalyzerDetail(
                check="README exists and is meaningful",
                passed=False, points_awarded=0, points_possible=4,
            )
        ]
        report = _make_report(
            readme_score=0, readme_details=readme_details,
            testing_score=0, test_file_count=0,
            cicd_score=0,
        )
        recs = self.recommender.generate(report)
        priorities = [r.priority for r in recs]
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        for i in range(len(priorities) - 1):
            assert priority_order.get(priorities[i], 99) <= priority_order.get(priorities[i + 1], 99)

    def test_all_recommendations_have_required_fields(self):
        report = _make_report(testing_score=0, test_file_count=0, docker_score=0,
                               dockerfile_found=False, compose_found=False, cicd_score=0)
        recs = self.recommender.generate(report)
        for rec in recs:
            assert rec.category
            assert rec.priority
            assert rec.title
            assert rec.action
            assert rec.recruiter_impact
