"""
testing_analyzer.py — Evaluates testing maturity (0–20 points).

Scoring rubric:
  Tests folder exists                        5 pts
  Test files found (≥1 matching pattern)     5 pts
  Testing framework config file              5 pts
  Non-trivial test count (≥3 test files)     5 pts
  ──────────────────────────────────────────────
  Total                                      20 pts
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, RepoData, TestingAnalysisResult
from utils.constants import (
    MAX_TESTING_SCORE,
    MIN_TEST_FUNCTION_COUNT,
    TEST_FILE_PATTERNS,
    TEST_FOLDERS,
    TESTING_CONFIG_FILES,
)

logger = logging.getLogger(__name__)

# Frameworks mapped to their config file indicators
_FRAMEWORK_INDICATORS: dict[str, list[str]] = {
    "pytest": ["pytest.ini", "pyproject.toml", "setup.cfg"],
    "Jest": ["jest.config.js", "jest.config.ts"],
    "JUnit": ["pom.xml", "build.gradle"],
    "Mocha": ["mocha.opts", ".mocharc.yml"],
    "RSpec": ["rspec"],
    "unittest": ["unittest"],
}


class TestingAnalyzer(BaseAnalyzer[TestingAnalysisResult]):
    """
    Analyzes the presence and maturity of automated testing.

    Goes beyond just 'does a tests folder exist' — checks for actual test
    files, testing framework configuration, and sufficient test coverage
    breadth (multiple test files).
    """

    def analyze(self, repo_data: RepoData) -> TestingAnalysisResult:
        tree = repo_data.file_tree
        details: list[AnalyzerDetail] = []
        total = 0

        # ── Check 1: Tests folder exists (5 pts) ───────────────────────────
        test_folder = self.any_folder_exists(tree, TEST_FOLDERS)
        pts = 5 if test_folder else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Dedicated tests folder exists",
            passed=bool(test_folder),
            points_awarded=pts,
            points_possible=5,
            note=(
                f"Tests folder found: '{test_folder}'"
                if test_folder
                else (
                    "No tests folder found. Create a 'tests/' directory to signal "
                    "that automated testing is part of the development workflow."
                )
            ),
        ))

        # ── Check 2: Test files found (5 pts) ──────────────────────────────
        test_file_count = self.count_files_matching(tree, TEST_FILE_PATTERNS)
        has_test_files = test_file_count > 0
        pts = 5 if has_test_files else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Test files detected (test_*.py, *.test.js, etc.)",
            passed=has_test_files,
            points_awarded=pts,
            points_possible=5,
            note=(
                f"{test_file_count} test file(s) detected."
                if has_test_files
                else (
                    "No test files found matching standard naming patterns. "
                    "Add files like test_main.py or app.test.js."
                )
            ),
        ))

        # ── Check 3: Testing framework config (5 pts) ──────────────────────
        config_file = self.any_file_exists(tree, TESTING_CONFIG_FILES)
        detected_framework = self._detect_framework(tree) if config_file else None
        pts = 5 if config_file else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Testing framework configuration file present",
            passed=bool(config_file),
            points_awarded=pts,
            points_possible=5,
            note=(
                f"Testing framework config detected: '{config_file}'"
                + (f" (Framework: {detected_framework})" if detected_framework else "")
                if config_file
                else (
                    "No testing framework config found (pytest.ini, jest.config.js, etc.). "
                    "A config file shows a structured testing setup."
                )
            ),
        ))

        # ── Check 4: Non-trivial test suite (5 pts) ─────────────────────────
        is_substantial = test_file_count >= MIN_TEST_FUNCTION_COUNT
        pts = 5 if is_substantial else (2 if test_file_count > 0 else 0)
        total += pts
        details.append(AnalyzerDetail(
            check=f"Substantial test suite (≥{MIN_TEST_FUNCTION_COUNT} test files)",
            passed=is_substantial,
            points_awarded=pts,
            points_possible=5,
            note=(
                f"Substantial test suite: {test_file_count} test files."
                if is_substantial
                else (
                    f"Only {test_file_count} test file(s) found. "
                    "Expand test coverage to demonstrate thorough quality assurance."
                    if test_file_count > 0
                    else "No test files to evaluate."
                )
            ),
        ))

        final_score = min(total, MAX_TESTING_SCORE)
        logger.debug(f"TestingAnalyzer score: {final_score}/{MAX_TESTING_SCORE}")

        return TestingAnalysisResult(
            score=final_score,
            max_score=MAX_TESTING_SCORE,
            details=details,
            test_file_count=test_file_count,
            detected_framework=detected_framework,
        )

    def _detect_framework(self, tree: list[str]) -> str | None:
        """Infer the testing framework from config file presence."""
        for framework, indicators in _FRAMEWORK_INDICATORS.items():
            if self.any_file_exists(tree, indicators):
                return framework
        return None
