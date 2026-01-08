# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from copy import deepcopy

st.set_page_config(page_title="CSV / Excel Data Explorer", layout="wide")

# =====================================================
# RESET
# =====================================================
def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0">📊 CSV / Excel Data Explorer</h3>
<small>BI-grade analysis tool</small>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Back to Start"):
    reset_app()

# =====================================================
# FILE UPLOAD (CSV + EXCEL)
# =====================================================
uploaded = st.session_state.get("file_upload")

if uploaded is None:
    with st.expander("📁 File Controls", expanded=True):
        file = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"]
        )
        if file:
            st.session_state.file_upload = file
            st.rerun()

uploaded = st.session_state.get("file_upload")
if not uploaded:
    st.stop()

# =====================================================
# LOAD DATA
# =====================================================
if "raw_df" not in st.session_state:
    if uploaded.name.endswith((".xlsx", ".xls")):
        st.session_state.raw_df = pd.read_excel(uploaded)
    else:
        st.session_state.raw_df = pd.read_csv(uploaded)

raw_df = st.session_state.raw_df.copy()

# =====================================================
# DATA PREVIEW + COLUMN SELECTION
# =====================================================
with st.expander("📋 Data Preview & Column Selection", expanded=True):
    selected_cols = st.multiselect(
        "Select columns",
        raw_df.columns.tolist(),
        default=raw_df.columns.tolist()
    )
    df = raw_df[selected_cols].copy()
    st.dataframe(df.head(50), use_container_width=True)

cols = df.columns.tolist()
num_cols = df.select_dtypes(include="number").columns.tolist()

# =====================================================
# GLOBAL FILTERS
# =====================================================
st.sidebar.header("🔍 Global Filters")

filtered_df = df.copy()
for c in cols:
    if filtered_df[c].dtype == object:
        options = sorted(filtered_df[c].dropna().astype(str).unique())
        selected = st.sidebar.multiselect(c, options, key=f"gf_{c}")
        if selected:
            filtered_df = filtered_df[filtered_df[c].astype(str).isin(selected)]

st.sidebar.caption(f"Rows after global filters: {len(filtered_df)}")

# =====================================================
# MULTI-CHART CONTROL
# =====================================================
st.sidebar.divider()
num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

# Init state holders
if "visual_filters" not in st.session_state:
    st.session_state.visual_filters = {}

if "custom_sort" not in st.session_state:
    st.session_state.custom_sort = {}

# =====================================================
# CHART CONFIGURATION
# =====================================================
charts_data = []

AGGS = ["Count", "Sum", "Average", "Min", "Max"]

