# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
import io

# =====================================================
# 1. PAGE CONFIG & MODERN UI/UX STYLING
# =====================================================
st.set_page_config(page_title="Data Explorer Pro", layout="wide", page_icon="📊")

# Custom CSS for the Floating Action Button (FAB) and Layout
st.markdown("""
<style>
    /* Force the popover to the bottom right and RESTRICT WIDTH */
    div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        width: max-content !important; 
        z-index: 999999 !important;
    }
    
    /* Style the button as a modern, high-contrast pill */
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
        height: 550px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2) !important;
    }

    /* Prevent content from being hidden behind the floating button */
    .block-container {
        padding-bottom: 120px !important;
    }
    
    /* Clean up headers */
    .stApp header {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 2. STATE & DATA UTILITIES
# =====================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

@st.cache_data(show_spinner="Reading file...")
def load_data(file):
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

def reset_app():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =====================================================
# 3. MAIN HEADER
# =====================================================
st.markdown("""
<div style="background:linear-gradient(90deg,#667eea,#764ba2);
padding:24px;border-radius:15px;color:white;margin-bottom:30px;box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
<h2 style="margin:0; font-weight: 700;">📊 Data Explorer & Local AI Analyst</h2>
<p style="margin:5px 0 0 0; opacity: 0.85; font-size: 1.1rem;">Upload, visualize, and chat with your raw data locally.</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# 4. FILE UPLOAD & PREVIEW
# =====================================================
with st.sidebar:
    st.markdown("### 🛠️ Controls")
    if st.button("🔄 Reset Environment", use_container_width=True):
        reset_app()
    
    st.divider()
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

if not uploaded_file:
    st.info("👋 Welcome! Please upload a dataset in the sidebar to start your analysis.")
    st.stop()

# Load and store data
if "raw_df" not in st.session_state:
    st.session_state.raw_df = load_data(uploaded_file)

df = st.session_state.raw_df.copy()
cols = df.columns.tolist()

with st.expander("🔍 View Raw Data Sample", expanded=False):
    st.dataframe(df.head(100), use_container_width=True)

# =====================================================
# 5. RAW DATA ANALYSIS (THE CORE FEATURE)
# =====================================================
st.markdown("### 📑 Full File Deep-Dive")
with st.container(border=True):
    col_btn, col_res = st.columns([1, 2])
    
    with col_btn:
        st.write("**Analyze Actual Rows**")
        st.caption("AI will read the raw text of your data to find patterns, anomalies, and insights.")
        run_analysis = st.button("🚀 Generate 6-Point Summary", type="primary", use_container_width=True)
    
    with col_res:
        if run_analysis:
            # 1. Prepare raw data string (CSV format is best for LLM understanding)
            # We limit to first 300 rows to ensure local Qwen 1.8b doesn't crash
            raw_data_string = df.head(300).to_csv(index=False)
            
            prompt = f"""
            You are a Senior Data Analyst. Read the following RAW DATA carefully.
            Provide a deep summary of the content in exactly 6 numbered bullet points.
            Highlight specific trends, unusual values, and data quality observations.

            RAW DATA CONTENT:
            {raw_data_string}
            """
            
            report_area = st.empty()
            full_report = ""
            
            try:
                api_key = st.secrets.get("OLLAMA_API_KEY", "ollama")
                client = OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key=api_key)
                
                stream = client.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2, # Lower temperature for factual analysis
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_report += chunk.choices[0].delta.content
                        report_area.info(full_report + "▌")
                report_area.info(full_report)
                
                # Sync report to chat memory for follow-up questions
                st.session_state.chat_history.append({"role": "assistant", "content": f"**Full File Summary:**\n{full_report}"})
            except:
                st.error("Connection failed. Check your Cloudflare tunnel and local Ollama server.")

# =====================================================
# 6. DYNAMIC DASHBOARD BUILDER
# =====================================================
st.sidebar.divider()
st.sidebar.markdown("### 📈 Visuals")
num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

charts_list = []
for i in range(num_charts):
    with st.sidebar.expander(f"Chart {i+1} Configuration"):
        type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"], key=f"t{i}")
        x = st.selectbox("X-Axis", cols, key=f"x{i}")
        y = st.selectbox("Y-Axis", cols, key=f"y{i}")
        agg = st.selectbox("Aggregation", ["Count", "Sum", "Average"], key=f"a{i}")
        
        try:
            if agg == "Count":
                p_df = df.groupby(x).size().reset_index(name="val")
            else:
                p_df = df.groupby(x)[y].agg(agg.lower().replace("average", "mean")).reset_index(name="val")
            
            if type == "Bar": fig = px.bar(p_df, x=x, y="val", color=x, template="plotly_white")
            elif type == "Line": fig = px.line(p_df, x=x, y="val", markers=True)
            elif type == "Scatter": fig = px.scatter(df, x=x, y=y, color_discrete_sequence=['#667eea'])
            else: fig = px.pie(p_df, names=x, values="val", hole=0.4)
            
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            charts_list.append((fig, p_df, f"{agg} of {y} by {x}"))
        except:
            charts_list.append((None, None, None))

# Render Dashboard Grid
st.markdown("### 📊 Dashboard Metrics")
cols_grid = st.columns(2) if num_charts > 1 else [st.container()]
for i, (fig, p_df, title) in enumerate(charts_list):
    with (cols_grid[i % 2] if num_charts > 1 else cols_grid[0]):
        if fig:
            st.markdown(f"**{title}**")
            st.plotly_chart(fig, use_container_width=True)
            # Individual chart analysis button
            if st.button(f"Analyze Visual {i+1}", key=f"ab{i}", use_container_width=True):
                st.chat_message("assistant").write_stream(OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key="ollama").chat.completions.create(
                    model="qwen2.5:3b",
                    messages=[{"role": "user", "content": f"Analyze this chart data briefly: {p_df.to_string()}"}],
                    stream=True
                ))

# =====================================================
# 7. FLOATING AI CHAT PILL (UX OPTIMIZED)
# =====================================================
with st.popover("💬 Ask AI Assistant"):
    st.markdown("#### 🤖 AI Data Companion")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    chat_area = st.container(height=350)
    for m in st.session_state.chat_history:
        chat_area.chat_message(m["role"]).write(m["content"])
    
    if user_q := st.chat_input("Ask a follow-up question..."):
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        chat_area.chat_message("user").write(user_q)
        
        with chat_area.chat_message("assistant"):
            full_res = ""
            place = st.empty()
            # Context includes the first 5 rows of data automatically
            context = f"Data Head:\n{df.head(5).to_csv(index=False)}\n\nUser Question: {user_q}"
            
            try:
                cli = OpenAI(base_url="https://test.mynewgen.xyz/v1", api_key="ollama")
                stream = cli.chat.completions.create(
                    model="qwen2.5:3b",
                    messages=[{"role": "system", "content": "You are a professional analyst."}] + st.session_state.chat_history,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        place.markdown(full_res)
                st.session_state.chat_history.append({"role": "assistant", "content": full_res})
            except:
                st.error("AI Server Offline")

# Export
st.sidebar.divider()
st.sidebar.download_button("📥 Export Current Data", df.to_csv(index=False), "data_export.csv", use_container_width=True)
