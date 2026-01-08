# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import numpy as np

st.set_page_config(
    page_title="CSV Data Explorer BI",
    layout="wide"
)

# =====================================================
# UTILITIES
# =====================================================

@st.cache_data(show_spinner=False)
def load_csv(file):
    return pd.read_csv(file)

def safe_export(fig, title, chart_type):
    try:
        png = pio.to_image(fig, format="png", width=3840, height=2160, scale=2)
        st.download_button(
            "📥 Download Chart (PNG)",
            png,
            f"{title}.png",
            mime="image/png"
        )
    except Exception:
        html = pio.to_html(fig, full_html=True)
        st.download_button(
            "📥 Download Chart (HTML)",
            html,
            f"{title}.html",
            mime="text/html"
        )

# =====================================================
# AI INSIGHTS ENGINE
# =====================================================

def generate_insights(df, x_col, y_col):
    if df.empty:
        return "No insights available."

    insights = []
    total = df[y_col].sum()

    top = df.sort_values(y_col, ascending=False).iloc[0]
    bottom = df.sort_values(y_col).iloc[0]

    pct = (top[y_col] / total * 100) if total else 0
    insights.append(
        f"**{top[x_col]}** contributes **{pct:.1f}%** of total value."
    )

    if top[y_col] > bottom[y_col] * 5:
        insights.append("Distribution is highly skewed.")

    mean = df[y_col].mean()
    std = df[y_col].std()
    outliers = df[df[y_col] > mean + 2 * std]

    if not outliers.empty:
        insights.append(
            f"Outliers detected: {', '.join(outliers[x_col].astype(str))}."
        )

    return " ".join(insights)

# =====================================================
# HEADER
# =====================================================

st.markdown("""
<style>
.header {
    background: linear-gradient(90deg,#667eea,#764ba2);
    padding:18px 28px;
    border-radius:10px;
    color:white;
}
</style>
<div class="header">
<h2>📊 CSV Data Explorer BI</h2>
<p>Save • Share • Reuse Dashboards</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if not uploaded:
    st.info("Upload a CSV file to begin.")
    st.stop()

df = load_csv(uploaded)

num_cols = df.select_dtypes(include=["number"]).columns.tolist()
cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

# =====================================================
# SIDEBAR – DASHBOARD CONTROLS
# =====================================================

st.sidebar.header("📊 Chart Configuration")

chart_type = st.sidebar.selectbox(
    "Chart Type",
    ["Bar", "Horizontal Bar", "Line", "Scatter", "Pie", "Donut", "Histogram"],
    key="chart_type"
)

x_col = st.sidebar.selectbox("X-axis", cat_cols + num_cols, key="x_col")

y_col = None
if chart_type != "Histogram":
    y_col = st.sidebar.selectbox("Y-axis", num_cols, key="y_col")

aggregation = st.sidebar.selectbox(
    "Aggregation",
    ["Count", "Sum", "Average"],
    key="aggregation"
)

# =====================================================
# AGGREGATION
# =====================================================

if aggregation == "Count":
    agg_df = df.groupby(x_col).size().reset_index(name="count")
    y_col = "count"
elif aggregation == "Sum":
    agg_df = df.groupby(x_col)[y_col].sum().reset_index()
else:
    agg_df = df.groupby(x_col)[y_col].mean().reset_index()

# =====================================================
# CUSTOM SORT
# =====================================================

custom_order = st.sidebar.multiselect(
    "Custom Category Order",
    agg_df[x_col].astype(str).tolist(),
    key="custom_order"
)

if custom_order:
    agg_df[x_col] = pd.Categorical(
        agg_df[x_col].astype(str),
        categories=custom_order,
        ordered=True
    )
    agg_df = agg_df.sort_values(x_col)

# =====================================================
# CUSTOM COLORS
# =====================================================

use_custom_colors = st.sidebar.checkbox("Enable Custom Colors")

color_map = None
if use_custom_colors:
    color_map = {}
    for v in agg_df[x_col].astype(str).unique():
        color_map[v] = st.sidebar.color_picker(f"{v}", "#1f77b4")

# =====================================================
# CHART
# =====================================================

if chart_type == "Bar":
    fig = px.bar(agg_df, x=x_col, y=y_col, color=x_col, color_discrete_map=color_map)
elif chart_type == "Horizontal Bar":
    fig = px.bar(agg_df, y=x_col, x=y_col, orientation="h", color=x_col, color_discrete_map=color_map)
elif chart_type == "Line":
    fig = px.line(agg_df, x=x_col, y=y_col, markers=True)
elif chart_type == "Scatter":
    fig = px.scatter(agg_df, x=x_col, y=y_col, color=x_col)
elif chart_type == "Pie":
    fig = px.pie(agg_df, names=x_col, values=y_col, color_discrete_map=color_map)
elif chart_type == "Donut":
    fig = px.pie(agg_df, names=x_col, values=y_col, hole=0.4, color_discrete_map=color_map)
else:
    fig = px.histogram(df, x=x_col)

fig.update_layout(height=550)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# AI INSIGHTS
# =====================================================

st.markdown("### 🧠 AI Chart Insights")
st.success(generate_insights(agg_df, x_col, y_col))

# =====================================================
# SAVE / LOAD DASHBOARD
# =====================================================

st.markdown("### 💾 Save / Share Dashboard")

dashboard_config = {
    "chart_type": chart_type,
    "x_col": x_col,
    "y_col": y_col,
    "aggregation": aggregation,
    "custom_order": custom_order,
    "colors": color_map
}

config_json = json.dumps(dashboard_config, indent=2)

st.download_button(
    "💾 Save Dashboard (.json)",
    config_json,
    file_name="dashboard_config.json",
    mime="application/json"
)

uploaded_config = st.file_uploader(
    "📤 Load Dashboard (.json)",
    type=["json"]
)

if uploaded_config:
    cfg = json.load(uploaded_config)

    for k, v in cfg.items():
        st.session_state[k] = v

    st.success("Dashboard loaded successfully.")
    st.experimental_rerun()

# =====================================================
# EXPORT
# =====================================================

st.markdown("### 📥 Export Chart")
safe_export(fig, "dashboard_chart", chart_type)

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<hr>
<p style="text-align:center;color:#777">
CSV Data Explorer BI • v3.0 • Built by <strong>Naved Khan</strong>
</p>
""", unsafe_allow_html=True)
