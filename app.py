# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(page_title="Data Explorer & AI", layout="wide", page_icon="📊")

# =====================================================
# AGGRESSIVE UI/UX CSS STYLING
# =====================================================
st.markdown("""
<style>
    /* 1. Force the popover to the bottom right */
    [data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        z-index: 999999 !important;
    }
    
    /* 2. Style the popover button as a modern SaaS pill */
    [data-testid="stPopover"] > button {
        border-radius: 30px !important;
        padding: 12px 28px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stPopover"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* 3. Style the open chat window */
    [data-testid="stPopoverBody"] {
        width: 400px !important;
        height: 600px !important;
        padding: 20px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15) !important;
        border: 1px solid #f0f2f6 !important;
    }
    
    /* 4. Make sure the bottom of the page isn't hidden by the widget */
    [data-testid="stMainBlockContainer"] {
        padding-bottom: 100px !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# STATE INITIALIZATION
# =====================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "custom_sort" not in st.session_state:
    st.session_state.custom_sort = {}

# =====================================================
# OPTIMIZATION: CACHE DATA & SMART DEFAULTS
# =====================================================
@st.cache_data(show_spinner="Loading data...")
def load_data(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

def get_smart_categorical_column(df, cols):
    """UX Feature: Prevents the 'barcode' chart by finding a good category (e.g., Status, Priority)"""
    for col in cols:
        # Look for a column with between 2 and 40 unique values (perfect for bar charts)
        if df[col].nunique() > 1 and df[col].nunique() < 40:
            return cols.index(col)
    return 0 # Fallback to first column

def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# HEADER & UPLOAD
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:20px;border-radius:12px;color:white;margin-bottom:24px;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h2 style="margin:0; font-weight: 600;">📊 CSV / Excel Data Explorer</h2>
<p style="margin:5px 0 0 0; opacity: 0.9;">BI-grade analysis tool with Secure Local AI</p>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Reset Environment", use_container_width=False):
    reset_app()

uploaded = st.session_state.get("file_upload")

if uploaded is None:
    with st.container(border=True):
        st.subheader("📁 Upload Dataset")
        file = st.file_uploader("Drop your IT logs, performance data, or standard CSV/Excel files here.", type=["csv", "xlsx", "xls"])
        if file:
            st.session_state.file_upload = file
            st.rerun()

uploaded = st.session_state.get("file_upload")
if not uploaded:
    st.stop()

# =====================================================
# LOAD & PREVIEW DATA
# =====================================================
if "raw_df" not in st.session_state:
    st.session_state.raw_df = load_data(uploaded)

raw_df = st.session_state.raw_df.copy()

with st.expander("📋 Data Preview & Column Selection", expanded=False):
    selected_cols = st.multiselect(
        "Select columns to include in analysis",
        raw_df.columns.tolist(),
        default=raw_df.columns.tolist()
    )
    df = raw_df[selected_cols].copy()
    st.dataframe(df.head(50), use_container_width=True)

cols = df.columns.tolist()
default_x_index = get_smart_categorical_column(df, cols)

# =====================================================
# GLOBAL FILTERS
# =====================================================
st.sidebar.markdown("### 🔍 Global Filters")
filtered_df = df.copy()

for c in cols:
    # UX: Only show filters for manageable categories (prevents lag and visual clutter)
    if filtered_df[c].nunique() < 50:
        options = sorted(filtered_df[c].dropna().astype(str).unique())
        selected = st.sidebar.multiselect(c, options, key=f"gf_{c}")
        if selected:
            filtered_df = filtered_df[filtered_df[c].astype(str).isin(selected)]

st.sidebar.caption(f"**Rows displaying:** {len(filtered_df):,}")

# =====================================================
# MULTI-CHART CONTROL
# =====================================================
st.sidebar.divider()
num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

charts_data = []
AGGS = ["Count", "Sum", "Average", "Min", "Max"]

for chart_num in range(num_charts):
    with st.sidebar.expander(f"📊 Chart {chart_num + 1} Config", expanded=(chart_num==0)):
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Area", "Pie", "Donut", "Histogram"], key=f"type_{chart_num}")
        
        # UX: Use the smart default for X-axis
        x_col = st.selectbox("X-axis (Category)", cols, index=default_x_index, key=f"x_{chart_num}")
        y_col = st.selectbox("Y-axis (Value)", cols, key=f"y_{chart_num}")
        
        aggregation = st.selectbox("Aggregation", AGGS, key=f"agg_{chart_num}")
        title = st.text_input("Chart Title", f"{aggregation} by {x_col}", key=f"title_{chart_num}")

        with st.expander("Appearance & Sorting"):
            show_labels = st.checkbox("Show Data Labels", False, key=f"lbl_{chart_num}")
            show_legend = st.checkbox("Show Legend", True, key=f"leg_{chart_num}")
            sort_mode = st.selectbox("Sort By", ["Value (Desc)", "Value (Asc)", "None"], key=f"sort_{chart_num}")
            st.session_state.custom_sort[chart_num] = {"mode": sort_mode}

    # --- DATA PREP FOR CHART ---
    chart_df = filtered_df.copy()
    
    try:
        if chart_type == "Histogram":
            fig = px.histogram(chart_df, x=x_col, title=title, color_discrete_sequence=['#667eea'])
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

            # Build Figure (UX: Cleaner default colors)
            color_seq = px.colors.qualitative.Pastel
            
            if chart_type == "Bar":
                fig = px.bar(agg_df, x=x_col, y=y_target, color=x_col, color_discrete_sequence=color_seq)
            elif chart_type == "Line":
                fig = px.line(agg_df, x=x_col, y=y_target, markers=True, color_discrete_sequence=['#667eea'])
            elif chart_type == "Scatter":
                fig = px.scatter(agg_df, x=x_col, y=y_target, color=x_col, size=y_target, color_discrete_sequence=color_seq)
            elif chart_type == "Area":
                fig = px.area(agg_df, x=x_col, y=y_target, color_discrete_sequence=['#764ba2'])
            elif chart_type == "Pie":
                fig = px.pie(agg_df, names=x_col, values=y_target, color_discrete_sequence=color_seq)
            elif chart_type == "Donut":
                fig = px.pie(agg_df, names=x_col, values=y_target, hole=0.5, color_discrete_sequence=color_seq)

        # Clean up layout
        fig.update_layout(
            title={'text': title, 'font': {'size': 18}},
            showlegend=show_legend,
            xaxis_title=x_col,
            yaxis_title=(y_col if chart_type != "Histogram" else "Count"),
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            plot_bgcolor='rgba(0,0,0,0)', # Clean white background
        )
        # Add gridlines
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f2f6')
        
        charts_data.append((chart_num, fig))
        
    except Exception as e:
        charts_data.append((chart_num, None))

# =====================================================
# DASHBOARD RENDERING
# =====================================================
st.markdown("### 📈 Dashboard Analytics")

if num_charts == 1:
    if charts_data[0][1]:
        st.plotly_chart(charts_data[0][1], use_container_width=True)
    else:
        st.warning("Could not render chart. Please adjust your axis or aggregation settings.")
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
    "📥 Download Filtered Data (CSV)",
    filtered_df.to_csv(index=False),
    "filtered_data.csv",
    type="secondary"
)

# =====================================================
# FLOATING AI CHAT WIDGET
# =====================================================
# The text here is what appears on the pill button
with st.popover("💬 Ask AI"):
    st.markdown("#### 🤖 Data Assistant")
    
    cols_header = st.columns([3, 1])
    if cols_header[1].button("Clear", help="Clear history", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    chat_container = st.container(height=400)
    
    for msg in st.session_state.chat_history:
        chat_container.chat_message(msg["role"]).write(msg["content"])
    
    with st.form("chat_form", clear_on_submit=True, border=False):
        cols = st.columns([4, 1])
        user_input = cols[0].text_input("Message", label_visibility="collapsed", placeholder="What trends do you see?")
        submitted = cols[1].form_submit_button("➤", use_container_width=True)
        
        if submitted and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            chat_container.chat_message("user").write(user_input)
            
            api_key = st.secrets.get("OLLAMA_API_KEY", "ollama")
            
            try:
                client = OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key=api_key)
                
                system_msg = f"""You are an expert Data Analyst and BI Consultant. 
                The user is viewing a dataset with {df.shape[0]} rows.
                Columns available: {', '.join(df.columns.tolist())}
                Provide precise, actionable insights. Format your response cleanly."""
                
                messages = [{"role": "system", "content": system_msg}] + st.session_state.chat_history
                
                with chat_container.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    stream = client.chat.completions.create(
                        model="qwen3.5:2b", 
                        messages=messages,
                        stream=True
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    
            except Exception as e:
                chat_container.error("Connection failed. Ensure the Cloudflare tunnel to your home server is active.")
