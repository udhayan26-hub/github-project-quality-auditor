"""
github_service.py — GitHub REST API v3 client.

Responsibility: Fetch ALL raw data required by the analyzer pipeline.
Analyzers never call requests directly; they only consume RepoData.

Design decisions:
  - Single responsibility: fetch, decode, and return a RepoData object.
  - Graceful degradation: missing README / empty tree → empty defaults.
  - Token-aware: uses GITHUB_TOKEN from env or caller-supplied token.
  - Rate-limit friendly: one session with persistent headers, minimal calls.
  - Error taxonomy: raises specific exceptions for 404, 403, and network errors.
"""

from __future__ import annotations

import base64
import logging
import os
import re
from typing import Optional

import requests
from dotenv import load_dotenv

from models.audit_report import RepoData, RepoMetadata

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class GitHubServiceError(Exception):
    """Base class for all GitHub service errors."""


class RepoNotFoundError(GitHubServiceError):
    """Raised when the repository does not exist or is private."""


class RateLimitError(GitHubServiceError):
    """Raised when the GitHub API rate limit is exceeded."""


class InvalidRepoURLError(GitHubServiceError):
    """Raised when the input URL cannot be parsed as a GitHub repository."""


# ---------------------------------------------------------------------------
# URL parser
# ---------------------------------------------------------------------------

