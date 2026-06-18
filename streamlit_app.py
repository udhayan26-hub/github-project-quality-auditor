"""
streamlit_app.py — Streamlit UI for the GitHub Project Quality Auditor.
Enterprise-grade light theme: clean, professional, SaaS-quality.
Inspired by Notion, Linear, Stripe Dashboard, Vercel, GitHub Enterprise.
"""

from __future__ import annotations

import logging
import time

import streamlit as st

from models.audit_report import AuditReport
from scoring.score_engine import ScoreEngine
from services.github_service import (
    GitHubService,
    GitHubServiceError,
    InvalidRepoURLError,
    RateLimitError,
    RepoNotFoundError,
    parse_github_url,
)

from analytics.database import init_db
from analytics.tracking import (
    track_visit,
    track_analysis,
    track_error,
    track_feature_usage,
)

# Initialize analytics database
init_db()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Project Quality Auditor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Full CSS theme ──────────────────────────────────────────────────────────
LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & base ─────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 14px;
    line-height: 1.6;
    color: #1F2937;
}

/* ── App background ───────────────────────────────────────────────────────── */
.stApp {
    background-color: #F9FAFB !important;
}

/* Main content padding */
.main .block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1200px;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
    box-shadow: 1px 0 4px rgba(0,0,0,0.04);
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.25rem;
}
[data-testid="stSidebar"] * {
    color: #374151 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #111827 !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #6B7280 !important;
    font-size: 0.8125rem;
}
[data-testid="stSidebar"] hr {
    border-color: #E5E7EB !important;
    margin: 1rem 0 !important;
}

/* ── Text inputs ──────────────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 8px !important;
    color: #111827 !important;
    font-size: 0.9375rem !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput > div > div > input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: #9CA3AF !important;
}
.stTextInput label {
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9375rem !important;
    padding: 10px 20px !important;
    letter-spacing: 0.01em !important;
    transition: background-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease !important;
    box-shadow: 0 1px 2px rgba(37,99,235,0.2) !important;
    width: 100%;
}
.stButton > button:hover {
    background-color: #1D4ED8 !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    background-color: #1E40AF !important;
}

/* Download buttons */
.stDownloadButton > button {
    background-color: #FFFFFF !important;
    color: #374151 !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 9px 16px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    width: 100%;
}
.stDownloadButton > button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.12) !important;
}

/* ── Metrics ──────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.06) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 1.875rem !important;
    font-weight: 700 !important;
}

/* ── Progress bars ────────────────────────────────────────────────────────── */
.stProgress {
    margin-top: 6px !important;
}
.stProgress > div > div {
    background-color: #E5E7EB !important;
    border-radius: 999px !important;
    height: 6px !important;
}
.stProgress > div > div > div {
    border-radius: 999px !important;
    height: 6px !important;
}

/* ── Expanders ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 0.9375rem !important;
    padding: 0.875rem 1rem !important;
    transition: background-color 0.15s ease !important;
}
.streamlit-expanderHeader:hover {
    background-color: #F9FAFB !important;
}
.streamlit-expanderContent {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    padding: 1rem !important;
}

/* ── Select boxes & misc inputs ───────────────────────────────────────────── */
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border-color: #D1D5DB !important;
    border-radius: 8px !important;
    color: #111827 !important;
}

/* ── Alerts / info boxes ──────────────────────────────────────────────────── */
.stAlert {
    border-radius: 8px !important;
}

/* ── Dividers ─────────────────────────────────────────────────────────────── */
hr {
    border-color: #E5E7EB !important;
    margin: 1.5rem 0 !important;
}

/* ── Tables ───────────────────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
}

/* ── Hide Streamlit chrome ────────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Spinner ──────────────────────────────────────────────────────────────── */
.stSpinner > div > div {
    border-top-color: #2563EB !important;
}

/* ── Custom component classes ─────────────────────────────────────────────── */

/* Page header */
.page-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 2rem;
}
.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #111827;
    margin: 0 0 0.375rem;
    letter-spacing: -0.02em;
}
.page-header p {
    color: #6B7280;
    font-size: 0.9375rem;
    margin: 0;
}

/* Search bar container */
.search-bar-wrap {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
}

/* Section label */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.875rem;
}

/* Section heading */
.section-heading {
    font-size: 1.125rem;
    font-weight: 700;
    color: #111827;
    margin: 0 0 0.25rem;
}

