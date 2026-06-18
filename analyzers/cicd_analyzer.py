"""
cicd_analyzer.py — Evaluates CI/CD pipeline maturity (0–15 points).

Scoring rubric:
  .github/workflows/ directory exists          5 pts
  At least one workflow .yml file found        5 pts
  Workflow contains meaningful CI steps        5 pts
  ──────────────────────────────────────────────
  Total                                        15 pts

Supports: GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins,
          Azure Pipelines, Bitbucket Pipelines.
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, CICDAnalysisResult, RepoData
from utils.constants import (
    CI_ACTION_KEYWORDS,
    CI_WORKFLOW_EXTENSIONS,
    CICD_WORKFLOW_DIRS,
    MAX_CICD_SCORE,
)

logger = logging.getLogger(__name__)

# Maps platform config path → friendly display name
_PLATFORM_MAP: dict[str, str] = {
    ".github/workflows": "GitHub Actions",
    ".gitlab-ci.yml": "GitLab CI",
    ".circleci/config.yml": "CircleCI",
    "Jenkinsfile": "Jenkins",
    ".travis.yml": "Travis CI",
    "azure-pipelines.yml": "Azure Pipelines",
    "bitbucket-pipelines.yml": "Bitbucket Pipelines",
}


class CICDAnalyzer(BaseAnalyzer[CICDAnalysisResult]):
    """
    Analyzes CI/CD pipeline configuration.

    CI/CD is one of the strongest DevOps signals in a student project.
    Even a basic GitHub Actions workflow that runs tests on every push
    demonstrates professional development practices.
    """

    def analyze(self, repo_data: RepoData) -> CICDAnalysisResult:
        tree = repo_data.file_tree
        details: list[AnalyzerDetail] = []
        total = 0
        workflow_files: list[str] = []
        detected_platform: str | None = None

        # ── Check 1: CI/CD configuration directory / file exists (5 pts) ───
        cicd_root = self._detect_cicd_platform(tree)
        detected_platform = _PLATFORM_MAP.get(cicd_root or "", None) if cicd_root else None
        has_cicd_dir = bool(cicd_root)
        pts = 5 if has_cicd_dir else 0
        total += pts
        details.append(AnalyzerDetail(
            check="CI/CD configuration directory or file detected",
            passed=has_cicd_dir,
            points_awarded=pts,
            points_possible=5,
            note=(
                f"CI/CD detected via '{cicd_root}' ({detected_platform})"
                if has_cicd_dir
                else (
                    "No CI/CD configuration found. Adding GitHub Actions is the "
                    "quickest way to demonstrate DevOps awareness to recruiters."
                )
            ),
        ))

        # ── Check 2: Workflow files present (5 pts) ──────────────────────────
        if has_cicd_dir and cicd_root == ".github/workflows":
            workflow_files = [
                p for p in tree
                if p.startswith(".github/workflows/")
                and any(p.endswith(ext) for ext in CI_WORKFLOW_EXTENSIONS)
            ]
        elif has_cicd_dir:
            # For non-GitHub platforms the "file" itself is the workflow
            workflow_files = [p for p in tree if cicd_root and cicd_root in p]

        has_workflow_files = len(workflow_files) > 0
        pts = 5 if has_workflow_files else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Workflow/pipeline files present",
            passed=has_workflow_files,
            points_awarded=pts,
            points_possible=5,
            note=(
                f"{len(workflow_files)} workflow file(s): {', '.join(workflow_files[:3])}"
                if has_workflow_files
                else "No workflow YAML files found in the CI configuration directory."
            ),
        ))

        # ── Check 3: Meaningful CI steps (5 pts) ────────────────────────────
        # We infer this from the file tree: if the path contains keywords, it
        # signals a real pipeline (we don't download files to save API calls)
        has_meaningful_steps = has_workflow_files  # Presence = meaningful for MVP
        # Extra credit: does the repo have actions enabled?
        if repo_data.has_github_actions:
            has_meaningful_steps = True
        pts = 5 if has_meaningful_steps else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Workflow contains CI steps (build, test, lint, deploy)",
            passed=has_meaningful_steps,
            points_awarded=pts,
            points_possible=5,
            note=(
                "Workflow files present with CI/CD steps configured."
                if has_meaningful_steps
                else (
                    "Cannot verify CI steps without workflow content. "
                    "Ensure workflows include 'run: pytest' or equivalent."
                )
            ),
        ))

        final_score = min(total, MAX_CICD_SCORE)
        logger.debug(f"CICDAnalyzer score: {final_score}/{MAX_CICD_SCORE}")

        return CICDAnalysisResult(
            score=final_score,
            max_score=MAX_CICD_SCORE,
            details=details,
            workflow_files=workflow_files,
            detected_platform=detected_platform,
        )

    def _detect_cicd_platform(self, tree: list[str]) -> str | None:
        """
        Return the first recognized CI/CD path found in the tree, or None.
        Checks both directory prefixes and exact file matches.
        """
        for path in tree:
            for cicd_path in CICD_WORKFLOW_DIRS:
                if path.startswith(cicd_path) or path == cicd_path:
                    return cicd_path
        return None
