from datetime import date as dt_date, datetime, timedelta
import logging
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from analytics.database import get_db
from analytics.models import Visitor, AnalysisHistory, DailyMetric, FeatureUsage
from ua_parser import user_agent_parser

logger = logging.getLogger(__name__)

# --- Helpers ---

def parse_user_agent(ua_string: str) -> tuple[str, str]:
    """
    Parses User-Agent into a sanitized browser/OS string and a device type.
    Ensures zero PII leakage.
    """
    if not ua_string or ua_string == "Unknown":
        return "Unknown Browser / Unknown OS", "desktop"
    
    try:
        parsed = user_agent_parser.Parse(ua_string)
        
        # OS Info
        os_info = parsed.get("os", {})
        os_name = os_info.get("family", "Unknown")
        os_major = os_info.get("major")
        os_str = f"{os_name} {os_major}" if os_major else os_name
        
        # Browser Info
        ua_info = parsed.get("user_agent", {})
        browser_name = ua_info.get("family", "Unknown")
        browser_major = ua_info.get("major")
        browser_str = f"{browser_name} {browser_major}" if browser_major else browser_name
        
        sanitized_ua = f"{browser_str} / {os_str}".strip()
        
        # Device Family / Type
        device_info = parsed.get("device", {})
        device_family = device_info.get("family", "").lower()
        os_family = os_info.get("family", "").lower()
        
        if "bot" in device_family or "spider" in device_family:
            device_type = "bot"
        elif os_family in ["ios", "android"] or any(k in ua_string.lower() for k in ["iphone", "android", "mobile"]):
            if "ipad" in ua_string.lower() or "tablet" in ua_string.lower():
                device_type = "tablet"
            else:
                device_type = "mobile"
        else:
            device_type = "desktop"
            
        return sanitized_ua, device_type
    except Exception:
        logger.exception("Failed to parse user agent")
        return "Unknown Browser / OS", "desktop"


def parse_country(accept_language: str) -> str:
    """Parses standard Accept-Language header to extract country code."""
    if not accept_language:
        return "US"
    try:
        primary_tag = accept_language.split(",")[0].strip()
        if "-" in primary_tag:
            parts = primary_tag.split("-")
            country = parts[-1].upper()
            if len(country) == 2:
                return country
        return "US"
    except Exception:
        return "US"

# --- Tracking Service ---

