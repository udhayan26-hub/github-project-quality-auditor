# System Architecture & Design Decisions

Welcome to the **GitHub Project Quality Auditor** developer documentation. This document outlines the core architecture, software design patterns, and engineering decisions behind the application.

---

## 🏛️ System Architecture

The application is structured using a clean, layered architecture separating data ingestion, business logic, scoring, and UI presentation.

```
┌─────────────────────────────────────────────────────────┐
│                      Streamlit UI                       │
│        (streamlit_app.py / analytics/dashboard.py)      │
└───────────────────────────┬─────────────────────────────┘
                            │ (consumes AuditReport)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      ScoreEngine                        │
│                 (scoring/score_engine.py)               │
└──────┬────────────────────┬────────────────────┬────────┘
       │ (runs)             │ (aggregates)       │ (analyzes)
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│READMEAnalyzer│    │ TestingTester│    │ CICDAnalyzer │
│(and others)  │    │ (and others) │    │ (and others) │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼ (consumes RepoData)
┌─────────────────────────────────────────────────────────┐
│                     GitHub Service                      │
│              (services/github_service.py)               │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Implemented Software Design Patterns

### 1. Strategy Pattern (Analyzers)
Each quality analyzer (e.g., `TestingAnalyzer`, `DockerAnalyzer`) inherits from `BaseAnalyzer` and implements the `analyze(repo_data: RepoData)` method. This allows:
- **Loose Coupling**: Analyzers do not know about each other's inner workings.
- **Extensibility**: Adding a new analyzer (e.g., security scan) requires creating a new strategy class without modifying existing runner pipelines.

### 2. Factory Method (ScoreEngine)
The `ScoreEngine` act as a factory that receives the raw repository payloads, instantiates all active analyzer strategies, executes them sequentially, and assembles the final, unified `AuditReport` data model.

### 3. Separation of Concerns
- **GitHubService**: Solely responsible for calling the GitHub REST API v3, managing authentication tokens, handle rate limit headers, and decoding base64 payloads. It returns a standardized Pydantic `RepoData` container.
- **Analyzers**: Solely responsible for inspecting file trees and text payloads to award points and log check flags.
- **Recommender**: Solely responsible for checking audit results against priority rules and generating actionable user recommendations.
