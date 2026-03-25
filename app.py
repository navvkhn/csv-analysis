# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
import io

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(page_title="Data Explorer & AI", layout="wide", page_icon="📊")

# =====================================================
# MODERN SAAS UI/UX CSS
# =====================================================
st.markdown("""
<style>
    /* Pin the AI Popover to bottom right and restrict width to prevent screen blocking */
    div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        width: max-content !important; 
        z-index: 999999 !important;
    }
    
    /* Modern Pill Button Styling */
    div[data-testid="stPopover"] > button {
        border-radius: 30px !important;
        padding: 12px 28px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stPopoverBody"] {
        width: 400px !important;
        height: 600px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15) !important;
    }

    /* Fix for main container padding */
    .block-container {
        padding-bottom: 150px !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# STATE & DATA HELPERS
# =====================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data(show_spinner="Loading data...")
def load_data(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:20px;border-radius:12px;color:white;margin-bottom:24px;">
<h2 style="margin:0;">📊 CSV / Excel Data Explorer</h2>
<p style="margin:0; opacity: 0.9;">Professional Analysis with Local AI Assistance</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR & UPLOAD
# =====================================================
with st.sidebar:
    st.header("📁 Data Source")
    if st.button("🔄 Reset App"):
        reset_app()
    
    file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx", "xls"])
    if not file:
        st.info("Upload a file to begin.")
        st.stop()

# Load Data
if "raw_df" not in st.session_state:
    st.session_state.raw_df = load_data(file)

df = st.session_state.raw_df.copy()
cols = df.columns.tolist()

# =====================================================
# FULL FILE AI ANALYSIS SECTION
# =====================================================
st.subheader("📑 Smart File Analysis")
with st.container(border=True):
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("**Full Dataset Report**")
        st.caption("AI will scan all columns, data types, and statistics to provide a high-level executive summary.")
        analyze_full = st.button("🚀 Run Full File Analysis", type="primary", use_container_width=True)
    
    with col2:
        report_placeholder = st.empty()
        if analyze_full:
            # Prepare the context-rich summary for the LLM
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()
            
            stats_summary = df.describe(include='all').transpose().to_string()
            
            prompt = f"""
            You are a Senior Data Scientist. Analyze this entire file and provide:
            1. An executive summary of what this data represents.
            2. 3 key observations regarding data quality or trends.
            3. 2 strategic recommendations for deeper investigation.

            DATASET METADATA:
            Rows: {df.shape[0]}, Columns: {df.shape[1]}
            
            STATISTICAL SUMMARY:
            {stats_summary}
            
            COLUMN TYPES:
            {info_str}
            """
            
            try:
                api_key = st.secrets.get("OLLAMA_API_KEY", "ollama")
                client = OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key=api_key)
                
                full_report = ""
                stream = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_report += chunk.choices[0].delta.content
                        report_placeholder.markdown(full_report + "▌")
                report_placeholder.markdown(full_report)
                # Sync to chat memory
                st.session_state.chat_history.append({"role": "assistant", "content": f"**Full File Report Summary:**\n{full_report}"})
            except:
                st.error("Connection to Local AI failed.")

# =====================================================
# DASHBOARD BUILDER
# =====================================================
st.sidebar.divider()
st.sidebar.header("🔍 Visual Controls")
num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

charts_data = []
for i in range(num_charts):
    with st.sidebar.expander(f"📊 Chart {i+1} Settings"):
        c_type = st.selectbox("Type", ["Bar", "Line", "Scatter", "Pie"], key=f"t{i}")
        x = st.selectbox("X-Axis", cols, key=f"x{i}")
        y = st.selectbox("Y-Axis", cols, key=f"y{i}")
        agg = st.selectbox("Aggregation", ["Count", "Sum", "Mean"], key=f"a{i}")
        
        # Build Figure
        try:
            if agg == "Count":
                plot_df = df.groupby(x).size().reset_index(name="val")
            else:
                plot_df = df.groupby(x)[y].agg(agg.lower()).reset_index(name="val")
            
            if c_type == "Bar": fig = px.bar(plot_df, x=x, y="val", color=x)
            elif c_type == "Line": fig = px.line(plot_df, x=x, y="val")
            elif c_type == "Scatter": fig = px.scatter(df, x=x, y=y)
            else: fig = px.pie(plot_df, names=x, values="val")
            
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            charts_data.append((fig, plot_df, f"{agg} of {y} by {x}"))
        except:
            charts_data.append((None, None, None))

# Render Charts
st.divider()
grid_cols = st.columns(2) if num_charts > 1 else [st.container()]
for i, (fig, data, title) in enumerate(charts_data):
    target_col = grid_cols[i % 2] if num_charts > 1 else grid_cols[0]
    with target_col:
        if fig:
            st.markdown(f"**{title}**")
            st.plotly_chart(fig, use_container_width=True)
            if st.button(f"🪄 Analyze this Chart", key=f"ai_btn_{i}"):
                with st.chat_message("assistant"):
                    st.write_stream(OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key="ollama").chat.completions.create(
                        model="qwen2.5:3b",
                        messages=[{"role": "user", "content": f"Briefly analyze this chart data: {data.to_string()}"}],
                        stream=True
                    ))

# =====================================================
# FLOATING CHAT WIDGET
# =====================================================
with st.popover("💬 Ask AI"):
    st.markdown("#### 🤖 Data Companion")
    
    if st.button("Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    chat_box = st.container(height=350)
    for m in st.session_state.chat_history:
        chat_box.chat_message(m["role"]).write(m["content"])
    
    if prompt_input := st.chat_input("Ask about your data..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt_input})
        chat_box.chat_message("user").write(prompt_input)
        
        with chat_box.chat_message("assistant"):
            response_text = ""
            resp_placeholder = st.empty()
            # Send current sample data + chat history for context
            context_prompt = f"Data Sample:\n{df.head(5).to_string()}\n\nUser Question: {prompt_input}"
            
            try:
                client = OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key="ollama")
                stream = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=[{"role": "system", "content": "You are a helpful data assistant."}] + st.session_state.chat_history,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                        resp_placeholder.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            except:
                st.error("AI Server Offline")
