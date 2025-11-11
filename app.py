import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

st.set_page_config(page_title="Data Explorer", layout="wide")

# --- COMPACT FULL-WIDTH HEADER ---
st.markdown("""
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .header-container {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 0;
            margin: 0 -50px 20px -50px;
            padding-top: 20px;
            padding-bottom: 20px;
        }
        .header-title {
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }
        .header-subtitle {
            font-size: 12px;
            opacity: 0.9;
            margin: 4px 0 0 0;
        }
        .footer-container {
            background: #f0f2f6;
            color: #666;
            padding: 15px 20px;
            text-align: center;
            font-size: 12px;
            margin: 20px -50px -20px -50px;
            border-top: 1px solid #ddd;
        }
    </style>
    <div class="header-container">
        <div class="header-title">📊 CSV Data Explorer</div>
        <div class="header-subtitle">by Naved Khan</div>
    </div>
""", unsafe_allow_html=True)

# --- FILE UPLOAD & PREPROCESSING ---
file_expander = st.expander("📁 File Controls", expanded=True)

with file_expander:
    uploaded = st.file_uploader(
        "Drag and drop file here (CSV, max 200MB) — or click to browse",
        type=["csv"],
        key="file_upload"
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("📂 New File", key="new_file_btn", width='stretch'):
            st.session_state.clear()
            st.rerun()
    with col_b:
        if st.button("🔄 Reset Filters", key="reset_filters_btn", width='stretch'):
            for key in list(st.session_state.keys()):
                if key.startswith("filter_") or key.startswith("dt_") or key.startswith("chart_"):
                    del st.session_state[key]
            st.rerun()

# If uploaded, collapse file expander to save space
if "file_upload" in st.session_state and st.session_state["file_upload"] is not None:
    file_expander.empty()
    uploaded = st.session_state["file_upload"]
else:
    uploaded = None

if uploaded:
    # Initialize raw dataframe
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded)
    
    raw_df = st.session_state.raw_df
    
    # --- STEP 1: COLUMN SELECTION ---
    st.subheader("🔧 Data Configuration")
    
    columns_applied = st.session_state.get("columns_applied", False)
    
    with st.expander("Step 1: Select Columns to Keep", expanded=not columns_applied):
        st.info("Select which columns you want to work with")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            selected_cols = st.multiselect(
                "Select columns to keep",
                raw_df.columns.tolist(),
                default=raw_df.columns.tolist(),
                key="selected_columns"
            )
        
        with col_right:
            st.write("")
            st.write("")
            if st.button("✅ Apply Column Selection", key="apply_cols_btn", width='stretch'):
                st.session_state.selected_cols = selected_cols
                st.session_state.columns_applied = True
                st.success(f"Selected {len(selected_cols)} columns")
                st.rerun()
    
    # Check if columns are selected
    if "columns_applied" not in st.session_state:
        st.warning("⚠️ Please select columns and click 'Apply Column Selection' to proceed")
        st.stop()
    
    selected_cols = st.session_state.selected_cols
    df = raw_df[selected_cols].copy()
    
    # --- STEP 2: SCHEMA CONFIGURATION ---
    schema_applied = st.session_state.get("schema_applied", False)
    
    with st.expander("Step 2: Configure Data Types", expanded=not schema_applied):
        st.info("Set data types for each column (optional)")
        
        dtype_config = {}
        cols_grid = st.columns(3)
        
        for idx, col in enumerate(selected_cols):
            current_type = str(df[col].dtype)
            col_idx = idx % 3
            
            with cols_grid[col_idx]:
                new_type = st.selectbox(
                    f"{col}",
                    ["auto", "string", "int64", "float64", "datetime64"],
                    index=0,
                    key=f"dtype_{col}"
                )
                dtype_config[col] = new_type
        
        st.write("")
        if st.button("✅ Apply Data Types", key="apply_schema_btn", width='stretch'):
            # Apply data type conversions
            for col, dtype in dtype_config.items():
                if dtype != "auto":
                    try:
                        if dtype == "datetime64":
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        elif dtype == "int64":
                            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                        elif dtype == "float64":
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        elif dtype == "string":
                            df[col] = df[col].astype(str)
                    except Exception as e:
                        st.warning(f"Could not convert '{col}' to {dtype}: {str(e)}")
            
            st.session_state.df_processed = df.copy()
            st.session_state.schema_applied = True
            st.success("Data types applied successfully!")
            st.rerun()
    
    # Check if schema is applied
    if "schema_applied" not in st.session_state:
        st.warning("⚠️ Please configure data types and click 'Apply Data Types' to proceed")
        st.stop()
    
    df = st.session_state.df_processed.copy()
    
    cols = df.columns.tolist()
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    # --- COMPACT FILENAME ---
    st.markdown(f"<p style='text-align:center;font-size:13px;margin:8px 0;color:#666;'>📄 <code>{uploaded.name}</code></p>", unsafe_allow_html=True)
    
    # Data preview section in body (collapsible)
    with st.expander("👁️ Data Preview", expanded=False):
        st.dataframe(df.head(), width='stretch')

    st.divider()

    st.sidebar.divider()
    
    # Left sidebar for filters
    st.sidebar.header("🔍 Configuration")
    
    # DateTime Configuration Panel
    with st.sidebar.expander("⏰ DateTime Configuration", expanded=False):
        st.info("ℹ️ Select columns to treat as DateTime")
        datetime_cols = st.multiselect(
            "Select DateTime Columns",
            cols,
            key="dt_config_cols"
        )
        
        # Convert selected columns to datetime
        for col in datetime_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                st.error(f"Could not convert '{col}' to DateTime")
    
    # Filter Configuration Panel
    with st.sidebar.expander("🎯 Filter Configuration", expanded=False):
        st.info("ℹ️ Select columns to use as filters")
        available_filter_cols = [c for c in cols if c not in datetime_cols]
        filter_cols = st.multiselect(
            "Select Filter Columns",
            available_filter_cols,
            key="filter_config_cols"
        )
    
    # Dynamic Filters based on configuration
    with st.sidebar.expander("Filter Options", expanded=True):
        filters = {}
        
        # Categorical filters based on selection
        for c in filter_cols:
            if c not in datetime_cols:
                options = sorted([str(x) for x in df[c].dropna().unique().tolist()])
                selected = st.multiselect(
                    f"Select {c}",
                    options,
                    help=f"Click to expand and select values for {c}",
                    key=f"filter_cat_{c}"
                )
                filters[c] = selected
        
        # DateTime filters based on selection
        for dt_col in datetime_cols:
            st.write(f"**{dt_col}** (Date Range)")
            
            # Remove NaT values for slider
            valid_dates = pd.to_datetime(df[dt_col], errors='coerce').dropna()
            
            if len(valid_dates) > 0:
                min_date = valid_dates.min().to_pydatetime()
                max_date = valid_dates.max().to_pydatetime()
                
                try:
                    # Calendar date picker
                    date_col1, date_col2 = st.columns(2)
                    with date_col1:
                        start_date = st.date_input(
                            f"Start",
                            value=min_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"filter_date_start_{dt_col}"
                        )
                    with date_col2:
                        end_date = st.date_input(
                            f"End",
                            value=max_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"filter_date_end_{dt_col}"
                        )
                    
                    # Timeline slider
                    date_range = st.slider(
                        f"Timeline for {dt_col}",
                        min_value=min_date,
                        max_value=max_date,
                        value=(pd.Timestamp(start_date).to_pydatetime(), pd.Timestamp(end_date).to_pydatetime()),
                        key=f"filter_date_slider_{dt_col}"
                    )
                    filters[dt_col] = date_range
                except Exception as e:
                    st.warning(f"Error with date range for {dt_col}: {str(e)}")
                    filters[dt_col] = None
            else:
                st.warning(f"No valid dates found in {dt_col}")
                filters[dt_col] = None

    filtered_df = df.copy()
    
    # Apply categorical filters
    for c, vals in filters.items():
        if c not in datetime_cols:
            if vals:
                filtered_df = filtered_df[filtered_df[c].astype(str).isin(vals)]
    
    # Apply datetime filters
    for dt_col in datetime_cols:
        if dt_col in filters and filters[dt_col] is not None:
            start_date, end_date = filters[dt_col]
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df[dt_col], errors='coerce') >= start_date) & 
                (pd.to_datetime(filtered_df[dt_col], errors='coerce') <= end_date)
            ]

    # --- METRICS DISPLAY AT TOP ---
    st.divider()
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("📊 Total Records", len(df))
    with metric_cols[1]:
        st.metric("🔍 Filtered Records", len(filtered_df))
    with metric_cols[2]:
        st.metric("📉 Reduction", f"{((len(df) - len(filtered_df)) / len(df) * 100):.1f}%")
    with metric_cols[3]:
        active_filter_count = sum(1 for v in filters.values() if v)
        st.metric("🎯 Active Filters", active_filter_count)
    
    # --- ACTIVE FILTERS DISPLAY ---
    if sum(1 for v in filters.values() if v) > 0:
        st.write("**Applied Filters:**")
        filter_text = []
        for filter_name, filter_values in filters.items():
            if filter_values:
                if filter_name in datetime_cols:
                    if filter_values:
                        filter_text.append(f"• **{filter_name}**: {filter_values[0].date()} → {filter_values[1].date()}")
                else:
                    if len(filter_values) <= 3:
                        vals_str = ", ".join(str(v) for v in filter_values)
                    else:
                        vals_str = ", ".join(str(v) for v in filter_values[:3]) + f", +{len(filter_values)-3} more"
                    filter_text.append(f"• **{filter_name}**: {vals_str}")
        
        for text in filter_text:
            st.write(text)
    else:
        st.info("ℹ️ No filters applied - showing all records")
    
    st.divider()

    # Number of charts selector
    st.sidebar.divider()
    num_charts = st.sidebar.slider("Number of Charts", 1, 4, 1)

    charts_data = []
    for chart_num in range(num_charts):
        # --- COLLAPSIBLE CHART SETTINGS ---
        with st.sidebar.expander(f"📊 Chart {chart_num + 1}", expanded=False) as chart_expander:
            
            chart_type = st.selectbox(
                f"Chart Type",
                ["Bar", "Horizontal Bar", "Line", "Area", "Scatter", "Bubble", 
                 "Box Plot", "Histogram", "Pie", "Donut", "Sunburst", "Funnel"],
                key=f"chart_type_{chart_num}"
            )

            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox(f"X-axis", ["Select column"] + cols, key=f"x_col_{chart_num}")
            with col2:
                y_col = st.selectbox(f"Y-axis", ["Select column"] + (num_cols if num_cols else cols), key=f"y_col_{chart_num}")

            # --- SWAP AXIS FUNCTIONALITY ---
            if st.button("🔄 Swap Axes", key=f"swap_axes_{chart_num}", width='stretch'):
                x_col, y_col = y_col, x_col
                st.rerun()

            # Check if columns are selected
            if x_col == "Select column" or y_col == "Select column":
                st.warning("⚠️ Please select both X and Y axis columns")
                continue

            # Only show aggregation for aggregatable charts
            aggregation = "Count"
            if chart_type not in ["Box Plot", "Histogram"]:
                aggregation = st.selectbox(
                    f"Y-axis Aggregation",
                    ["Count", "Sum", "Average", "Min", "Max"],
                    key=f"agg_{chart_num}"
                )

            # Dynamic title update based on selected columns
            default_title = f"{aggregation} of {y_col} by {x_col}"
            chart_title = st.text_input(f"Chart Title", value=default_title, key=f"title_{chart_num}")

            show_background = st.checkbox("Show Background", value=True, key=f"bg_{chart_num}")

            st.write("**Axis Configuration**")
            hide_x_axis = st.checkbox("Hide X-axis", value=False, key=f"hide_x_{chart_num}")
            hide_y_axis = st.checkbox("Hide Y-axis", value=False, key=f"hide_y_{chart_num}")
            
            # Axis labels auto-update based on column selection
            x_label = st.text_input(f"X-axis Label", value=x_col, key=f"x_label_{chart_num}")
            y_label = st.text_input(f"Y-axis Label", value=y_col, key=f"y_label_{chart_num}")

            # --- DYNAMIC FACET SUPPORT ---
            use_facet = False
            facet_col = None
            if chart_type in ["Bar", "Line", "Area", "Scatter", "Histogram"]:
                use_facet = st.checkbox("Use Small Multiples (Facets)", value=False, key=f"facet_{chart_num}")
                if use_facet:
                    facet_col = st.selectbox(
                        f"Facet by Column",
                        [c for c in cat_cols if c not in datetime_cols],
                        key=f"facet_col_{chart_num}"
                    )
            
            # --- DYNAMIC DATA LABELS (only for charts that support them) ---
            show_labels = False
            label_position = "outside"
            decimal_places = 2
            
            if chart_type in ["Bar", "Horizontal Bar"]:
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                if show_labels:
                    label_position = st.selectbox(
                        "Label Position",
                        ["outside", "inside"],
                        key=f"label_pos_{chart_num}"
                    )
                    decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type in ["Line", "Area", "Scatter"]:
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                if show_labels:
                    label_position = st.selectbox(
                        "Label Position",
                        ["top center", "middle center", "bottom center"],
                        key=f"label_pos_{chart_num}"
                    )
                    decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type in ["Bubble"]:
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                if show_labels:
                    label_position = st.selectbox(
                        "Label Position",
                        ["top center", "middle center", "bottom center"],
                        key=f"label_pos_{chart_num}"
                    )
                    decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type == "Histogram":
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                label_position = "auto"
                decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type == "Funnel":
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                label_position = "inside"
                decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type in ["Pie", "Donut"]:
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                label_position = "auto"
                decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            elif chart_type == "Sunburst":
                show_labels = st.checkbox("Show Data Labels", value=False, key=f"labels_{chart_num}")
                label_position = "auto"
                decimal_places = st.slider("Decimal Places", 0, 5, 2, key=f"decimals_{chart_num}")
            # Box Plot doesn't need labels option
            
            show_legend = st.checkbox("Show Legend", value=True, key=f"legend_{chart_num}")
            legend_position = "v"
            if show_legend:
                legend_position = st.selectbox(
                    "Legend Position",
                    ["v", "h"],
                    format_func=lambda x: "Vertical" if x == "v" else "Horizontal",
                    key=f"legend_pos_{chart_num}"
                )

            # --- COLOR CONFIGURATION ---
            st.write("**Color Configuration**")
            color_scheme = st.selectbox(
                "Color Scheme",
                ["Default", "Viridis", "Plotly", "Set1", "Set2", "Set3", "Pastel1", "Pastel2", "Dark2", "Paired", "Accent"],
                key=f"color_scheme_{chart_num}"
            )
            
            # Option to manually pick colors per category (not for Sunburst)
            use_custom_colors = False
            custom_colors = {}
            if chart_type != "Sunburst":
                use_custom_colors = st.checkbox("Custom Color per Category", value=False, key=f"use_custom_colors_{chart_num}")

            # --- SORTING OPTIONS (only for aggregatable charts) ---
            sort_by = "None"
            if chart_type not in ["Box Plot", "Histogram", "Sunburst"]:
                st.write("**Sorting**")
                sort_by = st.selectbox(
                    "Sort By",
                    ["None", "X-axis (A-Z)", "X-axis (Z-A)", "Y-axis (Low-High)", "Y-axis (High-Low)"],
                    key=f"sort_by_{chart_num}"
                )

            # --- BUBBLE SIZE OPTION (only for Bubble chart) ---
            size_col = y_col
            if chart_type == "Bubble":
                size_col = st.selectbox(f"Bubble Size", num_cols, key=f"bubble_{chart_num}") if num_cols else y_col

            # --- AXIS TYPE CONFIGURATION ---
            st.write("**Axis Type**")
            x_axis_type = "linear"
            y_axis_type = "linear"
            
            col_axis1, col_axis2 = st.columns(2)
            with col_axis1:
                if chart_type not in ["Pie", "Donut", "Sunburst"]:
                    x_axis_type = st.selectbox(
                        "X-axis Type",
                        ["linear", "category"],
                        key=f"x_axis_type_{chart_num}"
                    )
            with col_axis2:
                if chart_type not in ["Pie", "Donut", "Sunburst"]:
                    y_axis_type = st.selectbox(
                        "Y-axis Type",
                        ["linear", "log"],
                        key=f"y_axis_type_{chart_num}"
                    )

        # Prepare aggregated data
        agg_map = {"Sum": "sum", "Average": "mean", "Count": "count", "Min": "min", "Max": "max"}
        agg_func = agg_map[aggregation]
        
        try:
            if chart_type in ["Box Plot", "Histogram"]:
                # These charts don't need aggregation
                agg_df = filtered_df.copy()
            elif aggregation == "Count":
                agg_df = filtered_df.groupby(x_col).size().reset_index(name="count")
                agg_df.rename(columns={"count": y_col}, inplace=True)
            else:
                # Ensure y_col is numeric
                filtered_df_copy = filtered_df.copy()
                filtered_df_copy[y_col] = pd.to_numeric(filtered_df_copy[y_col], errors='coerce')
                agg_df = filtered_df_copy.groupby(x_col)[y_col].agg(agg_func).reset_index()
                agg_df.columns = [x_col, y_col]
        except Exception as e:
            st.error(f"Error aggregating data: {str(e)}")
            agg_df = filtered_df.copy()

        # Add custom colors after agg_df is created (skip for unsupported charts)
        if use_custom_colors and chart_type not in ["Pie", "Donut", "Sunburst", "Box Plot", "Histogram"]:
            unique_vals = sorted([str(x) for x in agg_df[x_col].unique()])
            for val in unique_vals:
                color = st.sidebar.color_picker(f"Color for '{val}'", value="#1f77b4", key=f"color_{chart_num}_{val}")
                custom_colors[str(val)] = color

        # Apply sorting (only for supported charts)
        if sort_by != "None" and chart_type not in ["Box Plot", "Histogram", "Sunburst"]:
            if sort_by == "X-axis (A-Z)":
                agg_df = agg_df.sort_values(by=x_col, ascending=True)
            elif sort_by == "X-axis (Z-A)":
                agg_df = agg_df.sort_values(by=x_col, ascending=False)
            elif sort_by == "Y-axis (Low-High)":
                agg_df = agg_df.sort_values(by=y_col, ascending=True)
            elif sort_by == "Y-axis (High-Low)":
                agg_df = agg_df.sort_values(by=y_col, ascending=False)

        # Create decimal format string
        decimal_format = f"%.{decimal_places}f"

        # --- CREATE CHARTS WITH DYNAMIC PROPERTIES ---
        if chart_type == "Bar":
            fig = px.bar(agg_df, x=x_col, y=y_col, color=x_col,
                         text=y_col if show_labels else None,
                         facet_col=facet_col if use_facet else None,
                         color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textposition=label_position, texttemplate=f'%{{y:{decimal_format}}}')
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker_color=colors_list)
        
        elif chart_type == "Horizontal Bar":
            fig = px.bar(agg_df, y=x_col, x=y_col, color=x_col, orientation='h',
                         text=y_col if show_labels else None,
                         color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textposition=label_position, texttemplate=f'%{{x:{decimal_format}}}')
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker_color=colors_list)
        
        elif chart_type == "Line":
            fig = px.line(agg_df, x=x_col, y=y_col, markers=True,
                         facet_col=facet_col if use_facet else None,
                         color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(mode="lines+markers+text", textposition=label_position, texttemplate=f'%{{y:{decimal_format}}}')
        
        elif chart_type == "Area":
            fig = px.area(agg_df, x=x_col, y=y_col,
                         facet_col=facet_col if use_facet else None,
                         color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(mode="lines+markers+text", textposition=label_position, texttemplate=f'%{{y:{decimal_format}}}')
        
        elif chart_type == "Scatter":
            fig = px.scatter(agg_df, x=x_col, y=y_col, color=x_col,
                            facet_col=facet_col if use_facet else None,
                            color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(mode="markers+text", textposition=label_position, texttemplate=f'%{{y:{decimal_format}}}')
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker=dict(color=colors_list))
        
        elif chart_type == "Bubble":
            fig = px.scatter(agg_df, x=x_col, y=y_col, size=size_col, color=x_col,
                            color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(mode="markers+text", textposition=label_position, texttemplate=f'%{{y:{decimal_format}}}')
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker=dict(color=colors_list))
        
        elif chart_type == "Box Plot":
            # Box Plot doesn't support labels, aggregation, or sorting
            fig = px.box(filtered_df, x=x_col, y=y_col, color=x_col,
                         color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
        
        elif chart_type == "Histogram":
            # Histogram doesn't support aggregation or sorting
            fig = px.histogram(filtered_df, x=x_col, color=x_col, nbins=30,
                              facet_col=facet_col if use_facet else None,
                              color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
        
        elif chart_type == "Pie":
            fig = px.pie(agg_df, names=x_col, values=y_col,
                        color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textinfo="label+percent+value", texttemplate=f'<b>%{{label}}</b><br>%{{percent}}<br>%{{value:{decimal_format}}}')
            else:
                fig.update_traces(textinfo="label+percent")
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker=dict(colors=colors_list))
        
        elif chart_type == "Donut":
            fig = px.pie(agg_df, names=x_col, values=y_col, hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textinfo="label+percent+value", texttemplate=f'<b>%{{label}}</b><br>%{{percent}}<br>%{{value:{decimal_format}}}')
            else:
                fig.update_traces(textinfo="label+percent")
            if use_custom_colors and custom_colors:
                colors_list = [custom_colors.get(str(val), "#1f77b4") for val in agg_df[x_col]]
                fig.update_traces(marker=dict(colors=colors_list))
        
        elif chart_type == "Sunburst":
            # Sunburst doesn't support custom colors or labels toggle
            fig = px.sunburst(agg_df, names=x_col, values=y_col,
                             color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textinfo="label+value", texttemplate=f'%{{value:{decimal_format}}}')
        
        elif chart_type == "Funnel":
            agg_df_sorted = agg_df.sort_values(y_col, ascending=False)
            fig = px.funnel(agg_df_sorted, x=y_col, y=x_col,
                           color_discrete_sequence=px.colors.qualitative.__dict__.get(color_scheme, px.colors.qualitative.Plotly))
            if show_labels:
                fig.update_traces(textposition="inside", texttemplate=f'%{{x:{decimal_format}}}')

        # Update layout with axis configuration
        fig.update_layout(
            showlegend=show_legend,
            legend_orientation="v" if legend_position == "v" else "h",
            title=chart_title,
            plot_bgcolor="rgba(240,240,240,0.5)" if show_background else "rgba(255,255,255,0)",
            paper_bgcolor="rgba(240,240,240,0.5)" if show_background else "rgba(255,255,255,0)",
            height=500,
            xaxis_title=x_label if not hide_x_axis else "",
            yaxis_title=y_label if not hide_y_axis else "",
            hovermode='closest'
        )
        
        # Apply axis types
        if chart_type not in ["Pie", "Donut", "Sunburst"]:
            fig.update_xaxes(type=x_axis_type)
            fig.update_yaxes(type=y_axis_type)
        
        # Hide axes if requested
        if hide_x_axis:
            fig.update_xaxes(showticklabels=False, showgrid=False)
        if hide_y_axis:
            fig.update_yaxes(showticklabels=False, showgrid=False)

        # Update sidebar expander title with chart type and title
        chart_display_title = f"{chart_type}: {chart_title[:30]}..." if len(chart_title) > 30 else f"{chart_type}: {chart_title}"

        charts_data.append({'fig': fig, 'title': chart_title, 'num': chart_num, 'type': chart_type})

    # Display charts (kept keys unique)
    if len(charts_data) > 0:
        st.markdown("### 📈 Charts")
        if num_charts == 1:
            st.plotly_chart(charts_data[0]['fig'], width='stretch', key=f"chart_display_{charts_data[0]['num']}")
        elif num_charts == 2:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(charts_data[0]['fig'], width='stretch', key=f"chart_display_{charts_data[0]['num']}")
            with c2:
                if len(charts_data) > 1:
                    st.plotly_chart(charts_data[1]['fig'], width='stretch', key=f"chart_display_{charts_data[1]['num']}")
        elif num_charts == 3:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(charts_data[0]['fig'], width='stretch', key=f"chart_display_{charts_data[0]['num']}")
            with c2:
                if len(charts_data) > 1:
                    st.plotly_chart(charts_data[1]['fig'], width='stretch', key=f"chart_display_{charts_data[1]['num']}")
            if len(charts_data) > 2:
                st.plotly_chart(charts_data[2]['fig'], width='stretch', key=f"chart_display_{charts_data[2]['num']}")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(charts_data[0]['fig'], width='stretch', key=f"chart_display_{charts_data[0]['num']}")
            with c2:
                st.plotly_chart(charts_data[1]['fig'], width='stretch', key=f"chart_display_{charts_data[1]['num']}")
            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(charts_data[2]['fig'], width='stretch', key=f"chart_display_{charts_data[2]['num']}")
            with c4:
                st.plotly_chart(charts_data[3]['fig'], width='stretch', key=f"chart_display_{charts_data[3]['num']}")
    else:
        st.info("⚠️ Configure at least one chart in the sidebar to display charts")

    # Export / CSV / metrics
    st.divider()
    e1, e2, e3 = st.columns(3)
    with e1:
        if st.button("📥 Export All Charts as 4K PNG"):
            if len(charts_data) == 0:
                st.warning("No charts to export")
            else:
                for chart_data in charts_data:
                    try:
                        # 4K ultra high quality export
                        png_data = pio.to_image(
                            chart_data['fig'],
                            format="png",
                            width=3840,      # 4K width
                            height=2160,     # 4K height
                            scale=2          # Additional 2x scaling for super quality
                        )
                        filename = f"{chart_data['type']}_{chart_data['title'].replace(' ', '_')[:40]}.png"
                        st.download_button(
                            label=f"📥 Download {chart_data['type']} Chart",
                            data=png_data,
                            file_name=filename,
                            mime="image/png",
                            key=f"export_4k_{chart_data['num']}"
                        )
                    except Exception as e:
                        st.error(f"Error exporting {chart_data['type']} chart: {str(e)}")
    with e2:
        st.download_button("📊 Download Filtered CSV", filtered_df.to_csv(index=False), "filtered.csv", width='stretch')
    with e3:
        st.metric("Records", len(filtered_df))

    # Applied filters
    st.divider()
    st.subheader("📌 Applied Filters")
    active_filters = {k: v for k, v in filters.items() if v}
    if active_filters:
        for filter_name, filter_values in active_filters.items():
            if filter_name in datetime_cols:
                if filter_values:
                    st.write(f"**{filter_name}:** {filter_values[0].date()} to {filter_values[1].date()}")
            else:
                st.write(f"**{filter_name}:** {', '.join(map(str, filter_values))}")
    else:
        st.info("ℹ️ No filters applied - showing all data")

# --- FOOTER ---
st.markdown("""
    <div class="footer-container">
        Made for Analysis by <strong>Naved Khan</strong> | CSV Data Explorer v1.0
    </div>
""", unsafe_allow_html=True)
