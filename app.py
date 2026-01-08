# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from copy import deepcopy
from streamlit_elements import elements, dashboard, mui, html

st.set_page_config(page_title="CSV Data Explorer BI", layout="wide")

# =====================================================
# RESET
# =====================================================
def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# INIT STATE
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
<small>Power BI–style visual authoring</small>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Back to Start"):
    reset_app()

# =====================================================
# FILE UPLOAD (CSV + EXCEL)
# =====================================================
uploaded = st.session_state.get("file_upload")

if uploaded is None:
    file = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
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
    if uploaded.name.endswith((".xlsx",".xls")):
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

cols = df.columns.tolist()
num_cols = df.select_dtypes(include="number").columns.tolist()

# =====================================================
# GLOBAL FILTERS
# =====================================================
st.sidebar.header("🔍 Global Filters")

filtered_df = df.copy()
for c in cols:
    if filtered_df[c].dtype == object:
        vals = sorted(filtered_df[c].dropna().astype(str).unique())
        sel = st.sidebar.multiselect(c, vals, key=f"gf_{c}")
        if sel:
            filtered_df = filtered_df[filtered_df[c].astype(str).isin(sel)]

# =====================================================
# LAYOUT MODE
# =====================================================
st.sidebar.divider()
layout_mode = st.sidebar.toggle("🧱 Layout Mode (Drag & Resize)", False)

# =====================================================
# ADD VISUAL
# =====================================================
st.sidebar.divider()
st.sidebar.header("➕ Add Visual")

ct = st.sidebar.selectbox(
    "Chart Type",
    ["Bar","Line","Scatter","Area","Pie","Donut","Histogram"]
)
x = st.sidebar.selectbox("X-axis", cols)
y = st.sidebar.selectbox("Y-axis", cols)

if st.sidebar.button("➕ Add Chart"):
    cid = f"chart_{st.session_state.chart_counter}"
    st.session_state.chart_counter += 1

    st.session_state.charts[cid] = {
        "type": ct,
        "x": x,
        "y": y,
        "aggregation": "Count",

        "title": f"{ct} Chart",
        "x_title": x,
        "y_title": y,

        "hide_x": False,
        "hide_y": False,

        "x_axis_type": "category",
        "y_axis_type": "linear",

        "show_labels": False,
        "label_position": "outside",
        "decimals": 2,

        "legend": True,
        "legend_pos": "v",

        "custom_sort": [],
        "custom_colors": {},

        "pie_label_mode": "label+percent",

        "bins": 30,

        "filters": {}
    }

    st.session_state.layout.append(
        dashboard.Item(cid, x=0, y=len(st.session_state.layout)*4, w=6, h=4)
    )
    st.rerun()

# =====================================================
# VISUAL SETTINGS (CHART-TYPE AWARE, NON-RESTRICTIVE)
# =====================================================
st.sidebar.divider()
st.sidebar.header("⚙️ Visual Settings")

AGGS = ["Count","Sum","Average","Min","Max"]

for cid, cfg in list(st.session_state.charts.items()):
    is_axis = cfg["type"] not in ["Pie","Donut","Histogram"]
    is_pie = cfg["type"] in ["Pie","Donut"]

    with st.sidebar.expander(cfg["title"], expanded=False):

        cfg["title"] = st.text_input("Chart Title", cfg["title"], key=f"t_{cid}")

        cfg["aggregation"] = st.selectbox(
            "Aggregation",
            AGGS,
            index=AGGS.index(cfg["aggregation"]),
            key=f"agg_{cid}"
        )

        cfg["x"] = st.selectbox("X-axis", cols, index=cols.index(cfg["x"]), key=f"x_{cid}")
        cfg["y"] = st.selectbox("Y-axis", cols, index=cols.index(cfg["y"]), key=f"y_{cid}")

        cfg["x_title"] = st.text_input("X-axis Title", cfg["x_title"], key=f"xt_{cid}")
        cfg["y_title"] = st.text_input("Y-axis Title", cfg["y_title"], key=f"yt_{cid}")

        if is_axis:
            cfg["hide_x"] = st.checkbox("Hide X-axis", cfg["hide_x"], key=f"hx_{cid}")
            cfg["hide_y"] = st.checkbox("Hide Y-axis", cfg["hide_y"], key=f"hy_{cid}")

            cfg["x_axis_type"] = st.selectbox(
                "X-axis Type", ["category","linear"],
                index=0 if cfg["x_axis_type"]=="category" else 1,
                key=f"xat_{cid}"
            )
            cfg["y_axis_type"] = st.selectbox(
                "Y-axis Type", ["linear","log"],
                index=0 if cfg["y_axis_type"]=="linear" else 1,
                key=f"yat_{cid}"
            )

        cfg["legend"] = st.checkbox("Show Legend", cfg["legend"], key=f"leg_{cid}")
        if cfg["legend"]:
            cfg["legend_pos"] = st.selectbox(
                "Legend Position", ["v","h"],
                index=0 if cfg["legend_pos"]=="v" else 1,
                key=f"legpos_{cid}"
            )

        cfg["show_labels"] = st.checkbox("Show Data Labels", cfg["show_labels"], key=f"lbl_{cid}")
        if cfg["show_labels"]:
            cfg["label_position"] = st.selectbox(
                "Label Position",
                ["outside","inside","top center","middle center","bottom center"],
                key=f"lblpos_{cid}"
            )
            cfg["decimals"] = st.slider("Decimals",0,5,cfg["decimals"],key=f"dec_{cid}")

        if is_pie:
            cfg["pie_label_mode"] = st.selectbox(
                "Pie Labels",
                ["label","percent","label+percent","value","value+percent"],
                key=f"plm_{cid}"
            )

        cats = sorted(filtered_df[cfg["x"]].dropna().astype(str).unique())
        cfg["custom_sort"] = st.multiselect(
            "Custom Sort Order",
            cats,
            cfg["custom_sort"],
            key=f"sort_{cid}"
        )

        st.markdown("**Custom Colors**")
        for v in cats:
            cfg["custom_colors"][v] = st.color_picker(
                v, cfg["custom_colors"].get(v,"#1f77b4"), key=f"clr_{cid}_{v}"
            )

        if cfg["type"]=="Histogram":
            cfg["bins"] = st.slider("Bins",5,100,cfg["bins"],key=f"bins_{cid}")

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
# BUILD FIGURES (FULL AGGREGATION SUPPORT)
# =====================================================
figs = {}

