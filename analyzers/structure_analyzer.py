"""
structure_analyzer.py — Evaluates project structure quality (0–20 points).

Scoring rubric:
  Source code folder (src/, app/, etc.)      4 pts
  Tests folder (tests/, test/, etc.)         4 pts
  Dependency file (requirements.txt, etc.)   4 pts
  Config / environment file (.env.example)   4 pts
  Documentation folder (docs/, wiki/)        4 pts
  ──────────────────────────────────────────────
  Total                                      20 pts
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, RepoData, StructureAnalysisResult
from utils.constants import (
    CONFIG_FILES,
    DEPENDENCY_FILES,
    DOCS_FOLDERS,
    MAX_STRUCTURE_SCORE,
    SRC_FOLDERS,
    TEST_FOLDERS,
)

logger = logging.getLogger(__name__)


class StructureAnalyzer(BaseAnalyzer[StructureAnalysisResult]):
    """
    Analyzes the project file/folder structure for industry-standard patterns.
    Language-agnostic: detects Python, Node, Java, Go, and other ecosystems.
    """

    def analyze(self, repo_data: RepoData) -> StructureAnalysisResult:
        tree = repo_data.file_tree
        details: list[AnalyzerDetail] = []
        total = 0

        # ── Check 1: Source code folder (4 pts) ────────────────────────────
        src_folder = self.any_folder_exists(tree, SRC_FOLDERS)
        pts = 4 if src_folder else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has dedicated source code folder (src/, app/, etc.)",
            passed=bool(src_folder),
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Source folder detected: '{src_folder}'"
                if src_folder
                else (
                    "No dedicated source folder found. Professional projects separate "
                    "source code from config, tests, and docs."
                )
            ),
        ))

        # ── Check 2: Tests folder (4 pts) ───────────────────────────────────
        test_folder = self.any_folder_exists(tree, TEST_FOLDERS)
        pts = 4 if test_folder else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has dedicated tests folder (tests/, test/, spec/)",
            passed=bool(test_folder),
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Tests folder detected: '{test_folder}'"
                if test_folder
                else (
                    "No tests folder found. Absence of a tests directory implies "
                    "no automated testing — a significant concern for recruiters."
                )
            ),
        ))

        # ── Check 3: Dependency file (4 pts) ───────────────────────────────
        dep_file = self.any_file_exists(tree, DEPENDENCY_FILES)
        pts = 4 if dep_file else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has dependency manifest (requirements.txt, package.json, etc.)",
            passed=bool(dep_file),
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Dependency file detected: '{dep_file}'"
                if dep_file
                else (
                    "No dependency file found. Without it, the project cannot be "
                    "installed or run by anyone else."
                )
            ),
        ))

        # ── Check 4: Config / environment file (4 pts) ─────────────────────
        config_file = self.any_file_exists(tree, CONFIG_FILES)
        pts = 4 if config_file else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has configuration / environment template (.env.example, config.yml, etc.)",
            passed=bool(config_file),
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Config file detected: '{config_file}'"
                if config_file
                else (
                    "No config or environment template found. "
                    "Projects often fail to run because secrets are not documented."
                )
            ),
        ))

        # ── Check 5: Documentation folder (4 pts) ──────────────────────────
        docs_folder = self.any_folder_exists(tree, DOCS_FOLDERS)
        pts = 4 if docs_folder else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has documentation folder (docs/, wiki/, guides/)",
            passed=bool(docs_folder),
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Documentation folder detected: '{docs_folder}'"
                if docs_folder
                else (
                    "No dedicated docs folder. Well-documented projects stand out "
                    "significantly in portfolio reviews."
                )
            ),
        ))

        final_score = min(total, MAX_STRUCTURE_SCORE)
        logger.debug(f"StructureAnalyzer score: {final_score}/{MAX_STRUCTURE_SCORE}")

        return StructureAnalysisResult(
            score=final_score,
            max_score=MAX_STRUCTURE_SCORE,
            details=details,
            detected_src_folder=src_folder,
            detected_test_folder=test_folder,
            detected_dependency_file=dep_file,
        )