class AnalyticsService:
    @staticmethod
    def record_visit(visitor_id: str, session_id: str, user_agent_raw: str, accept_language: str) -> None:
        """Records a user page visit, updating unique and daily metrics."""
        sanitized_ua, device_type = parse_user_agent(user_agent_raw)
        country = parse_country(accept_language)
        today = dt_date.today()
        
        with get_db() as session:
            # 1. Update or create Visitor
            visitor = session.query(Visitor).filter_by(visitor_id=visitor_id).first()
            is_new_visitor = False
            
            if visitor:
                visitor.last_seen = datetime.utcnow()
                visitor.visit_count += 1
                visitor.session_id = session_id  # Update with current active session
            else:
                is_new_visitor = True
                visitor = Visitor(
                    visitor_id=visitor_id,
                    session_id=session_id,
                    user_agent=sanitized_ua,
                    device_type=device_type,
                    country=country,
                    visit_count=1
                )
                session.add(visitor)
            
            # 2. Update Daily Metrics
            metric = session.query(DailyMetric).filter_by(date=today).first()
            if not metric:
                metric = DailyMetric(
                    date=today,
                    total_visitors=1,
                    unique_visitors=1 if is_new_visitor else 0,
                    analyses_performed=0
                )
                session.add(metric)
            else:
                metric.total_visitors += 1
                if is_new_visitor:
                    metric.unique_visitors += 1
                    
            session.commit()

    @staticmethod
    def record_analysis(visitor_id: str, repo_url: str, repo_name: str, total_score: int, resume_impact_score: int, duration: float, language: str) -> None:
        """Records a successful analysis event."""
        today = dt_date.today()
        with get_db() as session:
            # 1. Create AnalysisHistory record
            history = AnalysisHistory(
                visitor_id=visitor_id,
                repository_url=repo_url,
                repository_name=repo_name,
                total_score=total_score,
                resume_impact_score=resume_impact_score,
                analysis_duration=duration,
                status="success",
                language=language
            )
            session.add(history)
            
            # 2. Update Daily Metrics
            metric = session.query(DailyMetric).filter_by(date=today).first()
            if not metric:
                metric = DailyMetric(
                    date=today,
                    total_visitors=0,
                    unique_visitors=0,
                    analyses_performed=1
                )
                session.add(metric)
            else:
                metric.analyses_performed += 1
                
            session.commit()

    @staticmethod
    def record_error(visitor_id: str, repo_url: str, repo_name: str, error_type: str) -> None:
        """Records a failed analysis event."""
        with get_db() as session:
            history = AnalysisHistory(
                visitor_id=visitor_id,
                repository_url=repo_url,
                repository_name=repo_name,
                status="failed",
                error_type=error_type
            )
            session.add(history)
            session.commit()

    @staticmethod
    def record_feature_usage(feature_name: str) -> None:
        """Increments a feature usage counter."""
        with get_db() as session:
            feature = session.query(FeatureUsage).filter_by(feature_name=feature_name).first()
            if not feature:
                feature = FeatureUsage(feature_name=feature_name, usage_count=1)
                session.add(feature)
            else:
                feature.usage_count += 1
            session.commit()

    # --- Dashboard Reporting Queries ---

    @staticmethod
    def _apply_date_filter(query, model_class, field_name: str, days: int | None):
        """Helper to filter query by date range."""
        if days is not None and days > 0:
            cutoff = datetime.utcnow() - timedelta(days=days)
            field = getattr(model_class, field_name)
            return query.filter(field >= cutoff)
        return query

    @classmethod
    def get_overview_stats(cls, days: int | None = None) -> dict:
        """Computes key metrics cards values for dashboard."""
        with get_db() as session:
            # 1. Total Analyses (filtered)
            analyses_query = session.query(func.count(AnalysisHistory.analysis_id)).filter(AnalysisHistory.status == "success")
            analyses_query = cls._apply_date_filter(analyses_query, AnalysisHistory, "analysis_timestamp", days)
            total_analyses = analyses_query.scalar() or 0

            # 2. Unique Visitors (filtered)
            visitors_query = session.query(func.count(Visitor.visitor_id))
            visitors_query = cls._apply_date_filter(visitors_query, Visitor, "last_seen", days)
            unique_visitors = visitors_query.scalar() or 0

            # 3. Total Page Views (filtered)
            if days is not None:
                # Sum daily metrics total_visitors
                metric_query = session.query(func.sum(DailyMetric.total_visitors))
                # For daily metrics, the date field is Date type
                if days > 0:
                    cutoff_date = dt_date.today() - timedelta(days=days)
                    metric_query = metric_query.filter(DailyMetric.date >= cutoff_date)
                total_visits = metric_query.scalar() or 0
            else:
                total_visits = session.query(func.sum(Visitor.visit_count)).scalar() or 0

            # 4. Returning Users count
            returning_query = session.query(func.count(Visitor.visitor_id)).filter(Visitor.visit_count > 1)
            returning_query = cls._apply_date_filter(returning_query, Visitor, "last_seen", days)
            returning_users = returning_query.scalar() or 0

            # 5. Average Analysis Duration
            duration_query = session.query(func.avg(AnalysisHistory.analysis_duration)).filter(AnalysisHistory.status == "success")
            duration_query = cls._apply_date_filter(duration_query, AnalysisHistory, "analysis_timestamp", days)
            avg_duration = duration_query.scalar() or 0.0

            # 6. Success/Failure Rate
            success_count = total_analyses
            failed_query = session.query(func.count(AnalysisHistory.analysis_id)).filter(AnalysisHistory.status == "failed")
            failed_query = cls._apply_date_filter(failed_query, AnalysisHistory, "analysis_timestamp", days)
            failed_count = failed_query.scalar() or 0
            total_attempts = success_count + failed_count
            success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 100.0

            # 7. Active Users (DAU / WAU / MAU)
            dau = session.query(func.count(Visitor.visitor_id)).filter(Visitor.last_seen >= datetime.utcnow() - timedelta(days=1)).scalar() or 0
            wau = session.query(func.count(Visitor.visitor_id)).filter(Visitor.last_seen >= datetime.utcnow() - timedelta(days=7)).scalar() or 0
            mau = session.query(func.count(Visitor.visitor_id)).filter(Visitor.last_seen >= datetime.utcnow() - timedelta(days=30)).scalar() or 0

            return {
                "total_analyses": total_analyses,
                "unique_visitors": unique_visitors,
                "total_visits": total_visits,
                "returning_users": returning_users,
                "returning_rate": (returning_users / unique_visitors * 100) if unique_visitors > 0 else 0.0,
                "avg_duration": round(avg_duration, 2),
                "success_rate": round(success_rate, 1),
                "dau": dau,
                "wau": wau,
                "wau_val": wau,
                "mau": mau
            }

    @staticmethod
    def get_daily_metrics(days: int = 30) -> list[dict]:
        """Gets timeline of daily metrics for the charts."""
        cutoff_date = dt_date.today() - timedelta(days=days)
        with get_db() as session:
            metrics = (
                session.query(DailyMetric)
                .filter(DailyMetric.date >= cutoff_date)
                .order_by(DailyMetric.date.asc())
                .all()
            )
            return [
                {
                    "date": m.date.strftime("%Y-%m-%d"),
                    "total_visitors": m.total_visitors,
                    "unique_visitors": m.unique_visitors,
                    "analyses_performed": m.analyses_performed
                }
                for m in metrics
            ]

    @classmethod
    def get_top_repositories(cls, days: int | None = None, limit: int = 5) -> list[tuple[str, int]]:
        """Finds the most frequently audited repositories."""
        with get_db() as session:
            query = (
                session.query(AnalysisHistory.repository_name, func.count(AnalysisHistory.analysis_id).label("count"))
                .filter(AnalysisHistory.status == "success")
            )
            query = cls._apply_date_filter(query, AnalysisHistory, "analysis_timestamp", days)
            results = (
                query.group_by(AnalysisHistory.repository_name)
                .order_by(desc("count"))
                .limit(limit)
                .all()
            )
            return [(r[0], r[1]) for r in results]

    @classmethod
    def get_language_distribution(cls, days: int | None = None, limit: int = 5) -> list[tuple[str, int]]:
        """Gets language breakdown of successful audits."""
        with get_db() as session:
            query = (
                session.query(AnalysisHistory.language, func.count(AnalysisHistory.analysis_id).label("count"))
                .filter(AnalysisHistory.status == "success")
                .filter(AnalysisHistory.language.isnot(None))
            )
            query = cls._apply_date_filter(query, AnalysisHistory, "analysis_timestamp", days)
            results = (
                query.group_by(AnalysisHistory.language)
                .order_by(desc("count"))
                .limit(limit)
                .all()
            )
            return [(r[0], r[1]) for r in results]

    @classmethod
    def get_device_distribution(cls, days: int | None = None) -> list[tuple[str, int]]:
        """Gets device type breakdown of visitors."""
        with get_db() as session:
            query = session.query(Visitor.device_type, func.count(Visitor.visitor_id).label("count"))
            query = cls._apply_date_filter(query, Visitor, "last_seen", days)
            results = query.group_by(Visitor.device_type).order_by(desc("count")).all()
            return [(r[0], r[1]) for r in results]

    @classmethod
    def get_country_distribution(cls, days: int | None = None, limit: int = 5) -> list[tuple[str, int]]:
        """Gets country breakdown of visitors based on language headers."""
        with get_db() as session:
            query = session.query(Visitor.country, func.count(Visitor.visitor_id).label("count")).filter(Visitor.country.isnot(None))
            query = cls._apply_date_filter(query, Visitor, "last_seen", days)
            results = query.group_by(Visitor.country).order_by(desc("count")).limit(limit).all()
            return [(r[0], r[1]) for r in results]

    @staticmethod
    def get_feature_usage() -> list[dict]:
        """Gets all features usage statistics."""
        with get_db() as session:
            features = session.query(FeatureUsage).order_by(desc(FeatureUsage.usage_count)).all()
            return [{"feature_name": f.feature_name, "usage_count": f.usage_count} for f in features]

    @classmethod
    def get_score_distribution(cls, days: int | None = None) -> dict[str, list[int]]:
        """Gets list of score outcomes for histograms."""
        with get_db() as session:
            query = session.query(AnalysisHistory.total_score, AnalysisHistory.resume_impact_score).filter(AnalysisHistory.status == "success")
            query = cls._apply_date_filter(query, AnalysisHistory, "analysis_timestamp", days)
            results = query.all()
            
            return {
                "total_scores": [r[0] for r in results if r[0] is not None],
                "resume_impact_scores": [r[1] for r in results if r[1] is not None]
            }

    @staticmethod
    def export_analytics_data() -> dict[str, list[dict]]:
        """Exports raw DB records as dictionaries for admin CSV/JSON export."""
        with get_db() as session:
            visitors = session.query(Visitor).all()
            history = session.query(AnalysisHistory).all()
            daily = session.query(DailyMetric).all()
            
            return {
                "visitors": [
                    {
                        "visitor_id": v.visitor_id[:8],  # Truncate fingerprint hash for export privacy
                        "session_id": v.session_id,
                        "first_seen": v.first_seen.isoformat(),
                        "last_seen": v.last_seen.isoformat(),
                        "visit_count": v.visit_count,
                        "user_agent": v.user_agent,
                        "device_type": v.device_type,
                        "country": v.country
                    }
                    for v in visitors
                ],
                "analyses": [
                    {
                        "analysis_id": h.analysis_id,
                        "visitor_id": h.visitor_id[:8] if h.visitor_id else None,
                        "repository_name": h.repository_name,
                        "repository_url": h.repository_url,
                        "analysis_timestamp": h.analysis_timestamp.isoformat(),
                        "total_score": h.total_score,
                        "resume_impact_score": h.resume_impact_score,
                        "analysis_duration": h.analysis_duration,
                        "status": h.status,
                        "error_type": h.error_type,
                        "language": h.language
                    }
                    for h in history
                ],
                "daily_metrics": [
                    {
                        "date": d.date.strftime("%Y-%m-%d"),
                        "total_visitors": d.total_visitors,
                        "unique_visitors": d.unique_visitors,
                        "analyses_performed": d.analyses_performed
                    }
                    for d in daily
                ]
            }

    @classmethod
    def generate_report_markdown(cls, days: int = 7) -> str:
        """Generates a text report in Markdown summarizing platform growth and usage."""
        stats = cls.get_overview_stats(days)
        repos = cls.get_top_repositories(days, limit=5)
        langs = cls.get_language_distribution(days, limit=5)
        devices = cls.get_device_distribution(days)
        countries = cls.get_country_distribution(days, limit=5)

        title = "Weekly Usage Summary" if days == 7 else "Monthly Usage Summary"
        
        md = []
        md.append(f"# GitHub Project Quality Auditor — {title}")
        md.append(f"Report generated on: {dt_date.today().strftime('%Y-%m-%d')}\n")
        
        md.append("## 📈 Core Performance Indicators")
        md.append(f"- **Total Sessions (Page Views)**: {stats['total_visits']}")
        md.append(f"- **Unique Visitors**: {stats['unique_visitors']}")
        md.append(f"- **Successful Repository Analyses**: {stats['total_analyses']}")
        md.append(f"- **Analysis Success Rate**: {stats['success_rate']}%")
        md.append(f"- **Average Analysis Time**: {stats['avg_duration']} seconds")
        md.append(f"- **Returning User Rate**: {stats['returning_rate']:.1f}%\n")
        
        md.append("## 📊 User Engagement Metrics")
        md.append(f"- **Daily Active Users (DAU)**: {stats['dau']}")
        md.append(f"- **Weekly Active Users (WAU)**: {stats['wau_val']}")
        md.append(f"- **Monthly Active Users (MAU)**: {stats['mau']}\n")
        
        md.append("## 📦 Popular Repositories")
        if repos:
            for idx, (name, count) in enumerate(repos, 1):
                md.append(f"{idx}. **{name}** — {count} analyses")
        else:
            md.append("*No repository audits logged in this period.*")
        md.append("")

        md.append("## 💻 Tech Stack & Client Distribution")
        md.append("### Top Languages Audited")
        if langs:
            for lang, count in langs:
                md.append(f"- **{lang}**: {count} audits")
        else:
            md.append("*No languages detected.*")
        
        md.append("\n### Devices & OS Breakdown")
        for dev, count in devices:
            md.append(f"- **{dev.capitalize()}**: {count} users")

        md.append("\n### Approximate Geolocation (by Language)")
        if countries:
            for country, count in countries:
                md.append(f"- **{country}**: {count} visitors")
        else:
            md.append("*No geographic data inferred.*")
            
        return "\n".join(md)