for cid,cfg in st.session_state.charts.items():
    vdf = filtered_df.copy()

    for c,v in cfg["filters"].items():
        if v:
            vdf = vdf[vdf[c].astype(str).isin(v)]

    # ----- AGG -----
    if cfg["aggregation"]=="Count":
        agg_df = vdf.groupby(cfg["x"]).size().reset_index(name="value")
    else:
        vdf[cfg["y"]] = pd.to_numeric(vdf[cfg["y"]], errors="coerce")
        agg_map = {
            "Sum":"sum","Average":"mean","Min":"min","Max":"max"
        }
        agg_df = vdf.groupby(cfg["x"])[cfg["y"]].agg(
            agg_map[cfg["aggregation"]]
        ).reset_index(name="value")

    if cfg["custom_sort"]:
        agg_df[cfg["x"]] = pd.Categorical(
            agg_df[cfg["x"]].astype(str),
            categories=cfg["custom_sort"],
            ordered=True
        )
        agg_df = agg_df.sort_values(cfg["x"])

    # ----- CHART -----
    if cfg["type"]=="Bar":
        fig = px.bar(
            agg_df,x=cfg["x"],y="value",color=cfg["x"],
            color_discrete_map=cfg["custom_colors"]
        )
    elif cfg["type"]=="Line":
        fig = px.line(agg_df,x=cfg["x"],y="value",markers=True)
    elif cfg["type"]=="Scatter":
        fig = px.scatter(agg_df,x=cfg["x"],y="value",color=cfg["x"])
    elif cfg["type"]=="Area":
        fig = px.area(agg_df,x=cfg["x"],y="value")
    elif cfg["type"]=="Pie":
        fig = px.pie(
            agg_df,names=cfg["x"],values="value",
            color_discrete_map=cfg["custom_colors"]
        )
    elif cfg["type"]=="Donut":
        fig = px.pie(
            agg_df,names=cfg["x"],values="value",hole=0.4,
            color_discrete_map=cfg["custom_colors"]
        )
    else:
        fig = px.histogram(vdf,x=cfg["x"],nbins=cfg["bins"])

    if cfg["show_labels"] and cfg["type"] not in ["Pie","Donut"]:
        fig.update_traces(
            texttemplate=f"%{{y:.{cfg['decimals']}f}}",
            textposition=cfg["label_position"]
        )

    if cfg["type"] in ["Pie","Donut"]:
        fig.update_traces(textinfo=cfg["pie_label_mode"])

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

    figs[cid]=fig

# =====================================================
# DASHBOARD
# =====================================================
st.divider()
st.markdown("## 📈 Dashboard")

if not layout_mode:
    for cid,fig in figs.items():
        st.plotly_chart(fig,use_container_width=True,key=f"plot_{cid}")
else:
    with elements("dashboard"):
        with dashboard.Grid(
            st.session_state.layout,
            cols=12,rowHeight=90,
            draggableHandle=".drag-handle",
            onLayoutChange=lambda l: st.session_state.update({"layout":l})
        ):
            for cid,fig in figs.items():
                with mui.Card(key=cid,sx={"height":"100%"}):
                    mui.CardHeader(
                        title=st.session_state.charts[cid]["title"],
                        className="drag-handle"
                    )
                    mui.CardContent(
                        html.Div(fig.to_html(include_plotlyjs="cdn"),
                                 dangerouslySetInnerHTML=True)
                    )
