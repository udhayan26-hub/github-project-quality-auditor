"""
test_readme_analyzer.py — Unit tests for ReadmeAnalyzer.
"""

import pytest

from analyzers.readme_analyzer import ReadmeAnalyzer
from models.audit_report import RepoData, RepoMetadata


def _make_repo(readme: str, readme_exists: bool = True) -> RepoData:
    meta = RepoMetadata(
        name="test-repo",
        full_name="user/test-repo",
        description="A test repo",
        html_url="https://github.com/user/test-repo",
        default_branch="main",
    )
    return RepoData(
        metadata=meta,
        readme_content=readme,
        readme_exists=readme_exists,
        file_tree=[],
    )


class TestReadmeAnalyzer:

    def setup_method(self):
        self.analyzer = ReadmeAnalyzer()

    def test_no_readme_scores_zero(self):
        repo = _make_repo("", readme_exists=False)
        result = self.analyzer.analyze(repo)
        assert result.score == 0
        assert result.max_score == 20

    def test_short_readme_scores_partial(self):
        repo = _make_repo("# My Project", readme_exists=True)
        result = self.analyzer.analyze(repo)
        # Short README: 2 pts for existing but <200 chars; other sections may not match
        assert 2 <= result.score <= 6  # at least existence points, at most a few bonus

    def test_full_readme_scores_high(self):
        readme = """
# My Awesome Project

## About
This is a web application built for demonstration purposes.

## Installation
```bash
pip install -r requirements.txt
python app.py
```

## Usage
Run `python app.py` to start the server. Visit http://localhost:8000.

## Tech Stack
- Python
- FastAPI
- PostgreSQL

## Screenshots
![screenshot](docs/screenshot.png)

## Contributing
Pull requests are welcome. Please read CONTRIBUTING.md first.
        """ * 3  # repeat to exceed 200 chars
        repo = _make_repo(readme)
        result = self.analyzer.analyze(repo)
        assert result.score >= 15, f"Expected >=15, got {result.score}"

    def test_readme_with_only_description(self):
        readme = ("# Project\n\nThis project is about building an AI chatbot. " * 10)
        repo = _make_repo(readme)
        result = self.analyzer.analyze(repo)
        # Should get: exists(4) + description(3) = 7
        assert result.score >= 7

    def test_installation_section_detected(self):
        readme = "# Project\n" + ("About this project. " * 20) + "\n## Installation\npip install x"
        repo = _make_repo(readme)
        result = self.analyzer.analyze(repo)
        details = {d.check: d for d in result.details}
        assert details["Has installation / setup instructions"].passed

    def test_score_does_not_exceed_max(self):
        readme = """
# Super Project — About Installation Usage Tech Stack Screenshots Contributing
## Getting Started
```bash
pip install -r requirements.txt
```
## Usage
Run the app with python main.py
## Tech Stack
Python FastAPI Docker
## Contributing
Fork and PR. See CONTRIBUTING.md.
## Screenshots
![img](screen.png)
""" * 5
        repo = _make_repo(readme)
        result = self.analyzer.analyze(repo)
        assert result.score <= 20

    def test_all_details_have_valid_points(self):
        readme = "# x\n" + "content " * 50
        repo = _make_repo(readme)
        result = self.analyzer.analyze(repo)
        for detail in result.details:
            assert 0 <= detail.points_awarded <= detail.points_possible
