<div align="center">

<img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white"/>
<img src="https://img.shields.io/badge/GitHub_API-v3-181717?style=for-the-badge&logo=github&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Tests-44_passing-22C55E?style=for-the-badge&logo=pytest&logoColor=white"/>

<br/><br/>

# 🔍 GitHub Project Quality Auditor

### *Evaluate any GitHub repository from a recruiter and engineering maturity perspective*

**Built specifically for students, fresh graduates, internship seekers, and open-source contributors.**

[**Live Demo**](#) · [**Report Bug**](../../issues) · [**Request Feature**](../../issues)

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Scoring System](#-scoring-system)
- [Screenshots](#-screenshots)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Architecture](#-architecture)
- [Running Tests](#-running-tests)
- [Tech Stack](#-tech-stack)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 About

Thousands of students build projects and push them to GitHub — but never know:

- Whether the project follows industry standards
- Whether the README is complete enough
- Whether testing is implemented
- Whether CI/CD is configured
- Whether the project would impress a recruiter

Existing tools (SonarQube, CodeClimate, Codacy) are built for professional engineering teams.  
**GitHub Project Quality Auditor** is built for:

| User Type | Use Case |
|---|---|
| 🎓 BTech / AIML Students | Improve project quality before job applications |
| 💼 SDE Aspirants | Understand what recruiters look for |
| 🔍 Internship Seekers | Optimize GitHub portfolio |
| 📊 Placement Cells | Audit student projects at scale |
| 🧑‍💻 Open Source Mentors | Review contributor projects |

---

## ✨ Key Features

- **📄 README Analyzer** — Evaluates completeness: description, install guide, usage, screenshots, tech stack, contribution guide
- **🗂️ Structure Analyzer** — Detects `src/`, `tests/`, dependency files, config templates, docs — language-agnostic
- **🧪 Testing Analyzer** — Finds test folders, test files, framework configs (pytest, Jest, JUnit, etc.)
- **🐳 Docker Analyzer** — Checks for `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **⚙️ CI/CD Analyzer** — Detects GitHub Actions, GitLab CI, CircleCI, Travis, Jenkins, Azure Pipelines
- **📚 Documentation Analyzer** — Evaluates docs folder, API docs, LICENSE, CHANGELOG, README depth
- **💼 Resume Impact Score** — Unique weighted score biased toward what technical recruiters actually care about
- **💡 Recommendation Engine** — 20+ prioritized, actionable recommendations with code snippets
- **📥 Export** — Download full audit as Markdown or JSON

---

## ⚙️ How It Works

```
User pastes GitHub URL
        ↓
GitHubService (REST API v3)
        ↓
RepoData (Pydantic model)
        ↓
┌───────────────────────────────────────┐
│         Analyzer Pipeline             │
│  README · Structure · Testing         │
│  Docker  · CI/CD   · Documentation   │
└───────────────┬───────────────────────┘
                ↓
          ScoreEngine
      ┌─────────┴──────────┐
  TotalScore        ResumeImpactScore
      └─────────┬──────────┘
          Recommender
                ↓
       Streamlit Dashboard
```

---

## 📊 Scoring System

| Category | Max Score | Resume Weight | Why It Matters |
|---|---|---|---|
| 📄 README Quality | 20 | 15% | First thing a recruiter reads |
| 🗂️ Project Structure | 20 | 15% | Shows architectural awareness |
| 🧪 Testing | 20 | **30%** | Strongest signal of engineering discipline |
| 🐳 Docker | 10 | 15% | Demonstrates deployment knowledge |
| ⚙️ CI/CD | 15 | **20%** | Shows DevOps maturity |
| 📚 Documentation | 15 | 5% | Signals professional habits |
| **Total** | **100** | **100%** | |

> **Resume Impact Score** uses weighted normalization — so a project with CI/CD and tests ranks higher than one with only a polished README.

### Score Labels

| Score | Label |
|---|---|
| 85–100 | 🏆 Production Ready |
| 70–84 | ⭐ Good Quality |
| 50–69 | 👍 Average |
| 30–49 | ⚠️ Below Standard |
| 0–29 | ❌ Needs Major Work |

---

## 🖥️ Screenshots

> *Paste a GitHub URL, get a full engineering audit in seconds.*

**Landing Page — Enterprise light theme**
```
┌─────────────────────────────────────────────────┐
│  🔍 GitHub Project Quality Auditor              │
│  Evaluate any repository from a recruiter       │
│  and engineering maturity perspective.           │
│                                                 │
│  [ https://github.com/owner/repo        ] [→]  │
└─────────────────────────────────────────────────┘
```

**Audit Results Dashboard**
```
┌──────────────────────┬──────────────────────────┐
│  Repository Score    │  Resume Impact Score     │
│  72 / 100            │  68 / 100                │
│  ████████░░ Good     │  ███████░░░ Good         │
└──────────────────────┴──────────────────────────┘

┌────────┬───────────┬─────────┬───────┬────────┬──────┐
│ README │ Structure │ Testing │Docker │ CI/CD  │ Docs │
│ 16/20  │  18/20    │  5/20   │ 0/10  │  0/15  │10/15 │
└────────┴───────────┴─────────┴───────┴────────┴──────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/github-project-auditor.git
cd github-project-auditor

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up GitHub token (optional but recommended)
cp .env.example .env
# Edit .env — add your GitHub Personal Access Token
```

### Running the App

```bash
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### GitHub Token Setup

Without a token: **60 API requests/hour**  
With a token: **5,000 API requests/hour**

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate a new token (classic)
3. Select scope: `public_repo` (read-only)
4. Copy token into the sidebar, or add to `.env`:

```env
GITHUB_TOKEN=ghp_your_token_here
```

---

## 📁 Project Structure

```
github-project-auditor/
│
├── streamlit_app.py                 # Streamlit UI — enterprise light theme
├── requirements.txt                # Pinned dependencies
├── .env.example                    # Token template
├── LICENSE                         # MIT License
│
├── services/
│   └── github_service.py           # GitHub REST API v3 client
│
├── analyzers/
│   ├── base_analyzer.py            # Abstract Strategy base class
│   ├── readme_analyzer.py          # README quality (0–20 pts)
│   ├── structure_analyzer.py       # Project structure (0–20 pts)
│   ├── testing_analyzer.py         # Testing maturity (0–20 pts)
│   ├── docker_analyzer.py          # Containerization (0–10 pts)
│   ├── cicd_analyzer.py            # CI/CD pipeline (0–15 pts)
│   └── documentation_analyzer.py  # Documentation (0–15 pts)
│
├── scoring/
│   └── score_engine.py             # Aggregates scores, Resume Impact formula
│
├── recommendations/
│   └── recommender.py              # Rule-based recommendation engine (20+ rules)
│
├── models/
│   └── audit_report.py             # Pydantic v2 data contracts
│
├── utils/
│   └── constants.py                # All weights, patterns, rubrics
│
└── tests/                          # pytest test suite — 44 tests
    ├── test_github_service.py
    ├── test_readme_analyzer.py
    ├── test_structure_analyzer.py
    ├── test_score_engine.py
    └── test_recommender.py
```

---

## 🏛️ Architecture

### Design Patterns

| Pattern | Where Applied |
|---|---|
| **Strategy** | Each analyzer implements `BaseAnalyzer` independently |
| **Factory Method** | `ScoreEngine.audit()` assembles the complete `AuditReport` |
| **Chain of Responsibility** | Analyzers run sequentially, each populating the report |
| **Pydantic Models** | Type-safe data contracts between all layers |

### Resume Impact Formula

Each category score is normalized to 0–1 before applying weights:

```python
resume_impact = round((
    0.15 × (readme / 20)        +
    0.15 × (structure / 20)     +
    0.30 × (testing / 20)       +   # ← highest weight
    0.15 × (docker / 10)        +
    0.20 × (cicd / 15)          +   # ← second highest
    0.05 × (documentation / 15)
) × 100)
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short

# Run a specific test module
pytest tests/test_score_engine.py -v
```

**Current status: 44/44 tests passing**

```
tests/test_github_service.py      11 tests  ✅
tests/test_readme_analyzer.py      7 tests  ✅
tests/test_structure_analyzer.py   9 tests  ✅
tests/test_score_engine.py        10 tests  ✅
tests/test_recommender.py          7 tests  ✅
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.32+ with custom CSS (Inter font, enterprise light theme) |
| **Backend** | Python 3.11+ |
| **Data Models** | Pydantic v2 |
| **API** | GitHub REST API v3 |
| **HTTP Client** | requests |
| **Config** | python-dotenv |
| **Testing** | pytest + pytest-mock |

---

## 🗺️ Roadmap

- [x] **Phase 1** — GitHub fetcher, README analyzer, structure analyzer, Streamlit UI
- [x] **Phase 2** — Testing, Docker, CI/CD, documentation analyzers
- [x] **Phase 3** — Resume Impact engine, recommendation engine, export (MD/JSON)
- [ ] **Phase 4** — LLM-powered AI code reviewer (OpenAI / Gemini integration)
- [ ] **Phase 5** — FastAPI backend, PostgreSQL persistence, user history
- [ ] **Phase 6** — GitHub OAuth login, public leaderboard, comparison view

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Fork the repo and clone your fork
git clone https://github.com/YOUR_USERNAME/github-project-auditor.git

# Create a feature branch
git checkout -b feat/your-feature-name

# Make changes and run tests
pytest tests/ -v

# Commit with a descriptive message
git commit -m "feat: add XYZ analyzer"

# Push and open a Pull Request
git push origin feat/your-feature-name
```

**Please follow the existing code style:**
- All analyzers must inherit from `BaseAnalyzer`
- New scoring constants go in `utils/constants.py`
- All new logic must have corresponding tests in `tests/`

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ for students, fresh graduates, and internship seekers.

**[⬆ Back to top](#-github-project-quality-auditor)**

</div>
