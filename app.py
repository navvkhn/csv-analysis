# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from copy import deepcopy
from streamlit_elements import dashboard

st.set_page_config(page_title="CSV Data Explorer BI", layout="wide")

# =====================================================
# STATE
# =====================================================
if "charts" not in st.session_state:
    st.session_state.charts = {}

if "layout" not in st.session_state:
    st.session_state.layout = []

if "chart_counter" not in st.session_state:
    st.session_state.chart_counter = 0

# =====================================================
# FILE UPLOAD
# =====================================================
file = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
if not file:
    st.stop()

df_raw = pd.read_excel(file) if file.name.endswith(("xlsx","xls")) else pd.read_csv(file)
cols = df_raw.columns.tolist()

# =====================================================
# GLOBAL FILTERS (RESTORED)
# =====================================================
st.sidebar.header("🔍 Global Filters")

global_filtered_df = df_raw.copy()

for c in cols:
    if global_filtered_df[c].dtype == object:
        options = sorted(global_filtered_df[c].dropna().astype(str).unique())
        selected = st.sidebar.multiselect(f"{c}", options, key=f"gf_{c}")
        if selected:
            global_filtered_df = global_filtered_df[
                global_filtered_df[c].astype(str).isin(selected)
            ]

st.sidebar.caption(f"Rows after global filters: {len(global_filtered_df)}")

# =====================================================
# ADD VISUAL
# =====================================================
st.sidebar.divider()
st.sidebar.header("➕ Add Visual")

chart_type = st.sidebar.selectbox(
    "Chart Type",
    ["Bar","Line","Scatter","Area","Pie","Donut","Histogram"]
)

if st.sidebar.button("Add Chart"):
    cid = f"chart_{st.session_state.chart_counter}"
    st.session_state.chart_counter += 1

    st.session_state.charts[cid] = {
        "type": chart_type,
        "x": cols[0],
        "y": cols[1] if len(cols) > 1 else cols[0],
        "agg": "Count",

        "title": f"{chart_type} Chart",

        "filters": {},          # ← VISUAL FILTERS LIVE HERE

        # formatting
        "show_labels": False,
        "legend": True,
        "custom_colors": {}
    }
    st.rerun()

# =====================================================
# VISUAL SETTINGS (WITH FILTERS)
# =====================================================
st.sidebar.header("⚙️ Visual Settings")

AGGS = ["Count","Sum","Average","Min","Max"]

for cid, cfg in st.session_state.charts.items():
    with st.sidebar.expander(cfg["title"], expanded=False):

        cfg["title"] = st.text_input("Title", cfg["title"], key=f"t_{cid}")

        cfg["x"] = st.selectbox("X field", cols, key=f"x_{cid}")
        cfg["y"] = st.selectbox("Y field", cols, key=f"y_{cid}")

        cfg["agg"] = st.selectbox("Aggregation", AGGS, key=f"agg_{cid}")

        # ---------------- VISUAL FILTERS ----------------
        st.markdown("**Filters (Visual-level)**")

        for c in cols:
            if df_raw[c].dtype == object:
                options = sorted(df_raw[c].dropna().astype(str).unique())
                cfg["filters"][c] = st.multiselect(
                    c,
                    options,
                    cfg["filters"].get(c, []),
                    key=f"vf_{cid}_{c}"
                )

        # ---------------- ACTIONS ----------------
        if st.button("🗑 Delete", key=f"del_{cid}"):
            del st.session_state.charts[cid]
            st.rerun()

# =====================================================
# BUILD VISUALS (PIPELINE APPLIED)
# =====================================================
st.divider()
st.markdown("## 📈 Dashboard")

for cid, cfg in st.session_state.charts.items():

    # ---- APPLY GLOBAL FILTERS FIRST ----
    vdf = global_filtered_df.copy()

    # ---- APPLY VISUAL FILTERS SECOND ----
    for c, vals in cfg["filters"].items():
        if vals:
            vdf = vdf[vdf[c].astype(str).isin(vals)]

    # ---- AGGREGATION ----
    if cfg["agg"] == "Count":
        agg_df = vdf.groupby(cfg["x"]).size().reset_index(name="value")
    else:
        vdf[cfg["y"]] = pd.to_numeric(vdf[cfg["y"]], errors="coerce")
        agg_map = {"Sum":"sum","Average":"mean","Min":"min","Max":"max"}
        agg_df = vdf.groupby(cfg["x"])[cfg["y"]].agg(
            agg_map[cfg["agg"]]
        ).reset_index(name="value")

    # ---- CHART ----
    fig = (
        px.bar(agg_df, x=cfg["x"], y="value")
        if cfg["type"] == "Bar"
        else px.line(agg_df, x=cfg["x"], y="value")
        if cfg["type"] == "Line"
        else px.scatter(agg_df, x=cfg["x"], y="value")
        if cfg["type"] == "Scatter"
        else px.pie(agg_df, names=cfg["x"], values="value")
    )

    fig.update_layout(title=cfg["title"])
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{cid}")
