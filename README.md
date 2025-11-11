# 📊 CSV Data Explorer

A powerful, interactive **Streamlit-based data visualization and analysis tool** that lets you upload CSV files, apply filters, create customizable charts, and export results.

**Built by:** Naved Khan

---

## ✨ Features

### 📁 File Management
- **Drag & Drop Upload** - Easy CSV file upload (max 200MB)
- **Multiple File Support** - Switch between files without restarting
- **Reset Functionality** - Clear all filters and chart settings with one click

### 🔍 Data Filtering
- **Categorical Filters** - Multi-select filtering by column values
- **DateTime Filters** - Date range picker + timeline slider
- **Live Filtering** - Charts update instantly as you filter
- **Data Preview** - Quick peek at first 5 rows of your data

### 📈 Chart Types
- **12 Chart Types**: Bar, Horizontal Bar, Line, Area, Scatter, Bubble, Box Plot, Histogram, Pie, Donut, Sunburst, Funnel
- **Small Multiples (Facets)** - Create separate charts for different categories
- **Customizable Axes**:
  - Hide/show X and Y axes
  - Rename axis labels
  - Toggle axis labels/grid

### 🎨 Styling & Appearance
- **Color Schemes** - 11 pre-built palettes (Viridis, Plotly, Set1-3, Pastel1-2, Dark2, Paired, Accent)
- **Custom Colors** - Pick individual colors for each category
- **Data Labels** - Toggle labels with position control (inside/outside/auto)
- **Background Toggle** - Show/hide chart background
- **Legend Control** - Position (vertical/horizontal) and visibility

### 📊 Multiple Charts
- **1-4 Charts** - Create up to 4 charts side-by-side
- **Smart Grid Layout**:
  - 1 chart: Full width
  - 2 charts: Side by side
  - 3 charts: 2 + 1
  - 4 charts: 2x2 grid

### 📥 Export & Download
- **Chart Export** - Download charts as PNG images
- **CSV Export** - Download filtered data as CSV
- **Record Counter** - See how many rows match your filters

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone or download the repository**:
   ```bash
   cd data_explorer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

4. **Open in browser**:
   - Local: `http://localhost:8501`
   - Network: `http://<your-ip>:8501`

---

## 📦 Dependencies

- **streamlit** - Web app framework
- **pandas** - Data manipulation
- **plotly** - Interactive visualizations

See `requirements.txt` for exact versions.

---

## 📖 How to Use

### 1. **Upload CSV**
   - Click "Drag and drop file here" or browse your computer
   - File name appears in center header

### 2. **Configure Data**
   - **DateTime Configuration**: Mark columns as dates (enables date filtering)
   - **Filter Configuration**: Select which columns to filter by
   - **Filter Options**: Choose specific values/date ranges

### 3. **Create Charts**
   - Select number of charts (1-4)
   - For each chart:
     - Choose chart type
     - Pick X and Y axes
     - Set aggregation (Count, Sum, Average, Min, Max)
     - Customize title, colors, labels, axes

### 4. **Customize Appearance**
   - **Color Scheme**: Pick from 11 pre-built palettes
   - **Custom Colors**: Toggle and pick individual category colors
   - **Axis Configuration**: Hide axes, rename labels
   - **Small Multiples**: Create faceted charts by category
   - **Data Labels**: Show values on chart points

### 5. **Export**
   - **Export Charts**: Download individual or all charts as PNG
   - **Download CSV**: Get filtered data as CSV file
   - **View Metrics**: See record count

---

## 🎯 Chart Type Guide

