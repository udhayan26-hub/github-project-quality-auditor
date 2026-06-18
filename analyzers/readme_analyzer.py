"""
readme_analyzer.py — Evaluates README quality (0–20 points).

Scoring rubric:
  README exists              4 pts  — table stakes
  Description / intro        3 pts  — what does the project do?
  Installation section       3 pts  — can I run it?
  Usage / demo section       3 pts  — can I see it in action?
  Tech stack section         2 pts  — what was used?
  Screenshots / badges       3 pts  — visual proof of working product
  Contribution guide         2 pts  — signals open-source maturity
  ─────────────────────────────────
  Total                     20 pts
"""

from __future__ import annotations

import logging

from analyzers.base_analyzer import BaseAnalyzer
from models.audit_report import AnalyzerDetail, RepoData, ReadmeAnalysisResult
from utils.constants import (
    MAX_README_SCORE,
    MIN_README_LENGTH,
    README_CONTRIBUTION_KEYWORDS,
    README_DESCRIPTION_KEYWORDS,
    README_INSTALLATION_KEYWORDS,
    README_SCREENSHOT_PATTERNS,
    README_TECH_STACK_KEYWORDS,
    README_USAGE_KEYWORDS,
)

logger = logging.getLogger(__name__)


class ReadmeAnalyzer(BaseAnalyzer[ReadmeAnalysisResult]):
    """
    Analyzes the quality of a repository's README file.

    Each check produces an AnalyzerDetail with points awarded vs possible,
    making the scoring fully transparent to the UI layer.
    """

    def analyze(self, repo_data: RepoData) -> ReadmeAnalysisResult:
        details: list[AnalyzerDetail] = []
        total = 0

        readme = repo_data.readme_content
        readme_lower = readme.lower()

        # ── Check 1: README existence (4 pts) ──────────────────────────────
        exists = repo_data.readme_exists and len(readme.strip()) >= MIN_README_LENGTH
        pts = 4 if exists else (2 if repo_data.readme_exists else 0)
        total += pts
        details.append(AnalyzerDetail(
            check="README exists and is meaningful",
            passed=exists,
            points_awarded=pts,
            points_possible=4,
            note=(
                "README found and has substantial content."
                if exists
                else ("README exists but is very short (< 200 chars)."
                      if repo_data.readme_exists
                      else "No README found. This is the #1 red flag for recruiters.")
            ),
        ))

        # If no README at all, no point scoring sections
        if not repo_data.readme_exists:
            return ReadmeAnalysisResult(
                score=0,
                max_score=MAX_README_SCORE,
                details=details,
            )

        # ── Check 2: Description / introduction (3 pts) ────────────────────
        has_desc = self.keyword_in_text(readme_lower, README_DESCRIPTION_KEYWORDS)
        pts = 3 if has_desc else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has project description / introduction",
            passed=has_desc,
            points_awarded=pts,
            points_possible=3,
            note=(
                "Description section detected."
                if has_desc
                else "No description section found. Recruiters need to understand the project quickly."
            ),
        ))

        # ── Check 3: Installation section (3 pts) ──────────────────────────
        has_install = self.keyword_in_text(readme_lower, README_INSTALLATION_KEYWORDS)
        pts = 3 if has_install else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has installation / setup instructions",
            passed=has_install,
            points_awarded=pts,
            points_possible=3,
            note=(
                "Installation instructions detected."
                if has_install
                else "No installation guide found. Projects without setup instructions feel incomplete."
            ),
        ))

        # ── Check 4: Usage / demo section (3 pts) ──────────────────────────
        has_usage = self.keyword_in_text(readme_lower, README_USAGE_KEYWORDS)
        pts = 3 if has_usage else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has usage examples or demo",
            passed=has_usage,
            points_awarded=pts,
            points_possible=3,
            note=(
                "Usage / demo section detected."
                if has_usage
                else "No usage examples. Recruiters want to see what the project does."
            ),
        ))

        # ── Check 5: Tech stack (2 pts) ─────────────────────────────────────
        has_tech = self.keyword_in_text(readme_lower, README_TECH_STACK_KEYWORDS)
        pts = 2 if has_tech else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has tech stack / built-with section",
            passed=has_tech,
            points_awarded=pts,
            points_possible=2,
            note=(
                "Tech stack section detected."
                if has_tech
                else "No tech stack mentioned. This makes it hard for recruiters to assess skills."
            ),
        ))

        # ── Check 6: Screenshots / badges (3 pts) ──────────────────────────
        has_visuals = any(p.lower() in readme_lower for p in README_SCREENSHOT_PATTERNS)
        pts = 3 if has_visuals else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has screenshots, badges, or visual assets",
            passed=has_visuals,
            points_awarded=pts,
            points_possible=3,
            note=(
                "Visual content (screenshots/badges) detected."
                if has_visuals
                else "No screenshots or badges. Visuals dramatically improve first impressions."
            ),
        ))

        # ── Check 7: Contribution guide (2 pts) ────────────────────────────
        has_contrib = self.keyword_in_text(readme_lower, README_CONTRIBUTION_KEYWORDS)
        pts = 2 if has_contrib else 0
        total += pts
        details.append(AnalyzerDetail(
            check="Has contribution guide",
            passed=has_contrib,
            points_awarded=pts,
            points_possible=2,
            note=(
                "Contribution guide detected."
                if has_contrib
                else "No contribution guide. Signals project is not open-source friendly."
            ),
        ))

        final_score = min(total, MAX_README_SCORE)
        logger.debug(f"ReadmeAnalyzer score: {final_score}/{MAX_README_SCORE}")

        return ReadmeAnalysisResult(
            score=final_score,
            max_score=MAX_README_SCORE,
            details=details,
        )
