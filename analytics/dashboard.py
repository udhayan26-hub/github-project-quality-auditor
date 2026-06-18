import os
import json
import pandas as pd
import streamlit as st
from analytics.analytics_service import AnalyticsService

def check_password() -> bool:
    """Returns True if the user has authenticated with the correct password."""
    # Read the password from environment variables
    correct_password = os.getenv("ADMIN_PASSWORD", "")
    
    if not correct_password:
        st.warning("Admin Dashboard is disabled because ADMIN_PASSWORD is not configured in the environment.")
        return False

    if "admin_authenticated" in st.session_state and st.session_state["admin_authenticated"]:
        return True

    # Render a clean login form
    st.markdown("""
    <div style="max-width: 400px; margin: 4rem auto 1rem; padding: 2rem; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
        <h2 style="margin-top:0; font-size: 1.25rem; font-weight: 700; color: #111827; text-align: center;">Admin Verification Required</h2>
        <p style="font-size: 0.875rem; color: #6B7280; text-align: center; margin-bottom: 1.5rem;">Please enter the administrator password to view application usage analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        password = st.text_input("Administrator Password", type="password")
        submit = st.form_submit_button("Verify Password")
        
        if submit:
            if password == correct_password:
                st.session_state["admin_authenticated"] = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Incorrect password. Access Denied.")
                
    return False


def render_dashboard() -> None:
    """Renders the entire Admin Analytics Dashboard."""
    # Enable logout option in top right
    if st.sidebar.button("🔓 Admin Log Out"):
        st.session_state["admin_authenticated"] = False
        st.rerun()

    st.markdown("""
    <div class="page-header">
        <h1>📊 Usage & System Analytics</h1>
        <p>Real-time platform insights, performance metrics, and repository audit activity history.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filter Controls ──────────────────────────────────────────────────
    col_filter, _ = st.columns([1, 3])
    with col_filter:
        time_range = st.selectbox(
            "Select Time Frame",
            ["Today", "Last 7 Days", "Last 30 Days", "All Time"],
            index=2  # Default to 30 days
        )

    # Map time frame to days
    days_map = {
        "Today": 1,
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "All Time": None
    }
    days = days_map[time_range]

    # Fetch stats
    with st.spinner("Fetching analytics data..."):
        stats = AnalyticsService.get_overview_stats(days)
        daily_metrics = AnalyticsService.get_daily_metrics(days if days else 90)
        top_repos = AnalyticsService.get_top_repositories(days)
        languages = AnalyticsService.get_language_distribution(days)
        devices = AnalyticsService.get_device_distribution(days)
        countries = AnalyticsService.get_country_distribution(days)
        features = AnalyticsService.get_feature_usage()
        scores = AnalyticsService.get_score_distribution(days)

    # ── KPI Cards ────────────────────────────────────────────────────────
    st.markdown("### Platform Overview")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("Total Page Views", f"{stats['total_visits']:,}")
    with kpi_col2:
        st.metric("Unique Visitors", f"{stats['unique_visitors']:,}")
    with kpi_col3:
        st.metric("Successful Audits", f"{stats['total_analyses']:,}")
    with kpi_col4:
        st.metric("Returning User Rate", f"{stats['returning_rate']:.1f}%")

    st.markdown("---")

    # ── Time series charts ───────────────────────────────────────────────
    st.markdown("### Usage Over Time")
    if daily_metrics:
        df_daily = pd.DataFrame(daily_metrics)
        df_daily.set_index("date", inplace=True)
        
        # Rename columns for display
        df_daily.rename(columns={
            "total_visitors": "Total Visitors",
            "unique_visitors": "Unique Visitors",
            "analyses_performed": "Analyses Performed"
        }, inplace=True)
        
        st.line_chart(df_daily[["Total Visitors", "Unique Visitors", "Analyses Performed"]], height=260)
    else:
        st.info("No daily traffic logged yet.")

    st.markdown("---")

    # ── Dual column distribution stats ───────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📦 Top Audited Repositories")
        if top_repos:
            df_repos = pd.DataFrame(top_repos, columns=["Repository", "Audits"])
            st.bar_chart(df_repos.set_index("Repository"), horizontal=True, color="#2563EB", height=220)
        else:
            st.info("No repository analysis data recorded for this period.")

    with col_right:
        st.markdown("### 💻 Programming Languages")
        if languages:
            df_langs = pd.DataFrame(languages, columns=["Language", "Audits"])
            st.bar_chart(df_langs.set_index("Language"), horizontal=True, color="#059669", height=220)
        else:
            st.info("No language data available.")

    st.markdown("---")

    col_dev, col_geo = st.columns(2)

    with col_dev:
        st.markdown("### 📱 Device Types")
        if devices:
            df_dev = pd.DataFrame(devices, columns=["Device", "Users"])
            st.bar_chart(df_dev.set_index("Device"), color="#4B5563", height=200)
        else:
            st.info("No device data recorded.")

    with col_geo:
        st.markdown("### 🌍 Top Locations (by language preference)")
        if countries:
            df_geo = pd.DataFrame(countries, columns=["Country Code", "Visitors"])
            st.bar_chart(df_geo.set_index("Country Code"), color="#3B82F6", height=200)
        else:
            st.info("No geolocation data available.")

    st.markdown("---")

    # ── Scoring Profile and Features ─────────────────────────────────────
    col_feat, col_dist = st.columns([1, 1])

    with col_feat:
        st.markdown("### 💡 Feature Usage")
        if features:
            df_feat = pd.DataFrame(features)
            df_feat.columns = ["Feature Name", "Click Count"]
            st.dataframe(df_feat, use_container_width=True, hide_index=True)
        else:
            st.info("No feature interactions logged yet.")

    with col_dist:
        st.markdown("### 🏆 Score Distribution")
        if scores and scores["total_scores"]:
            df_scores = pd.DataFrame({
                "Audit Score": scores["total_scores"],
                "Resume Impact Score": scores["resume_impact_scores"]
            })
            st.area_chart(df_scores, height=220)
        else:
            st.info("No audit scores available.")

    st.markdown("---")

    # ── System Performance Card ──────────────────────────────────────────
    st.markdown("### ⚡ System Performance & Success Metrics")
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    with perf_col1:
        st.metric("Avg Analysis Speed", f"{stats['avg_duration']}s")
    with perf_col2:
        st.metric("Analysis Success Rate", f"{stats['success_rate']}%")
    with perf_col3:
        st.metric("Daily Active Users (DAU)", f"{stats['dau']}")

    st.markdown("---")

    # ── Automated Reports & Exports ──────────────────────────────────────
    st.markdown("### 📂 Reporting & Raw Data Export")
    
    rep_col1, rep_col2 = st.columns(2)
    
    with rep_col1:
        st.markdown("#### Generate Reports")
        report_period = st.selectbox("Select Report Period", ["Weekly Report (Last 7 Days)", "Monthly Report (Last 30 Days)"])
        report_days = 7 if "Weekly" in report_period else 30
        
        if st.button("📄 Generate Report Summary"):
            report_content = AnalyticsService.generate_report_markdown(report_days)
            st.markdown("##### Generated Markdown:")
            st.code(report_content, language="markdown")
            
            st.download_button(
                label="⬇ Download Generated Report (.md)",
                data=report_content,
                file_name=f"platform_analytics_report_{report_days}d.md",
                mime="text/markdown"
            )

    with rep_col2:
        st.markdown("#### Raw Data Exports")
        st.write("Export full visitor and audit logs for external processing (biometrics, sheets, Excel).")
        
        raw_data = AnalyticsService.export_analytics_data()
        
        # 1. JSON Export
        json_str = json.dumps(raw_data, indent=2)
        st.download_button(
            label="⬇ Export Database logs to JSON",
            data=json_str,
            file_name="github_project_auditor_logs.json",
            mime="application/json",
            use_container_width=True
        )
        
        # 2. CSV Exports
        if raw_data["analyses"]:
            df_analyses = pd.DataFrame(raw_data["analyses"])
            csv_analyses = df_analyses.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇ Export Analyses Table to CSV",
                data=csv_analyses,
                file_name="analyses_history_logs.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        if raw_data["visitors"]:
            df_visitors = pd.DataFrame(raw_data["visitors"])
            csv_visitors = df_visitors.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇ Export Visitors Table to CSV",
                data=csv_visitors,
                file_name="visitor_logs.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    # ── Admin Footer ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-footer">
        <div class="footer-left">
            Administrator Analytics Dashboard &nbsp;·&nbsp; Secure session Active
        </div>
        <div class="footer-right">
            Database: PostgreSQL Ready
        </div>
    </div>
    """, unsafe_allow_html=True)