| Chart Type | Best For | Supports Custom Colors | Supports Facets |
|---|---|---|---|
| **Bar** | Comparisons | ✅ | ✅ |
| **Horizontal Bar** | Long category names | ✅ | ❌ |
| **Line** | Trends over time | ✅ | ✅ |
| **Area** | Cumulative trends | ✅ | ✅ |
| **Scatter** | Relationships/clusters | ✅ | ✅ |
| **Bubble** | 3-dimensional data | ✅ | ❌ |
| **Box Plot** | Distribution/outliers | ✅ | ❌ |
| **Histogram** | Distribution | ✅ | ✅ |
| **Pie** | Part-to-whole | ✅ | ❌ |
| **Donut** | Part-to-whole (ring) | ✅ | ❌ |
| **Sunburst** | Hierarchical data | ✅ | ❌ |
| **Funnel** | Sequential stages | ✅ | ❌ |

---

## 🎨 Available Color Schemes

1. **Default** - Plotly default
2. **Viridis** - Perceptually uniform
3. **Plotly** - Plotly standard
4. **Set1-3** - Bold, distinct colors
5. **Pastel1-2** - Soft, muted tones
6. **Dark2** - Dark with contrast
7. **Paired** - Coordinated pairs
8. **Accent** - Accent colors

---

## 📋 File Structure

```
data_explorer/
├── app.py                 # Main app (single-file version)
├── upload.py             # Upload page (if using multi-page)
├── pages/
│   └── explorer.py      # Explorer page (if using multi-page)
├── requirements.txt      # Dependencies
└── README.md            # This file
```

---

## 🔧 Configuration

### DateTime Columns
When you select a column as DateTime:
- Streamlit automatically converts it to date format
- Enables date range filtering with calendar picker
- Allows timeline slider for precise date selection

### Filters
- **Categorical**: Multi-select from unique values
- **DateTime**: Calendar date picker + timeline slider
- All filters apply in real-time to charts

### Axis Labels
- Rename X/Y axes to custom labels
- Hide axes completely to focus on data
- Hide only axis labels (grid stays visible)

---

## ⚙️ Advanced Features

### Small Multiples (Facets)
Create a grid of smaller charts, one per category:
1. Choose a chart type that supports facets (Bar, Line, Area, Scatter, Histogram)
2. Enable "Use Small Multiples (Facets)" toggle
3. Select the column to facet by
4. Charts will split automatically

### Custom Color Per Category
1. Enable "Custom Color per Category" toggle
2. Color pickers appear for each unique value
3. Pick your colors and apply instantly

### Aggregation Options
- **Count** - Number of rows
- **Sum** - Total values
- **Average** - Mean value
- **Min** - Minimum value
- **Max** - Maximum value

---

## 🐛 Troubleshooting

### "No CSV loaded" error
- Go back to Upload page and upload a file first

### Duplicate key error
- Click "Reset Filters" button to clear session state
- Restart Streamlit (Ctrl+C, then `streamlit run app.py`)

### Chart not updating
- Check that filters are correctly applied (see "Applied Filters" section)
- Try resetting the chart settings

### Color picker not working
- Only available for non-Pie charts (Pie/Donut/Sunburst use different coloring)
- Make sure "Custom Color per Category" toggle is ON

### Export to PNG fails
- Requires `kaleido` library: `pip install kaleido`
- Check that Plotly charts render correctly first

---

## 💡 Tips & Tricks

1. **Preset Filters**: Set up filters before creating charts for faster visualization
2. **Multiple Views**: Create 4 different charts to compare different aspects
3. **Color Consistency**: Use custom colors across multiple charts for consistent branding
4. **Export Workflow**: Export filtered data as CSV, then create reports in Excel
5. **Small Multiples**: Great for comparing trends across regions/categories

---

## 📝 License

Open source - free to use and modify

---

## 👤 Author

**Naved Khan**

---

## 📞 Support

For issues, questions, or feature requests, please reach out or check the code comments.

---

## 🚧 Roadmap

- [ ] Correlation matrices
- [ ] Statistical tests
- [ ] Custom SQL filters
- [ ] Save chart configurations
- [ ] Import from databases
- [ ] Pivot table support
- [ ] Time series forecasting

---

**Happy exploring! 📊**