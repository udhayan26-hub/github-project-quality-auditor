"""
test_github_service.py — Unit tests for GitHubService and URL parser.

Uses pytest-mock to patch requests.Session so no real network calls are made.
"""

import pytest
from unittest.mock import MagicMock, patch

from services.github_service import (
    GitHubService,
    InvalidRepoURLError,
    RateLimitError,
    RepoNotFoundError,
    parse_github_url,
)


# ---------------------------------------------------------------------------
# URL parser tests
# ---------------------------------------------------------------------------

class TestParseGithubUrl:

    def test_full_https_url(self):
        owner, repo = parse_github_url("https://github.com/tiangolo/fastapi")
        assert owner == "tiangolo"
        assert repo == "fastapi"

    def test_url_with_git_suffix(self):
        owner, repo = parse_github_url("https://github.com/psf/requests.git")
        assert owner == "psf"
        assert repo == "requests"

    def test_url_without_https(self):
        owner, repo = parse_github_url("github.com/pallets/flask")
        assert owner == "pallets"
        assert repo == "flask"

    def test_url_with_trailing_slash(self):
        owner, repo = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    def test_invalid_url_raises(self):
        with pytest.raises(InvalidRepoURLError):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_empty_url_raises(self):
        with pytest.raises(InvalidRepoURLError):
            parse_github_url("")

    def test_non_github_raises(self):
        with pytest.raises(InvalidRepoURLError):
            parse_github_url("https://example.com/owner/repo")

    def test_hyphenated_repo_name(self):
        owner, repo = parse_github_url("https://github.com/my-org/my-project")
        assert owner == "my-org"
        assert repo == "my-project"


# ---------------------------------------------------------------------------
# GitHubService tests
# ---------------------------------------------------------------------------

class TestGitHubService:

    def _make_service(self) -> GitHubService:
        return GitHubService(token=None)

    def _mock_response(self, json_data: dict | list, status_code: int = 200) -> MagicMock:
        mock = MagicMock()
        mock.status_code = status_code
        mock.ok = status_code < 400
        mock.json.return_value = json_data
        mock.headers = {"Link": "", "X-RateLimit-Remaining": "59"}
        mock.text = str(json_data)
        return mock

    @patch("services.github_service.requests.Session")
    def test_fetch_returns_repo_data(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.headers = {}

        # Patch all sub-calls
        def side_effect(url, **kwargs):
            if "/readme" in url:
                import base64
                content = base64.b64encode(b"# Hello World\n\nThis is a test.").decode()
                return self._mock_response({"content": content})
            if "/git/trees" in url:
                return self._mock_response({
                    "tree": [{"path": "src/main.py"}, {"path": "tests/test_main.py"}],
                    "truncated": False,
                })
            if "/commits" in url:
                return self._mock_response([{}, {}])
            if "/languages" in url:
                return self._mock_response({"Python": 12000})
            # default: repo metadata
            return self._mock_response({
                "name": "my-project",
                "full_name": "user/my-project",
                "description": "A test project",
                "html_url": "https://github.com/user/my-project",
                "default_branch": "main",
                "language": "Python",
                "topics": ["python", "ml"],
                "stargazers_count": 5,
                "forks_count": 1,
                "open_issues_count": 2,
                "watchers_count": 5,
                "size": 100,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-06-01T00:00:00Z",
                "fork": False,
                "has_wiki": False,
                "has_issues": True,
                "license": {"name": "MIT License"},
            })

        mock_session.get.side_effect = side_effect

        service = GitHubService.__new__(GitHubService)
        service._session = mock_session

        repo_data = service.fetch("https://github.com/user/my-project")

        assert repo_data.metadata.name == "my-project"
        assert repo_data.readme_exists is True
        assert "Hello World" in repo_data.readme_content
        assert "src/main.py" in repo_data.file_tree
        assert "tests/test_main.py" in repo_data.file_tree

    def test_404_raises_repo_not_found(self):
        service = GitHubService.__new__(GitHubService)
        mock_session = MagicMock()
        service._session = mock_session

        mock_resp = self._mock_response({}, status_code=404)
        mock_resp.ok = False
        mock_session.get.return_value = mock_resp

        with pytest.raises(RepoNotFoundError):
            service._get("/repos/nobody/nowhere")

    def test_rate_limit_raises_rate_limit_error(self):
        service = GitHubService.__new__(GitHubService)
        mock_session = MagicMock()
        service._session = mock_session

        mock_resp = self._mock_response({}, status_code=403)
        mock_resp.ok = False
        mock_resp.headers = {"X-RateLimit-Remaining": "0"}
        mock_session.get.return_value = mock_resp

        with pytest.raises(RateLimitError):
            service._get("/repos/owner/repo")
