"""
constants.py — Single source of truth for all scoring weights, file patterns,
and rubric definitions used throughout the GitHub Project Quality Auditor.

Design note: All magic numbers live here. Changing a weight or adding a new
file pattern requires editing only this file, keeping analyzer logic clean.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Scoring maximums (must sum to 100)
# ---------------------------------------------------------------------------
MAX_README_SCORE: Final[int] = 20
MAX_STRUCTURE_SCORE: Final[int] = 20
MAX_TESTING_SCORE: Final[int] = 20
MAX_DOCKER_SCORE: Final[int] = 10
MAX_CICD_SCORE: Final[int] = 15
MAX_DOCUMENTATION_SCORE: Final[int] = 15
MAX_TOTAL_SCORE: Final[int] = 100

# ---------------------------------------------------------------------------
# Resume Impact Score weights (must sum to 1.0)
# Rationale: Testing & CI/CD signal engineering maturity most strongly to
# technical recruiters, while README/Structure are table-stakes expectations.
# ---------------------------------------------------------------------------
RESUME_IMPACT_WEIGHTS: Final[dict] = {
    "readme": 0.15,
    "structure": 0.15,
    "testing": 0.30,   # highest — proves quality discipline
    "docker": 0.15,
    "cicd": 0.20,      # second — shows DevOps awareness
    "documentation": 0.05,
}

# ---------------------------------------------------------------------------
# README analyzer — keyword patterns (case-insensitive)
# ---------------------------------------------------------------------------
README_DESCRIPTION_KEYWORDS: Final[list[str]] = [
    "about", "overview", "introduction", "what is", "this project",
    "description", "purpose", "goal",
]

README_INSTALLATION_KEYWORDS: Final[list[str]] = [
    "install", "installation", "setup", "getting started", "prerequisites",
    "requirements", "how to run", "quick start",
]

README_USAGE_KEYWORDS: Final[list[str]] = [
    "usage", "use", "demo", "example", "how to use", "run",
    "screenshot", "demo", "walkthrough",
]

README_TECH_STACK_KEYWORDS: Final[list[str]] = [
    "tech stack", "technologies", "built with", "tools", "stack",
    "framework", "library", "language",
]

README_CONTRIBUTION_KEYWORDS: Final[list[str]] = [
    "contributing", "contribution", "contribute", "pull request", "pr",
    "how to contribute", "guidelines",
]

README_SCREENSHOT_PATTERNS: Final[list[str]] = [
    "![", "badge", "shield", "img.shields.io", "screenshot",
    "preview", "demo gif", ".gif", ".png", ".jpg",
]

# ---------------------------------------------------------------------------
# Structure analyzer — file/folder patterns
# ---------------------------------------------------------------------------
# Dependency files (any one is sufficient)
DEPENDENCY_FILES: Final[list[str]] = [
    "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "package.json", "pom.xml", "build.gradle", "Gemfile", "go.mod",
    "Cargo.toml", "composer.json",
]

# Config / env files
CONFIG_FILES: Final[list[str]] = [
    ".env.example", ".env.sample", "config.py", "config.yml",
    "config.yaml", "settings.py", "pyproject.toml", "setup.cfg",
    "setup.py", ".eslintrc", ".prettierrc", "tsconfig.json",
    "webpack.config.js", "vite.config.js",
]

# Documentation folders
DOCS_FOLDERS: Final[list[str]] = [
    "docs", "doc", "documentation", "wiki", "guides",
]

# Source folders (language-agnostic)
SRC_FOLDERS: Final[list[str]] = [
    "src", "app", "lib", "core", "source", "main", "backend",
    "frontend", "api", "server", "client",
]

# Test folders
TEST_FOLDERS: Final[list[str]] = [
    "tests", "test", "spec", "__tests__", "testing",
]

# ---------------------------------------------------------------------------
# Testing analyzer — patterns
# ---------------------------------------------------------------------------
TEST_FILE_PATTERNS: Final[list[str]] = [
    "test_", "_test.py", ".test.js", ".test.ts", ".spec.js",
    ".spec.ts", "_spec.rb", "Test.java", "Tests.cs",
]

TESTING_CONFIG_FILES: Final[list[str]] = [
    "pytest.ini", "setup.cfg", "pyproject.toml", "jest.config.js",
    "jest.config.ts", ".noserc", "karma.conf.js", "mocha.opts",
    "phpunit.xml", "rspec",
]

# ---------------------------------------------------------------------------
# Docker analyzer — exact filenames
# ---------------------------------------------------------------------------
DOCKER_FILES: Final[list[str]] = [
    "Dockerfile",
    "dockerfile",
    "Dockerfile.dev",
    "Dockerfile.prod",
]

DOCKER_COMPOSE_FILES: Final[list[str]] = [
    "docker-compose.yml",
    "docker-compose.yaml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
]

DOCKER_IGNORE_FILES: Final[list[str]] = [
    ".dockerignore",
]

# ---------------------------------------------------------------------------
# CI/CD analyzer — workflow directory patterns
# ---------------------------------------------------------------------------
CICD_WORKFLOW_DIRS: Final[list[str]] = [
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "Jenkinsfile",
    ".travis.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
]

CI_WORKFLOW_EXTENSIONS: Final[list[str]] = [".yml", ".yaml"]

CI_ACTION_KEYWORDS: Final[list[str]] = [
    "run:", "uses:", "steps:", "jobs:", "on:", "push", "pull_request",
    "test", "build", "lint", "deploy",
]

# ---------------------------------------------------------------------------
# Documentation analyzer — patterns
# ---------------------------------------------------------------------------
API_DOC_FILES: Final[list[str]] = [
    "openapi.yml", "openapi.yaml", "swagger.yml", "swagger.yaml",
    "api.md", "API.md", "docs/api.md",
]

DOCSTRING_LANGUAGES: Final[list[str]] = [
    ".py", ".js", ".ts", ".java", ".go", ".rs", ".cs",
]

# Minimum README length (characters) to count as "meaningful"
MIN_README_LENGTH: Final[int] = 200

# Minimum number of test functions to count as "non-trivial" testing
MIN_TEST_FUNCTION_COUNT: Final[int] = 3

# ---------------------------------------------------------------------------
# Recommendation priorities
# ---------------------------------------------------------------------------
class Priority:
    CRITICAL = "🔴 Critical"
    HIGH = "🟠 High"
    MEDIUM = "🟡 Medium"
    LOW = "🟢 Low"

# ---------------------------------------------------------------------------
# Resume impact labels by score range
# ---------------------------------------------------------------------------
RESUME_IMPACT_LABELS: Final[dict] = {
    (90, 101): ("Exceptional", "🏆", "#00c853"),
    (75, 90):  ("Strong",      "⭐", "#64dd17"),
    (55, 75):  ("Good",        "👍", "#ffd600"),
    (35, 55):  ("Needs Work",  "⚠️",  "#ff6d00"),
    (0, 35):   ("Weak",        "❌", "#d50000"),
}

# Overall score labels
OVERALL_SCORE_LABELS: Final[dict] = {
    (85, 101): ("Production Ready",  "#00c853"),
    (70, 85):  ("Good Quality",      "#64dd17"),
    (50, 70):  ("Average",           "#ffd600"),
    (30, 50):  ("Below Standard",    "#ff6d00"),
    (0, 30):   ("Needs Major Work",  "#d50000"),
}
