# Changelog

All notable changes to the **GitHub Project Quality Auditor** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-06-24
### Added
- **Docker Support**: Created `Dockerfile`, `docker-compose.yml`, and `.dockerignore` for containerized environments.
- **CI/CD Integration**: Integrated GitHub Actions CI workflow (`.github/workflows/ci.yml`) to execute pytest testing suites on changes.
- **Project Structure**: Introduced dedicated `src/` folder structure and custom `pytest.ini` config.
- **Structured Documentation**: Created a detailed `docs/` folder containing architecture guides (`docs/index.md`) and API contracts (`docs/api.md`).

## [1.1.0] — 2026-06-18
### Added
- **Usage Telemetry Database**: Built a database layer using SQLAlchemy (SQLite/PostgreSQL compatible) to track visits and audits.
- **Anonymized Fingerprinting**: Implemented privacy-first, salted SHA-256 visitor fingerprint tracking.
- **Interactive Admin Dashboard**: Designed a password-protected analytics control panel with Altair charts, geographic telemetry, feature counters, and CSV/JSON downloads.
- **Unit Test Suite**: Developed 8 unit tests in `tests/test_analytics.py` confirming database operations and telemetry stability.

### Changed
- Refactored frontend theme from dark glassmorphism to an **enterprise light theme** resembling Stripe and Linear, featuring responsive flex grids, custom CSS fonts, and semantic score badges.
- Renamed main entry point file from `app.py` to `streamlit_app.py` to support official Streamlit Community Cloud automatic deployments.

## [1.0.0] — 2026-06-16
### Added
- **GitHub Service**: Established REST API v3 client with error caching (404, rate limits) and header session reuse.
- **Audit Engines**: Crafted 6 independent strategy-pattern analyzers covering README content, directories structure, testing folders, Docker, CI/CD pipelines, and documentation.
- **Resume Impact Formula**: Devised a weighted score emphasizing testing (30%) and CI/CD (20%) over other metrics to gauge candidate maturity.
- **Testing Core**: Established initial core tests achieving 44 passing cases across scoring math, regex URL parsers, and recommendation outputs.
