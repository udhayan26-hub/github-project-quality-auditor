"""
recommender.py — Rule-based recommendation engine.

Generates prioritized, actionable recommendations from a populated AuditReport.

Design:
  - Each rule is a method that inspects a specific AuditReport field and
    appends a Recommendation if the criterion is not met.
  - Rules are independent — adding a new rule never touches existing ones.
  - Priority ordering: Critical → High → Medium → Low
  - Recruiter impact is always explained — not just "add this file."
"""

from __future__ import annotations

import logging

from models.audit_report import AuditReport, Recommendation
from utils.constants import Priority

logger = logging.getLogger(__name__)


class Recommender:
    """
    Generates an ordered list of Recommendation objects from an AuditReport.

    Each recommendation includes:
      - What to do (action)
      - Why it matters to recruiters (recruiter_impact)
      - A code/command hint where applicable
    """

    def generate(self, report: AuditReport) -> list[Recommendation]:
        """
        Run all recommendation rules and return an ordered list.
        Returns recommendations sorted by priority (Critical first).
        """
        recs: list[Recommendation] = []

        # ── README rules ──────────────────────────────────────────────────
        self._readme_rules(report, recs)

        # ── Structure rules ───────────────────────────────────────────────
        self._structure_rules(report, recs)

        # ── Testing rules ─────────────────────────────────────────────────
        self._testing_rules(report, recs)

        # ── Docker rules ──────────────────────────────────────────────────
        self._docker_rules(report, recs)

        # ── CI/CD rules ───────────────────────────────────────────────────
        self._cicd_rules(report, recs)

        # ── Documentation rules ───────────────────────────────────────────
        self._documentation_rules(report, recs)

        # Sort: Critical → High → Medium → Low
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        recs.sort(key=lambda r: priority_order.get(r.priority, 99))

        logger.debug(f"Generated {len(recs)} recommendations.")
        return recs

    # ------------------------------------------------------------------
    # README rules
    # ------------------------------------------------------------------

    def _readme_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        readme = report.readme

        if not report.metadata.name:
            return

        # Check individual details from the analyzer
        failed_checks = {d.check: d for d in readme.details if not d.passed}

        if "README exists and is meaningful" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.CRITICAL,
                title="Create a comprehensive README.md",
                action=(
                    "Create README.md in the project root with project title, "
                    "description, installation steps, usage examples, and tech stack."
                ),
                recruiter_impact=(
                    "The README is the first thing a recruiter sees. "
                    "A missing or empty README immediately disqualifies a project "
                    "from serious consideration."
                ),
                code_hint="# Project Name\n\n> One-line description\n\n## Installation\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n```bash\npython app.py\n```",
            ))

        if "Has installation / setup instructions" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.HIGH,
                title="Add installation and setup instructions",
                action=(
                    "Add a '## Getting Started' or '## Installation' section to README.md "
                    "with step-by-step commands to run the project locally."
                ),
                recruiter_impact=(
                    "Recruiters and team leads try to run projects. "
                    "No install instructions means the project cannot be evaluated — "
                    "it signals a lack of empathy for the reader."
                ),
                code_hint="## Installation\n```bash\ngit clone https://github.com/you/repo\ncd repo\npip install -r requirements.txt\n```",
            ))

        if "Has usage examples or demo" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.HIGH,
                title="Add usage examples or a demo",
                action=(
                    "Add a '## Usage' section with code examples, CLI commands, "
                    "or a link to a live demo or Loom video."
                ),
                recruiter_impact=(
                    "Without a demo, recruiters cannot quickly understand what the "
                    "project does or how impressive it is."
                ),
            ))

        if "Has project description / introduction" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.MEDIUM,
                title="Add a clear project description",
                action="Add a short paragraph at the top of README.md explaining what the project does and why.",
                recruiter_impact=(
                    "Recruiters spend 30–60 seconds on a project. "
                    "If they cannot understand it immediately, they move on."
                ),
            ))

        if "Has tech stack / built-with section" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.MEDIUM,
                title="Add a tech stack / built-with section",
                action="Add a '## Tech Stack' section listing all languages, frameworks, and tools used.",
                recruiter_impact=(
                    "Tech stack sections help recruiters quickly identify relevant skills "
                    "without reading the entire codebase."
                ),
                code_hint="## Tech Stack\n- **Backend**: Python, FastAPI\n- **Frontend**: React\n- **Database**: PostgreSQL\n- **Deployment**: Docker, GitHub Actions",
            ))

        if "Has screenshots, badges, or visual assets" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.MEDIUM,
                title="Add screenshots, GIFs, or status badges",
                action=(
                    "Add screenshots of the UI, a demo GIF, or GitHub Actions status badges. "
                    "Store images in a docs/images/ or assets/ folder."
                ),
                recruiter_impact=(
                    "Visual projects are remembered. A GIF or screenshot makes the project "
                    "stand out in a portfolio and proves it actually works."
                ),
                code_hint='![App Screenshot](docs/images/screenshot.png)\n\n[![CI](https://github.com/user/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/user/repo/actions)',
            ))

        if "Has contribution guide" in failed_checks:
            recs.append(Recommendation(
                category="README",
                priority=Priority.LOW,
                title="Add a contribution guide",
                action="Add a CONTRIBUTING.md file or a '## Contributing' section in README.md.",
                recruiter_impact=(
                    "Open-source contribution guidelines signal team collaboration skills "
                    "and engineering maturity beyond a solo project."
                ),
            ))

    # ------------------------------------------------------------------
    # Structure rules
    # ------------------------------------------------------------------

    def _structure_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        failed = {d.check for d in report.structure.details if not d.passed}

        if "Has dedicated source code folder (src/, app/, etc.)" in failed:
            recs.append(Recommendation(
                category="Structure",
                priority=Priority.HIGH,
                title="Organize code into a dedicated source folder",
                action=(
                    "Move all application code into a src/ or app/ directory. "
                    "Keep only config files and README at the root level."
                ),
                recruiter_impact=(
                    "Flat project structure signals a tutorial-level project. "
                    "Organized structure demonstrates understanding of software architecture."
                ),
            ))

        if "Has dependency manifest (requirements.txt, package.json, etc.)" in failed:
            recs.append(Recommendation(
                category="Structure",
                priority=Priority.CRITICAL,
                title="Add a dependency manifest file",
                action=(
                    "Run 'pip freeze > requirements.txt' (Python) or use npm/yarn to "
                    "generate package.json. Pin all dependencies with exact versions."
                ),
                recruiter_impact=(
                    "Without a dependency file, the project cannot be installed or run "
                    "by anyone else — making it impossible to evaluate in a technical interview."
                ),
                code_hint="pip freeze > requirements.txt\n# Or for production-only:\npip install pipreqs\npipreqs . --force",
            ))

        if "Has configuration / environment template (.env.example, config.yml, etc.)" in failed:
            recs.append(Recommendation(
                category="Structure",
                priority=Priority.HIGH,
                title="Add an environment configuration template",
                action=(
                    "Create a .env.example file listing all required environment variables "
                    "with placeholder values. Never commit actual secrets."
                ),
                recruiter_impact=(
                    "Missing environment templates cause projects to fail silently when "
                    "others try to run them — a sign of poor documentation and security awareness."
                ),
                code_hint="# .env.example\nDATABASE_URL=postgresql://localhost:5432/mydb\nSECRET_KEY=your-secret-key-here\nDEBUG=True",
            ))

        if "Has documentation folder (docs/, wiki/, guides/)" in failed:
            recs.append(Recommendation(
                category="Structure",
                priority=Priority.LOW,
                title="Add a documentation folder",
                action="Create a docs/ directory with architecture diagrams, API reference, or design decisions.",
                recruiter_impact=(
                    "A docs/ folder signals senior engineering habits — "
                    "most junior projects skip this entirely."
                ),
            ))

    # ------------------------------------------------------------------
    # Testing rules
    # ------------------------------------------------------------------

    def _testing_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        testing = report.testing

        if testing.score == 0:
            recs.append(Recommendation(
                category="Testing",
                priority=Priority.CRITICAL,
                title="Add automated unit tests",
                action=(
                    "Create a tests/ directory and add test files using pytest (Python), "
                    "Jest (JavaScript), or JUnit (Java). Aim for ≥80% coverage of core logic."
                ),
                recruiter_impact=(
                    "Projects without tests signal that the developer has never worked in "
                    "a production environment. Testing is table stakes for any SDE role."
                ),
                code_hint="# Install pytest\npip install pytest\n\n# Create tests/test_main.py\ndef test_example():\n    assert 1 + 1 == 2\n\n# Run tests\npytest tests/ -v",
            ))
        elif testing.test_file_count < 3:
            recs.append(Recommendation(
                category="Testing",
                priority=Priority.HIGH,
                title="Expand test coverage beyond basic tests",
                action=(
                    "Add more test files covering edge cases, error conditions, and "
                    "integration scenarios. Aim for ≥3 test files."
                ),
                recruiter_impact=(
                    "A single test file suggests testing was an afterthought. "
                    "Breadth of testing demonstrates systematic quality engineering."
                ),
            ))

        if not report.testing.detected_framework:
            recs.append(Recommendation(
                category="Testing",
                priority=Priority.MEDIUM,
                title="Add testing framework configuration",
                action=(
                    "Add a pytest.ini, pyproject.toml [tool.pytest.ini_options], or "
                    "jest.config.js to configure the test runner."
                ),
                recruiter_impact=(
                    "A testing config file shows the project has a structured test pipeline, "
                    "not just ad-hoc test scripts."
                ),
                code_hint="# pytest.ini\n[pytest]\ntestpaths = tests\npython_files = test_*.py\npython_functions = test_*\naddopts = -v --tb=short",
            ))

    # ------------------------------------------------------------------
    # Docker rules
    # ------------------------------------------------------------------

    def _docker_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        docker = report.docker

        if not docker.dockerfile_found:
            recs.append(Recommendation(
                category="Docker",
                priority=Priority.HIGH,
                title="Add a Dockerfile for containerization",
                action=(
                    "Create a Dockerfile in the project root. Use a multi-stage build "
                    "to keep the final image small."
                ),
                recruiter_impact=(
                    "Docker knowledge is expected in modern SDE and DevOps roles. "
                    "Its absence signals unfamiliarity with production deployment practices."
                ),
                code_hint="FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD [\"python\", \"app.py\"]",
            ))

        if docker.dockerfile_found and not docker.compose_found:
            recs.append(Recommendation(
                category="Docker",
                priority=Priority.MEDIUM,
                title="Add docker-compose.yml for multi-service orchestration",
                action=(
                    "Create a docker-compose.yml to define services (app, database, cache). "
                    "Makes local development and CI setup trivial."
                ),
                recruiter_impact=(
                    "docker-compose knowledge shows awareness of real-world service architectures "
                    "beyond single-container deployments."
                ),
                code_hint='version: "3.9"\nservices:\n  app:\n    build: .\n    ports:\n      - "8000:8000"\n    env_file:\n      - .env',
            ))

    # ------------------------------------------------------------------
    # CI/CD rules
    # ------------------------------------------------------------------

    def _cicd_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        cicd = report.cicd

        if cicd.score == 0:
            recs.append(Recommendation(
                category="CI/CD",
                priority=Priority.HIGH,
                title="Configure GitHub Actions CI pipeline",
                action=(
                    "Create .github/workflows/ci.yml to run tests automatically "
                    "on every push and pull request."
                ),
                recruiter_impact=(
                    "A CI pipeline proves the project is maintainable. "
                    "It's the clearest signal of professional engineering habits "
                    "in a student portfolio."
                ),
                code_hint='name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - run: pip install -r requirements.txt\n      - run: pytest tests/ -v',
            ))
        elif len(cicd.workflow_files) == 1:
            recs.append(Recommendation(
                category="CI/CD",
                priority=Priority.LOW,
                title="Add a CD (deployment) workflow",
                action=(
                    "Add a separate workflow for deployment (e.g., deploy to Render, "
                    "Railway, or Heroku on merge to main)."
                ),
                recruiter_impact=(
                    "Separate CI and CD pipelines mirror real-world GitOps practices "
                    "and show end-to-end delivery maturity."
                ),
            ))

    # ------------------------------------------------------------------
    # Documentation rules
    # ------------------------------------------------------------------

    def _documentation_rules(self, report: AuditReport, recs: list[Recommendation]) -> None:
        failed = {d.check for d in report.documentation.details if not d.passed}

        if "License file present" in failed:
            recs.append(Recommendation(
                category="Documentation",
                priority=Priority.MEDIUM,
                title="Add a LICENSE file",
                action=(
                    "Add a LICENSE file to the repository root. "
                    "Use MIT for open-source, or Apache 2.0 for commercial-friendly projects."
                ),
                recruiter_impact=(
                    "A license file is required for any project intended for open-source "
                    "or portfolio sharing. Its absence suggests legal unawareness."
                ),
            ))

        if "API documentation or structured docs files present" in failed:
            recs.append(Recommendation(
                category="Documentation",
                priority=Priority.LOW,
                title="Add API documentation or structured docs",
                action=(
                    "Create docs/api.md or an OpenAPI spec (openapi.yml). "
                    "For FastAPI/Django, auto-generate docs with Swagger UI."
                ),
                recruiter_impact=(
                    "API documentation signals backend engineering maturity and "
                    "readiness for team collaboration."
                ),
            ))

        if "CHANGELOG or release notes present" in failed:
            recs.append(Recommendation(
                category="Documentation",
                priority=Priority.LOW,
                title="Add a CHANGELOG.md",
                action=(
                    "Create CHANGELOG.md documenting version history, features added, "
                    "and bugs fixed. Follow Keep a Changelog format."
                ),
                recruiter_impact=(
                    "A changelog signals that the project evolves with discipline — "
                    "not just pushed once and abandoned."
                ),
            ))
