# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit.components.v1 as components

# Layout mode deps (safe)
from streamlit_elements import elements, dashboard, mui, html

# =====================================================
# APP CONFIG
# =====================================================
st.set_page_config(page_title="CSV Data Explorer", layout="wide")

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
<style>
.header-container {
    background: linear-gradient(90deg,#667eea,#764ba2);
    color:white;
    padding:18px 28px;
    border-radius:10px;
    margin-bottom:20px;
    display:flex;
    justify-content:space-between;
    align-items:center;
}
</style>
<div class="header-container">
  <div>
    <h3 style="margin:0">📊 CSV Data Explorer</h3>
    <small>by Naved Khan</small>
  </div>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Back to Start"):
    reset_app()

# =====================================================
# FILE UPLOAD (CSV + EXCEL)
# =====================================================
st.divider()

uploaded = st.session_state.get("file_upload")

if uploaded is None:
    with st.expander("📁 File Controls", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload CSV / Excel",
            type=["csv", "xlsx", "xls"]
        )
        if uploaded_file:
            st.session_state.file_upload = uploaded_file
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
# COLUMN SELECTION
# =====================================================
with st.expander("📋 Data Preview & Column Selection", expanded=True):
    selected_cols = st.multiselect(
        "Columns",
        raw_df.columns.tolist(),
        default=raw_df.columns.tolist()
    )
    df = raw_df[selected_cols].copy()
    st.dataframe(df.head(50), use_container_width=True)

# =====================================================
# COLUMN GROUPS
# =====================================================
cols = df.columns.tolist()
num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(exclude="number").columns.tolist()

# =====================================================
# FILTERS (GLOBAL)
# =====================================================
st.sidebar.header("🔍 Filters")

filters = {}
for c in cat_cols:
    vals = sorted(df[c].dropna().astype(str).unique())
    sel = st.sidebar.multiselect(c, vals, key=f"f_{c}")
    if sel:
        filters[c] = sel

filtered_df = df.copy()
for c, v in filters.items():
    filtered_df = filtered_df[filtered_df[c].astype(str).isin(v)]

# =====================================================
# METRICS
# =====================================================
m1, m2, m3 = st.columns(3)
m1.metric("Total Rows", len(df))
m2.metric("Filtered Rows", len(filtered_df))
m3.metric("Active Filters", len(filters))

# =====================================================
# LAYOUT MODE TOGGLE
# =====================================================
st.sidebar.divider()
layout_mode = st.sidebar.toggle("🧱 Layout Mode (Drag & Resize)", value=False)

# =====================================================
# CHART CONFIG
# =====================================================
st.sidebar.divider()
num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

charts_data = []

for i in range(num_charts):
    with st.sidebar.expander(f"📊 Chart {i+1}", expanded=False):
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Line", "Scatter", "Pie", "Histogram"],
            key=f"ct_{i}"
        )
        x_col = st.selectbox("X-axis", cols, key=f"x_{i}")
        y_col = None
        if chart_type != "Histogram":
            y_col = st.selectbox("Y-axis", num_cols, key=f"y_{i}")

        agg = st.selectbox("Aggregation", ["Count", "Sum", "Average"], key=f"a_{i}")

        title = st.text_input(
            "Chart Title",
            f"{agg} of {y_col} by {x_col}" if y_col else f"{chart_type} of {x_col}",
            key=f"t_{i}"
        )

        hide_x = st.checkbox("Hide X-axis", key=f"hx_{i}")
        hide_y = st.checkbox("Hide Y-axis", key=f"hy_{i}")

        x_axis_type = st.selectbox("X-axis Type", ["category", "linear"], key=f"xat_{i}")
        y_axis_type = st.selectbox("Y-axis Type", ["linear", "log"], key=f"yat_{i}")

    # ===== AGG =====
    if agg == "Count":
        agg_df = filtered_df.groupby(x_col).size().reset_index(name="count")
        y_val = "count"
    elif agg == "Sum":
        agg_df = filtered_df.groupby(x_col)[y_col].sum().reset_index()
        y_val = y_col
    else:
        agg_df = filtered_df.groupby(x_col)[y_col].mean().reset_index()
        y_val = y_col

    # ===== CHART =====
    if chart_type == "Bar":
        fig = px.bar(agg_df, x=x_col, y=y_val)
    elif chart_type == "Line":
        fig = px.line(agg_df, x=x_col, y=y_val, markers=True)
    elif chart_type == "Scatter":
        fig = px.scatter(agg_df, x=x_col, y=y_val)
    elif chart_type == "Pie":
        fig = px.pie(agg_df, names=x_col, values=y_val)
    else:
        fig = px.histogram(filtered_df, x=x_col)

    fig.update_layout(
        title=title,
        height=450,
        xaxis_title="" if hide_x else x_col,
        yaxis_title="" if hide_y else y_col,
    )
    fig.update_xaxes(type=x_axis_type)
    fig.update_yaxes(type=y_axis_type)

    charts_data.append({
        "fig": fig,
        "title": title,
        "id": f"chart_{i}"
    })

# =====================================================
# DISPLAY
# =====================================================
st.divider()
st.markdown("## 📈 Dashboard")

if not layout_mode:
    # ORIGINAL BEHAVIOR
    for c in charts_data:
        st.plotly_chart(c["fig"], use_container_width=True)

else:
    # LAYOUT MODE (SAFE)
    if "grid" not in st.session_state:
        st.session_state.grid = [
            dashboard.Item(c["id"], x=(i % 2) * 6, y=(i // 2) * 4, w=6, h=4)
            for i, c in enumerate(charts_data)
        ]

    with elements("dashboard"):
        with dashboard.Grid(
            st.session_state.grid,
            cols=12,
            rowHeight=90,
            draggableHandle=".drag-handle",
            onLayoutChange=lambda l: st.session_state.update({"grid": l})
        ):
            for c in charts_data:
                with mui.Card(key=c["id"], sx={"height": "100%"}):
                    mui.CardHeader(
                        title=c["title"],
                        className="drag-handle",
                        sx={"cursor": "move"}
                    )
                    mui.CardContent(
                        html.Div(
                            c["fig"].to_html(include_plotlyjs="cdn"),
                            dangerouslySetInnerHTML=True
                        )
                    )

# =====================================================
# EXPORT
# =====================================================
st.divider()
if st.button("📥 Export All Charts (PNG / HTML fallback)"):
    for c in charts_data:
        try:
            png = pio.to_image(c["fig"], format="png", width=3840, height=2160, scale=2)
            st.download_button(
                f"Download {c['title']}",
                png,
                f"{c['title']}.png",
                mime="image/png",
                key=c["id"]
            )
        except:
            html_data = c["fig"].to_html(full_html=True)
            st.download_button(
                f"Download {c['title']}",
                html_data,
                f"{c['title']}.html",
                mime="text/html",
                key=f"{c['id']}_html"
            )

# =====================================================
# FOOTER
# =====================================================
st.markdown("""
<hr>
<p style="text-align:center;color:#777">
CSV Data Explorer • Layout Mode Enabled • Built by <strong>Naved Khan</strong>
</p>
""", unsafe_allow_html=True)
