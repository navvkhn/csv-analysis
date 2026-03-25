# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

st.set_page_config(page_title="CSV / Excel Data Explorer", layout="wide", page_icon="📊")

# =====================================================
# OPTIMIZATION: CACHE DATA LOADING
# =====================================================
@st.cache_data(show_spinner="Loading data...")
def load_data(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

# =====================================================
# AI ANALYSIS FUNCTION
# =====================================================
def get_ai_analysis(dataframe):
    try:
        # Fails gracefully if secrets aren't set up yet
        api_key = st.secrets.get("OLLAMA_API_KEY", "ollama")
        
        client = OpenAI(
            base_url="https://test.mynewgen.xyz/v1", 
            api_key=api_key
        )

        data_summary = f"""
        Dataset Summary:
        - Total Rows: {dataframe.shape[0]}
        - Total Columns: {dataframe.shape[1]}
        - Columns: {', '.join(dataframe.columns.tolist())}
        - Basic Stats: \n{dataframe.describe().to_string()}
        """
        
        prompt = f"You are an expert Data Analyst. Based on this dataset summary, provide a brief 3-sentence analysis of the data structure, and suggest exactly 2 specific chart types the user should build using the available columns.\n\n{data_summary}"
        
        return client.chat.completions.create(
            model="qwen3.5:1.8b", # Ensure this matches your local Ollama instance
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
    except Exception as e:
        return None

# =====================================================
# RESET
# =====================================================
def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# HEADER & UPLOAD
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0">📊 CSV / Excel Data Explorer</h3>
<small>BI-grade analysis tool with Local AI</small>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Reset App"):
    reset_app()

uploaded = st.session_state.get("file_upload")

if uploaded is None:
    with st.expander("📁 File Controls", expanded=True):
        file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
        if file:
            st.session_state.file_upload = file
            st.rerun()

uploaded = st.session_state.get("file_upload")
if not uploaded:
    st.info("Please upload a dataset to begin.")
    st.stop()

# =====================================================
# LOAD & PREVIEW DATA
# =====================================================
if "raw_df" not in st.session_state:
    st.session_state.raw_df = load_data(uploaded)

raw_df = st.session_state.raw_df.copy()

with st.expander("📋 Data Preview & Column Selection", expanded=True):
    selected_cols = st.multiselect(
        "Select columns to include in analysis",
        raw_df.columns.tolist(),
        default=raw_df.columns.tolist()
    )
    df = raw_df[selected_cols].copy()
    st.dataframe(df.head(50), use_container_width=True)

cols = df.columns.tolist()

# =====================================================
# AI ASSISTANT UI
# =====================================================
st.subheader("🤖 Ask Local AI")
if st.button("Generate AI Insights", type="primary"):
    with st.spinner("Connecting to secure home AI server..."):
        response_stream = get_ai_analysis(df)
        if response_stream:
            response_container = st.empty()
            full_response = ""
            for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_container.info(full_response + "▌")
            response_container.info(full_response)
        else:
            st.error("Could not connect to the AI server. Check your Cloudflare tunnel and API key.")

# =====================================================
# GLOBAL FILTERS
# =====================================================
st.sidebar.header("🔍 Global Filters")
filtered_df = df.copy()

for c in cols:
    # Only create filters for categorical data with reasonable unique counts
    if filtered_df[c].dtype == object and filtered_df[c].nunique() < 50:
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

if "visual_filters" not in st.session_state:
    st.session_state.visual_filters = {}
if "custom_sort" not in st.session_state:
    st.session_state.custom_sort = {}

charts_data = []
AGGS = ["Count", "Sum", "Average", "Min", "Max"]

for chart_num in range(num_charts):
    with st.sidebar.expander(f"📊 Chart {chart_num + 1} Configuration", expanded=(chart_num==0)):
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Area", "Pie", "Donut", "Histogram"], key=f"type_{chart_num}")
        x_col = st.selectbox("X-axis (Category)", cols, key=f"x_{chart_num}")
        y_col = st.selectbox("Y-axis (Value)", cols, key=f"y_{chart_num}")
        aggregation = st.selectbox("Aggregation", AGGS, key=f"agg_{chart_num}")
        title = st.text_input("Chart Title", f"{aggregation} of {y_col} by {x_col}", key=f"title_{chart_num}")

        with st.expander("Axes & Labels"):
            hide_x = st.checkbox("Hide X-axis", False, key=f"hx_{chart_num}")
            hide_y = st.checkbox("Hide Y-axis", False, key=f"hy_{chart_num}")
            show_labels = st.checkbox("Show Data Labels", False, key=f"lbl_{chart_num}")
            decimals = st.slider("Decimals", 0, 5, 2, key=f"dec_{chart_num}")

        with st.expander("Legend & Sorting"):
            show_legend = st.checkbox("Show Legend", True, key=f"leg_{chart_num}")
            legend_pos = st.selectbox("Legend Position", ["v", "h"], key=f"legpos_{chart_num}")
            sort_mode = st.selectbox("Sort By", ["None", "Value (Asc)", "Value (Desc)"], key=f"sort_mode_{chart_num}")
            st.session_state.custom_sort[chart_num] = {"mode": sort_mode}

    # --- DATA PREP FOR CHART ---
    chart_df = filtered_df.copy()
    
    try:
        if chart_type == "Histogram":
            fig = px.histogram(chart_df, x=x_col, title=title)
        else:
            if aggregation == "Count":
                agg_df = chart_df.groupby(x_col).size().reset_index(name="value")
                y_target = "value"
            else:
                chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
                agg_map = {"Sum": "sum", "Average": "mean", "Min": "min", "Max": "max"}
                agg_df = chart_df.groupby(x_col)[y_col].agg(agg_map[aggregation]).reset_index(name="value")
                y_target = "value"

            # Apply Sorting
            sort_cfg = st.session_state.custom_sort.get(chart_num, {})
            if sort_cfg.get("mode") == "Value (Asc)":
                agg_df = agg_df.sort_values(y_target, ascending=True)
            elif sort_cfg.get("mode") == "Value (Desc)":
                agg_df = agg_df.sort_values(y_target, ascending=False)

            # Build Figure
            if chart_type == "Bar":
                fig = px.bar(agg_df, x=x_col, y=y_target, color=x_col)
            elif chart_type == "Line":
                fig = px.line(agg_df, x=x_col, y=y_target, markers=True)
            elif chart_type == "Scatter":
                fig = px.scatter(agg_df, x=x_col, y=y_target, color=x_col, size=y_target)
            elif chart_type == "Area":
                fig = px.area(agg_df, x=x_col, y=y_target)
            elif chart_type == "Pie":
                fig = px.pie(agg_df, names=x_col, values=y_target)
            elif chart_type == "Donut":
                fig = px.pie(agg_df, names=x_col, values=y_target, hole=0.4)

        # Apply Layout Updates
        if show_labels and chart_type not in ["Pie", "Donut", "Histogram"]:
            fig.update_traces(texttemplate=f"%{{y:.{decimals}f}}", textposition="outside")

        fig.update_layout(
            title=title,
            showlegend=show_legend,
            legend_orientation="v" if legend_pos == "v" else "h",
            xaxis_title="" if hide_x else x_col,
            yaxis_title="" if hide_y else (y_col if chart_type != "Histogram" else "Count"),
            height=450
        )
        charts_data.append((chart_num, fig))
        
    except Exception as e:
        charts_data.append((chart_num, None)) # Pass None if calculation fails

# =====================================================
# DASHBOARD RENDERING (SMART GRID)
# =====================================================
st.divider()
st.markdown("## 📈 Dashboard")

if num_charts == 1:
    if charts_data[0][1]:
        st.plotly_chart(charts_data[0][1], use_container_width=True)
    else:
        st.warning("Could not render chart. Please check your X/Y axis and aggregation settings.")
elif num_charts == 2:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts_data[0][1], use_container_width=True) if charts_data[0][1] else st.warning("Chart 1 Error")
    with col2:
        st.plotly_chart(charts_data[1][1], use_container_width=True) if charts_data[1][1] else st.warning("Chart 2 Error")
elif num_charts >= 3:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts_data[0][1], use_container_width=True) if charts_data[0][1] else st.warning("Chart 1 Error")
        if num_charts == 4:
            st.plotly_chart(charts_data[2][1], use_container_width=True) if charts_data[2][1] else st.warning("Chart 3 Error")
    with col2:
        st.plotly_chart(charts_data[1][1], use_container_width=True) if charts_data[1][1] else st.warning("Chart 2 Error")
        if num_charts == 3:
            st.plotly_chart(charts_data[2][1], use_container_width=True) if charts_data[2][1] else st.warning("Chart 3 Error")
        if num_charts == 4:
            st.plotly_chart(charts_data[3][1], use_container_width=True) if charts_data[3][1] else st.warning("Chart 4 Error")

# =====================================================
# EXPORT
# =====================================================
st.divider()
st.download_button(
    "📥 Download Filtered Data as CSV",
    filtered_df.to_csv(index=False),
    "filtered_data.csv",
    type="primary"
)
