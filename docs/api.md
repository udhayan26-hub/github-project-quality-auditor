# Data Models & API Integration Contracts

This document outlines the core data models, Pydantic contracts, and API integration pathways within the **GitHub Project Quality Auditor**.

---

## 📦 Data Contracts (Pydantic Models)

We utilize **Pydantic v2** to enforce strict type checking and serialization contracts between our data ingestion layer and evaluation engines.

### 1. `RepoMetadata`
Represents the raw metadata parsed from the GitHub repository endpoint `/repos/{owner}/{repo}`:
```python
class RepoMetadata(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    default_branch: str
    language: Optional[str] = None
    topics: list[str] = []
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    size_kb: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_fork: bool = False
    has_wiki: bool = False
    has_issues: bool = True
    license_name: Optional[str] = None
    commit_count: int = 0
    languages: dict[str, int] = {}
```

### 2. `RepoData`
The primary container passed to the analyzer pipeline, bundling repository contents and metadata:
```python
class RepoData(BaseModel):
    metadata: RepoMetadata
    readme_content: str
    file_tree: list[str]
    readme_exists: bool
    has_github_actions: bool
```

---

## 📡 API Integration Lifecycle

All communications with the GitHub API follow these performance guidelines:
- **Connection Pooling**: Reuses a single `requests.Session` across calls to keep TCP connections open.
- **Header Optimization**: Passes standard `Accept` and API version headers (`2022-11-28`).
- **Token-based Authentication**: Automatically appends the `Authorization: Bearer <token>` header if a token is present, expanding the rate limit from 60 to 5,000 requests/hour.