_GITHUB_URL_PATTERN = re.compile(
    r"^(?:https?://)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$"
)


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract (owner, repo) from a GitHub URL.

    Accepts:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - github.com/owner/repo
    """
    url = url.strip().rstrip("/")
    match = _GITHUB_URL_PATTERN.match(url)
    if not match:
        raise InvalidRepoURLError(
            f"Could not parse '{url}' as a GitHub repository URL.\n"
            "Expected format: https://github.com/owner/repository"
        )
    return match.group(1), match.group(2)


# ---------------------------------------------------------------------------
# GitHub Service
# ---------------------------------------------------------------------------

class GitHubService:
    """
    Fetches repository data from the GitHub REST API v3.

    Usage:
        service = GitHubService(token="ghp_...")
        repo_data = service.fetch(url="https://github.com/owner/repo")
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None) -> None:
        """
        Args:
            token: GitHub Personal Access Token. Falls back to GITHUB_TOKEN
                   environment variable, then unauthenticated mode.
        """
        resolved_token = token or os.getenv("GITHUB_TOKEN")
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if resolved_token:
            self._session.headers["Authorization"] = f"Bearer {resolved_token}"
            logger.info("GitHubService: authenticated mode (5000 req/hr)")
        else:
            logger.warning(
                "GitHubService: unauthenticated mode (60 req/hr). "
                "Set GITHUB_TOKEN for higher limits."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, url: str) -> RepoData:
        """
        Main entry point. Given a GitHub repo URL, returns a fully-populated
        RepoData object ready for the analyzer pipeline.

        Raises:
            InvalidRepoURLError: URL cannot be parsed.
            RepoNotFoundError: Repo is private or does not exist.
            RateLimitError: API rate limit exceeded.
            GitHubServiceError: Any other API error.
        """
        owner, repo = parse_github_url(url)
        logger.info(f"Fetching repository: {owner}/{repo}")

        metadata = self._fetch_metadata(owner, repo)
        readme_content, readme_exists = self._fetch_readme(owner, repo)
        file_tree = self._fetch_file_tree(owner, repo, metadata.default_branch)
        commit_count = self._fetch_commit_count(owner, repo)
        languages = self._fetch_languages(owner, repo)

        metadata.commit_count = commit_count
        metadata.languages = languages

        has_github_actions = any(
            p.startswith(".github/workflows") for p in file_tree
        )

        logger.info(
            f"Fetch complete: {len(file_tree)} files, "
            f"{commit_count} commits, readme={'yes' if readme_exists else 'no'}"
        )

        return RepoData(
            metadata=metadata,
            readme_content=readme_content,
            file_tree=file_tree,
            readme_exists=readme_exists,
            has_github_actions=has_github_actions,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict | list:
        """
        Make an authenticated GET request to the GitHub API.
        Raises specific exceptions based on HTTP status codes.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self._session.get(url, params=params, timeout=15)
        except requests.exceptions.ConnectionError as exc:
            raise GitHubServiceError(
                "Network error: could not reach api.github.com. "
                "Check your internet connection."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise GitHubServiceError(
                "Request timed out. GitHub API may be slow, please try again."
            ) from exc

        if response.status_code == 404:
            raise RepoNotFoundError(
                "Repository not found. It may be private, deleted, or the URL is incorrect."
            )
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            if remaining == "0":
                raise RateLimitError(
                    "GitHub API rate limit exceeded. "
                    "Add a GitHub token in the sidebar to increase limits to 5,000 req/hr."
                )
            raise GitHubServiceError(
                f"GitHub API forbidden (403). Response: {response.text[:200]}"
            )
        if response.status_code == 401:
            raise GitHubServiceError(
                "Invalid GitHub token. Check your personal access token and try again."
            )
        if not response.ok:
            raise GitHubServiceError(
                f"GitHub API error {response.status_code}: {response.text[:200]}"
            )

        return response.json()

    def _fetch_metadata(self, owner: str, repo: str) -> RepoMetadata:
        """Fetch core repository metadata."""
        data = self._get(f"/repos/{owner}/{repo}")
        return RepoMetadata(
            name=data.get("name", ""),
            full_name=data.get("full_name", f"{owner}/{repo}"),
            description=data.get("description"),
            html_url=data.get("html_url", ""),
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            topics=data.get("topics", []),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            watchers=data.get("watchers_count", 0),
            size_kb=data.get("size", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_fork=data.get("fork", False),
            has_wiki=data.get("has_wiki", False),
            has_issues=data.get("has_issues", False),
            license_name=(
                data["license"]["name"]
                if data.get("license") else None
            ),
        )

    def _fetch_readme(self, owner: str, repo: str) -> tuple[str, bool]:
        """
        Fetch and decode the README. Returns (content, exists).
        GitHub returns README content base64-encoded.
        """
        try:
            data = self._get(f"/repos/{owner}/{repo}/readme")
            content_b64 = data.get("content", "")
            # GitHub pads base64 with newlines; strip them before decoding
            decoded = base64.b64decode(content_b64.replace("\n", "")).decode(
                "utf-8", errors="replace"
            )
            return decoded, True
        except RepoNotFoundError:
            # README endpoint returns 404 when no README exists
            logger.debug(f"No README found for {owner}/{repo}")
            return "", False

    def _fetch_file_tree(
        self, owner: str, repo: str, branch: str
    ) -> list[str]:
        """
        Fetch the full recursive file tree using the Git Trees API.
        Returns a flat list of file paths relative to the repo root.

        Falls back to an empty list if the tree is too large (truncated).
        """
        try:
            data = self._get(
                f"/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
            )
            if data.get("truncated"):
                logger.warning(
                    "File tree truncated by GitHub (repo > 100k files). "
                    "Some checks may be incomplete."
                )
            return [item["path"] for item in data.get("tree", [])]
        except (GitHubServiceError, KeyError) as exc:
            logger.warning(f"Could not fetch file tree: {exc}")
            return []

    def _fetch_commit_count(self, owner: str, repo: str) -> int:
        """
        Estimate total commit count using the Contributors Stats endpoint.
        Falls back to the paginated commits endpoint (first page only) if
        contributors stats are unavailable.
        """
        try:
            # Use the contributors endpoint with per_page=1 and check Link header
            response = self._session.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/commits",
                params={"per_page": 1},
                headers=self._session.headers,
                timeout=15,
            )
            if not response.ok:
                return 0
            link_header = response.headers.get("Link", "")
            if 'rel="last"' in link_header:
                # Extract the page number from the last link
                import re as _re
                match = _re.search(r'page=(\d+)>; rel="last"', link_header)
                if match:
                    return int(match.group(1))
            # If no pagination, only one page of results
            return len(response.json())
        except Exception as exc:
            logger.warning(f"Could not fetch commit count: {exc}")
            return 0

    def _fetch_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Fetch language breakdown (language → bytes of code)."""
        try:
            data = self._get(f"/repos/{owner}/{repo}/languages")
            return dict(data)  # type: ignore[arg-type]
        except GitHubServiceError as exc:
            logger.warning(f"Could not fetch languages: {exc}")
            return {}
