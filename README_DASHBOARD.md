# UIDAI Analytics Dashboard

Interactive dashboard for visualizing Aadhaar update surges and anomalies analysis.

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Dashboard

1. First, ensure you have run the data preprocessing and analysis scripts:
```bash
python data_preprocessing.py
python exploratory_data_analysis.py
```

2. Start the Streamlit dashboard:
```bash
streamlit run dashboard.py
```

3. The dashboard will open in your default web browser (usually at http://localhost:8501)

## Dashboard Features

### 📈 Overview Tab
- Key metrics and summary statistics
- Dataset comparison (pie charts)
- Top states visualization
- Recent trends (last 30 days)

### 📅 Temporal Analysis Tab
- Time series trends (line/area charts)
- Weekly patterns (day of week analysis)
- Monthly trends

### 🗺️ Geographic Analysis Tab
- State-level analysis with filters
- Top states by different metrics
- District-level analysis (filterable by state)
- Geographic distribution charts

### 👥 Age Group Analysis Tab
- Age group distributions (pie charts)
- Age group trends over time
- Biometric, Demographic, and Enrolment age breakdowns

### ⚠️ Coverage & Anomalies Tab
- Coverage Completeness Index analysis
- Districts needing attention
- Anomaly detection (statistical outliers)
- Coverage distribution histograms

### 💡 Insights & Recommendations Tab
- Key insights with priority levels
- Actionable recommendations
- Insights summary statistics
- Category distribution

## Interactive Filters

- **Date Range**: Filter data by date range
- **State Selection**: Filter analysis by state
- **Top N Selection**: Adjust number of items displayed
- **Coverage Threshold**: Adjust threshold for coverage analysis
- **Priority Filter**: Filter insights by priority level

## Data Sources

The dashboard uses:
- `analysis_results/daily_aggregated_data.csv` - Daily aggregated statistics
- `analysis_results/state_level_analysis.csv` - State-level analysis
- `analysis_results/district_coverage_analysis.csv` - Coverage metrics
- `analysis_results/key_insights.csv` - Generated insights
- `processed_data/` - Cleaned raw data for detailed analysis