for chart_num in range(num_charts):

    with st.sidebar.expander(f"📊 Chart {chart_num + 1}", expanded=False):

        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Line", "Scatter", "Area", "Pie", "Donut", "Histogram"],
            key=f"type_{chart_num}"
        )

        x_col = st.selectbox("X-axis", cols, key=f"x_{chart_num}")
        y_col = st.selectbox("Y-axis", cols, key=f"y_{chart_num}")

        aggregation = st.selectbox(
            "Aggregation",
            AGGS,
            key=f"agg_{chart_num}"
        )

        title = st.text_input(
            "Chart Title",
            f"{aggregation} of {y_col} by {x_col}",
            key=f"title_{chart_num}"
        )

        # ---------------- AXES ----------------
        with st.expander("Axes"):
            hide_x = st.checkbox("Hide X-axis", False, key=f"hx_{chart_num}")
            hide_y = st.checkbox("Hide Y-axis", False, key=f"hy_{chart_num}")
            x_title = st.text_input("X-axis Title", x_col, key=f"xt_{chart_num}")
            y_title = st.text_input("Y-axis Title", y_col, key=f"yt_{chart_num}")

        # ---------------- LABELS ----------------
        with st.expander("Labels"):
            show_labels = st.checkbox("Show Data Labels", False, key=f"lbl_{chart_num}")
            decimals = st.slider("Decimals", 0, 5, 2, key=f"dec_{chart_num}")

        # ---------------- LEGEND ----------------
        with st.expander("Legend"):
            show_legend = st.checkbox("Show Legend", True, key=f"leg_{chart_num}")
            legend_pos = st.selectbox(
                "Legend Position",
                ["v", "h"],
                key=f"legpos_{chart_num}"
            )

        # ---------------- SORTING (NEW) ----------------
        with st.expander("Sorting"):
            sort_mode = st.selectbox(
                "Sort By",
                ["None", "Value (Asc)", "Value (Desc)", "Manual Order"],
                key=f"sort_mode_{chart_num}"
            )

            manual_order = []
            if sort_mode == "Manual Order":
                manual_order = st.multiselect(
                    "Custom Category Order",
                    filtered_df[x_col].astype(str).unique().tolist(),
                    key=f"manual_sort_{chart_num}"
                )

            st.session_state.custom_sort[chart_num] = {
                "mode": sort_mode,
                "order": manual_order
            }

        # ---------------- VISUAL FILTERS ----------------
        with st.expander("Filters (Visual-level)"):
            chart_filters = st.session_state.visual_filters.get(chart_num, {})
            for c in cols:
                if df[c].dtype == object:
                    options = sorted(df[c].dropna().astype(str).unique())
                    chart_filters[c] = st.multiselect(
                        c,
                        options,
                        chart_filters.get(c, []),
                        key=f"vf_{chart_num}_{c}"
                    )
            st.session_state.visual_filters[chart_num] = chart_filters

    # =================================================
    # DATA PIPELINE (GLOBAL → VISUAL FILTER → AGG)
    # =================================================
    chart_df = filtered_df.copy()
    for c, vals in st.session_state.visual_filters.get(chart_num, {}).items():
        if vals:
            chart_df = chart_df[chart_df[c].astype(str).isin(vals)]

    if aggregation == "Count":
        agg_df = chart_df.groupby(x_col).size().reset_index(name="value")
    else:
        chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
        agg_map = {
            "Sum": "sum",
            "Average": "mean",
            "Min": "min",
            "Max": "max"
        }
        agg_df = chart_df.groupby(x_col)[y_col].agg(
            agg_map[aggregation]
        ).reset_index(name="value")

    # ---------------- APPLY SORTING ----------------
    sort_cfg = st.session_state.custom_sort.get(chart_num, {})

    if sort_cfg.get("mode") == "Value (Asc)":
        agg_df = agg_df.sort_values("value", ascending=True)

    elif sort_cfg.get("mode") == "Value (Desc)":
        agg_df = agg_df.sort_values("value", ascending=False)

    elif sort_cfg.get("mode") == "Manual Order" and sort_cfg.get("order"):
        agg_df[x_col] = pd.Categorical(
            agg_df[x_col].astype(str),
            categories=sort_cfg["order"],
            ordered=True
        )
        agg_df = agg_df.sort_values(x_col)

    # =================================================
    # CHART CREATION
    # =================================================
    if chart_type == "Bar":
        fig = px.bar(agg_df, x=x_col, y="value", color=x_col)
    elif chart_type == "Line":
        fig = px.line(agg_df, x=x_col, y="value", markers=True)
    elif chart_type == "Scatter":
        fig = px.scatter(agg_df, x=x_col, y="value", color=x_col)
    elif chart_type == "Area":
        fig = px.area(agg_df, x=x_col, y="value")
    elif chart_type == "Pie":
        fig = px.pie(agg_df, names=x_col, values="value")
    elif chart_type == "Donut":
        fig = px.pie(agg_df, names=x_col, values="value", hole=0.4)
    else:
        fig = px.histogram(chart_df, x=x_col)

    if show_labels and chart_type not in ["Pie", "Donut"]:
        fig.update_traces(
            texttemplate=f"%{{y:.{decimals}f}}",
            textposition="outside"
        )

    fig.update_layout(
        title=title,
        showlegend=show_legend,
        legend_orientation="v" if legend_pos == "v" else "h",
        xaxis_title="" if hide_x else x_title,
        yaxis_title="" if hide_y else y_title,
        height=450
    )

    charts_data.append((chart_num, fig))

# =====================================================
# DASHBOARD
# =====================================================
st.divider()
st.markdown("## 📈 Charts")

for idx, fig in charts_data:
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{idx}")

# =====================================================
# EXPORT
# =====================================================
st.divider()
st.download_button(
    "📥 Download Filtered CSV",
    filtered_df.to_csv(index=False),
    "filtered_data.csv"
)