/* Repo header card */
.repo-header {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.repo-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.25rem;
}
.repo-desc {
    color: #6B7280;
    font-size: 0.9375rem;
    margin-bottom: 0.75rem;
}
.repo-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
}
.repo-meta-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    color: #6B7280;
    font-size: 0.8125rem;
    font-weight: 500;
}
.repo-meta-item strong { color: #374151; }
.lang-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: #EFF6FF;
    color: #1D4ED8;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #BFDBFE;
}
.topic-tag {
    display: inline-block;
    background: #F3F4F6;
    color: #4B5563;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 1px solid #E5E7EB;
    margin: 2px 3px 2px 0;
}

/* Hero score tiles */
.hero-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.hero-tile {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}
.hero-tile::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}
.hero-tile.score-tile::before { background: linear-gradient(90deg, #2563EB, #3B82F6); }
.hero-tile.resume-tile::before { background: linear-gradient(90deg, #059669, #10B981); }
.hero-tile-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.75rem;
}
.hero-tile-value {
    font-size: 3rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
    letter-spacing: -0.03em;
    margin-bottom: 0.375rem;
}
.hero-tile-sub {
    color: #9CA3AF;
    font-size: 0.9375rem;
    margin-bottom: 0.875rem;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 999px;
}

/* Score card grid */
.score-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.score-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.score-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.score-card-icon { font-size: 1.125rem; margin-bottom: 0.75rem; }
.score-card-name {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.score-card-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.score-card-max {
    font-size: 0.8125rem;
    color: #9CA3AF;
    margin-bottom: 0.75rem;
}
.score-progress-track {
    height: 5px;
    background: #F3F4F6;
    border-radius: 999px;
    overflow: hidden;
}
.score-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
}

/* Detail check rows */
.check-list { list-style: none; padding: 0; margin: 0; }
.check-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.875rem 0;
    border-bottom: 1px solid #F3F4F6;
}
.check-item:last-child { border-bottom: none; }
.check-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.625rem;
    font-weight: 700;
    margin-top: 1px;
}
.check-icon.pass { background: #D1FAE5; color: #065F46; }
.check-icon.fail { background: #FEE2E2; color: #991B1B; }
.check-body { flex: 1; }
.check-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.25rem;
}
.check-note {
    font-size: 0.8125rem;
    color: #6B7280;
    line-height: 1.5;
}
.check-pts {
    flex-shrink: 0;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
}
.check-pts.pass { background: #D1FAE5; color: #065F46; }
.check-pts.fail { background: #FEE2E2; color: #991B1B; }

/* Recommendation cards */
.rec-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 3px solid;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s ease;
}
.rec-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.rec-card.critical { border-left-color: #EF4444; }
.rec-card.high     { border-left-color: #F97316; }
.rec-card.medium   { border-left-color: #3B82F6; }
.rec-card.low      { border-left-color: #6B7280; }

.rec-header { display: flex; align-items: center; gap: 0.625rem; margin-bottom: 0.75rem; }
.priority-badge {
    font-size: 0.6875rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.priority-badge.critical { background: #FEE2E2; color: #B91C1C; }
.priority-badge.high     { background: #FFEDD5; color: #C2410C; }
.priority-badge.medium   { background: #DBEAFE; color: #1D4ED8; }
.priority-badge.low      { background: #F3F4F6; color: #4B5563; }

.category-badge {
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    color: #6B7280;
}
.rec-title {
    font-size: 0.9375rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.5rem;
}
.rec-section-label {
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #9CA3AF;
    margin-bottom: 0.25rem;
    margin-top: 0.625rem;
}
.rec-action {
    font-size: 0.875rem;
    color: #374151;
    line-height: 1.55;
}
.rec-impact {
    font-size: 0.875rem;
    color: #6B7280;
    line-height: 1.55;
    font-style: italic;
}
.rec-code {
    margin-top: 0.75rem;
    background: #F8FAFC;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 0.8125rem;
    color: #1E3A5F;
    white-space: pre-wrap;
    overflow-x: auto;
}

/* Summary stat strip */
.summary-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.strip-item {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.strip-num {
    font-size: 1.5rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.strip-lbl {
    font-size: 0.75rem;
    font-weight: 500;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Export section */
.export-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

/* Empty state */
.empty-state {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 3.5rem 2rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}
.empty-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.5rem;
}
.empty-sub {
    color: #6B7280;
    font-size: 0.9375rem;
    max-width: 420px;
    margin: 0 auto 2rem;
    line-height: 1.6;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    max-width: 640px;
    margin: 0 auto;
}
.feature-item {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.feature-icon { font-size: 1.25rem; margin-bottom: 0.375rem; }
.feature-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.125rem;
}
.feature-pts {
    font-size: 0.6875rem;
    color: #9CA3AF;
}

/* Footer */
.app-footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #E5E7EB;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.footer-left {
    font-size: 0.8125rem;
    color: #9CA3AF;
}
.footer-right {
    font-size: 0.8125rem;
    color: #9CA3AF;
}

/* Sidebar logo area */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid #E5E7EB;
}
.sidebar-logo-icon {
    width: 34px;
    height: 34px;
    background: #EFF6FF;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.125rem;
    border: 1px solid #BFDBFE;
}
.sidebar-logo-text {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}
.sidebar-logo-sub {
    font-size: 0.6875rem;
    color: #9CA3AF;
}

/* Sidebar section */
.sidebar-section-title {
    font-size: 0.6875rem;
    font-weight: 700;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.75rem;
}
.weight-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.375rem 0;
    border-bottom: 1px solid #F3F4F6;
    font-size: 0.8125rem;
}
.weight-row:last-child { border-bottom: none; }
.weight-label { color: #4B5563; font-weight: 500; }
.weight-val { color: #2563EB; font-weight: 700; font-size: 0.75rem; }
.weight-val.high { color: #059669; }

/* Step list */
.step-list { list-style: none; padding: 0; margin: 0; }
.step-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.5rem 0;
    font-size: 0.8125rem;
    color: #4B5563;
    align-items: flex-start;
}
.step-num {
    flex-shrink: 0;
    width: 18px;
    height: 18px;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.625rem;
    font-weight: 700;
    color: #1D4ED8;
    margin-top: 1px;
}

/* Info callout */
.info-callout {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    font-size: 0.8125rem;
    color: #1D4ED8;
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    margin-bottom: 1rem;
}
.success-callout {
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    font-size: 0.9375rem;
    font-weight: 600;
    color: #065F46;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 1rem;
}

/* Detected badge */
.detected-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #065F46;
    margin-top: 0.5rem;
}

/* Expander section label */
.exp-header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}
.exp-score-badge {
    font-size: 0.8125rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 999px;
    margin-left: auto;
}

/* Rec filter bar */
.rec-filter-bar {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    border: 1px solid;
}
.filter-chip.critical { background:#FEF2F2; border-color:#FCA5A5; color:#B91C1C; }
.filter-chip.high     { background:#FFF7ED; border-color:#FDBA74; color:#C2410C; }
.filter-chip.medium   { background:#EFF6FF; border-color:#93C5FD; color:#1D4ED8; }
.filter-chip.low      { background:#F9FAFB; border-color:#D1D5DB; color:#4B5563; }

/* Audit timestamp */
.audit-stamp {
    font-size: 0.75rem;
    color: #9CA3AF;
    display: flex;
    align-items: center;
    gap: 0.375rem;
}
</style>
"""

# ─── Color helpers ───────────────────────────────────────────────────────────
def _score_color(score: int, max_score: int) -> tuple[str, str, str]:
    """Return (fill_color, bg_color, text_color) based on ratio."""
    ratio = score / max_score if max_score else 0
    if ratio >= 0.80:
        return "#10B981", "#D1FAE5", "#065F46"   # green
    elif ratio >= 0.60:
        return "#3B82F6", "#DBEAFE", "#1D4ED8"   # blue
    elif ratio >= 0.40:
        return "#F97316", "#FFEDD5", "#C2410C"   # orange
    else:
        return "#EF4444", "#FEE2E2", "#B91C1C"   # red


def _label_for_score(score: int, max_score: int = 100) -> tuple[str, str, str]:
    from utils.constants import OVERALL_SCORE_LABELS
    ratio = score / max_score if max_score else 0
    normalized = round(ratio * 100)
    for (lo, hi), (label, color) in OVERALL_SCORE_LABELS.items():
        if lo <= normalized < hi:
            return label, color, _score_color(score, max_score)[0]
    return "Unknown", "#6B7280", "#6B7280"


# ─── Component renderers ─────────────────────────────────────────────────────

def _render_sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">📊</div>
            <div>
                <div class="sidebar-logo-text">Project Auditor</div>
                <div class="sidebar-logo-sub">GitHub Quality Analyzer</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-title">Navigation</div>', unsafe_allow_html=True)
        view = st.radio("Go to", ["Auditor Dashboard", "Admin Analytics"], label_visibility="collapsed")

        st.markdown("---")
        st.markdown('<div class="sidebar-section-title">Scoring Weights</div>', unsafe_allow_html=True)
        weights = [
            ("README",     "20 pts", "15%",  False),
            ("Structure",  "20 pts", "15%",  False),
            ("Testing",    "20 pts", "30%",  True),
            ("Docker",     "10 pts", "15%",  False),
            ("CI/CD",      "15 pts", "20%",  True),
            ("Docs",       "15 pts", "5%",   False),
        ]
        rows_html = ""
        for name, pts, weight, is_high in weights:
            wclass = "weight-val high" if is_high else "weight-val"
            rows_html += f"""
            <div class="weight-row">
                <span class="weight-label">{name} <span style="color:#9CA3AF;font-weight:400;">({pts})</span></span>
                <span class="{wclass}">{weight}</span>
            </div>"""
        st.markdown(rows_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sidebar-section-title">How It Works</div>', unsafe_allow_html=True)
        st.markdown("""
        <ol class="step-list">
            <li class="step-item"><span class="step-num">1</span>Paste a public GitHub repository URL</li>
            <li class="step-item"><span class="step-num">2</span>System fetches data via GitHub API v3</li>
            <li class="step-item"><span class="step-num">3</span>6 analyzers evaluate engineering quality</li>
            <li class="step-item"><span class="step-num">4</span>Resume Impact Score weights by recruiter priority</li>
            <li class="step-item"><span class="step-num">5</span>Actionable recommendations are generated</li>
        </ol>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="font-size:0.75rem;color:#9CA3AF;line-height:1.6;">
            Built for students, fresh graduates<br>& internship seekers.<br><br>
            Powered by GitHub REST API v3.
        </div>
        """, unsafe_allow_html=True)

    return view


def _render_score_card_html(icon: str, name: str, score: int, max_score: int) -> str:
    fill, bg, fg = _score_color(score, max_score)
    pct = round((score / max_score) * 100) if max_score else 0
    return f"""
    <div class="score-card">
        <div class="score-card-icon">{icon}</div>
        <div class="score-card-name">{name}</div>
        <div class="score-card-value">{score}</div>
        <div class="score-card-max">out of {max_score}</div>
        <div class="score-progress-track">
            <div class="score-progress-fill" style="width:{pct}%;background:{fill};"></div>
        </div>
    </div>
    """


def _render_repo_header(report: AuditReport) -> None:
    meta = report.metadata
    license_str = meta.license_name or "No license"
    lang_html = f'<span class="lang-badge">◉ {meta.language}</span>' if meta.language else ""
    topics_html = "".join(
        f'<span class="topic-tag">{t}</span>'
        for t in meta.topics[:8]
    )
    created = (meta.created_at or "")[:10]
    updated = (meta.updated_at or "")[:10]

    st.markdown(f"""
    <div class="repo-header">
        <div class="repo-title">
            {meta.full_name}
            &nbsp;<span style="font-size:0.875rem;color:#9CA3AF;font-weight:400;">
                &mdash; {license_str}
            </span>
        </div>
        <div class="repo-desc">{meta.description or "No description provided."}</div>
        <div class="repo-meta-row">
            {lang_html}
            <span class="repo-meta-item">⭐ <strong>{meta.stars:,}</strong> stars</span>
            <span class="repo-meta-item">🍴 <strong>{meta.forks:,}</strong> forks</span>
            <span class="repo-meta-item">📝 <strong>{meta.commit_count:,}</strong> commits</span>
            <span class="repo-meta-item">🐛 <strong>{meta.open_issues}</strong> issues</span>
            <span class="repo-meta-item" style="margin-left:auto;color:#9CA3AF;">
                Audited {report.audited_at[:10]}
            </span>
        </div>
        {"<div style='margin-top:0.75rem;'>" + topics_html + "</div>" if topics_html else ""}
    </div>
    """, unsafe_allow_html=True)


def _render_hero_scores(report: AuditReport) -> None:
    # Overall score
    fill, bg, fg = _score_color(report.total_score, 100)
    overall_pct = report.total_score

    # Resume impact
    rfill, rbg, rfg = _score_color(report.resume_impact_score, 100)

    st.markdown(f"""
    <div class="hero-grid">
        <div class="hero-tile score-tile">
            <div class="hero-tile-label">📋 Repository Quality Score</div>
            <div class="hero-tile-value">{report.total_score}<span style="font-size:1.5rem;color:#9CA3AF;font-weight:400;">/100</span></div>
            <div style="margin:0.75rem 0 0.875rem;">
                <div class="score-progress-track" style="height:7px;">
                    <div class="score-progress-fill" style="width:{overall_pct}%;background:{fill};"></div>
                </div>
            </div>
            <span class="status-pill" style="background:{bg};color:{fg};">
                {report.overall_label}
            </span>
        </div>
        <div class="hero-tile resume-tile">
            <div class="hero-tile-label">💼 Resume Impact Score</div>
            <div class="hero-tile-value">{report.resume_impact_score}<span style="font-size:1.5rem;color:#9CA3AF;font-weight:400;">/100</span></div>
            <div style="margin:0.75rem 0 0.875rem;">
                <div class="score-progress-track" style="height:7px;">
                    <div class="score-progress-fill" style="width:{report.resume_impact_score}%;background:{rfill};"></div>
                </div>
            </div>
            <span class="status-pill" style="background:{rbg};color:{rfg};">
                {report.resume_emoji} {report.resume_label}
            </span>
            <div style="margin-top:0.75rem;font-size:0.75rem;color:#9CA3AF;">
                Testing (30%) &amp; CI/CD (20%) weighted highest
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_category_grid(report: AuditReport) -> None:
    cards = [
        ("📄", "README",      report.readme.score,        20),
        ("🗂️", "Structure",   report.structure.score,     20),
        ("🧪", "Testing",     report.testing.score,       20),
        ("🐳", "Docker",      report.docker.score,        10),
        ("⚙️", "CI / CD",     report.cicd.score,          15),
        ("📚", "Docs",        report.documentation.score, 15),
    ]
    html = '<div class="score-grid">'
    for icon, name, score, max_score in cards:
        html += _render_score_card_html(icon, name, score, max_score)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_detail_section(label: str, icon: str, details: list,
                             score: int, max_score: int,
                             extra_html: str = "") -> None:
    fill, bg, fg = _score_color(score, max_score)
    pct = round((score / max_score) * 100) if max_score else 0
    with st.expander(f"{icon} {label}  ·  {score}/{max_score}", expanded=False):
        # Score bar inside expander
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
            <div class="score-progress-track" style="flex:1;height:6px;">
                <div class="score-progress-fill" style="width:{pct}%;background:{fill};"></div>
            </div>
            <span class="status-pill" style="background:{bg};color:{fg};font-size:0.75rem;padding:2px 10px;">
                {pct}%
            </span>
        </div>
        """, unsafe_allow_html=True)

        if extra_html:
            st.markdown(extra_html, unsafe_allow_html=True)

        # Check rows
        rows_html = '<ul class="check-list">'
        for d in details:
            icon_cls = "pass" if d.passed else "fail"
            icon_sym = "✓" if d.passed else "✕"
            pts_cls  = "pass" if d.passed else "fail"
            pts_str  = f"+{d.points_awarded}" if d.passed else f"0/{d.points_possible}"
            rows_html += f"""
            <li class="check-item">
                <span class="check-icon {icon_cls}">{icon_sym}</span>
                <div class="check-body">
                    <div class="check-title">{d.check}</div>
                    <div class="check-note">{d.note}</div>
                </div>
                <span class="check-pts {pts_cls}">{pts_str} pts</span>
            </li>"""
        rows_html += '</ul>'
        st.markdown(rows_html, unsafe_allow_html=True)


def _render_recommendations(report: AuditReport) -> None:
    from utils.constants import Priority
    recs = report.recommendations

    if not recs:
        st.markdown("""
        <div class="success-callout">
            ✅ Excellent — no major issues found. This project is in great shape!
        </div>
        """, unsafe_allow_html=True)
        return

    # Priority counts
    c_crit = sum(1 for r in recs if r.priority == Priority.CRITICAL)
    c_high = sum(1 for r in recs if r.priority == Priority.HIGH)
    c_med  = sum(1 for r in recs if r.priority == Priority.MEDIUM)
    c_low  = sum(1 for r in recs if r.priority == Priority.LOW)

    chips_html = '<div class="rec-filter-bar">'
    if c_crit: chips_html += f'<span class="filter-chip critical">🔴 Critical &nbsp;{c_crit}</span>'
    if c_high: chips_html += f'<span class="filter-chip high">🟠 High &nbsp;{c_high}</span>'
    if c_med:  chips_html += f'<span class="filter-chip medium">🔵 Medium &nbsp;{c_med}</span>'
    if c_low:  chips_html += f'<span class="filter-chip low">⚪ Low &nbsp;{c_low}</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    for i, rec in enumerate(recs, 1):
        p_lower = rec.priority.split()[-1].lower()
        code_html = ""
        if rec.code_hint:
            escaped = rec.code_hint.replace("<", "&lt;").replace(">", "&gt;")
            code_html = f'<div class="rec-code">{escaped}</div>'

        st.markdown(f"""
        <div class="rec-card {p_lower}">
            <div class="rec-header">
                <span class="priority-badge {p_lower}">{rec.priority}</span>
                <span class="category-badge">{rec.category}</span>
            </div>
            <div class="rec-title">{i}. {rec.title}</div>
            <div class="rec-section-label">What to do</div>
            <div class="rec-action">{rec.action}</div>
            <div class="rec-section-label">Recruiter impact</div>
            <div class="rec-impact">{rec.recruiter_impact}</div>
            {code_html}
        </div>
        """, unsafe_allow_html=True)


def _render_executive_summary(report: AuditReport) -> None:
    meta = report.metadata
    total_checks = sum(
        len(r.details) for r in [
            report.readme, report.structure, report.testing,
            report.docker, report.cicd, report.documentation,
        ]
    )
    passed_checks = sum(
        sum(1 for d in r.details if d.passed) for r in [
            report.readme, report.structure, report.testing,
            report.docker, report.cicd, report.documentation,
        ]
    )
    n_recs = len(report.recommendations)
    from utils.constants import Priority
    critical_recs = sum(1 for r in report.recommendations if r.priority == Priority.CRITICAL)

    st.markdown(f"""
    <div class="summary-strip">
        <div class="strip-item">
            <div class="strip-num">{report.total_score}<span style="font-size:1rem;color:#9CA3AF;">/100</span></div>
            <div class="strip-lbl">Quality Score</div>
        </div>
        <div class="strip-item">
            <div class="strip-num">{passed_checks}<span style="font-size:1rem;color:#9CA3AF;">/{total_checks}</span></div>
            <div class="strip-lbl">Checks Passed</div>
        </div>
        <div class="strip-item">
            <div class="strip-num">{n_recs}</div>
            <div class="strip-lbl">Recommendations</div>
        </div>
        <div class="strip-item">
            <div class="strip-num" style="{'color:#EF4444' if critical_recs else 'color:#10B981'}">{critical_recs}</div>
            <div class="strip-lbl">Critical Issues</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_full_report(report: AuditReport) -> None:
    track_feature_usage("View Audit Report")
    # ── Repo header ────────────────────────────────────────────────────────
    _render_repo_header(report)

    # ── Executive summary ──────────────────────────────────────────────────
    st.markdown('<div class="section-label">Executive Summary</div>', unsafe_allow_html=True)
    _render_executive_summary(report)

    # ── Hero scores ────────────────────────────────────────────────────────
    _render_hero_scores(report)

    st.markdown("---")

    # ── Engineering quality report ─────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:1rem;">
        <div class="section-label">Engineering Quality Report</div>
        <div class="section-heading">Score Breakdown</div>
        <div style="color:#6B7280;font-size:0.875rem;margin-top:0.25rem;">
            Click any category to view detailed check results.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _render_category_grid(report)

    # ── Detailed per-category expanders ───────────────────────────────────
    _render_detail_section(
        "README Quality", "📄",
        report.readme.details,
        report.readme.score, 20,
    )

    _render_detail_section(
        "Project Structure", "🗂️",
        report.structure.details,
        report.structure.score, 20,
        extra_html=(
            f'<span class="detected-badge">📁 Source: {report.structure.detected_src_folder}</span>&nbsp;'
            if report.structure.detected_src_folder else ""
        ) + (
            f'<span class="detected-badge">🧪 Tests: {report.structure.detected_test_folder}</span>'
            if report.structure.detected_test_folder else ""
        ),
    )

    _render_detail_section(
        "Testing Maturity", "🧪",
        report.testing.details,
        report.testing.score, 20,
        extra_html=(
            f'<span class="detected-badge">🧰 Framework: {report.testing.detected_framework}</span>'
            if report.testing.detected_framework else ""
        ),
    )

    _render_detail_section(
        "Docker / Containerization", "🐳",
        report.docker.details,
        report.docker.score, 10,
    )

    _render_detail_section(
        "CI/CD Pipeline", "⚙️",
        report.cicd.details,
        report.cicd.score, 15,
        extra_html=(
            f'<span class="detected-badge">🔧 Platform: {report.cicd.detected_platform}</span>'
            if report.cicd.detected_platform else ""
        ) + (
            f'&nbsp;<span class="detected-badge">📄 {len(report.cicd.workflow_files)} workflow file(s)</span>'
            if report.cicd.workflow_files else ""
        ),
    )

    _render_detail_section(
        "Documentation", "📚",
        report.documentation.details,
        report.documentation.score, 15,
    )

    st.markdown("---")

    # ── Resume Impact Analysis ─────────────────────────────────────────────
    rfill, rbg, rfg = _score_color(report.resume_impact_score, 100)
    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <div class="section-label">Resume Impact Analysis</div>
        <div class="section-heading">How Recruiters See This Project</div>
    </div>
    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
                padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
            <div>
                <div style="font-size:3rem;font-weight:800;color:#111827;line-height:1;letter-spacing:-0.03em;">
                    {report.resume_impact_score}
                    <span style="font-size:1.25rem;color:#9CA3AF;font-weight:400;">/100</span>
                </div>
                <span class="status-pill" style="background:{rbg};color:{rfg};margin-top:0.5rem;display:inline-flex;">
                    {report.resume_emoji} {report.resume_label}
                </span>
            </div>
            <div style="flex:1;min-width:200px;">
                <div style="font-size:0.8125rem;color:#6B7280;margin-bottom:0.875rem;line-height:1.6;">
                    The Resume Impact Score weights engineering signals by their importance
                    to technical recruiters and hiring managers.
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
                    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;padding:0.625rem 0.875rem;">
                        <div style="font-size:0.6875rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Testing</div>
                        <div style="font-size:1rem;font-weight:700;color:#059669;">30% weight</div>
                    </div>
                    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;padding:0.625rem 0.875rem;">
                        <div style="font-size:0.6875rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">CI/CD</div>
                        <div style="font-size:1rem;font-weight:700;color:#2563EB;">20% weight</div>
                    </div>
                    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;padding:0.625rem 0.875rem;">
                        <div style="font-size:0.6875rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">README</div>
                        <div style="font-size:1rem;font-weight:700;color:#374151;">15% weight</div>
                    </div>
                    <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;padding:0.625rem 0.875rem;">
                        <div style="font-size:0.6875rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;">Structure</div>
                        <div style="font-size:1rem;font-weight:700;color:#374151;">15% weight</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Recommendations ────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:1rem;">
        <div class="section-label">Recommendations</div>
        <div class="section-heading">Actionable Improvements</div>
        <div style="color:#6B7280;font-size:0.875rem;margin-top:0.25rem;">
            Prioritized by impact on engineering maturity and recruiter perception.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _render_recommendations(report)

    st.markdown("---")

    # ── Export ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:0.875rem;">
        <div class="section-label">Export</div>
        <div class="section-heading">Download Full Report</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇  Download Markdown Report",
            data=report.to_markdown(),
            file_name=f"{report.metadata.name}_audit_report.md",
            mime="text/markdown",
            use_container_width=True,
            on_click=lambda: track_feature_usage("Download Markdown Report")
        )
    with col2:
        st.download_button(
            label="⬇  Download JSON Report",
            data=report.model_dump_json(indent=2),
            file_name=f"{report.metadata.name}_audit_report.json",
            mime="application/json",
            use_container_width=True,
            on_click=lambda: track_feature_usage("Download JSON Report")
        )

    # ── Footer ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-footer">
        <div class="footer-left">
            GitHub Project Quality Auditor &nbsp;·&nbsp; Built for students, graduates &amp; internship seekers
        </div>
        <div class="footer-right">
            Powered by GitHub REST API v3
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    # Track page visit
    track_visit()

    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

    view = _render_sidebar()

    if view == "Admin Analytics":
        from analytics.dashboard import check_password, render_dashboard
        if check_password():
            render_dashboard()
        return

    # ── Page header ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <h1>GitHub Project Quality Auditor</h1>
        <p>
            Evaluate any public repository across 6 engineering dimensions.
            Get a quality score, resume impact analysis, and actionable recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Search bar ─────────────────────────────────────────────────────────
    st.markdown('<div class="search-bar-wrap">', unsafe_allow_html=True)
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        repo_url = st.text_input(
            label="Repository URL",
            placeholder="https://github.com/owner/repository",
            label_visibility="collapsed",
            key="repo_url_input",
        )
    with col_btn:
        analyze = st.button("Analyze →", use_container_width=True)

    st.markdown("""
    <div style="margin-top:0.625rem;font-size:0.8125rem;color:#9CA3AF;">
        <strong style="color:#6B7280;">Try:</strong>&nbsp;
        github.com/tiangolo/fastapi &nbsp;·&nbsp;
        github.com/pallets/flask &nbsp;·&nbsp;
        github.com/psf/requests
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Analysis pipeline ──────────────────────────────────────────────────
    if analyze:
        if not repo_url or not repo_url.strip():
            st.error("Please enter a GitHub repository URL.")
            return

        try:
            owner, repo_name = parse_github_url(repo_url.strip())
        except InvalidRepoURLError as e:
            st.error(f"Invalid URL: {e}")
            return

        # Progress feedback
        progress = st.progress(0)
        status   = st.empty()

        def _update(pct: int, msg: str) -> None:
            progress.progress(pct)
            status.markdown(
                f'<div style="text-align:center;font-size:0.875rem;color:#6B7280;'
                f'padding:0.5rem 0;">{msg}</div>',
                unsafe_allow_html=True,
            )

        try:
            start_time = time.time()
            _update(10, "🔗 Connecting to GitHub API…")
            svc = GitHubService()
            time.sleep(0.15)

            _update(25, f"📦 Fetching <strong>{owner}/{repo_name}</strong>…")
            repo_data = svc.fetch(repo_url.strip())

            _update(60, "🔬 Running 6 engineering analyzers…")
            time.sleep(0.2)

            engine = ScoreEngine()
            report = engine.audit(repo_data, repo_url.strip())

            _update(95, "✅ Analysis complete!")
            time.sleep(0.3)

            progress.empty()
            status.empty()

            # Track successful analysis
            duration = time.time() - start_time
            track_analysis(
                repo_url=repo_url.strip(),
                repo_name=f"{owner}/{repo_name}",
                total_score=report.total_score,
                resume_impact_score=report.resume_impact_score,
                duration=duration,
                language=repo_data.metadata.language
            )

            _render_full_report(report)

        except InvalidRepoURLError as e:
            progress.empty(); status.empty()
            st.error(f"Invalid URL — {e}")
            track_error(repo_url.strip(), f"{owner}/{repo_name}", e)

        except RepoNotFoundError as e:
            progress.empty(); status.empty()
            st.error(f"Repository not found — {e}")
            st.info(
                "Ensure the repository is **public** and the URL is correct. "
                "Private repositories are not supported without an appropriate token."
            )
            track_error(repo_url.strip(), f"{owner}/{repo_name}", e)

        except RateLimitError as e:
            progress.empty(); status.empty()
            st.warning(f"GitHub API rate limit reached — {e}")
            st.info(
                "Add a GitHub Personal Access Token in the sidebar "
                "to increase the limit from 60 to 5,000 requests per hour."
            )
            track_error(repo_url.strip(), f"{owner}/{repo_name}", e)

        except GitHubServiceError as e:
            progress.empty(); status.empty()
            st.error(f"GitHub API error — {e}")
            track_error(repo_url.strip(), f"{owner}/{repo_name}", e)

        except Exception as e:
            progress.empty(); status.empty()
            logger.exception("Unexpected error")
            st.error(f"Unexpected error — {e}")
            track_error(repo_url.strip(), f"{owner}/{repo_name}", e)

    else:
        # ── Landing / empty state ──────────────────────────────────────────
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-title">Evaluate Your GitHub Project Like a Recruiter</div>
            <div class="empty-sub">
                Enter a public GitHub repository URL above to receive a comprehensive
                engineering quality audit — in seconds.
            </div>
            <div class="feature-grid">
                <div class="feature-item">
                    <div class="feature-icon">📄</div>
                    <div class="feature-name">README</div>
                    <div class="feature-pts">up to 20 pts</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🗂️</div>
                    <div class="feature-name">Structure</div>
                    <div class="feature-pts">up to 20 pts</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🧪</div>
                    <div class="feature-name">Testing</div>
                    <div class="feature-pts">up to 20 pts</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🐳</div>
                    <div class="feature-name">Docker</div>
                    <div class="feature-pts">up to 10 pts</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">⚙️</div>
                    <div class="feature-name">CI / CD</div>
                    <div class="feature-pts">up to 15 pts</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📚</div>
                    <div class="feature-name">Docs</div>
                    <div class="feature-pts">up to 15 pts</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
