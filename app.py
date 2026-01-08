# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import json

from streamlit_elements import elements, dashboard, mui

st.set_page_config(layout="wide")

# =====================================================
# STATE INIT
# =====================================================

if "layout" not in st.session_state:
    st.session_state.layout = []

if "visuals" not in st.session_state:
    st.session_state.visuals = {}

# =====================================================
# HEADER
# =====================================================

st.markdown("""
<style>
.header {
    background: linear-gradient(90deg,#667eea,#764ba2);
    padding:16px 24px;
    border-radius:10px;
    color:white;
    margin-bottom:16px;
}
</style>
<div class="header">
<h2>📊 BI Dashboard – Layout Mode</h2>
<p>Drag • Resize • Configure Visuals (Power BI Style)</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded)
num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(exclude="number").columns.tolist()

# =====================================================
# GLOBAL FILTERS
# =====================================================

st.sidebar.header("🔍 Global Filters")

global_filters = {}
for col in cat_cols:
    vals = sorted(df[col].dropna().astype(str).unique())
    sel = st.sidebar.multiselect(col, vals, key=f"g_{col}")
    if sel:
        global_filters[col] = sel

filtered_df = df.copy()
for col, vals in global_filters.items():
    filtered_df = filtered_df[filtered_df[col].astype(str).isin(vals)]

# =====================================================
# ADD VISUAL
# =====================================================

st.sidebar.divider()
st.sidebar.header("➕ Add Visual")

v_type = st.sidebar.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"])
x_col = st.sidebar.selectbox("X-axis", cat_cols + num_cols)
y_col = st.sidebar.selectbox("Y-axis", num_cols)

if st.sidebar.button("➕ Add to Canvas"):
    vid = f"visual_{len(st.session_state.visuals)+1}"

    st.session_state.visuals[vid] = {
        "type": v_type,
        "x": x_col,
        "y": y_col,
        "title": f"{v_type} Chart",
        "agg": "Count",
        "hide_x": False,
        "hide_y": False,
        "x_title": x_col,
        "y_title": y_col,
        "x_axis_type": "category",
        "y_axis_type": "linear",
        "filters": {}
    }

    st.session_state.layout.append(
        dashboard.Item(vid, x=0, y=0, w=6, h=4)
    )

# =====================================================
# DASHBOARD CANVAS
# =====================================================

with elements("dashboard"):

    with dashboard.Grid(
        st.session_state.layout,
        cols=12,
        rowHeight=90,
        draggableHandle=".drag-handle",
        onLayoutChange=lambda l: st.session_state.update({"layout": l}),
    ):

        for vid, cfg in st.session_state.visuals.items():

            # ---------------- DATA (VISUAL LEVEL FILTERS) ----------------
            vdf = filtered_df.copy()
            for c, vals in cfg["filters"].items():
                vdf = vdf[vdf[c].astype(str).isin(vals)]

            # ---------------- AGG ----------------
            if cfg["agg"] == "Count":
                agg_df = vdf.groupby(cfg["x"]).size().reset_index(name="count")
                y_val = "count"
            else:
                agg_df = vdf.groupby(cfg["x"])[cfg["y"]].mean().reset_index()
                y_val = cfg["y"]

            # ---------------- CHART ----------------
            if cfg["type"] == "Bar":
                fig = px.bar(agg_df, x=cfg["x"], y=y_val)
            elif cfg["type"] == "Line":
                fig = px.line(agg_df, x=cfg["x"], y=y_val, markers=True)
            elif cfg["type"] == "Scatter":
                fig = px.scatter(agg_df, x=cfg["x"], y=y_val)
            else:
                fig = px.pie(agg_df, names=cfg["x"], values=y_val)

            fig.update_layout(
                title=cfg["title"],
                xaxis_title="" if cfg["hide_x"] else cfg["x_title"],
                yaxis_title="" if cfg["hide_y"] else cfg["y_title"],
                xaxis_type=cfg["x_axis_type"],
                yaxis_type=cfg["y_axis_type"],
                height=100 * st.session_state.layout[
                    next(i for i, l in enumerate(st.session_state.layout) if l["i"] == vid)
                ]["h"]
            )

            # ---------------- CARD ----------------
            with mui.Card(key=vid, sx={"height": "100%"}):
                mui.CardHeader(
                    title=cfg["title"],
                    className="drag-handle",
                    sx={"cursor": "move"},
                    action=mui.IconButton("⚙️", onClick=lambda v=vid: st.session_state.update({"edit": v}))
                )
                mui.CardContent(st.plotly_chart(fig, use_container_width=True))

# =====================================================
# VISUAL SETTINGS PANEL (POWER BI FORMAT PANE)
# =====================================================

if "edit" in st.session_state:
    vid = st.session_state.edit
    cfg = st.session_state.visuals[vid]

    st.sidebar.divider()
    st.sidebar.header(f"⚙️ Visual Settings")

    cfg["title"] = st.sidebar.text_input("Chart Title", cfg["title"])
    cfg["agg"] = st.sidebar.selectbox("Aggregation", ["Count", "Average"], index=0 if cfg["agg"]=="Count" else 1)

    cfg["hide_x"] = st.sidebar.checkbox("Hide X-axis", cfg["hide_x"])
    cfg["hide_y"] = st.sidebar.checkbox("Hide Y-axis", cfg["hide_y"])

    cfg["x_title"] = st.sidebar.text_input("X-axis Title", cfg["x_title"])
    cfg["y_title"] = st.sidebar.text_input("Y-axis Title", cfg["y_title"])

    cfg["x_axis_type"] = st.sidebar.selectbox("X-axis Type", ["category", "linear"], index=0)
    cfg["y_axis_type"] = st.sidebar.selectbox("Y-axis Type", ["linear", "log"], index=0)

    st.sidebar.markdown("**Visual Filters**")
    for col in cat_cols:
        opts = sorted(df[col].dropna().astype(str).unique())
        cfg["filters"][col] = st.sidebar.multiselect(
            col, opts, cfg["filters"].get(col, [])
        )

    if st.sidebar.button("❌ Close Settings"):
        del st.session_state.edit

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<hr>
<p style="text-align:center;color:#777">
BI Dashboard • Layout Mode • Built by <strong>Naved Khan</strong>
</p>
""", unsafe_allow_html=True)
