"""
documentation_analyzer.py — Evaluates documentation quality (0–15 points).

Scoring rubric:
  Dedicated docs folder or wiki enabled      4 pts
  API documentation file present             4 pts
  Has license file                           3 pts
  Multiple code file types (polyglot signal) 2 pts
  README length signals depth                2 pts
  ──────────────────────────────────────────────
  Total                                      15 pts
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, DocumentationAnalysisResult, RepoData
from utils.constants import (
    API_DOC_FILES,
    DOCS_FOLDERS,
    MAX_DOCUMENTATION_SCORE,
    MIN_README_LENGTH,
)

logger = logging.getLogger(__name__)

_LICENSE_FILES = [
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "LICENCE", "LICENCE.md", "LICENCE.txt",
]

_CHANGELOG_FILES = [
    "CHANGELOG.md", "CHANGELOG.txt", "CHANGELOG",
    "CHANGES.md", "HISTORY.md",
]


class DocumentationAnalyzer(BaseAnalyzer[DocumentationAnalysisResult]):
    """
    Analyzes overall documentation quality beyond just the README.

    Looks for dedicated docs folders, API documentation, license files,
    and other indicators that the developer treats documentation as a
    first-class citizen.
    """

    def analyze(self, repo_data: RepoData) -> DocumentationAnalysisResult:
        tree = repo_data.file_tree
        readme = repo_data.readme_content
        metadata = repo_data.metadata
        details: list[AnalyzerDetail] = []
        total = 0

        # ── Check 1: Docs folder or wiki (4 pts) ────────────────────────────
        docs_folder = self.any_folder_exists(tree, DOCS_FOLDERS)
        has_wiki = metadata.has_wiki
        has_docs = bool(docs_folder) or has_wiki
        pts = 4 if has_docs else 0
        total += pts
        source = f"'{docs_folder}'" if docs_folder else "GitHub Wiki enabled"
        details.append(AnalyzerDetail(
            check="Dedicated documentation folder or GitHub Wiki",
            passed=has_docs,
            points_awarded=pts,
            points_possible=4,
            note=(
                f"Documentation source: {source}"
                if has_docs
                else (
                    "No docs folder or wiki found. A docs/ folder with architecture "
                    "decisions, API references, or design docs signals engineering maturity."
                )
            ),
        ))

        # ── Check 2: API documentation file (4 pts) ─────────────────────────
        api_doc = self.any_file_exists(tree, API_DOC_FILES)
        # Also check for .md files inside a docs folder
        has_markdown_docs = any(
            p.startswith("docs/") and p.endswith(".md")
            for p in tree
        )
        has_api_docs = bool(api_doc) or has_markdown_docs
        pts = 4 if has_api_docs else 0
        total += pts
        details.append(AnalyzerDetail(
            check="API documentation or structured docs files present",
            passed=has_api_docs,
            points_awarded=pts,
            points_possible=4,
            note=(
                f"API/documentation file found: '{api_doc or 'docs/*.md'}'"
                if has_api_docs
                else (
                    "No API documentation found. openapi.yml or docs/api.md "
                    "dramatically improves project professionalism."
                )
            ),
        ))

        # ── Check 3: License file (3 pts) ───────────────────────────────────
        license_file = self.any_file_exists(tree, _LICENSE_FILES)
        has_license = bool(license_file) or bool(metadata.license_name)
        pts = 3 if has_license else 0
        total += pts
        details.append(AnalyzerDetail(
            check="License file present",
            passed=has_license,
            points_awarded=pts,
            points_possible=3,
            note=(
                f"License: {metadata.license_name or license_file}"
                if has_license
                else (
                    "No license file found. A LICENSE file is required for any "
                    "project intended for open-source or portfolio use."
                )
            ),
        ))

        # ── Check 4: Changelog or release notes (2 pts) ─────────────────────
        changelog = self.any_file_exists(tree, _CHANGELOG_FILES)
        pts = 2 if changelog else 0
        total += pts
        details.append(AnalyzerDetail(
            check="CHANGELOG or release notes present",
            passed=bool(changelog),
            points_awarded=pts,
            points_possible=2,
            note=(
                f"Changelog found: '{changelog}'"
                if changelog
                else (
                    "No CHANGELOG found. A changelog signals that the project "
                    "evolves with documented version history."
                )
            ),
        ))

        # ── Check 5: In-depth README (2 pts) ────────────────────────────────
        readme_word_count = len(readme.split()) if readme else 0
        is_detailed_readme = readme_word_count >= 150
        pts = 2 if is_detailed_readme else (1 if readme_word_count >= 50 else 0)
        total += pts
        details.append(AnalyzerDetail(
            check=f"README is detailed (≥150 words, found {readme_word_count})",
            passed=is_detailed_readme,
            points_awarded=pts,
            points_possible=2,
            note=(
                f"README has {readme_word_count} words — comprehensive documentation."
                if is_detailed_readme
                else (
                    f"README has only {readme_word_count} words. "
                    "Expand it with architecture diagrams, API examples, and design decisions."
                )
            ),
        ))

        final_score = min(total, MAX_DOCUMENTATION_SCORE)
        logger.debug(f"DocumentationAnalyzer score: {final_score}/{MAX_DOCUMENTATION_SCORE}")

        return DocumentationAnalysisResult(
            score=final_score,
            max_score=MAX_DOCUMENTATION_SCORE,
            details=details,
        )
