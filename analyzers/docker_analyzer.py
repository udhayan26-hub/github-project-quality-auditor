"""
docker_analyzer.py — Evaluates containerization readiness (0–10 points).

Scoring rubric:
  Dockerfile present           5 pts
  docker-compose.yml present   3 pts
  .dockerignore present        2 pts
  ──────────────────────────────────
  Total                        10 pts
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, DockerAnalysisResult, RepoData
from utils.constants import (
    DOCKER_COMPOSE_FILES,
    DOCKER_FILES,
    DOCKER_IGNORE_FILES,
    MAX_DOCKER_SCORE,
)

logger = logging.getLogger(__name__)


class DockerAnalyzer(BaseAnalyzer[DockerAnalysisResult]):
    """
    Analyzes containerization readiness.

    Docker is a strong signal of deployment maturity. Even for student projects,
    including a Dockerfile demonstrates awareness of production environments —
    a differentiator that many recruiters explicitly look for.
    """

    def analyze(self, repo_data: RepoData) -> DockerAnalysisResult:
        tree = repo_data.file_tree
        details: list[AnalyzerDetail] = []
        total = 0

        # ── Check 1: Dockerfile (5 pts) ─────────────────────────────────────
        dockerfile = self.any_file_exists(tree, DOCKER_FILES)
        pts = 5 if dockerfile else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Dockerfile present",
            passed=bool(dockerfile),
            points_awarded=pts,
            points_possible=5,
            note=(
                f"Dockerfile found: '{dockerfile}'"
                if dockerfile
                else (
                    "No Dockerfile found. Adding one shows awareness of containerization "
                    "and deployment — critical for SDE and DevOps roles."
                )
            ),
        ))

        # ── Check 2: docker-compose.yml (3 pts) ─────────────────────────────
        compose_file = self.any_file_exists(tree, DOCKER_COMPOSE_FILES)
        pts = 3 if compose_file else 0
        total += pts
        details.append(AnalyzerDetail(
            check="docker-compose.yml present",
            passed=bool(compose_file),
            points_awarded=pts,
            points_possible=3,
            note=(
                f"Docker Compose file found: '{compose_file}'"
                if compose_file
                else (
                    "No docker-compose.yml found. A compose file demonstrates "
                    "multi-service orchestration knowledge."
                )
            ),
        ))

        # ── Check 3: .dockerignore (2 pts) ──────────────────────────────────
        dockerignore = self.any_file_exists(tree, DOCKER_IGNORE_FILES)
        pts = 2 if dockerignore else 0
        total += pts
        details.append(AnalyzerDetail(
            check=".dockerignore present",
            passed=bool(dockerignore),
            points_awarded=pts,
            points_possible=2,
            note=(
                ".dockerignore found — keeps Docker images lean."
                if dockerignore
                else (
                    "No .dockerignore found. Without it, unnecessary files "
                    "are included in the Docker image, increasing size."
                )
            ),
        ))

        final_score = min(total, MAX_DOCKER_SCORE)
        logger.debug(f"DockerAnalyzer score: {final_score}/{MAX_DOCKER_SCORE}")

        return DockerAnalysisResult(
            score=final_score,
            max_score=MAX_DOCKER_SCORE,
            details=details,
            dockerfile_found=bool(dockerfile),
            compose_found=bool(compose_file),
        )
