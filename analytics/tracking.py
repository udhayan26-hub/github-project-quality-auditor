import hashlib
import os
import uuid
import logging
import streamlit as st
from analytics.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Run-once module level salt if GITHUB_DEPLOYMENT or ANALYTICS_SALT is missing.
# Changing on restart enforces additional privacy protection.
RUN_TIME_SALT = os.getenv("ANALYTICS_SALT", uuid.uuid4().hex)

def get_visitor_fingerprint() -> tuple[str, str, str]:
    """
    Computes a privacy-safe visitor fingerprint from connection headers.
    Returns: (visitor_id, user_agent_raw, accept_language)
    """
    try:
        headers = st.context.headers
        # Get client IP (support cloud proxies)
        ip_raw = headers.get("X-Forwarded-For", "127.0.0.1")
        ip = ip_raw.split(",")[0].strip()
        
        # Get User Agent & Language
        user_agent = headers.get("User-Agent", "Unknown")
        accept_language = headers.get("Accept-Language", "en-US")
    except Exception:
        # Fallback for local testing if st.context is unavailable
        ip = "127.0.0.1"
        user_agent = "Unknown"
        accept_language = "en-US"

    # Compute hash of IP + User-Agent + Salt
    hash_payload = f"{ip}:{user_agent}:{RUN_TIME_SALT}".encode("utf-8")
    visitor_id = hashlib.sha256(hash_payload).hexdigest()
    
    return visitor_id, user_agent, accept_language


def track_session() -> None:
    """Allocates a unique session UUID per browser tab session if not present."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())


def track_visit() -> None:
    """Tracks page visits once per Streamlit session state lifetime."""
    track_session()
    
    if "visit_tracked" not in st.session_state:
        try:
            visitor_id, user_agent_raw, accept_language = get_visitor_fingerprint()
            st.session_state["visitor_id"] = visitor_id
            
            # Record via service
            AnalyticsService.record_visit(
                visitor_id=visitor_id,
                session_id=st.session_state["session_id"],
                user_agent_raw=user_agent_raw,
                accept_language=accept_language
            )
            st.session_state["visit_tracked"] = True
            logger.info("New session page-visit tracked successfully")
        except Exception:
            logger.exception("Error tracking page visit")


def track_analysis(repo_url: str, repo_name: str, total_score: int, resume_impact_score: int, duration: float, language: str | None) -> None:
    """Tracks a successful repository analysis event."""
    try:
        visitor_id = st.session_state.get("visitor_id", "Unknown")
        AnalyticsService.record_analysis(
            visitor_id=visitor_id,
            repo_url=repo_url,
            repo_name=repo_name,
            total_score=total_score,
            resume_impact_score=resume_impact_score,
            duration=duration,
            language=language or "Unknown"
        )
        logger.info(f"Successful audit tracked for {repo_name}")
    except Exception:
        logger.exception("Error tracking analysis event")


def track_error(repo_url: str, repo_name: str, error: Exception) -> None:
    """Tracks a failed analysis event."""
    try:
        visitor_id = st.session_state.get("visitor_id", "Unknown")
        error_type = error.__class__.__name__
        AnalyticsService.record_error(
            visitor_id=visitor_id,
            repo_url=repo_url,
            repo_name=repo_name,
            error_type=error_type
        )
        logger.info(f"Analysis failure tracked for {repo_name} (Error: {error_type})")
    except Exception:
        logger.exception("Error tracking failure event")


def track_feature_usage(feature_name: str) -> None:
    """Tracks a specific feature invocation (e.g., Download Markdown, View Resume Impact)."""
    try:
        AnalyticsService.record_feature_usage(feature_name)
        logger.info(f"Feature usage tracked: {feature_name}")
    except Exception:
        logger.exception(f"Error tracking feature usage: {feature_name}")
