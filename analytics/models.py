from datetime import date as dt_date, datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Visitor(Base):
    __tablename__ = "visitors"
    
    visitor_id = Column(String(64), primary_key=True)  # SHA-256 fingerprint of IP + UA
    session_id = Column(String(36), nullable=False)    # UUID generated per Streamlit session
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    visit_count = Column(Integer, default=1)
    user_agent = Column(String(256))                    # Sanitized User-Agent (Browser/OS)
    device_type = Column(String(50))                    # desktop, mobile, tablet
    country = Column(String(10))                        # 2-letter country code (Accept-Language)

    analyses = relationship("AnalysisHistory", back_populates="visitor")

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    visitor_id = Column(String(64), ForeignKey("visitors.visitor_id"), nullable=True)
    repository_url = Column(String(512), nullable=False)
    repository_name = Column(String(256), nullable=False)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    total_score = Column(Integer, nullable=True)
    resume_impact_score = Column(Integer, nullable=True)
    analysis_duration = Column(Float, nullable=True)     # seconds taken for analysis
    status = Column(String(50), default="success")       # success, failed
    error_type = Column(String(100), nullable=True)      # Exception class name if failed
    language = Column(String(100), nullable=True)        # Primary repo language

    visitor = relationship("Visitor", back_populates="analyses")

class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    
    date = Column(Date, primary_key=True)               # YYYY-MM-DD
    total_visitors = Column(Integer, default=0)         # Total session views
    unique_visitors = Column(Integer, default=0)        # Unique fingerprint views
    analyses_performed = Column(Integer, default=0)     # Successful analyses count

class FeatureUsage(Base):
    __tablename__ = "feature_usage"
    
    feature_name = Column(String(100), primary_key=True)
    usage_count = Column(Integer, default=0)
