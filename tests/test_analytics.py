import pytest
from datetime import date as dt_date, datetime
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Override the database for the test duration to be in-memory SQLite
import analytics.database as db
db.DATABASE_URL = "sqlite:///:memory:"
db.engine = create_engine(db.DATABASE_URL, connect_args={"check_same_thread": False})
db.session_factory = sessionmaker(bind=db.engine)
db.db_session = scoped_session(db.session_factory)

# Import models and initialization
from analytics.models import Base, Visitor, AnalysisHistory, DailyMetric, FeatureUsage
from analytics.analytics_service import AnalyticsService, parse_user_agent, parse_country
from analytics.tracking import RUN_TIME_SALT, get_visitor_fingerprint

# Initialize the schema in memory
db.init_db()


@pytest.fixture(autouse=True)
def clean_db():
    """Clear database tables before each test case."""
    with db.get_db() as session:
        session.query(AnalysisHistory).delete()
        session.query(Visitor).delete()
        session.query(DailyMetric).delete()
        session.query(FeatureUsage).delete()
        session.commit()
    yield


def test_parse_user_agent():
    # Test Desktop User-Agent
    desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    sanitized, device = parse_user_agent(desktop_ua)
    assert "Chrome 120" in sanitized
    assert "Windows 10" in sanitized
    assert device == "desktop"

    # Test Mobile User-Agent
    mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    sanitized, device = parse_user_agent(mobile_ua)
    assert "Mobile Safari" in sanitized or "Safari" in sanitized
    assert "iOS" in sanitized
    assert device == "mobile"

    # Test Unknown User-Agent
    sanitized, device = parse_user_agent("")
    assert "Unknown Browser" in sanitized
    assert device == "desktop"


def test_parse_country():
    assert parse_country("en-IN,en;q=0.9,hi;q=0.8") == "IN"
    assert parse_country("en-US,en;q=0.5") == "US"
    assert parse_country("fr-FR") == "FR"
    assert parse_country("") == "US"
    assert parse_country("invalid_header") == "US"


def test_record_visit_new_and_returning():
    visitor_id = "test_fingerprint_123"
    session_id = "test_session_abc"
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
    lang = "en-IN,en;q=0.9"

    # 1. Record first visit (New Visitor)
    AnalyticsService.record_visit(visitor_id, session_id, ua, lang)

    with db.get_db() as session:
        visitor = session.query(Visitor).filter_by(visitor_id=visitor_id).first()
        assert visitor is not None
        assert visitor.visit_count == 1
        assert visitor.device_type == "desktop"
        assert visitor.country == "IN"

        metric = session.query(DailyMetric).filter_by(date=dt_date.today()).first()
        assert metric is not None
        assert metric.total_visitors == 1
        assert metric.unique_visitors == 1

    # 2. Record second visit (Returning Visitor)
    AnalyticsService.record_visit(visitor_id, session_id, ua, lang)

    with db.get_db() as session:
        visitor = session.query(Visitor).filter_by(visitor_id=visitor_id).first()
        assert visitor.visit_count == 2

        metric = session.query(DailyMetric).filter_by(date=dt_date.today()).first()
        assert metric.total_visitors == 2
        assert metric.unique_visitors == 1  # Unique remains 1


def test_record_analysis():
    visitor_id = "test_fingerprint_123"
    session_id = "test_session_abc"
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"

    # Set up visitor first
    AnalyticsService.record_visit(visitor_id, session_id, ua, "")

    # Record successful analysis
    AnalyticsService.record_analysis(
        visitor_id=visitor_id,
        repo_url="https://github.com/tiangolo/fastapi",
        repo_name="tiangolo/fastapi",
        total_score=92,
        resume_impact_score=94,
        duration=1.45,
        language="Python"
    )

    with db.get_db() as session:
        analysis = session.query(AnalysisHistory).filter_by(repository_name="tiangolo/fastapi").first()
        assert analysis is not None
        assert analysis.total_score == 92
        assert analysis.resume_impact_score == 94
        assert analysis.status == "success"
        assert analysis.language == "Python"

        metric = session.query(DailyMetric).filter_by(date=dt_date.today()).first()
        assert metric.analyses_performed == 1


def test_record_error():
    visitor_id = "test_fingerprint_123"
    
    AnalyticsService.record_error(
        visitor_id=visitor_id,
        repo_url="https://github.com/owner/nonexistent",
        repo_name="owner/nonexistent",
        error_type="RepoNotFoundError"
    )

    with db.get_db() as session:
        analysis = session.query(AnalysisHistory).filter_by(status="failed").first()
        assert analysis is not None
        assert analysis.error_type == "RepoNotFoundError"
        assert analysis.repository_name == "owner/nonexistent"


def test_record_feature_usage():
    AnalyticsService.record_feature_usage("Download Markdown Report")
    AnalyticsService.record_feature_usage("Download Markdown Report")
    AnalyticsService.record_feature_usage("Download JSON Report")

    with db.get_db() as session:
        feat_md = session.query(FeatureUsage).filter_by(feature_name="Download Markdown Report").first()
        assert feat_md.usage_count == 2

        feat_json = session.query(FeatureUsage).filter_by(feature_name="Download JSON Report").first()
        assert feat_json.usage_count == 1


def test_get_overview_stats():
    # Set up some dummy visits and analyses
    AnalyticsService.record_visit("v1", "s1", "", "")
    AnalyticsService.record_visit("v2", "s2", "", "")
    AnalyticsService.record_visit("v1", "s1", "", "") # Returning v1

    AnalyticsService.record_analysis("v1", "url1", "repo1", 80, 85, 1.2, "Python")
    AnalyticsService.record_analysis("v2", "url2", "repo2", 60, 65, 0.8, "JavaScript")
    AnalyticsService.record_error("v1", "url3", "repo3", "RateLimitError")

    stats = AnalyticsService.get_overview_stats()
    assert stats["total_analyses"] == 2
    assert stats["unique_visitors"] == 2
    assert stats["returning_users"] == 1
    assert stats["success_rate"] == 66.7  # 2 successes out of 3 attempts
    assert stats["avg_duration"] == 1.0   # (1.2 + 0.8) / 2


def test_generate_report_markdown():
    AnalyticsService.record_visit("v1", "s1", "", "")
    AnalyticsService.record_analysis("v1", "url1", "repo1", 80, 85, 1.2, "Python")
    
    report_md = AnalyticsService.generate_report_markdown()
    assert "# GitHub Project Quality Auditor" in report_md
    assert "Core Performance Indicators" in report_md
    assert "repo1" in report_md
    assert "Python" in report_md
