"""
test_structure_analyzer.py — Unit tests for StructureAnalyzer.
"""

import pytest

from analyzers.structure_analyzer import StructureAnalyzer
from models.audit_report import RepoData, RepoMetadata


def _make_repo(file_tree: list[str]) -> RepoData:
    meta = RepoMetadata(
        name="test-repo",
        full_name="user/test-repo",
        description=None,
        html_url="https://github.com/user/test-repo",
        default_branch="main",
    )
    return RepoData(metadata=meta, file_tree=file_tree)


class TestStructureAnalyzer:

    def setup_method(self):
        self.analyzer = StructureAnalyzer()

    def test_empty_repo_scores_zero(self):
        repo = _make_repo([])
        result = self.analyzer.analyze(repo)
        assert result.score == 0

    def test_full_python_project_scores_20(self):
        tree = [
            "src/__init__.py",
            "src/main.py",
            "tests/__init__.py",
            "tests/test_main.py",
            "requirements.txt",
            ".env.example",
            "docs/index.md",
            "README.md",
        ]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.score == 20

    def test_node_project_detects_package_json(self):
        tree = ["src/index.js", "package.json", "tests/app.test.js", ".env.example"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.detected_dependency_file == "package.json"

    def test_src_folder_detected(self):
        tree = ["src/app.py", "README.md"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.detected_src_folder == "src"

    def test_app_folder_detected_as_src(self):
        tree = ["app/main.py", "app/models.py"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.detected_src_folder is not None

    def test_tests_folder_detected(self):
        tree = ["tests/test_app.py", "src/app.py"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.detected_test_folder is not None

    def test_docs_folder_gives_points(self):
        tree = ["docs/index.md", "src/app.py"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        details = {d.check: d for d in result.details}
        assert details["Has documentation folder (docs/, wiki/, guides/)"].passed

    def test_no_docs_fails_gracefully(self):
        tree = ["src/app.py", "requirements.txt"]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        details = {d.check: d for d in result.details}
        assert not details["Has documentation folder (docs/, wiki/, guides/)"].passed

    def test_score_bounded_by_max(self):
        tree = [
            "src/app.py", "tests/test.py", "requirements.txt",
            ".env.example", "docs/index.md", "package.json",
            "pyproject.toml", "setup.cfg",
        ]
        repo = _make_repo(tree)
        result = self.analyzer.analyze(repo)
        assert result.score <= 20
