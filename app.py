# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from copy import deepcopy
from streamlit_elements import elements, dashboard, mui, html

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
# HEADER
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0">📊 CSV Data Explorer BI</h3>
<small>Capability-based visual editor</small>
</div>
""", unsafe_allow_html=True)

# =====================================================
# FILE UPLOAD
# =====================================================
file = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
if not file:
    st.stop()

df = pd.read_excel(file) if file.name.endswith(("xlsx","xls")) else pd.read_csv(file)
cols = df.columns.tolist()

# =====================================================
# ADD VISUAL
# =====================================================
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

        # data
        "x": cols[0],
        "y": cols[1] if len(cols) > 1 else cols[0],

        # aggregation
        "agg": "Count",

        # axes
        "x_title": "",
        "y_title": "",
        "hide_x": False,
        "hide_y": False,
        "x_axis_type": "category",
        "y_axis_type": "linear",

        # labels
        "show_labels": False,
        "label_position": "outside",
        "decimals": 2,

        # legend
        "legend": True,
        "legend_pos": "v",

        # colors & sort
        "custom_colors": {},
        "custom_sort": [],

        # filters
        "filters": {},

        "title": f"{chart_type} Chart"
    }

    st.session_state.layout.append(
        dashboard.Item(cid, x=0, y=len(st.session_state.layout)*4, w=6, h=4)
    )
    st.rerun()

# =====================================================
# VISUAL SETTINGS (CAPABILITY-BASED)
# =====================================================
st.sidebar.header("⚙️ Visual Settings")

AGGS = ["Count","Sum","Average","Min","Max"]

for cid, cfg in st.session_state.charts.items():
    with st.sidebar.expander(cfg["title"], expanded=False):

        # ---------------- COMMON ----------------
        cfg["title"] = st.text_input("Title", cfg["title"], key=f"title_{cid}")

        # ---------------- DATA ----------------
        st.markdown("**Data Mapping**")
        cfg["x"] = st.selectbox("X field", cols, index=cols.index(cfg["x"]), key=f"x_{cid}")
        cfg["y"] = st.selectbox("Y field", cols, index=cols.index(cfg["y"]), key=f"y_{cid}")

        # ---------------- AGGREGATION ----------------
        st.markdown("**Aggregation**")
        cfg["agg"] = st.selectbox("Aggregation", AGGS, AGGS.index(cfg["agg"]), key=f"agg_{cid}")

        # ---------------- AXES ----------------
        axes_enabled = cfg["type"] not in ["Pie","Donut"]
        with st.expander("Axes", expanded=axes_enabled):
            if not axes_enabled:
                st.caption("This visual does not render axes")
            cfg["x_title"] = st.text_input("X title", cfg["x_title"], key=f"xt_{cid}")
            cfg["y_title"] = st.text_input("Y title", cfg["y_title"], key=f"yt_{cid}")
            cfg["hide_x"] = st.checkbox("Hide X axis", cfg["hide_x"], key=f"hx_{cid}")
            cfg["hide_y"] = st.checkbox("Hide Y axis", cfg["hide_y"], key=f"hy_{cid}")
            cfg["x_axis_type"] = st.selectbox("X scale", ["category","linear"], key=f"xat_{cid}")
            cfg["y_axis_type"] = st.selectbox("Y scale", ["linear","log"], key=f"yat_{cid}")

        # ---------------- LABELS ----------------
        with st.expander("Labels"):
            cfg["show_labels"] = st.checkbox("Show labels", cfg["show_labels"], key=f"lbl_{cid}")
            if cfg["show_labels"]:
                cfg["label_position"] = st.selectbox(
                    "Position",
                    ["outside","inside","top center","middle center","bottom center"],
                    key=f"lblpos_{cid}"
                )
                cfg["decimals"] = st.slider("Decimals",0,5,cfg["decimals"],key=f"dec_{cid}")

        # ---------------- LEGEND ----------------
        with st.expander("Legend"):
            cfg["legend"] = st.checkbox("Show legend", cfg["legend"], key=f"leg_{cid}")
            if cfg["legend"]:
                cfg["legend_pos"] = st.selectbox("Orientation", ["v","h"], key=f"legpos_{cid}")

        # ---------------- COLORS ----------------
        with st.expander("Colors"):
            cats = sorted(df[cfg["x"]].dropna().astype(str).unique())
            for v in cats:
                cfg["custom_colors"][v] = st.color_picker(
                    v, cfg["custom_colors"].get(v,"#1f77b4"), key=f"clr_{cid}_{v}"
                )

        # ---------------- SORT ----------------
        with st.expander("Sorting"):
            cfg["custom_sort"] = st.multiselect(
                "Manual order",
                cats,
                cfg["custom_sort"],
                key=f"sort_{cid}"
            )

        # ---------------- ACTIONS ----------------
        col1,col2 = st.columns(2)
        with col1:
            if st.button("🗑 Delete", key=f"del_{cid}"):
                del st.session_state.charts[cid]
                st.session_state.layout=[l for l in st.session_state.layout if l["i"]!=cid]
                st.rerun()
        with col2:
            if st.button("📄 Duplicate", key=f"dup_{cid}"):
                nid=f"chart_{st.session_state.chart_counter}"
                st.session_state.chart_counter+=1
                st.session_state.charts[nid]=deepcopy(cfg)
                st.session_state.layout.append(
                    dashboard.Item(nid,x=0,y=len(st.session_state.layout)*4,w=6,h=4)
                )
                st.rerun()

# =====================================================
# BUILD FIGURES
# =====================================================
figs = {}

for cid,cfg in st.session_state.charts.items():
    d = df.copy()

    if cfg["agg"] == "Count":
        agg_df = d.groupby(cfg["x"]).size().reset_index(name="value")
    else:
        d[cfg["y"]] = pd.to_numeric(d[cfg["y"]], errors="coerce")
        agg_map = {"Sum":"sum","Average":"mean","Min":"min","Max":"max"}
        agg_df = d.groupby(cfg["x"])[cfg["y"]].agg(agg_map[cfg["agg"]]).reset_index(name="value")

    if cfg["custom_sort"]:
        agg_df[cfg["x"]] = pd.Categorical(
            agg_df[cfg["x"]].astype(str),
            categories=cfg["custom_sort"],
            ordered=True
        )
        agg_df = agg_df.sort_values(cfg["x"])

    if cfg["type"]=="Bar":
        fig = px.bar(agg_df,x=cfg["x"],y="value",color=cfg["x"],
                     color_discrete_map=cfg["custom_colors"])
    elif cfg["type"]=="Line":
        fig = px.line(agg_df,x=cfg["x"],y="value",markers=True)
    elif cfg["type"]=="Scatter":
        fig = px.scatter(agg_df,x=cfg["x"],y="value",color=cfg["x"])
    elif cfg["type"]=="Area":
        fig = px.area(agg_df,x=cfg["x"],y="value")
    elif cfg["type"]=="Pie":
        fig = px.pie(agg_df,names=cfg["x"],values="value",
                     color_discrete_map=cfg["custom_colors"])
    elif cfg["type"]=="Donut":
        fig = px.pie(agg_df,names=cfg["x"],values="value",hole=0.4,
                     color_discrete_map=cfg["custom_colors"])
    else:
        fig = px.histogram(d,x=cfg["x"])

    if cfg["show_labels"] and cfg["type"] not in ["Pie","Donut"]:
        fig.update_traces(
            texttemplate=f"%{{y:.{cfg['decimals']}f}}",
            textposition=cfg["label_position"]
        )

    fig.update_layout(
        title=cfg["title"],
        showlegend=cfg["legend"],
        legend_orientation="v" if cfg["legend_pos"]=="v" else "h",
        xaxis_title="" if cfg["hide_x"] else cfg["x_title"],
        yaxis_title="" if cfg["hide_y"] else cfg["y_title"],
        height=450
    )
    fig.update_xaxes(type=cfg["x_axis_type"])
    fig.update_yaxes(type=cfg["y_axis_type"])

    figs[cid] = fig

# =====================================================
# DASHBOARD
# =====================================================
st.divider()
st.markdown("## 📈 Dashboard")

for cid,fig in figs.items():
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{cid}")
