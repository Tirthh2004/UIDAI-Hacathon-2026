"""
Interactive Dashboard for UIDAI Hackathon Project
AI-Driven Early Warning System for Aadhaar Update Surges and Anomalies

Streamlit dashboard with visualizations, charts, and interactive filters
for administrators to explore data patterns and insights.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, date
import warnings
import json
from chatbot import display_chatbot
from utils_export import render_export_button
warnings.filterwarnings('ignore')

# Import Indian states coordinates and GeoJSON helper
try:
    from india_states_geojson import get_state_coordinates, INDIA_STATE_COORDINATES
except ImportError:
    # Fallback if file doesn't exist
    def get_state_coordinates(state_name):
        return (20.5937, 78.9629)  # Center of India
    INDIA_STATE_COORDINATES = {}

try:
    from india_geojson_helper import load_india_geojson, get_state_name_field, create_state_name_mapping
    GEOJSON_HELPER_AVAILABLE = True
except ImportError:
    GEOJSON_HELPER_AVAILABLE = False

# Import Forensic Analyzer
try:
    from forensic_analysis import ForensicAnalyzer
    FORENSIC_AVAILABLE = True
except ImportError:
    FORENSIC_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="UIDAI Analytics Dashboard | Government of India",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Indian Government styling
st.markdown("""
    <style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Variable definitions for easy maintenance */
    :root {
        --primary: #4E89E8;
        --bg-dark: #0E1117;
        --bg-secondary: #262730;
        --text-main: #FAFAFA;
        --text-muted: #A0AEC0;
        
        --saffron: #FF9933;
        --green: #138808;
        --navy: #000080;
        --gold: #D4AF37;
        
        --success: #48BB78;
        --danger: #F56565;
        
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Main background */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-main);
    }
    
    /* Smooth animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Government header with emblem */
    .gov-header {
        background: linear-gradient(135deg, var(--navy) 0%, #001A33 50%, var(--navy) 100%);
        background-size: 200% 200%;
        animation: gradientShift 15s ease infinite;
        padding: 2rem 2rem;
        border-bottom: 4px solid var(--gold);
        box-shadow: 0 4px 20px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
        margin: -1rem -1rem 2rem -1rem;
        position: relative;
        overflow: hidden;
    }
    
    .gov-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        animation: shimmer 3s infinite;
    }
    
    .gov-header::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(212,175,55,0.1) 0%, transparent 70%);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    .gov-header-content {
        display: flex;
        align-items: center;
        gap: 2rem;
        max-width: 1400px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }
    
    .emblem-container {
        flex-shrink: 0;
        transition: transform 0.3s ease;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
    }
    
    .emblem-container:hover {
        transform: scale(1.05) rotate(2deg);
    }
    
    .emblem-img {
        width: 75px;
        height: auto;
        display: block;
    }
    
    .header-text {
        flex-grow: 1;
    }
    
    .gov-title {
        color: var(--text-main);
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0;
        letter-spacing: 1px;
        text-transform: uppercase;
        opacity: 0.95;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header {
        color: var(--text-main) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin: 0.5rem 0 0.3rem 0 !important;
        letter-spacing: 0.5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        border: none !important;
        padding: 0 !important;
        position: relative;
        display: inline-block;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, var(--saffron) 0%, var(--gold) 50%, var(--green) 100%);
    }
    
    .sub-header {
        color: var(--saffron);
        font-size: 1.3rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        letter-spacing: 0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--glass-border);
        box-shadow: 2px 0 15px rgba(0,0,0,0.2);
    }
    
    section[data-testid="stSidebar"] h2 {
        color: var(--text-main) !important;
        border-left: 4px solid var(--saffron) !important;
        padding-left: 1rem !important;
        background: linear-gradient(90deg, rgba(255,153,51,0.1) 0%, transparent 100%);
        padding: 0.5rem 1rem;
        margin: 0 -1rem 1rem -1rem;
    }
    
    /* Metric cards: Clean and Professional */
    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        padding: 1rem 1.25rem !important;
        border-radius: 10px;
        border: 1px solid var(--glass-border);
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: var(--primary);
        background: rgba(78, 137, 232, 0.05);
    }
    
    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: normal !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-main) !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
        line-height: 1 !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }

    /* Delta colors */
    [data-testid="stMetricDelta"][data-direction="up"] { color: var(--success) !important; }
    [data-testid="stMetricDelta"][data-direction="down"] { color: var(--danger) !important; }
    
    /* Insight boxes: Subtle */
    .insight-box {
        background: rgba(255, 255, 255, 0.02);
        border-left: 4px solid var(--primary);
        padding: 1.25rem;
        margin: 1rem 0;
        border-radius: 6px;
        border-top: 1px solid var(--glass-border);
        border-right: 1px solid var(--glass-border);
        border-bottom: 1px solid var(--glass-border);
    }
    
    /* Tabs styling: Clean */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
        padding: 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid var(--glass-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0;
        color: var(--text-muted);
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-bottom: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }
    
    /* Headers: Professional */
    h1, h2, h3 {
        color: var(--text-main) !important;
        margin-top: 1.25rem !important;
        margin-bottom: 1rem !important;
        font-weight: 600 !important;
    }
    
    h1 {
        font-size: 1.8rem !important;
    }
    
    h2 {
        font-size: 1.4rem !important;
    }
    
    h3 {
        font-size: 1.2rem !important;
    }

    .tab-description {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-bottom: 1rem;
    }
    
    /* Buttons: Standard */
    .stButton > button {
        background: var(--primary);
        border-radius: 4px;
        font-weight: 500;
    }
    
    /* Plotly container */
    .element-container:has(.js-plotly-plot) {
        margin: 1rem 0;
    }

    /* Plotly background */
    .js-plotly-plot {
        background-color: var(--bg-secondary);
        border-radius: 8px;
        border: 1px solid var(--glass-border);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--bg-secondary); border-radius: 3px; }
    </style>
""", unsafe_allow_html=True)



# State name normalization mapping to fix duplicates and spelling errors
STATE_NAME_MAPPING = {
    # West Bengal variants
    'West Bangal': 'West Bengal',
    'Westbengal': 'West Bengal',
    'West  Bengal': 'West Bengal',  # double space
    'West Bengli': 'West Bengal',
    
    # Chhattisgarh variants
    'Chhatisgarh': 'Chhattisgarh',
    
    # Uttarakhand variants
    'Uttaranchal': 'Uttarakhand',
    
    # Tamil Nadu variants
    'Tamilnadu': 'Tamil Nadu',
    
    # Union Territory variants (standardize to "And" format)
    'Andaman & Nicobar Islands': 'Andaman And Nicobar Islands',
    'Daman & Diu': 'Daman And Diu',
    'Dadra & Nagar Haveli': 'Dadra And Nagar Haveli',
    'Jammu & Kashmir': 'Jammu And Kashmir',
    
    # Puducherry variants
    'Pondicherry': 'Puducherry',
    
    # Long name variants
    'The Dadra And Nagar Haveli And Daman And Diu': 'Dadra And Nagar Haveli And Daman And Diu',
}

# Invalid entries that are not states (cities, numbers, etc.)
INVALID_STATE_ENTRIES = {
    '100000',
    'Balanagar',
    'Jaipur',
    'Darbhanga',
    'Madanapalle',
    'Nagpur',
    'Puttenahalli',
    'Raja Annamalai Puram',
}

def normalize_state_name(state_name):
    """Normalize state name to canonical form"""
    if pd.isna(state_name):
        return state_name
    state_str = str(state_name).strip()
    # Check if it's an invalid entry
    if state_str in INVALID_STATE_ENTRIES:
        return None
    # Return mapped name or original if no mapping exists
    return STATE_NAME_MAPPING.get(state_str, state_str)

def normalize_state_column(df, column='state'):
    """Apply state normalization to a DataFrame column"""
    if column not in df.columns:
        return df
    df = df.copy()
    df[column] = df[column].apply(normalize_state_name)
    # Remove rows with invalid state entries (None values)
    df = df[df[column].notna()]
    return df

def get_unique_states(data):
    """Get sorted list of unique normalized state names from all data sources"""
    all_states = set()
    
    if 'state' in data and 'state' in data['state'].columns:
        all_states.update(data['state']['state'].dropna().unique())
    if 'biometric' in data and 'state' in data['biometric'].columns:
        all_states.update(data['biometric']['state'].dropna().unique())
    if 'demographic' in data and 'state' in data['demographic'].columns:
        all_states.update(data['demographic']['state'].dropna().unique())
    if 'enrolment' in data and 'state' in data['enrolment'].columns:
        all_states.update(data['enrolment']['state'].dropna().unique())
    
    # Remove any remaining invalid entries
    all_states = all_states - INVALID_STATE_ENTRIES
    
    return sorted(list(all_states))

def filter_data_by_state(data, selected_state):
    """Filter all datasets by selected state and recalculate aggregates"""
    if selected_state == 'All':
        return data
    
    filtered_data = {}
    
    for key, df in data.items():
        if isinstance(df, pd.DataFrame):
            if 'state' in df.columns:
                filtered_data[key] = df[df['state'] == selected_state].copy()
            else:
                # Keep data that doesn't have state column (will be recalculated below)
                filtered_data[key] = df.copy()
        else:
            # Keep non-DataFrame items (like dictionaries/JSON)
            filtered_data[key] = df
    
    # Recalculate daily aggregates from filtered raw data
    if 'biometric' in filtered_data and 'demographic' in filtered_data and 'enrolment' in filtered_data:
        try:
            # Aggregate biometric data by date
            bio_daily = filtered_data['biometric'].groupby('date').agg({
                'bio_age_5_17': 'sum',
                'bio_age_17_': 'sum'
            }).reset_index()
            bio_daily['bio_total'] = bio_daily['bio_age_5_17'] + bio_daily['bio_age_17_']
            
            # Aggregate demographic data by date
            demo_daily = filtered_data['demographic'].groupby('date').agg({
                'demo_age_5_17': 'sum',
                'demo_age_17_': 'sum'
            }).reset_index()
            demo_daily['demo_total'] = demo_daily['demo_age_5_17'] + demo_daily['demo_age_17_']
            
            # Aggregate enrolment data by date
            enrol_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
            available_enrol_cols = [c for c in enrol_cols if c in filtered_data['enrolment'].columns]
            if available_enrol_cols:
                enrol_daily = filtered_data['enrolment'].groupby('date').agg({
                    col: 'sum' for col in available_enrol_cols
                }).reset_index()
                enrol_daily['enrol_total'] = enrol_daily[available_enrol_cols].sum(axis=1)
            else:
                enrol_daily = filtered_data['enrolment'].groupby('date').size().reset_index(name='enrol_total')
            
            # Merge all into daily aggregates
            daily_agg = bio_daily.merge(demo_daily, on='date', how='outer')
            daily_agg = daily_agg.merge(enrol_daily, on='date', how='outer')
            daily_agg = daily_agg.fillna(0)
            
            # Add time-based columns
            daily_agg['date'] = pd.to_datetime(daily_agg['date'])
            daily_agg['weekday'] = daily_agg['date'].dt.day_name()
            daily_agg['week'] = daily_agg['date'].dt.isocalendar().week
            daily_agg['month'] = daily_agg['date'].dt.month
            daily_agg['day_num'] = (daily_agg['date'] - daily_agg['date'].min()).dt.days
            
            # Sort by date
            daily_agg = daily_agg.sort_values('date').reset_index(drop=True)
            
            filtered_data['daily'] = daily_agg
            
        except Exception as e:
            # If aggregation fails, keep existing daily data
            pass
    
    # Recalculate state-level summary for filtered state
    if 'state' in filtered_data and len(filtered_data['state']) > 0:
        # State data is already filtered, just keep it
        pass
    
    return filtered_data


@st.cache_data
def load_data():
    """Load all analysis results and raw data"""
    data_path = Path('analysis_results')
    processed_path = Path('processed_data')
    
    data = {}
    
    try:
        # Load analysis results
        data['daily'] = pd.read_csv(data_path / 'daily_aggregated_data.csv', parse_dates=['date'])
        data['state'] = pd.read_csv(data_path / 'state_level_analysis.csv')
        data['district_coverage'] = pd.read_csv(data_path / 'district_coverage_analysis.csv')
        data['insights'] = pd.read_csv(data_path / 'key_insights.csv')
        
        # Load anomaly detection results
        anomaly_path = Path('anomaly_results')
        try:
            if (anomaly_path / 'anomalies_detected.csv').exists():
                anomalies_df = pd.read_csv(anomaly_path / 'anomalies_detected.csv')
                if 'date' in anomalies_df.columns:
                    anomalies_df['date'] = pd.to_datetime(anomalies_df['date'], errors='coerce')
                data['anomalies'] = anomalies_df
            if (anomaly_path / 'anomalies_geographic.csv').exists():
                data['anomalies_geo'] = pd.read_csv(anomaly_path / 'anomalies_geographic.csv')
        except Exception as e:
            # Anomaly results not available yet
            pass
        
        # Load pattern learning results (Feature 1)
        pattern_path = Path('pattern_results')
        try:
            if (pattern_path / 'daily_patterns_summary.csv').exists():
                data['daily_patterns'] = pd.read_csv(pattern_path / 'daily_patterns_summary.csv')
            if (pattern_path / 'state_patterns_summary.csv').exists():
                data['state_patterns'] = pd.read_csv(pattern_path / 'state_patterns_summary.csv')
        except Exception as e:
            # Pattern learning results not available yet
            pass
        
        # Load forecasting results (Feature 2)
        forecast_path = Path('forecast_results')
        try:
            if (forecast_path / 'daily_forecasts.csv').exists():
                data['daily_forecasts'] = pd.read_csv(forecast_path / 'daily_forecasts.csv')
            if (forecast_path / 'daily_forecasts_summary.csv').exists():
                data['daily_forecasts_summary'] = pd.read_csv(forecast_path / 'daily_forecasts_summary.csv')
            if (forecast_path / 'state_forecasts.csv').exists():
                data['state_forecasts'] = pd.read_csv(forecast_path / 'state_forecasts.csv')
            if (forecast_path / 'state_forecasts_summary.csv').exists():
                data['state_forecasts_summary'] = pd.read_csv(forecast_path / 'state_forecasts_summary.csv')
        except Exception as e:
            # Forecasting results not available yet
            pass
        
        # Load surge prediction results (Feature 4)
        surge_path = Path('surge_results')
        try:
            if (surge_path / 'surge_predictions.csv').exists():
                surge_df = pd.read_csv(surge_path / 'surge_predictions.csv')
                if 'predicted_date' in surge_df.columns:
                    surge_df['predicted_date'] = pd.to_datetime(surge_df['predicted_date'], errors='coerce')
                data['surge_predictions'] = surge_df
            if (surge_path / 'upcoming_surges.csv').exists():
                upcoming_df = pd.read_csv(surge_path / 'upcoming_surges.csv')
                if 'predicted_date' in upcoming_df.columns:
                    upcoming_df['predicted_date'] = pd.to_datetime(upcoming_df['predicted_date'], errors='coerce')
                data['upcoming_surges'] = upcoming_df
        except Exception as e:
            # Surge prediction results not available yet
            pass
        
        # Load feature engineering results (Feature 5)
        feature_path = Path('feature_results')
        try:
            if (feature_path / 'features_daily.csv').exists():
                feature_daily_df = pd.read_csv(feature_path / 'features_daily.csv')
                if 'date' in feature_daily_df.columns:
                    feature_daily_df['date'] = pd.to_datetime(feature_daily_df['date'], errors='coerce')
                data['features_daily'] = feature_daily_df
            if (feature_path / 'features_state.csv').exists():
                data['features_state'] = pd.read_csv(feature_path / 'features_state.csv')
            if (feature_path / 'feature_engineering_summary.json').exists():
                with open(feature_path / 'feature_engineering_summary.json', 'r') as f:
                    data['features_summary'] = json.load(f)
        except Exception as e:
            # Feature engineering results not available yet
            pass
        
        # Load district & pincode model results (Feature 6)
        district_pincode_path = Path('district_pincode_results')
        try:
            if (district_pincode_path / 'district_forecasts.csv').exists():
                data['district_forecasts'] = pd.read_csv(district_pincode_path / 'district_forecasts.csv')
            if (district_pincode_path / 'pincode_anomalies.csv').exists():
                data['pincode_anomalies'] = pd.read_csv(district_pincode_path / 'pincode_anomalies.csv')
            if (district_pincode_path / 'state_aggregations.csv').exists():
                data['district_state_aggregations'] = pd.read_csv(district_pincode_path / 'state_aggregations.csv')
            if (district_pincode_path / 'volume_aggregations.csv').exists():
                data['district_volume_aggregations'] = pd.read_csv(district_pincode_path / 'volume_aggregations.csv')
            if (district_pincode_path / 'district_pincode_summary.json').exists():
                with open(district_pincode_path / 'district_pincode_summary.json', 'r') as f:
                    data['district_pincode_summary'] = json.load(f)
        except Exception as e:
            # District & pincode results not available yet
            pass
        
        # Load actionable insights (Feature 9)
        insights_path = Path('insights_results')
        try:
            if (insights_path / 'actionable_insights.csv').exists():
                data['actionable_insights'] = pd.read_csv(insights_path / 'actionable_insights.csv')
            if (insights_path / 'insights_summary.json').exists():
                with open(insights_path / 'insights_summary.json', 'r') as f:
                    data['insights_summary'] = json.load(f)
        except Exception as e:
            # Actionable insights not available yet
            pass
        
        # Load raw data for detailed analysis
        data['biometric'] = pd.read_csv(processed_path / 'biometric_cleaned.csv', parse_dates=['date'])
        data['demographic'] = pd.read_csv(processed_path / 'demographic_cleaned.csv', parse_dates=['date'])
        data['enrolment'] = pd.read_csv(processed_path / 'enrolment_cleaned.csv', parse_dates=['date'])
        
        # Ensure date columns are datetime
        for key in ['daily', 'biometric', 'demographic', 'enrolment']:
            if 'date' in data[key].columns:
                data[key]['date'] = pd.to_datetime(data[key]['date'])
        
        # Apply state name normalization to fix duplicates and spelling errors
        datasets_with_state = [
            'state', 'biometric', 'demographic', 'enrolment', 
            'anomalies_geo', 'state_patterns', 'state_forecasts', 
            'state_forecasts_summary', 'features_state', 'district_forecasts',
            'pincode_anomalies', 'district_state_aggregations', 'actionable_insights'
        ]
        for key in datasets_with_state:
            if key in data and isinstance(data[key], pd.DataFrame):
                data[key] = normalize_state_column(data[key], 'state')
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please run exploratory_data_analysis.py first to generate analysis results.")
        return None
    
    return data


def main():
    """Main dashboard application"""
    
    # Government Header with Emblem
    # Try multiple possible filenames
    possible_emblem_files = ["india_emblem.png", "india_emblem.jpg"]
    emblem_path = None
    
    for filename in possible_emblem_files:
        if Path(filename).exists():
            emblem_path = filename
            break
            
    # Fallback to absolute path if needed (though local should work)
    if not emblem_path:
        # Check if it was the full path from previous version but maybe filename changed
        pass
    
    try:
        if emblem_path:
            import base64
            with open(emblem_path, "rb") as img_file:
                emblem_b64 = base64.b64encode(img_file.read()).decode()
            
            # Determine mime type based on extension
            mime_type = "image/png" if emblem_path.lower().endswith(".png") else "image/jpeg"
            
            st.markdown(f"""
            <div class="gov-header">
                <div class="gov-header-content">
                    <div class="emblem-container">
                        <img src="data:{mime_type};base64,{emblem_b64}" class="emblem-img" alt="State Emblem of India">
                    </div>
                    <div class="header-text">
                        <p class="gov-title">भारत सरकार | Government of India</p>
                        <h1 class="main-header">UIDAI Analytics Dashboard</h1>
                        <p class="sub-header">AI-Driven Early Warning System for Aadhaar Update Surges and Anomalies</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            raise FileNotFoundError("Emblem image not found")
            
    except Exception as e:
        # Fallback header if emblem image not found
        st.markdown("""
        <div class="gov-header">
            <div class="gov-header-content">
                <div class="header-text">
                    <p class="gov-title">🇮🇳 भारत सरकार | Government of India</p>
                    <h1 class="main-header">UIDAI Analytics Dashboard</h1>
                    <p class="sub-header">AI-Driven Early Warning System for Aadhaar Update Surges and Anomalies</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    if data is None:
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # State filter (apply first so date range uses state-filtered data)
    if 'state' in data:
        # Use normalized unique states from all data sources
        unique_states = get_unique_states(data)
        all_states = ['All'] + unique_states
        # selected_state = st.sidebar.selectbox("Select State", all_states)
        selected_state = st.sidebar.selectbox(
            "Select State",
            all_states,
            format_func=lambda x: x.title() if x != 'All' else x
        )

        
        # Apply state filter to all data
        if selected_state != 'All':
            data = filter_data_by_state(data, selected_state)
            st.sidebar.success(f"📍 Showing data for: {selected_state}")
    else:
        selected_state = 'All'
    
    # Date range filter (applies to all datasets with date column)
    if 'daily' in data and len(data['daily']) > 0:
        min_date = data['daily']['date'].min().date()
        max_date = data['daily']['date'].max().date()
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            # Convert to pandas Timestamp for proper comparison with datetime64
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # End of day
            
            # Apply date filter to all datasets with date column
            for key in ['daily', 'biometric', 'demographic', 'enrolment', 'anomalies', 'features_daily']:
                if key in data and isinstance(data[key], pd.DataFrame) and 'date' in data[key].columns:
                    data[key] = data[key][
                        (data[key]['date'] >= start_ts) & 
                        (data[key]['date'] <= end_ts)
                    ]




    # Dashboard tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
        "📈 Overview", 
        "📅 Temporal Analysis", 
        "🔮 Forecasting & Predictions",
        "🗺️ Geographic Analysis",
        "👥 Age Group Analysis",
        "⚠️ Coverage & Anomalies",
        "💡 Insights & Recommendations",
        "🚨 Surge Predictions",
        "⚙️ Feature Engineering",
        "🏘️ District & Pincode Models",
        "🎯 Actionable Insights",
        "🕵️ Forensic Signal Intelligence"
    ])
    
    # Tab 1: Overview
    with tab1:
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        st.markdown("""
        <div class="tab-description">
            High-level summary of biometric and demographic updates and enrolments across India.
        </div>
        """, unsafe_allow_html=True)
        if 'daily' in data:
            render_export_button(data['daily'], "Overview_Data", "tab1_export")
        st.header("Dashboard Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        if 'daily' in data and len(data['daily']) > 0:
            with col1:
                total_bio = data['daily']['bio_total'].sum()
                st.metric("Biometric Updates", f"{total_bio:,.0f}")
            
            with col2:
                total_demo = data['daily']['demo_total'].sum()
                st.metric("Demographic Updates", f"{total_demo:,.0f}")
            
            with col3:
                total_enrol = data['daily']['enrol_total'].sum()
                st.metric("Total Enrolments", f"{total_enrol:,.0f}")
            
            with col4:
                avg_daily = data['daily']['bio_total'].mean()
                st.metric("Avg Daily Updates", f"{avg_daily:,.0f}")
        
        st.markdown("---")

        # ---------------------------------------------------------
        # NEW: Impact & Utility Section (User Request)
        # ---------------------------------------------------------
        with st.expander("🚀 Project Impact & Strategic Utility", expanded=True):
            imp_col1, imp_col2 = st.columns(2)
            
            with imp_col1:
                st.markdown("""
                ### 🌟 Social & Administrative Benefit
                *   **Targeted Service Delivery:** Identify high-demand areas for **Biometric Updates** to deploy mobile Aadhaar camps, reducing citizen wait times.
                *   **Resource Optimization:** Use **Demographic Update** trends to allocate staff efficiently during peak operational periods.
                *   **Policy Planning:** **Age Group Analysis** assists in linking Aadhaar with school admissions (5-17 yrs) or voter ID updates (18+ yrs).
                """)
                
            with imp_col2:
                st.markdown("""
                ### 🛠️ Practicality & Feasibility
                *   **Proactive Management:** **Forecasting** modules allow administrators to prepare for demand surges 7-30 days in advance.
                *   **Anomaly Detection:** Automatically flags irregular drops in enrolment, enabling quick technical interventions in specific districts.
                *   **Actionable Granularity:** Drill-down capabilities from **State to District** level make insights directly usable for local administration.
                """)
        
        st.markdown("---")
        
        # Quick summary charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dataset Comparison")
            if 'daily' in data:
                comparison_data = {
                    'Biometric': data['daily']['bio_total'].sum(),
                    'Demographic': data['daily']['demo_total'].sum(),
                    'Enrolment': data['daily']['enrol_total'].sum()
                }
                fig = px.pie(
                    values=list(comparison_data.values()),
                    names=list(comparison_data.keys()),
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if selected_state == 'All':
                st.subheader("Top 5 States by Biometric Updates")
                if 'state' in data:
                    top_states = data['state'].nlargest(5, 'bio_total')[['state', 'bio_total']]
                    fig = px.bar(
                        top_states,
                        x='bio_total',
                        y='state',
                        orientation='h',
                        labels={'bio_total': 'Biometric Updates', 'state': 'State'},
                        color='bio_total',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.subheader(f"Top Districts in {selected_state}")
                if 'biometric' in data and len(data['biometric']) > 0:
                    # Aggregate by district for the selected state
                    district_data = data['biometric'].groupby('district').agg({
                        'bio_age_5_17': 'sum',
                        'bio_age_17_': 'sum'
                    }).reset_index()
                    district_data['bio_total'] = district_data['bio_age_5_17'] + district_data['bio_age_17_']
                    top_districts = district_data.nlargest(10, 'bio_total')[['district', 'bio_total']]
                    
                    fig = px.bar(
                        top_districts,
                        x='bio_total',
                        y='district',
                        orientation='h',
                        title=f"Top 10 Districts in {selected_state}",
                        labels={'bio_total': 'Biometric Updates', 'district': 'District'},
                        color='bio_total',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No district data available for {selected_state}")
        
        # Recent trends
        st.subheader("Recent Trends (Last 30 Days)")
        if 'daily' in data and len(data['daily']) > 0:
            recent_data = data['daily'].tail(30).copy()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=recent_data['date'],
                y=recent_data['bio_total'],
                mode='lines+markers',
                name='Biometric',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=recent_data['date'],
                y=recent_data['demo_total'],
                mode='lines+markers',
                name='Demographic',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=recent_data['date'],
                y=recent_data['enrol_total'],
                mode='lines+markers',
                name='Enrolment',
                line=dict(color='#2ca02c', width=2)
            ))
            fig.update_layout(
                title="Daily Updates Trend",
                xaxis_title="Date",
                yaxis_title="Count",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Temporal Analysis
    with tab2:
        st.markdown('<div class="tab-description">Analysis of daily, weekly, and monthly trends in update volumes.</div>', unsafe_allow_html=True)
        
        if 'daily' in data:
            render_export_button(data['daily'], "Temporal_Trends", "tab2_export")

        st.header("Temporal Pattern Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'daily' in data and len(data['daily']) > 0:
            # Overview Section: Daily, Weekly, Monthly Averages
            st.subheader("Volume Overview (Averages)")
            
            # Create a temporary dataframe with date index for resampling
            df_temp = data['daily'].set_index('date').copy()
            
            # Calculate averages for each metric
            metrics = {
                'Biometric': 'bio_total',
                'Demographic': 'demo_total',
                'Enrolment': 'enrol_total'
            }
            
            # Display in columns by Timeframe
            col_d, col_w, col_m = st.columns(3)
            
            with col_d:
                st.markdown("#### 📅 Daily Average")
                for label, col in metrics.items():
                    val = df_temp[col].mean()
                    st.metric(f"{label}", f"{val:,.0f}")
            
            with col_w:
                st.markdown("#### 🗓️ Weekly Average")
                for label, col in metrics.items():
                    val = df_temp[col].resample('W').sum().mean()
                    st.metric(f"{label}", f"{val:,.0f}")
                    
            with col_m:
                st.markdown("#### 📆 Monthly Average")
                for label, col in metrics.items():
                    val = df_temp[col].resample('ME').sum().mean()
                    st.metric(f"{label}", f"{val:,.0f}")
            
            st.markdown("---")

            # Time series chart
            st.subheader("Time Series Trends")
            
            chart_type = st.radio("Select Chart Type", ["Line Chart", "Pattern Heatmap"], horizontal=True)
            
            if chart_type == "Line Chart":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['bio_total'],
                    mode='lines',
                    name='Biometric Updates',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['demo_total'],
                    mode='lines',
                    name='Demographic Updates',
                    line=dict(color='#ff7f0e', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['enrol_total'],
                    mode='lines',
                    name='Enrolments',
                    line=dict(color='#2ca02c', width=2)
                ))
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=500,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Heatmap Pattern: Month vs Day of Month (Calendar View)
                heatmap_metric = st.selectbox(
                    "Select Metric for Heatmap",
                    ["Biometric Updates", "Demographic Updates", "Enrolments"],
                    key="temp_heatmap_metric"
                )
                
                metric_map = {
                    "Biometric Updates": "bio_total",
                    "Demographic Updates": "demo_total",
                    "Enrolments": "enrol_total"
                }
                
                target_col = metric_map[heatmap_metric]
                
                # Pivot data for heatmap: Month vs Day of Month
                df_heatmap = data['daily'].copy()
                df_heatmap['month'] = df_heatmap['date'].dt.month
                df_heatmap['day_of_month'] = df_heatmap['date'].dt.day
                
                # Aggregate to handle multiple years if present (taking average)
                pivot_df = df_heatmap.groupby(['month', 'day_of_month'])[target_col].mean().unstack()
                
                # Ensure all 12 months and 31 days exist
                pivot_df = pivot_df.reindex(index=range(1, 13), columns=range(1, 32))
                
                # Map Month Numbers to Names for Y-axis
                month_names = {
                    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
                }
                pivot_df.index = pivot_df.index.map(month_names)
                
                fig = px.imshow(
                    pivot_df,
                    labels=dict(x="Day of Month", y="Month", color="Avg Volume"),
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    color_continuous_scale='Viridis', # High volume = Lighter/Brighter
                    aspect="auto"
                )
                
                fig.update_layout(
                    title=f"Calendar Seasonality: {heatmap_metric}",
                    height=600,
                    margin=dict(l=20, r=20, t=50, b=20),
                    xaxis_title="Day of Month (1-31)",
                    yaxis_title="Month",
                    coloraxis_colorbar=dict(title="Avg Volume")
                )
                
                # Show every day on X axis
                fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
                
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"ℹ️ **How to read:** This 'Calendar Heatmap' shows the average daily volume for each day of every month. Darker colors indicate lower activity, while brighter/yellow colors indicate high activity. Look for horizontal bands (busy months) or vertical stripes (busy days, e.g., end-of-month surges).")
            
            # Weekly patterns
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Weekly Pattern (Day of Week)")
                if 'weekday' in data['daily'].columns:
                    weekday_avg = data['daily'].groupby('weekday')[
                        ['bio_total', 'demo_total', 'enrol_total']
                    ].mean().reset_index()
                    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    weekday_avg['weekday'] = pd.Categorical(weekday_avg['weekday'], categories=weekday_order, ordered=True)
                    weekday_avg = weekday_avg.sort_values('weekday')
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=weekday_avg['weekday'],
                        y=weekday_avg['bio_total'],
                        name='Biometric',
                        marker_color='#1f77b4'
                    ))
                    fig.add_trace(go.Bar(
                        x=weekday_avg['weekday'],
                        y=weekday_avg['demo_total'],
                        name='Demographic',
                        marker_color='#ff7f0e'
                    ))
                    fig.add_trace(go.Bar(
                        x=weekday_avg['weekday'],
                        y=weekday_avg['enrol_total'],
                        name='Enrolment',
                        marker_color='#2ca02c'
                    ))
                    fig.update_layout(
                        title="Average by Day of Week",
                        xaxis_title="Day",
                        yaxis_title="Average Count",
                        barmode='group',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Monthly Trend")
                if 'month' in data['daily'].columns:
                    monthly_avg = data['daily'].groupby('month')[
                        ['bio_total', 'demo_total', 'enrol_total']
                    ].mean().reset_index()
                    month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                    monthly_avg['month_name'] = monthly_avg['month'].map(month_names)
                    
                    fig = px.line(
                        monthly_avg,
                        x='month_name',
                        y=['bio_total', 'demo_total', 'enrol_total'],
                        title="Average by Month",
                        labels={'value': 'Average Count', 'month_name': 'Month', 'variable': 'Type'},
                        markers=True
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Pattern Learning Visualizations (Feature 1)
            if 'daily_patterns' in data or 'state_patterns' in data:
                st.markdown("---")
                st.subheader("📊 Pattern Insights")
                
                with st.expander("ℹ️ About Pattern Learning"):
                    st.markdown("""
                    This system uses automated decomposition to separate regular trends from seasonal cycles. 
                    It helps identify whether a particular metric is consistently increasing or just showing normal periodic fluctuation.
                    """)
                
                # Daily Patterns Section
                if 'daily_patterns' in data:
                    st.markdown("#### Daily Aggregated Patterns")
                    
                    daily_patterns_df = data['daily_patterns']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("##### Trend Directions")
                        # Create trend direction chart
                        trend_counts = daily_patterns_df['trend_direction'].value_counts().reset_index()
                        trend_counts.columns = ['Direction', 'Count']
                        
                        # Color mapping
                        color_map = {
                            'increasing': '#2ca02c',
                            'decreasing': '#d62728',
                            'stable': '#ff7f0e',
                            'insufficient_data': '#7f7f7f'
                        }
                        trend_counts['color'] = trend_counts['Direction'].map(color_map)
                        
                        fig = px.bar(
                            trend_counts,
                            x='Direction',
                            y='Count',
                            title="Trend Direction Distribution",
                            color='Direction',
                            color_discrete_map=color_map,
                            labels={'Count': 'Number of Metrics'}
                        )
                        fig.update_layout(showlegend=False, height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("##### Trend Slopes")
                        fig = px.bar(
                            daily_patterns_df,
                            x='metric',
                            y='trend_slope',
                            title="Trend Slopes by Metric",
                            labels={'metric': 'Metric', 'trend_slope': 'Trend Slope'},
                            color='trend_slope',
                            color_continuous_scale='RdYlGn'
                        )
                        fig.update_layout(height=300, xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col3:
                        st.markdown("##### Pattern Statistics")
                        # Display key statistics
                        for idx, row in daily_patterns_df.iterrows():
                            metric_name = row['metric'].replace('_', ' ').title()
                            st.metric(
                                label=f"{metric_name}",
                                value=row['trend_direction'].title(),
                                delta=f"Slope: {row['trend_slope']:.2f}"
                            )
                    
                    # Detailed pattern table
                    with st.expander("📋 View Detailed Pattern Data"):
                        display_cols = ['metric', 'trend_direction', 'trend_slope', 'trend_mean', 'seasonal_amplitude', 'resid_std']
                        display_df = daily_patterns_df[display_cols].copy()
                        display_df.columns = ['Metric', 'Trend Direction', 'Trend Slope', 'Trend Mean', 'Seasonal Amplitude', 'Residual Std']
                        display_df['Trend Slope'] = display_df['Trend Slope'].apply(lambda x: f"{x:,.2f}")
                        display_df['Trend Mean'] = display_df['Trend Mean'].apply(lambda x: f"{x:,.2f}")
                        display_df['Seasonal Amplitude'] = display_df['Seasonal Amplitude'].apply(lambda x: f"{x:,.2f}")
                        display_df['Residual Std'] = display_df['Residual Std'].apply(lambda x: f"{x:,.2f}")
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # State-Level Patterns Section
                if 'state_patterns' in data:
                    st.markdown("#### State-Level Patterns")
                    
                    state_patterns_df = data['state_patterns']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Top States by Trend Slope")
                        top_n_states = st.slider("Number of States", 5, 30, 15, key="top_pattern_states")
                        top_states = state_patterns_df.nlargest(top_n_states, 'trend_slope')
                        
                        fig = px.bar(
                            top_states,
                            x='trend_slope',
                            y='state',
                            orientation='h',
                            title=f"Top {top_n_states} States by Trend Slope",
                            labels={'trend_slope': 'Trend Slope', 'state': 'State'},
                            color='trend_slope',
                            color_continuous_scale='Greens'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("##### Trend Direction Distribution (States)")
                        state_trend_counts = state_patterns_df['trend_direction'].value_counts().reset_index()
                        state_trend_counts.columns = ['Direction', 'Count']
                        
                        color_map = {
                            'increasing': '#2ca02c',
                            'decreasing': '#d62728',
                            'stable': '#ff7f0e',
                            'insufficient_data': '#7f7f7f'
                        }
                        state_trend_counts['color'] = state_trend_counts['Direction'].map(color_map)
                        
                        fig = px.pie(
                            state_trend_counts,
                            values='Count',
                            names='Direction',
                            title="State Trend Directions",
                            color='Direction',
                            color_discrete_map=color_map
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # State pattern statistics
                        st.markdown("##### State Pattern Statistics")
                        col_stat1, col_stat2 = st.columns(2)
                        with col_stat1:
                            avg_slope = state_patterns_df['trend_slope'].mean()
                            st.metric("Avg Trend Slope", f"{avg_slope:.2f}")
                        with col_stat2:
                            increasing_count = (state_patterns_df['trend_direction'] == 'increasing').sum()
                            st.metric("Increasing Trends", f"{increasing_count}/{len(state_patterns_df)}")
                    
                    # State patterns table
                    with st.expander("📋 View All State Patterns"):
                        display_cols = ['state', 'trend_direction', 'trend_slope', 'trend_mean', 'seasonal_amplitude', 'resid_std']
                        display_df = state_patterns_df[display_cols].copy().sort_values('trend_slope', ascending=False)
                        display_df.columns = ['State', 'Trend Direction', 'Trend Slope', 'Trend Mean', 'Seasonal Amplitude', 'Residual Std']
                        display_df['Trend Slope'] = display_df['Trend Slope'].apply(lambda x: f"{x:,.2f}")
                        display_df['Trend Mean'] = display_df['Trend Mean'].apply(lambda x: f"{x:,.2f}")
                        display_df['Seasonal Amplitude'] = display_df['Seasonal Amplitude'].apply(lambda x: f"{x:,.2f}")
                        display_df['Residual Std'] = display_df['Residual Std'].apply(lambda x: f"{x:,.2f}")
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    
    # Tab 3: Forecasting & Predictions
    with tab3:
        st.markdown('<div class="tab-description">30 to 90-day projections for Aadhaar update workloads.</div>', unsafe_allow_html=True)
        
        # Export forecast data if available, otherwise daily data
        if 'daily_forecasts' in data:
            render_export_button(data['daily_forecasts'], "Forecasts", "tab3_export")
        elif 'daily' in data:
            render_export_button(data['daily'], "Forecast_Input_Data", "tab3_export")

        st.header("Forecasting & Predictions")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        # Forecasting Visualizations (Feature 2)
        if 'daily_forecasts' in data or 'state_forecasts' in data:
            # Daily Forecasts Section
            if 'daily_forecasts' in data and 'daily_forecasts_summary' in data:
                st.markdown("#### Daily Aggregated Forecasts")
                
                daily_forecasts_df = data['daily_forecasts']
                daily_summary_df = data['daily_forecasts_summary']
                
                # Forecast type selector
                forecast_type = st.radio(
                    "Select Forecast Type",
                    ["short_term", "medium_term"],
                    format_func=lambda x: "Short-term (1-3 months)" if x == "short_term" else "Medium-term (3-6 months)",
                    horizontal=True,
                    key="daily_forecast_type"
                )
                    
                filtered_forecasts = daily_forecasts_df[daily_forecasts_df['forecast_type'] == forecast_type]
                    
                # Metric selector
                metrics = filtered_forecasts['metric'].unique()
                selected_metric = st.selectbox("Select Metric", metrics, key="daily_forecast_metric")
                    
                metric_forecasts = filtered_forecasts[filtered_forecasts['metric'] == selected_metric]
                metric_summary = daily_summary_df[
                    (daily_summary_df['metric'] == selected_metric) & 
                    (daily_summary_df['forecast_type'] == forecast_type)
                ].iloc[0] if len(daily_summary_df[
                    (daily_summary_df['metric'] == selected_metric) & 
                    (daily_summary_df['forecast_type'] == forecast_type)
                ]) > 0 else None
                    
                col1, col2 = st.columns(2)
                    
                with col1:
                    # Forecast chart with confidence intervals
                    st.markdown("##### Forecast with Confidence Intervals")
                    fig = go.Figure()
                        
                    # Forecast line
                    fig.add_trace(go.Scatter(
                        x=metric_forecasts['period'],
                        y=metric_forecasts['forecast_value'],
                        mode='lines+markers',
                        name='Forecast',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=4)
                    ))
                        
                    # Confidence intervals
                    fig.add_trace(go.Scatter(
                        x=metric_forecasts['period'],
                        y=metric_forecasts['conf_upper'],
                        mode='lines',
                        name='Upper Bound (95%)',
                        line=dict(width=0),
                        showlegend=False
                    ))
                    fig.add_trace(go.Scatter(
                        x=metric_forecasts['period'],
                        y=metric_forecasts['conf_lower'],
                        mode='lines',
                        name='Lower Bound (95%)',
                        line=dict(width=0),
                        fillcolor='rgba(31, 119, 180, 0.2)',
                        fill='tonexty',
                        showlegend=True
                    ))
                        
                    fig.update_layout(
                        title=f"{selected_metric.replace('_', ' ').title()} Forecast ({forecast_type.replace('_', ' ').title()})",
                        xaxis_title="Period (Days Ahead)",
                        yaxis_title="Forecasted Value",
                        hovermode='x unified',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col2:
                    st.markdown("##### Forecast Insights")
                    if metric_summary is not None:
                        # User-friendly metrics
                        mape = metric_summary['mape']
                        if mape < 5:
                            reliability = "High"
                            reliability_color = "#48BB78" # Green
                            reliability_msg = "Excellent forecast accuracy."
                        elif mape < 15:
                            reliability = "Medium"
                            reliability_color = "#FF9933" # Orange
                            reliability_msg = "Moderate forecast accuracy."
                        else:
                            reliability = "Low"
                            reliability_color = "#F56565" # Red
                            reliability_msg = "Low forecast accuracy; use with caution."
                        
                        # Determine trend
                        try:
                            start_val = metric_forecasts['forecast_value'].iloc[0]
                            end_val = metric_forecasts['forecast_value'].iloc[-1]
                            pct_change = ((end_val - start_val) / start_val) * 100
                            
                            if pct_change > 2:
                                trend = "Increasing 📈"
                            elif pct_change < -2:
                                trend = "Decreasing 📉"
                            else:
                                trend = "Stable ➡️"
                        except:
                            trend = "Stable ➡️"

                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 5px; border-left: 5px solid {reliability_color}; margin-bottom: 15px;">
                            <h3 style="margin:0; font-size: 1.1rem; color: #FAFAFA;">Forecast Reliability: <span style="color:{reliability_color}">{reliability}</span></h3>
                            <p style="margin:5px 0 0 0; color: #A0AEC0; font-size: 0.9rem;">{reliability_msg}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Total Projected Volume
                        total_projected = metric_forecasts['forecast_value'].sum()
                        st.metric("Total Projected Volume", f"{total_projected:,.0f}", help=f"Total projected {selected_metric.replace('_', ' ')} for the next {int(metric_summary['forecast_periods'])} days")
                        
                        col_trend1, col_trend2 = st.columns(2)
                        with col_trend1:
                            st.metric("Expected Trend", trend)
                        with col_trend2:
                            st.metric("Forecast Horizon", f"{int(metric_summary['forecast_periods'])} days")
                        
                    st.markdown("##### Model Information")
                    if metric_summary is not None:
                        st.info(f"""
                        This forecast is generated using advanced time-series analysis optimized for {selected_metric.replace('_', ' ')}.
                        The model automatically adjusts for seasonal patterns and historical trends.
                        """)
                    
                # Forecast comparison table
                with st.expander("📋 View Detailed Forecast Data"):
                    display_cols = ['metric', 'forecast_type', 'period', 'forecast_value', 'conf_lower', 'conf_upper']
                    display_df = metric_forecasts[display_cols].copy()
                    display_df.columns = ['Metric', 'Forecast Type', 'Period', 'Forecast Value', 'Confidence Lower', 'Confidence Upper']
                    display_df['Forecast Value'] = display_df['Forecast Value'].apply(lambda x: f"{x:,.2f}")
                    display_df['Confidence Lower'] = display_df['Confidence Lower'].apply(lambda x: f"{x:,.2f}")
                    display_df['Confidence Upper'] = display_df['Confidence Upper'].apply(lambda x: f"{x:,.2f}")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            # State-Level Forecasts Section
            if 'state_forecasts' in data and 'state_forecasts_summary' in data:
                st.markdown("#### State-Level Forecasts")
                    
                state_forecasts_df = data['state_forecasts']
                state_summary_df = data['state_forecasts_summary']

                # --- Normalize state names (FIXES mismatch & iloc error) ---
                for df in [state_forecasts_df, state_summary_df]:
                    if 'state' in df.columns:
                        df['state'] = (
                            df['state']
                            .astype(str)
                            .str.strip()
                            .str.lower()
                        )


                col1, col2 = st.columns(2)
                    
                with col1:
                    st.markdown("##### Top States Forecast Performance")
                    top_n_states = st.slider("Number of States", 5, 15, 10, key="top_forecast_states")
                    top_states_forecast = state_summary_df.nlargest(top_n_states, 'forecast_periods')
                        
                    fig = px.bar(
                        top_states_forecast,
                        x='mae',
                        y='state',
                        orientation='h',
                        title=f"Forecast MAE by State (Top {top_n_states})",
                        labels={'mae': 'Mean Absolute Error', 'state': 'State'},
                        color='mae',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col2:
                    st.markdown("##### State Forecast Summary")
                    # State selector
                    # states = state_summary_df['state'].unique()
                    states = sorted(state_summary_df['state'].dropna().unique())

                    selected_state_forecast = st.selectbox("Select State", states, key="state_forecast_select")
                        
                    #state_forecast_data = state_summary_df[state_summary_df['state'] == selected_state_forecast].iloc[0]
                    filtered_df = state_summary_df[
                        state_summary_df['state'] == selected_state_forecast
                    ]

                    if not filtered_df.empty:
                        state_forecast_data = filtered_df.iloc[0]

                        # User-friendly metrics
                        mape = state_forecast_data['mape']
                        if mape < 5:
                            reliability = "High"
                            reliability_color = "#48BB78"
                        elif mape < 15:
                            reliability = "Medium"
                            reliability_color = "#FF9933"
                        else:
                            reliability = "Low"
                            reliability_color = "#F56565"
                        
                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 5px; border-left: 5px solid {reliability_color}; margin-bottom: 15px;">
                            <h3 style="margin:0; font-size: 1.1rem; color: #FAFAFA;">Forecast Reliability: <span style="color:{reliability_color}">{reliability}</span></h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Total Projected Volume for State
                        state_fc_subset = state_forecasts_df[state_forecasts_df['state'] == selected_state_forecast]
                        if not state_fc_subset.empty:
                            total_projected = state_fc_subset['forecast_value'].sum()
                            st.metric("Total Projected Volume", f"{total_projected:,.0f}")

                        st.metric("Forecast Horizon", f"{int(state_forecast_data['forecast_periods'])} days")
                    else:
                        st.warning("No forecast summary available for this state.")
                        st.stop()
    
                    # Forecast chart for selected state
                    state_fc = state_forecasts_df[state_forecasts_df['state'] == selected_state_forecast]
                    if len(state_fc) > 0:
                        fig_state = go.Figure()
                        fig_state.add_trace(go.Scatter(
                            x=state_fc['period'],
                            y=state_fc['forecast_value'],
                            mode='lines+markers',
                            name='Forecast',
                            line=dict(color='#2ca02c', width=2)
                        ))
                        fig_state.add_trace(go.Scatter(
                            x=state_fc['period'],
                            y=state_fc['conf_upper'],
                            mode='lines',
                            name='Upper',
                            line=dict(width=0),
                            showlegend=False
                        ))
                        fig_state.add_trace(go.Scatter(
                            x=state_fc['period'],
                            y=state_fc['conf_lower'],
                            mode='lines',
                            name='Lower',
                            line=dict(width=0),
                            fillcolor='rgba(44, 160, 44, 0.2)',
                            fill='tonexty',
                            showlegend=False
                        ))
                        fig_state.update_layout(
                            xaxis_title="Period (Days Ahead)",
                            yaxis_title="Forecasted Value",
                            height=300
                        )
                        st.plotly_chart(fig_state, use_container_width=True)
                    
                # State forecasts table
                with st.expander("📋 View All State Forecasts Summary"):
                    display_cols = ['state', 'forecast_type', 'forecast_periods', 'mape']
                    display_df = state_summary_df[display_cols].copy().sort_values('mape', ascending=True)
                    display_df.columns = ['State', 'Forecast Type', 'Forecast Horizon', 'Error Rate (MAPE)']
                    display_df['Error Rate (MAPE)'] = display_df['Error Rate (MAPE)'].apply(lambda x: f"{x:.2f}%")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    
    # Tab 4: Geographic Analysis
    with tab4:
        st.markdown('<div class="tab-description">Spatial distribution of Aadhaar activity and state-wise comparisons.</div>', unsafe_allow_html=True)
        
        if 'state' in data:
            render_export_button(data['state'], "Geographic_Data", "tab4_export")
        st.header("Geographic Distribution Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'state' in data:
            # Indian Map Visualization with State-wise Heatmap
            st.subheader("🗺️ Indian Map: State-wise Heatmap Visualization")
            
            map_metric_choice = st.selectbox(
                "Select Metric for Map",
                ["Biometric Updates", "Demographic Updates", "Enrolments"],
                key="map_metric"
            )
            
            map_metric_col = {
                "Biometric Updates": "bio_total",
                "Demographic Updates": "demo_total",
                "Enrolments": "enrol_total"
            }[map_metric_choice]
            
            # Prepare data for map
            state_map_data = data['state'][['state', map_metric_col]].copy()
            
            # Try to create proper choropleth map with GeoJSON
            if GEOJSON_HELPER_AVAILABLE:
                india_geojson = load_india_geojson()
                
                if india_geojson:
                    state_name_field = get_state_name_field(india_geojson)
                    
                    if state_name_field:
                        try:
                            # ---------------------------------------------------------
                            # FIX: Align data state names with GeoJSON state names
                            # ---------------------------------------------------------
                            # Get all state names from GeoJSON
                            geojson_states = set()
                            for feature in india_geojson['features']:
                                if 'properties' in feature and state_name_field in feature['properties']:
                                    geojson_states.add(feature['properties'][state_name_field])
                            
                            # Define specific mapping corrections (Data Name -> GeoJSON Name)
                            name_replacements = {}
                            
                            # 1. Jammu & Kashmir
                            if "Jammu and Kashmir" in geojson_states:
                                # Data might have "Jammu And Kashmir" or "Jammu & Kashmir"
                                if "Jammu And Kashmir" in state_map_data['state'].values:
                                    name_replacements["Jammu And Kashmir"] = "Jammu and Kashmir"
                                elif "Jammu & Kashmir" in state_map_data['state'].values:
                                    name_replacements["Jammu & Kashmir"] = "Jammu and Kashmir"
                            
                            # 2. Andaman & Nicobar
                            if "Andaman and Nicobar" in geojson_states:
                                if "Andaman And Nicobar Islands" in state_map_data['state'].values:
                                    name_replacements["Andaman And Nicobar Islands"] = "Andaman and Nicobar"
                            
                            # 3. Dadra & Nagar Haveli and Daman & Diu
                            # GeoJSON might have them separate or combined. The debug output showed them separate.
                            # "Dadra and Nagar Haveli", "Daman and Diu"
                            # Data likely has "Dadra And Nagar Haveli And Daman And Diu"
                            # This is tricky because one data row maps to two GeoJSON features.
                            # For now, we can try to map to one of them or leave it (it might just show on one part).
                            # If we want to show on both, we'd need to duplicate the row in data. 
                            # Let's check if we can map to the larger one or just skip for now to avoid errors.
                            
                            # 4. Odisha / Orissa
                            if "Orissa" in geojson_states and "Odisha" in state_map_data['state'].values:
                                name_replacements["Odisha"] = "Orissa"
                                
                            # 5. Uttarakhand / Uttaranchal
                            if "Uttaranchal" in geojson_states and "Uttarakhand" in state_map_data['state'].values:
                                name_replacements["Uttarakhand"] = "Uttaranchal"

                            # Apply replacements
                            if name_replacements:
                                state_map_data['state'] = state_map_data['state'].replace(name_replacements)
                            # ---------------------------------------------------------

                            # Create choropleth map with proper boundaries
                            fig_map = px.choropleth(
                                state_map_data,
                                geojson=india_geojson,
                                locations='state',
                                featureidkey=f'properties.{state_name_field}',
                                color=map_metric_col,
                                color_continuous_scale='YlOrRd',
                                title=f'🗺️ Indian States Choropleth Map: {map_metric_choice}',
                                hover_data=['state'],
                                labels={map_metric_col: map_metric_choice}
                            )
                            
                            # Update layout for India
                            fig_map.update_geos(
                                fitbounds="locations",
                                visible=False,
                                projection_type="mercator",
                                center=dict(lon=78.9629, lat=20.5937),
                                projection_scale=4.5
                            )
                            
                            fig_map.update_layout(
                                height=750,
                                margin=dict(l=0, r=0, t=50, b=0),
                                coloraxis_colorbar=dict(
                                    title=dict(text=map_metric_choice, font=dict(size=14)),
                                    len=0.7,
                                    thickness=20
                                )
                            )
                            
                            st.plotly_chart(fig_map, use_container_width=True)
                            st.success("✅ Using proper choropleth map with state boundaries!")
                            
                        except Exception as e:
                            st.warning(f"Could not create choropleth map: {str(e)}. Using fallback visualization.")
                            create_marker_fallback_map(state_map_data, map_metric_col, map_metric_choice)
                    else:
                        st.warning("Could not detect state name field in GeoJSON. Using fallback visualization.")
                        create_marker_fallback_map(state_map_data, map_metric_col, map_metric_choice)
                else:
                    st.info("ℹ️ GeoJSON file not found. Using marker-based visualization. To get proper boundaries, download 'india_states.geojson' file.")
                    create_marker_fallback_map(state_map_data, map_metric_col, map_metric_choice)
            else:
                create_marker_fallback_map(state_map_data, map_metric_col, map_metric_choice)
    
    # Tab 5: Age Group Analysis
    with tab5:
        st.markdown('<div class="tab-description">Analysis of updates across different demographic age groups.</div>', unsafe_allow_html=True)
        
        if 'daily' in data:
            render_export_button(data['daily'], "Age_Group_Data", "tab5_export")
        st.header("Age Group Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'daily' in data and len(data['daily']) > 0:
            # Age group distributions
            st.subheader("Age Group Distributions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### Biometric Updates by Age Group")
                if 'bio_age_5_17' in data['daily'].columns and 'bio_age_17_' in data['daily'].columns:
                    bio_age_totals = {
                        '5-17 years': data['daily']['bio_age_5_17'].sum(),
                        '17+ years': data['daily']['bio_age_17_'].sum()
                    }
                    bio_total = sum(bio_age_totals.values())
                    if bio_total > 0:
                        fig = px.pie(
                            values=list(bio_age_totals.values()),
                            names=list(bio_age_totals.keys()),
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show totals
                        st.markdown("**Total Biometric Updates:**")
                        for age, count in bio_age_totals.items():
                            pct = (count / bio_total * 100) if bio_total > 0 else 0
                            st.markdown(f"- {age}: {count:,.0f} ({pct:.1f}%)")
            
            with col2:
                st.markdown("##### Demographic Updates by Age Group")
                if 'demo_age_5_17' in data['daily'].columns and 'demo_age_17_' in data['daily'].columns:
                    demo_age_totals = {
                        '5-17 years': data['daily']['demo_age_5_17'].sum(),
                        '17+ years': data['daily']['demo_age_17_'].sum()
                    }
                    demo_total = sum(demo_age_totals.values())
                    if demo_total > 0:
                        fig = px.pie(
                            values=list(demo_age_totals.values()),
                            names=list(demo_age_totals.keys()),
                            color_discrete_sequence=px.colors.qualitative.Set1
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show totals
                        st.markdown("**Total Demographic Updates:**")
                        for age, count in demo_age_totals.items():
                            pct = (count / demo_total * 100) if demo_total > 0 else 0
                            st.markdown(f"- {age}: {count:,.0f} ({pct:.1f}%)")
            
            with col3:
                st.markdown("##### Enrolments by Age Group")
                if 'age_0_5' in data['daily'].columns and 'age_5_17' in data['daily'].columns and 'age_18_greater' in data['daily'].columns:
                    enrol_age_totals = {
                        '0-5 years': data['daily']['age_0_5'].sum(),
                        '5-17 years': data['daily']['age_5_17'].sum(),
                        '18+ years': data['daily']['age_18_greater'].sum()
                    }
                    enrol_total = sum(enrol_age_totals.values())
                    if enrol_total > 0:
                        fig = px.pie(
                            values=list(enrol_age_totals.values()),
                            names=list(enrol_age_totals.keys()),
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show totals
                        st.markdown("**Total Enrolments:**")
                        for age, count in enrol_age_totals.items():
                            pct = (count / enrol_total * 100) if enrol_total > 0 else 0
                            st.markdown(f"- {age}: {count:,.0f} ({pct:.1f}%)")
            
            st.markdown("---")
            
            # Age group trends over time
            st.subheader("Age Group Trends Over Time")
            
            age_metric = st.selectbox(
                "Select Metric",
                ["Biometric", "Demographic", "Enrolment"],
                key="age_trend_metric"
            )
            
            if age_metric == "Biometric" and 'bio_age_5_17' in data['daily'].columns and 'bio_age_17_' in data['daily'].columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['bio_age_5_17'],
                    mode='lines+markers',
                    name='5-17 years',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['bio_age_17_'],
                    mode='lines+markers',
                    name='17+ years',
                    line=dict(color='#ff7f0e', width=2)
                ))
                fig.update_layout(
                    title="Biometric Updates by Age Group Over Time",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif age_metric == "Demographic" and 'demo_age_5_17' in data['daily'].columns and 'demo_age_17_' in data['daily'].columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['demo_age_5_17'],
                    mode='lines+markers',
                    name='5-17 years',
                    line=dict(color='#2ca02c', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['demo_age_17_'],
                    mode='lines+markers',
                    name='17+ years',
                    line=dict(color='#d62728', width=2)
                ))
                fig.update_layout(
                    title="Demographic Updates by Age Group Over Time",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif age_metric == "Enrolment" and 'age_0_5' in data['daily'].columns and 'age_5_17' in data['daily'].columns and 'age_18_greater' in data['daily'].columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['age_0_5'],
                    mode='lines+markers',
                    name='0-5 years',
                    line=dict(color='#9467bd', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['age_5_17'],
                    mode='lines+markers',
                    name='5-17 years',
                    line=dict(color='#8c564b', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['age_18_greater'],
                    mode='lines+markers',
                    name='18+ years',
                    line=dict(color='#e377c2', width=2)
                ))
                fig.update_layout(
                    title="Enrolments by Age Group Over Time",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # State-level age group analysis
            if 'state' in data:
                st.markdown("---")
                st.subheader("State-Level Age Group Analysis")
                
                if 'bio_age_5_17' in data['state'].columns and 'bio_age_17_' in data['state'].columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Top States by Biometric Updates (5-17 years)")
                        top_n_age = st.slider("Number of States", 5, 20, 10, key="top_age_states")
                        top_states_age = data['state'].nlargest(top_n_age, 'bio_age_5_17')[['state', 'bio_age_5_17']]
                        fig = px.bar(
                            top_states_age,
                            x='bio_age_5_17',
                            y='state',
                            orientation='h',
                            title=f"Top {top_n_age} States by Biometric Updates (5-17 years)",
                            labels={'bio_age_5_17': 'Biometric Updates (5-17)', 'state': 'State'},
                            color='bio_age_5_17',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("##### Top States by Biometric Updates (17+ years)")
                        top_states_age17 = data['state'].nlargest(top_n_age, 'bio_age_17_')[['state', 'bio_age_17_']]
                        fig = px.bar(
                            top_states_age17,
                            x='bio_age_17_',
                            y='state',
                            orientation='h',
                            title=f"Top {top_n_age} States by Biometric Updates (17+ years)",
                            labels={'bio_age_17_': 'Biometric Updates (17+)', 'state': 'State'},
                            color='bio_age_17_',
                            color_continuous_scale='Oranges'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                
                # State age comparison table
                with st.expander("📋 View All States Age Group Data"):
                    if 'bio_age_5_17' in data['state'].columns:
                        display_cols = ['state', 'bio_age_5_17', 'bio_age_17_', 'demo_age_5_17', 'demo_age_17_', 'age_0_5', 'age_5_17', 'age_18_greater']
                        available_cols = [col for col in display_cols if col in data['state'].columns]
                        if len(available_cols) > 1:
                            # Sort by first numeric column (skip 'state' which is index 0)
                            sort_col = available_cols[1] if len(available_cols) > 1 else available_cols[0]
                            display_df = data['state'][available_cols].copy().sort_values(sort_col, ascending=False)
                            # Format columns
                            for col in available_cols[1:]:
                                if col in display_df.columns:
                                    display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Tab 6: Coverage & Anomalies
    with tab6:
        st.markdown('<div class="tab-description">Detection of service coverage gaps and unusual update spikes.</div>', unsafe_allow_html=True)
        
        if 'district_coverage' in data:
            render_export_button(data['district_coverage'], "Coverage_Data", "tab6_export")
        elif 'anomalies' in data:
            render_export_button(data['anomalies'], "Anomaly_Data", "tab6_export")  
        st.header("Coverage & Anomaly Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        # Coverage Analysis Section
        if 'district_coverage' in data:
            st.subheader("📊 Coverage Completeness Analysis")
            
            # Coverage statistics
            col1, col2, col3, col4 = st.columns(4)
            
            coverage_df = data['district_coverage'].copy()
            coverage_df = coverage_df[coverage_df['coverage_index'].notna()]
            
            with col1:
                avg_coverage = coverage_df['coverage_index'].mean()
                st.metric("Avg Coverage", f"{avg_coverage:.2f}")
            
            with col2:
                low_coverage = (coverage_df['coverage_index'] < 0.5).sum()
                st.metric("Low Coverage", f"{low_coverage}")
            
            with col3:
                good_coverage = (coverage_df['coverage_index'] >= 1.0).sum()
                st.metric("Good Coverage", f"{good_coverage}")
            
            with col4:
                total_districts = len(coverage_df)
                st.metric("Districts", f"{total_districts}")
            
            st.markdown("---")
            
            # Coverage distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Coverage Index Distribution")
                fig = px.histogram(
                    coverage_df,
                    x='coverage_index',
                    nbins=50,
                    labels={'coverage_index': 'Coverage Index', 'count': 'Number of Districts'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig.add_vline(x=1.0, line_dash="dash", line_color="green", annotation_text="Ideal (1.0)")
                fig.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Low (0.5)")
                fig.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("##### Districts Needing Attention (Low Coverage)")
                threshold = st.slider("Coverage Threshold", 0.0, 1.0, 0.5, 0.1, key="coverage_threshold")
                low_coverage_districts = coverage_df[coverage_df['coverage_index'] < threshold].sort_values('coverage_index')
                
                if len(low_coverage_districts) > 0:
                    top_low = low_coverage_districts.head(20)[['state', 'district', 'coverage_index', 'demo_total', 'bio_total']]
                    fig = px.bar(
                        top_low,
                        x='coverage_index',
                        y='district',
                        orientation='h',
                        color='coverage_index',
                        color_continuous_scale='Reds',
                        title=f"Top 20 Districts with Coverage < {threshold}",
                        labels={'coverage_index': 'Coverage Index', 'district': 'District'},
                        hover_data=['state', 'demo_total', 'bio_total']
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No districts found with coverage below {threshold}")
            
            # Coverage by state
            st.markdown("---")
            st.markdown("##### Coverage by State")
            state_coverage = coverage_df.groupby('state').agg({
                'coverage_index': 'mean',
                'district': 'count',
                'demo_total': 'sum',
                'bio_total': 'sum'
            }).reset_index()
            state_coverage.columns = ['state', 'avg_coverage_index', 'district_count', 'demo_total', 'bio_total']
            state_coverage = state_coverage.sort_values('avg_coverage_index', ascending=False)
            
            top_n_coverage = st.slider("Number of States", 5, 30, 15, key="top_coverage_states")
            top_states_coverage = state_coverage.head(top_n_coverage)
            
            fig = px.bar(
                top_states_coverage,
                x='avg_coverage_index',
                y='state',
                orientation='h',
                color='avg_coverage_index',
                color_continuous_scale='RdYlGn',
                labels={'avg_coverage_index': 'Avg Coverage', 'state': 'State'},
                hover_data=['district_count', 'demo_total', 'bio_total']
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            # Coverage table
            with st.expander("📋 View All Coverage Data"):
                display_df = coverage_df[['state', 'district', 'coverage_index', 'demo_total', 'bio_total']].copy().sort_values('coverage_index', ascending=True)
                display_df['coverage_index'] = display_df['coverage_index'].apply(lambda x: f"{x:.3f}")
                display_df['demo_total'] = display_df['demo_total'].apply(lambda x: f"{x:,.0f}")
                display_df['bio_total'] = display_df['bio_total'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Anomaly Detection Section
        if 'anomalies' in data:
            st.markdown("---")
            st.subheader("⚠️ Anomaly Detection Results")
            
            anomalies_df = data['anomalies'].copy()
            
            # Filter anomalies
            detection_level = st.selectbox(
                "Detection Level",
                ['All'] + anomalies_df['detection_level'].unique().tolist(),
                key="anomaly_level"
            )
            
            if detection_level != 'All':
                anomalies_df = anomalies_df[anomalies_df['detection_level'] == detection_level]
            
            metric_filter = st.selectbox(
                "Metric",
                ['All'] + anomalies_df['metric'].unique().tolist(),
                key="anomaly_metric"
            )
            
            if metric_filter != 'All':
                anomalies_df = anomalies_df[anomalies_df['metric'] == metric_filter]
            
            # Anomaly statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_anomalies = len(anomalies_df)
                st.metric("Anomalies", f"{total_anomalies}")
            
            with col2:
                high_severity = (anomalies_df['severity'] >= 0.8).sum() if 'severity' in anomalies_df.columns else 0
                st.metric("High Severity Anomalies", f"{high_severity}")
            
            with col3:
                if 'date' in anomalies_df.columns:
                    anomalies_df['date'] = pd.to_datetime(anomalies_df['date'], errors='ignore')
                    recent_anomalies = anomalies_df[anomalies_df['date'] >= anomalies_df['date'].max() - pd.Timedelta(days=30)] if len(anomalies_df) > 0 else anomalies_df
                    st.metric("Last 30 Days", f"{len(recent_anomalies)}")
            
            # Temporal anomalies visualization
            if 'date' in anomalies_df.columns and len(anomalies_df) > 0:
                st.markdown("##### Temporal Anomalies")
                temporal_anomalies = anomalies_df[anomalies_df['detection_level'] == 'temporal'] if 'detection_level' in anomalies_df.columns else anomalies_df
                if len(temporal_anomalies) > 0:
                    fig = go.Figure()
                    
                    # Plot anomalies
                    if 'value' in temporal_anomalies.columns:
                        fig.add_trace(go.Scatter(
                            x=temporal_anomalies['date'],
                            y=temporal_anomalies['value'],
                            mode='markers',
                            name='Anomalies',
                            marker=dict(
                                size=10,
                                color='red',
                                symbol='x'
                            ),
                            text=temporal_anomalies['metric'] if 'metric' in temporal_anomalies.columns else None,
                            hovertemplate='Date: %{x}<br>Value: %{y:,.0f}<br>Metric: %{text}<extra></extra>'
                        ))
                    
                    fig.update_layout(
                        title="Detected Temporal Anomalies",
                        xaxis_title="Date",
                        yaxis_title="Value",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Geographic anomalies
            if 'state' in anomalies_df.columns and len(anomalies_df[anomalies_df['state'].notna()]) > 0:
                st.markdown("##### Geographic Anomalies by State")
                geo_anomalies = anomalies_df[anomalies_df['state'].notna()]
                if len(geo_anomalies) > 0:
                    state_anomaly_counts = geo_anomalies.groupby('state').size().reset_index(name='anomaly_count')
                    state_anomaly_counts = state_anomaly_counts.sort_values('anomaly_count', ascending=False).head(20)
                    
                    fig = px.bar(
                        state_anomaly_counts,
                        x='anomaly_count',
                        y='state',
                        orientation='h',
                        title="Top 20 States by Anomaly Count",
                        labels={'anomaly_count': 'Number of Anomalies', 'state': 'State'},
                        color='anomaly_count',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Anomalies table
            with st.expander("📋 View All Anomalies"):
                display_cols = ['detection_level', 'metric', 'date', 'value', 'severity', 'state']
                available_cols = [col for col in display_cols if col in anomalies_df.columns]
                display_df = anomalies_df[available_cols].copy()
                if 'value' in display_df.columns:
                    display_df['value'] = display_df['value'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
                if 'severity' in display_df.columns:
                    display_df['severity'] = display_df['severity'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Anomaly detection data not available. Please run anomaly detection analysis first.")
    
    # Tab 7: Insights & Recommendations
    with tab7:
        st.markdown('<div class="tab-description">Actionable findings and prioritized recommendations.</div>', unsafe_allow_html=True)
        
        if 'insights' in data:
            render_export_button(data['insights'], "Insights_Recommendations", "tab7_export")    
        st.header("Insights & Recommendations")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'insights' in data:
            insights_df = data['insights'].copy()
            
            # Filter by priority
            priority_filter = st.selectbox(
                "Filter by Priority",
                ['All', 'High', 'Medium', 'Low'],
                key="priority_filter"
            )
            
            if priority_filter != 'All':
                insights_df = insights_df[insights_df['priority'] == priority_filter]
            
            # Insights summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_insights = len(insights_df)
                st.metric("Total Insights", f"{total_insights}")
            
            with col2:
                high_priority = (insights_df['priority'] == 'High').sum() if 'priority' in insights_df.columns else 0
                st.metric("High Priority", f"{high_priority}", delta_color="inverse")
            
            with col3:
                medium_priority = (insights_df['priority'] == 'Medium').sum() if 'priority' in insights_df.columns else 0
                st.metric("Medium Priority", f"{medium_priority}")
            
            with col4:
                low_priority = (insights_df['priority'] == 'Low').sum() if 'priority' in insights_df.columns else 0
                st.metric("Low Priority", f"{low_priority}")
            
            st.markdown("---")
            
            # Category distribution
            if 'category' in insights_df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Insights by Category")
                    category_counts = insights_df['category'].value_counts().reset_index()
                    category_counts.columns = ['Category', 'Count']
                    
                    fig = px.pie(
                        category_counts,
                        values='Count',
                        names='Category',
                        title="Distribution of Insights by Category",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### Insights by Priority")
                    if 'priority' in insights_df.columns:
                        priority_counts = insights_df['priority'].value_counts().reset_index()
                        priority_counts.columns = ['Priority', 'Count']
                        priority_order = ['High', 'Medium', 'Low']
                        priority_counts['Priority'] = pd.Categorical(priority_counts['Priority'], categories=priority_order, ordered=True)
                        priority_counts = priority_counts.sort_values('Priority')
                        
                        color_map = {'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'}
                        
                        fig = px.bar(
                            priority_counts,
                            x='Priority',
                            y='Count',
                            title="Distribution of Insights by Priority",
                            labels={'Count': 'Number of Insights', 'Priority': 'Priority Level'},
                            color='Priority',
                            color_discrete_map=color_map
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Display insights
            st.subheader("Key Insights & Recommendations")
            
            for idx, row in insights_df.iterrows():
                priority = row.get('priority', 'N/A')
                category = row.get('category', 'General')
                finding = row.get('finding', '')
                recommendation = row.get('recommendation', '')
                
                # Color based on priority
                if priority == 'High':
                    border_color = '#d62728'
                    bg_color = '#ffe6e6'
                elif priority == 'Medium':
                    border_color = '#ff7f0e'
                    bg_color = '#fff4e6'
                else:
                    border_color = '#2ca02c'
                    bg_color = '#e6ffe6'
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 1rem; border-left: 4px solid {border_color}; border-radius: 0.25rem; margin: 1rem 0;">
                    <h4 style="color: {border_color}; margin-top: 0;">
                        {category} - {priority} Priority
                    </h4>
                    <p style="margin-bottom: 0.5rem; color: black;"><strong>Finding:</strong> {finding}</p>
                    <p style="margin-bottom: 0; color: black;"><strong>Recommendation:</strong> {recommendation}</p>

                </div>
                """, unsafe_allow_html=True)
            
            # Insights table
            with st.expander("📋 View All Insights in Table Format"):
                display_df = insights_df.copy()
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Insights data not available. Please run exploratory data analysis to generate insights.")
    
    # Tab 8: Surge Predictions
    with tab8:
        st.markdown('<div class="tab-description">Early warnings for upcoming surges based on age transitions and regional patterns.</div>', unsafe_allow_html=True)
        
        if 'surge_predictions' in data:
            render_export_button(data['surge_predictions'], "Surge_Predictions", "tab8_export")
        st.header("🚨 Surge Prediction System")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'surge_predictions' in data:
            predictions_df = data['surge_predictions'].copy()
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_predictions = len(predictions_df)
                st.metric("Total Surge Predictions", f"{total_predictions}")
            
            with col2:
                high_priority = len(predictions_df[predictions_df['priority'] == 'High']) if 'priority' in predictions_df.columns else 0
                st.metric("High Priority Surges", f"{high_priority}", delta_color="inverse")
            
            with col3:
                upcoming_30 = len(predictions_df[predictions_df['days_until_surge'] <= 30]) if 'days_until_surge' in predictions_df.columns else 0
                st.metric("Upcoming (30 days)", f"{upcoming_30}", delta_color="inverse")
            
            with col4:
                avg_confidence = predictions_df['confidence'].mean() if 'confidence' in predictions_df.columns else 0
                st.metric("Avg Confidence", f"{avg_confidence:.2f}")
            
            st.markdown("---")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                surge_type_filter = st.selectbox(
                    "Filter by Surge Type",
                    ['All'] + predictions_df['surge_type'].unique().tolist() if 'surge_type' in predictions_df.columns else ['All'],
                    key="surge_type_filter"
                )
            
            with col2:
                priority_filter = st.selectbox(
                    "Filter by Priority",
                    ['All', 'High', 'Medium', 'Low'],
                    key="surge_priority_filter"
                )
            
            with col3:
                time_horizon = st.selectbox(
                    "Time Horizon",
                    ['All', 'Next 30 days', 'Next 60 days', 'Next 90 days'],
                    key="surge_time_horizon"
                )
            
            # Apply filters
            filtered_df = predictions_df.copy()
            
            if surge_type_filter != 'All' and 'surge_type' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['surge_type'] == surge_type_filter]
            
            if priority_filter != 'All' and 'priority' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
            
            if time_horizon != 'All' and 'days_until_surge' in filtered_df.columns:
                if time_horizon == 'Next 30 days':
                    filtered_df = filtered_df[filtered_df['days_until_surge'] <= 30]
                elif time_horizon == 'Next 60 days':
                    filtered_df = filtered_df[filtered_df['days_until_surge'] <= 60]
                elif time_horizon == 'Next 90 days':
                    filtered_df = filtered_df[filtered_df['days_until_surge'] <= 90]
            
            st.markdown("---")
            
            # Surge predictions visualization
            if len(filtered_df) > 0:
                # Surge type distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Surges by Type")
                    if 'surge_type' in filtered_df.columns:
                        type_counts = filtered_df['surge_type'].value_counts().reset_index()
                        type_counts.columns = ['Surge Type', 'Count']
                        
                        fig = px.pie(
                            type_counts,
                            values='Count',
                            names='Surge Type',
                            title="Distribution of Surge Predictions by Type",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### Surges by Priority")
                    if 'priority' in filtered_df.columns:
                        priority_counts = filtered_df['priority'].value_counts().reset_index()
                        priority_counts.columns = ['Priority', 'Count']
                        priority_order = ['High', 'Medium', 'Low']
                        priority_counts['Priority'] = pd.Categorical(
                            priority_counts['Priority'], 
                            categories=priority_order, 
                            ordered=True
                        )
                        priority_counts = priority_counts.sort_values('Priority')
                        
                        color_map = {'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'}
                        
                        fig = px.bar(
                            priority_counts,
                            x='Priority',
                            y='Count',
                            title="Distribution of Surge Predictions by Priority",
                            labels={'Count': 'Number of Surges', 'Priority': 'Priority Level'},
                            color='Priority',
                            color_discrete_map=color_map
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Timeline visualization
                st.markdown("##### Surge Timeline")
                if 'predicted_date' in filtered_df.columns and 'days_until_surge' in filtered_df.columns:
                    timeline_df = filtered_df.copy()
                    timeline_df = timeline_df.sort_values('predicted_date')
                    
                    fig = go.Figure()
                    
                    # Color by priority
                    for priority in timeline_df['priority'].unique() if 'priority' in timeline_df.columns else ['High']:
                        priority_data = timeline_df[timeline_df['priority'] == priority] if 'priority' in timeline_df.columns else timeline_df
                        
                        color_map = {'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'}
                        color = color_map.get(priority, '#1f77b4')
                        
                        fig.add_trace(go.Scatter(
                            x=priority_data['predicted_date'],
                            y=priority_data['expected_magnitude'] if 'expected_magnitude' in priority_data.columns else range(len(priority_data)),
                            mode='markers+lines',
                            name=f'{priority} Priority',
                            marker=dict(size=10, color=color),
                            line=dict(color=color, width=2),
                            hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Magnitude: %{y:.2f}<extra></extra>',
                            text=priority_data['state'] if 'state' in priority_data.columns else None
                        ))
                    
                    fig.update_layout(
                        title="Surge Predictions Timeline",
                        xaxis_title="Predicted Date",
                        yaxis_title="Expected Surge Magnitude",
                        hovermode='closest',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Top surges by magnitude
                st.markdown("##### Top Surges by Expected Magnitude")
                if 'expected_magnitude' in filtered_df.columns:
                    top_surges = filtered_df.nlargest(20, 'expected_magnitude')
                    
                    fig = px.bar(
                        top_surges,
                        x='expected_magnitude',
                        y='state' if 'state' in top_surges.columns else top_surges.index,
                        orientation='h',
                        color='confidence' if 'confidence' in top_surges.columns else None,
                        title="Top 20 Surge Predictions by Magnitude",
                        labels={'expected_magnitude': 'Expected Surge Magnitude', 'state': 'State'},
                        color_continuous_scale='Reds',
                        hover_data=['days_until_surge', 'confidence', 'priority'] if all(col in top_surges.columns for col in ['days_until_surge', 'confidence', 'priority']) else None
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Detailed surge predictions table
                st.markdown("##### Detailed Surge Predictions")
                display_cols = ['surge_type', 'subtype', 'state', 'predicted_date', 'days_until_surge', 
                               'expected_magnitude', 'estimated_volume', 'confidence', 'priority']
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                display_df = filtered_df[available_cols].copy().sort_values('days_until_surge', ascending=True)
                
                # Format columns
                if 'predicted_date' in display_df.columns:
                    display_df['predicted_date'] = display_df['predicted_date'].dt.strftime('%Y-%m-%d')
                if 'expected_magnitude' in display_df.columns:
                    display_df['expected_magnitude'] = display_df['expected_magnitude'].apply(lambda x: f"{x:.2f}")
                if 'estimated_volume' in display_df.columns:
                    display_df['estimated_volume'] = display_df['estimated_volume'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
                if 'confidence' in display_df.columns:
                    display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Upcoming surges alert
                if 'upcoming_surges' in data and len(data['upcoming_surges']) > 0:
                    st.markdown("---")
                    st.markdown("##### 🚨 Upcoming Surges (Next 30 Days)")
                    upcoming_df = data['upcoming_surges'].copy()
                    
                    for idx, row in upcoming_df.iterrows():
                        priority = row.get('priority', 'High')
                        state = row.get('state', 'Unknown')
                        days_until = row.get('days_until_surge', 0)
                        magnitude = row.get('expected_magnitude', 0)
                        confidence = row.get('confidence', 0)
                        
                        if priority == 'High':
                            border_color = '#d62728'
                            bg_color = '#ffe6e6'
                        elif priority == 'Medium':
                            border_color = '#ff7f0e'
                            bg_color = '#fff4e6'
                        else:
                            border_color = '#2ca02c'
                            bg_color = '#e6ffe6'
                        
                        st.markdown(f"""
                        <div style="background-color: {bg_color}; padding: 1rem; border-left: 4px solid {border_color}; border-radius: 0.25rem; margin: 1rem 0;">
                            <h4 style="color: {border_color}; margin-top: 0;">
                                {state} - {priority} Priority Surge
                            </h4>
                            <p style="margin-bottom: 0.5rem;"><strong>Days Until Surge:</strong> {days_until} days</p>
                            <p style="margin-bottom: 0.5rem;"><strong>Expected Magnitude:</strong> {magnitude:.2f}x baseline</p>
                            <p style="margin-bottom: 0;"><strong>Confidence:</strong> {confidence:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
            else:
                st.info("No surge predictions found with the selected filters.")
        else:
            st.info("Surge prediction data not available. Please run surge_prediction.py to generate predictions.")
    
    # Tab 9: Feature Engineering
    with tab9:
        st.markdown('<div class="tab-description">Engineered data variables used by the AI models.</div>', unsafe_allow_html=True)
        
        if 'features_daily' in data:
            render_export_button(data['features_daily'], "Feature_Engineering_Data", "tab9_export")
        st.header("⚙️ Data Variable Insights")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'features_daily' in data or 'features_state' in data:
            # Feature summary
            if 'features_summary' in data:
                summary = data['features_summary']
                st.subheader("Feature Engineering Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_features = sum(
                        summary['feature_counts'][k]['num_features_created'] 
                        for k in summary['feature_counts'].keys()
                    )
                    st.metric("Total Features Created", f"{total_features}")
                
                with col2:
                    daily_features = summary['feature_counts'].get('daily', {}).get('num_features_created', 0)
                    st.metric("Daily Features", f"{daily_features}")
                
                with col3:
                    state_features = summary['feature_counts'].get('state', {}).get('num_features_created', 0)
                    st.metric("State Features", f"{state_features}")
                
                with col4:
                    st.metric("Feature Types", "7 types")
                
                st.markdown("---")
            
            # Feature types visualization
            if 'features_summary' in data and 'feature_types' in data['features_summary']:
                st.subheader("Feature Types Distribution")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Daily Features by Type")
                    if 'daily' in data['features_summary']['feature_types']:
                        daily_types = data['features_summary']['feature_types']['daily']
                        type_df = pd.DataFrame([
                            {'Type': 'Lag Features', 'Count': daily_types.get('lag_features', 0)},
                            {'Type': 'Rolling Features', 'Count': daily_types.get('rolling_features', 0)},
                            {'Type': 'Seasonal Features', 'Count': daily_types.get('seasonal_features', 0)},
                            {'Type': 'Z-Score Features', 'Count': daily_types.get('z_score_features', 0)},
                            {'Type': 'IQR Features', 'Count': daily_types.get('iqr_features', 0)},
                            {'Type': 'Scaled Features', 'Count': daily_types.get('scaled_features', 0)},
                        ])
                        
                        fig = px.bar(
                            type_df,
                            x='Type',
                            y='Count',
                            title="Daily Feature Types",
                            labels={'Count': 'Number of Features', 'Type': 'Feature Type'},
                            color='Count',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### State Features by Type")
                    if 'state' in data['features_summary']['feature_types']:
                        state_types = data['features_summary']['feature_types']['state']
                        type_df = pd.DataFrame([
                            {'Type': 'Geographic Features', 'Count': state_types.get('geographic_features', 0)},
                            {'Type': 'Scaled Features', 'Count': state_types.get('scaled_features', 0)},
                        ])
                        
                        if len(type_df) > 0:
                            fig = px.bar(
                                type_df,
                                x='Type',
                                y='Count',
                                title="State Feature Types",
                                labels={'Count': 'Number of Features', 'Type': 'Feature Type'},
                                color='Count',
                                color_continuous_scale='Oranges'
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Daily features visualization
            if 'features_daily' in data:
                st.subheader("Daily Features Analysis")
                
                features_daily_df = data['features_daily'].copy()
                
                # Feature category selector
                feature_category = st.selectbox(
                    "Select Feature Category",
                    ['Lag Features', 'Rolling Statistics', 'Z-Score Features', 'IQR Features', 'Seasonal Features'],
                    key="feature_category"
                )
                
                # Get relevant columns
                if feature_category == 'Lag Features':
                    feature_cols = [col for col in features_daily_df.columns if '_lag_' in col]
                elif feature_category == 'Rolling Statistics':
                    feature_cols = [col for col in features_daily_df.columns if '_rolling_' in col]
                elif feature_category == 'Z-Score Features':
                    feature_cols = [col for col in features_daily_df.columns if '_z_score' in col or '_deviation' in col or '_pct_change' in col]
                elif feature_category == 'IQR Features':
                    feature_cols = [col for col in features_daily_df.columns if '_iqr' in col]
                elif feature_category == 'Seasonal Features':
                    feature_cols = [col for col in features_daily_df.columns if any(x in col for x in ['day_of_week', 'month', 'quarter', 'week_of_year'])]
                else:
                    feature_cols = []
                
                if len(feature_cols) > 0 and 'date' in features_daily_df.columns:
                    # Select a feature to visualize
                    selected_feature = st.selectbox("Select Feature", feature_cols[:10], key="selected_feature_daily")
                    
                    if selected_feature in features_daily_df.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"##### {selected_feature} Over Time")
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=features_daily_df['date'],
                                y=features_daily_df[selected_feature],
                                mode='lines+markers',
                                name=selected_feature,
                                line=dict(color='#1f77b4', width=2)
                            ))
                            fig.update_layout(
                                title=f"{selected_feature} Timeline",
                                xaxis_title="Date",
                                yaxis_title="Feature Value",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.markdown(f"##### {selected_feature} Statistics")
                            feature_stats = features_daily_df[selected_feature].describe()
                            
                            col_stat1, col_stat2 = st.columns(2)
                            with col_stat1:
                                st.metric("Mean", f"{feature_stats.get('mean', 0):.2f}")
                                st.metric("Std", f"{feature_stats.get('std', 0):.2f}")
                            with col_stat2:
                                st.metric("Min", f"{feature_stats.get('min', 0):.2f}")
                                st.metric("Max", f"{feature_stats.get('max', 0):.2f}")
                            
                            # Distribution histogram
                            fig = px.histogram(
                                features_daily_df,
                                x=selected_feature,
                                nbins=30,
                                labels={'count': 'Frequency'},
                                color_discrete_sequence=['#1f77b4']
                            )
                            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # State features visualization
            if 'features_state' in data:
                st.subheader("State Features Analysis")
                
                features_state_df = data['features_state'].copy()
                
                # Get feature columns (exclude state name)
                feature_cols = [col for col in features_state_df.columns if col != 'state']
                
                if len(feature_cols) > 0:
                    selected_feature_state = st.selectbox("Select Feature", feature_cols[:15], key="selected_feature_state")
                    
                    if selected_feature_state in features_state_df.columns and 'state' in features_state_df.columns:
                        # Top states by feature value
                        top_n_features = st.slider("Number of States", 5, 30, 15, key="top_n_features")
                        top_states = features_state_df.nlargest(top_n_features, selected_feature_state)[['state', selected_feature_state]]
                        
                        fig = px.bar(
                            top_states,
                            x=selected_feature_state,
                            y='state',
                            orientation='h',
                            labels={selected_feature_state: 'Feature Value', 'state': 'State'},
                            color=selected_feature_state,
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Feature data tables
            with st.expander("📋 View Daily Features Data"):
                if 'features_daily' in data:
                    display_df = data['features_daily'].copy()
                    # Show only first 20 columns for performance
                    display_cols = display_df.columns[:20].tolist()
                    if 'date' in display_df.columns:
                        display_cols = ['date'] + [c for c in display_cols if c != 'date']
                    st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True)
            
            with st.expander("📋 View State Features Data"):
                if 'features_state' in data:
                    display_df = data['features_state'].copy()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Feature engineering data not available. Please run feature_engineering.py to generate features.")
    
    # Tab 10: District & Pincode Models
    with tab10:
        st.markdown('<div class="tab-description">Granular forecasting and anomaly detection at district and pincode levels.</div>', unsafe_allow_html=True)
        
        if 'district_forecasts' in data:
            render_export_button(data['district_forecasts'], "District_Forecasts", "tab10_export")
        st.header("🏘️ District & Pincode Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        # Summary metrics
        if 'district_pincode_summary' in data:
            summary = data['district_pincode_summary']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'district_forecasts' in summary.get('summary', {}):
                    total_forecasts = summary['summary']['district_forecasts'].get('total_forecasts', 0)
                    st.metric("Dist. Forecasts", f"{total_forecasts}")
                else:
                    st.metric("Dist. Forecasts", "0")
            
            with col2:
                if 'pincode_anomalies' in summary.get('summary', {}):
                    total_anomalies = summary['summary']['pincode_anomalies'].get('total_anomalies', 0)
                    st.metric("Pincode Anomalies", f"{total_anomalies}")
                else:
                    st.metric("Pincode Anomalies", "0")
            
            with col3:
                if 'district_forecasts' in summary.get('summary', {}):
                    unique_states = summary['summary']['district_forecasts'].get('unique_states', 0)
                    st.metric("States Analyzed", f"{unique_states}")
                else:
                    st.metric("States Analyzed", "0")
            
            with col4:
                if 'pincode_anomalies' in summary.get('summary', {}):
                    unique_pincodes = summary['summary']['pincode_anomalies'].get('unique_pincodes', 0)
                    st.metric("Pincodes Analyzed", f"{unique_pincodes}")
                else:
                    st.metric("Pincodes Analyzed", "0")
        
        st.markdown("---")
        
        # District-level forecasts section
        if 'district_forecasts' in data:
            st.subheader("District-Level Forecasts")
            
            district_forecasts_df = data['district_forecasts'].copy()
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                state_filter = st.selectbox(
                    "Filter by State",
                    ['All'] + sorted(district_forecasts_df['state'].unique().tolist()) if 'state' in district_forecasts_df.columns else ['All'],
                    key="district_state_filter"
                )
            
            with col2:
                volume_filter = st.selectbox(
                    "Filter by Volume Classification",
                    ['All', 'high_volume', 'low_volume'],
                    key="district_volume_filter"
                )
            
            # Apply filters
            filtered_district_df = district_forecasts_df.copy()
            if state_filter != 'All' and 'state' in filtered_district_df.columns:
                filtered_district_df = filtered_district_df[filtered_district_df['state'] == state_filter]
            if volume_filter != 'All' and 'volume_classification' in filtered_district_df.columns:
                filtered_district_df = filtered_district_df[filtered_district_df['volume_classification'] == volume_filter]
            
            if len(filtered_district_df) > 0:
                # Volume classification distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Forecasts by Volume Classification")
                    if 'volume_classification' in filtered_district_df.columns:
                        volume_counts = filtered_district_df['volume_classification'].value_counts().reset_index()
                        volume_counts.columns = ['Volume Classification', 'Count']
                        
                        fig = px.pie(
                            volume_counts,
                            values='Count',
                            names='Volume Classification',
                            title="District Forecasts by Volume Type",
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### Top Districts by Forecast Mean")
                    if 'forecast_mean' in filtered_district_df.columns:
                        top_n_districts = st.slider("Number of Districts", 5, 30, 15, key="top_districts_forecast")
                        top_districts = filtered_district_df.nlargest(top_n_districts, 'forecast_mean')
                        
                        fig = px.bar(
                            top_districts,
                            x='forecast_mean',
                            y='district',
                            orientation='h',
                            color='volume_classification' if 'volume_classification' in top_districts.columns else None,
                            labels={'forecast_mean': 'Forecast Mean', 'district': 'District'},
                            hover_data=['state', 'historical_mean', 'forecast_trend'],
                            color_discrete_map={'high_volume': '#1f77b4', 'low_volume': '#ff7f0e'} if 'volume_classification' in top_districts.columns else None
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig, use_container_width=True)
                
                # State aggregations
                if 'district_state_aggregations' in data:
                    st.markdown("---")
                    st.markdown("##### State-Level Aggregations (Resource Planning)")
                    state_agg_df = data['district_state_aggregations'].copy()
                    
                    fig = px.bar(
                        state_agg_df,
                        x='state',
                        y='total_forecast_mean',
                        color='forecast_increase',
                        labels={'total_forecast_mean': 'Total Forecast Mean', 'state': 'State', 'forecast_increase': 'Forecast Increase (%)'},
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=400, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                # District forecasts table
                with st.expander("📋 View District Forecasts Data"):
                    display_cols = ['state', 'district', 'metric', 'volume_classification', 'historical_mean', 
                                   'forecast_mean', 'forecast_trend', 'forecast_periods', 'data_points']
                    available_cols = [col for col in display_cols if col in filtered_district_df.columns]
                    display_df = filtered_district_df[available_cols].copy().sort_values('forecast_mean', ascending=False)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No district forecasts found with the selected filters.")
        else:
            st.info("District forecast data not available. Please run district_pincode_models.py to generate forecasts.")
        
        st.markdown("---")
        
        # Pincode-level anomalies section
        if 'pincode_anomalies' in data:
            st.subheader("Pincode-Level Anomalies")
            
            pincode_anomalies_df = data['pincode_anomalies'].copy()
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                pincode_state_filter = st.selectbox(
                    "Filter by State",
                    ['All'] + sorted(pincode_anomalies_df['state'].unique().tolist()) if 'state' in pincode_anomalies_df.columns else ['All'],
                    key="pincode_state_filter"
                )
            
            with col2:
                severity_filter = st.selectbox(
                    "Filter by Severity",
                    ['All', 'High (≥0.7)', 'Medium (0.4-0.7)', 'Low (<0.4)'],
                    key="pincode_severity_filter"
                )
            
            # Apply filters
            filtered_pincode_df = pincode_anomalies_df.copy()
            if pincode_state_filter != 'All' and 'state' in filtered_pincode_df.columns:
                filtered_pincode_df = filtered_pincode_df[filtered_pincode_df['state'] == pincode_state_filter]
            if severity_filter != 'All' and 'severity' in filtered_pincode_df.columns:
                if severity_filter == 'High (≥0.7)':
                    filtered_pincode_df = filtered_pincode_df[filtered_pincode_df['severity'] >= 0.7]
                elif severity_filter == 'Medium (0.4-0.7)':
                    filtered_pincode_df = filtered_pincode_df[(filtered_pincode_df['severity'] >= 0.4) & (filtered_pincode_df['severity'] < 0.7)]
                else:
                    filtered_pincode_df = filtered_pincode_df[filtered_pincode_df['severity'] < 0.4]
            
            if len(filtered_pincode_df) > 0:
                # Volume classification distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Anomalies by Volume Classification")
                    if 'volume_classification' in filtered_pincode_df.columns:
                        volume_counts = filtered_pincode_df['volume_classification'].value_counts().reset_index()
                        volume_counts.columns = ['Volume Classification', 'Count']
                        
                        fig = px.pie(
                            volume_counts,
                            values='Count',
                            names='Volume Classification',
                            title="Pincode Anomalies by Volume Type",
                            color_discrete_sequence=px.colors.qualitative.Set1
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### Top Pincodes by Anomaly Severity")
                    if 'severity' in filtered_pincode_df.columns:
                        top_n_pincodes = st.slider("Number of Pincodes", 5, 50, 20, key="top_pincodes_anomalies")
                        top_pincodes = filtered_pincode_df.nlargest(top_n_pincodes, 'severity')
                        
                        fig = px.bar(
                            top_pincodes,
                            x='severity',
                            y='pincode',
                            orientation='h',
                            color='severity',
                            title=f"Top {top_n_pincodes} Pincodes by Anomaly Severity",
                            labels={'severity': 'Severity', 'pincode': 'Pincode'},
                            hover_data=['state', 'district', 'value', 'mad_z_score'],
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                        st.plotly_chart(fig, use_container_width=True)
                
                # State-level anomaly summary
                if 'state' in filtered_pincode_df.columns:
                    st.markdown("---")
                    st.markdown("##### Anomalies by State")
                    state_anomaly_counts = filtered_pincode_df.groupby('state').agg({
                        'pincode': 'count',
                        'severity': 'mean'
                    }).reset_index()
                    state_anomaly_counts.columns = ['state', 'anomaly_count', 'avg_severity']
                    state_anomaly_counts = state_anomaly_counts.sort_values('anomaly_count', ascending=False).head(20)
                    
                    fig = px.bar(
                        state_anomaly_counts,
                        x='anomaly_count',
                        y='state',
                        orientation='h',
                        color='avg_severity',
                        title="Top 20 States by Pincode Anomaly Count",
                        labels={'anomaly_count': 'Number of Anomalies', 'state': 'State', 'avg_severity': 'Avg Severity'},
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Pincode anomalies table
                with st.expander("📋 View Pincode Anomalies Data"):
                    display_cols = ['pincode', 'state', 'district', 'metric', 'value', 'volume_classification',
                                   'severity', 'mad_z_score', 'is_high_anomaly']
                    available_cols = [col for col in display_cols if col in filtered_pincode_df.columns]
                    display_df = filtered_pincode_df[available_cols].copy().sort_values('severity', ascending=False)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No pincode anomalies found with the selected filters.")
        else:
            st.info("Pincode anomaly data not available. Please run district_pincode_models.py to generate anomalies.")
    
    # Tab 11: Actionable Insights
    with tab11:
        st.markdown('<div class="tab-description">Synthesis of AI findings into task-oriented recommendations.</div>', unsafe_allow_html=True)
        
        # --- NEW EXPORT CODE STARTS HERE ---
        # We try to export 'filtered_insights' if it exists, otherwise 'insights_df'
        # We check locals() to see which dataframe is available to avoid errors
        if 'filtered_insights' in locals():
            export_df = filtered_insights
        elif 'insights_df' in locals():
            export_df = insights_df
        elif 'actionable_insights' in data:
            export_df = data['actionable_insights']
        else:
            export_df = None

        if export_df is not None:
            render_export_button(export_df, "Actionable_Insights", "tab11")
        # --- NEW EXPORT CODE ENDS HERE ---
        st.header("🎯 Final Action Plans")
        
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}**...")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'actionable_insights' in data:
            insights_df = data['actionable_insights'].copy()
            
            # Summary metrics from insights_summary if available
            if 'insights_summary' in data:
                summary = data['insights_summary']
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_insights = summary.get('total_insights', len(insights_df))
                    st.metric("Total Insights", f"{total_insights}")
                
                with col2:
                    high_priority = summary.get('by_priority', {}).get('High', 0)
                    st.metric("High Priority", f"{high_priority}", delta_color="inverse")
                
                with col3:
                    critical_priority = summary.get('by_priority', {}).get('Critical', 0)
                    if critical_priority > 0:
                        st.metric("Critical Priority", f"{critical_priority}", delta_color="inverse")
                    else:
                        medium_priority = summary.get('by_priority', {}).get('Medium', 0)
                        st.metric("Medium Priority", f"{medium_priority}")
                
                with col4:
                    high_impact = summary.get('by_impact', {}).get('High', 0)
                    st.metric("High Impact", f"{high_impact}", delta_color="inverse")
            else:
                # Fallback to calculating from dataframe
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_insights = len(insights_df)
                    st.metric("Total Insights", f"{total_insights}")
                
                with col2:
                    high_priority = len(insights_df[insights_df['priority'] == 'High']) if 'priority' in insights_df.columns else 0
                    st.metric("High Priority", f"{high_priority}", delta_color="inverse")
                
                with col3:
                    critical_priority = len(insights_df[insights_df['priority'] == 'Critical']) if 'priority' in insights_df.columns else 0
                    if critical_priority > 0:
                        st.metric("Critical Priority", f"{critical_priority}", delta_color="inverse")
                    else:
                        medium_priority = len(insights_df[insights_df['priority'] == 'Medium']) if 'priority' in insights_df.columns else 0
                        st.metric("Medium Priority", f"{medium_priority}")
                
                with col4:
                    high_impact = len(insights_df[insights_df['impact'] == 'High']) if 'impact' in insights_df.columns else 0
                    st.metric("High Impact", f"{high_impact}", delta_color="inverse")
            
            st.markdown("---")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                insight_type_filter = st.selectbox(
                    "Filter by Insight Type",
                    ['All'] + insights_df['insight_type'].unique().tolist() if 'insight_type' in insights_df.columns else ['All'],
                    key="actionable_insight_type_filter"
                )
            
            with col2:
                priority_filter = st.selectbox(
                    "Filter by Priority",
                    ['All', 'Critical', 'High', 'Medium', 'Low'],
                    key="actionable_priority_filter"
                )
            
            with col3:
                state_filter = st.selectbox(
                    "Filter by State",
                    ['All'] + sorted([s for s in insights_df['state'].dropna().unique().tolist() if pd.notna(s)]) if 'state' in insights_df.columns else ['All'],
                    key="actionable_state_filter"
                )
            
            # Apply filters
            filtered_insights = insights_df.copy()
            if insight_type_filter != 'All' and 'insight_type' in filtered_insights.columns:
                filtered_insights = filtered_insights[filtered_insights['insight_type'] == insight_type_filter]
            if priority_filter != 'All' and 'priority' in filtered_insights.columns:
                filtered_insights = filtered_insights[filtered_insights['priority'] == priority_filter]
            if state_filter != 'All' and 'state' in filtered_insights.columns:
                filtered_insights = filtered_insights[filtered_insights['state'] == state_filter]
            
            st.markdown(f"**Showing {len(filtered_insights)} of {len(insights_df)} insights**")
            st.markdown("---")
            
            # Visualizations
            if len(filtered_insights) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Insights by Type")
                    if 'insight_type' in filtered_insights.columns:
                        type_counts = filtered_insights['insight_type'].value_counts().reset_index()
                        type_counts.columns = ['Insight Type', 'Count']
                        
                        # Format insight type names
                        type_counts['Insight Type'] = type_counts['Insight Type'].str.replace('_', ' ').str.title()
                        
                        fig = px.pie(
                            type_counts,
                            values='Count',
                            names='Insight Type',
                            title="Distribution by Insight Type",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("##### Insights by Priority")
                    if 'priority' in filtered_insights.columns:
                        priority_counts = filtered_insights['priority'].value_counts().reset_index()
                        priority_counts.columns = ['Priority', 'Count']
                        
                        priority_order = ['Critical', 'High', 'Medium', 'Low']
                        priority_counts['Priority'] = pd.Categorical(priority_counts['Priority'], categories=priority_order, ordered=True)
                        priority_counts = priority_counts.sort_values('Priority')
                        
                        color_map = {'Critical': '#8B0000', 'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'}
                        
                        fig = px.bar(
                            priority_counts,
                            x='Priority',
                            y='Count',
                            title="Distribution by Priority",
                            labels={'Count': 'Number of Insights', 'Priority': 'Priority Level'},
                            color='Priority',
                            color_discrete_map=color_map
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # State distribution if available
                if 'state' in filtered_insights.columns and filtered_insights['state'].notna().sum() > 0:
                    st.markdown("---")
                    st.markdown("##### Insights by State")
                    state_counts = filtered_insights[filtered_insights['state'].notna()]['state'].value_counts().head(15).reset_index()
                    state_counts.columns = ['State', 'Count']
                    
                    fig = px.bar(
                        state_counts,
                        x='Count',
                        y='State',
                        orientation='h',
                        title="Top 15 States by Number of Insights",
                        labels={'Count': 'Number of Insights', 'State': 'State'},
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")

  #change title color in bottom tabs          
            # Display insights
            st.subheader("Actionable Insights & Recommendations")
            
            if len(filtered_insights) > 0:
                for idx, row in filtered_insights.iterrows():
                    priority = row.get('priority', 'Medium')
                    insight_type = row.get('insight_type', 'general').replace('_', ' ').title()
                    title = row.get('title', 'Insight')
                    rationale = row.get('rationale', '')
                    expected_impact = row.get('expected_impact', '')
                    timeline = row.get('timeline', 'Not specified')
                    state = row.get('state', 'N/A')
                    district = row.get('district', '')
                    
                    # Parse action items (could be string or list)
                    action_items_str = row.get('action_items', '')
                    if isinstance(action_items_str, str):
                        action_items = [item.strip() for item in action_items_str.split(';') if item.strip()]
                    else:
                        action_items = action_items_str if isinstance(action_items_str, list) else []
                    
                    # Color based on priority
                    if priority == 'Critical':
                        border_color = '#8B0000'
                        bg_color = '#ffe6e6'
                        priority_icon = '🔴'
                    elif priority == 'High':
                        border_color = '#d62728'
                        bg_color = '#ffe6e6'
                        priority_icon = '🟠'
                    elif priority == 'Medium':
                        border_color = '#ff7f0e'
                        bg_color = '#fff4e6'
                        priority_icon = '🟡'
                    else:
                        border_color = '#2ca02c'
                        bg_color = '#e6ffe6'
                        priority_icon = '🟢'
                    
                    # Build location string
                    location = state if state != 'N/A' and pd.notna(state) else 'National'
                    if district and pd.notna(district):
                        location = f"{district}, {location}"
                    
                    # Build action items HTML
                    action_items_html = ""
                    if action_items:
                        action_items_html = "<ul style='margin-top: 0.5rem; margin-bottom: 0.5rem; color: #333;'>"
                        for item in action_items[:5]:  # Limit to 5 items for display
                            action_items_html += f"<li style='margin-bottom: 0.25rem; color: #333;'>{item}</li>"
                        if len(action_items) > 5:
                            action_items_html += f"<li style='color: #666;'><em>... and {len(action_items) - 5} more</em></li>"
                        action_items_html += "</ul>"
                    
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 1.5rem; border-left: 5px solid {border_color}; border-radius: 0.5rem; margin: 1.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: #333;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                            <h3 style="color: {border_color}; margin-top: 0; margin-bottom: 0.5rem;">
                                {priority_icon} {title}
                            </h3>
                            <span style="background-color: {border_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.85rem; font-weight: bold;">
                                {priority}
                            </span>
                        </div>
                        <div style="margin-bottom: 0.75rem; color: #333;">
                            <strong style="color: #555;">Type:</strong> <span style="color: #333;">{insight_type}</span> | 
                            <strong style="color: #555;">Location:</strong> <span style="color: #333;">{location}</span> | 
                            <strong style="color: #555;">Timeline:</strong> <span style="color: #333;">{timeline}</span>
                        </div>
                        {f'<div style="margin-bottom: 0.75rem; color: #333;"><strong style="color: #555;">Rationale:</strong> <span style="color: #333;">{rationale}</span></div>' if rationale else ''}
                        {f'<div style="margin-bottom: 0.75rem; color: #333;"><strong style="color: #555;">Expected Impact:</strong> <span style="color: #333;">{expected_impact}</span></div>' if expected_impact else ''}
                        {f'<div style="margin-bottom: 0; color: #333;"><strong style="color: #555;">Action Items:</strong>{action_items_html}</div>' if action_items_html else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Insights table
                st.markdown("---")
                with st.expander("📋 View All Insights in Table Format"):
                    display_cols = ['insight_id', 'insight_type', 'title', 'priority', 'impact', 'state', 'district', 'timeline']
                    available_cols = [col for col in display_cols if col in filtered_insights.columns]
                    display_df = filtered_insights[available_cols].copy()
                    
                    # Format display
                    if 'insight_type' in display_df.columns:
                        display_df['insight_type'] = display_df['insight_type'].str.replace('_', ' ').str.title()
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No insights match the selected filters.")
        else:
            st.info("⚠️ Actionable insights data not available. Please run `insights_generator.py` to generate actionable insights.")
            st.markdown("""
            **To generate actionable insights:**
            1. Ensure you have run the following modules:
               - `surge_prediction.py` (for surge predictions)
               - `advanced_anomaly_detection.py` (for anomaly detection)
               - `forecasting_models.py` (for forecasts)
               - `pattern_learning.py` (for patterns)
               - `district_pincode_models.py` (optional, for district-level insights)
            
            2. Run the insights generator:
            ```bash
            python insights_generator.py
            ```
            
            3. Refresh this dashboard to view the insights.
            """)

    # Tab 12: Forensic Signal Intelligence
    with tab12:
        st.markdown('<div class="tab-description">Forensic-grade detection of statistical anomalies in adult enrollments.</div>', unsafe_allow_html=True)
        
        # Forensic results are calculated on-the-fly, so we export the raw input data here
        # (Detailed forensic reports have their own download button at the bottom of this tab)
        if 'enrolment' in data:
            render_export_button(data['enrolment'], "Forensic_Input_Data", "tab12_export")
        st.header("🕵️ Enrollment Pattern Risk Intelligence (Forensic Signal)")
        
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")

        if not FORENSIC_AVAILABLE:
            st.error("⚠️ Forensic Analysis module (`forensic_analysis.py`) is missing or failed to load.")
        else:
            if 'enrolment' in data and 'biometric' in data and 'demographic' in data:
                # Run Analysis
                with st.spinner("Running forensic algorithms (Temporal, Spatial, Cross-Signal)..."):
                    # Initialize with current data (already filtered by date/state)
                    analyzer = ForensicAnalyzer(data['enrolment'], data['biometric'], data['demographic'])
                    # Run analysis
                    results_df = analyzer.run_analysis()
                    # Get temporal summary
                    temporal_df = analyzer.get_temporal_summary(interval='2M')
                
                if not temporal_df.empty:
                    # --- TEMPORAL FORENSIC MAP ---
                    st.subheader("🗺️ Temporal Forensic Map (2-Month Intervals)")
                    
                    # Date Slider
                    unique_periods = sorted(temporal_df['period'].unique())
                    period_labels = [p.strftime('%b %Y') for p in unique_periods]
                    
                    if len(period_labels) > 0:
                        selected_label = st.select_slider(
                            "Select Time Period",
                            options=period_labels,
                            value=period_labels[-1]
                        )
                        
                        # Find corresponding timestamp
                        selected_idx = period_labels.index(selected_label)
                        selected_period = unique_periods[selected_idx]
                        
                        # Filter data by Period
                        period_data = temporal_df[temporal_df['period'] == selected_period]

                        # --- DRILL-DOWN FILTERS ---
                        f_col1, f_col2, f_col3 = st.columns(3)
                        with f_col1:
                            # State Filter
                            all_states = sorted(period_data['state'].unique().tolist())
                            sel_state = st.selectbox("Filter by State", ["All"] + all_states, key='forensic_state')
                        
                        with f_col2:
                            # District Filter
                            if sel_state != "All":
                                districts = sorted(period_data[period_data['state'] == sel_state]['district'].unique().tolist())
                                sel_dist = st.selectbox("Filter by District", ["All"] + districts, key='forensic_dist')
                            else:
                                sel_dist = st.selectbox("Filter by District", ["All"], disabled=True, key='forensic_dist')
                        
                        with f_col3:
                            # Pincode Filter (Optional search)
                            if sel_dist != "All":
                                pincodes = sorted(period_data[(period_data['state'] == sel_state) & (period_data['district'] == sel_dist)]['pincode'].unique().tolist())
                                sel_pin = st.selectbox("Filter by Pincode", ["All"] + [str(p) for p in pincodes], key='forensic_pin')
                            else:
                                sel_pin = st.selectbox("Filter by Pincode", ["All"], disabled=True, key='forensic_pin')

                        # Apply Filters
                        filtered_view = period_data.copy()
                        if sel_state != "All":
                            filtered_view = filtered_view[filtered_view['state'] == sel_state]
                        if sel_dist != "All":
                            filtered_view = filtered_view[filtered_view['district'] == sel_dist]
                        if sel_pin != "All":
                             filtered_view = filtered_view[filtered_view['pincode'] == int(sel_pin)]

                        # --- MAP VISUALIZATION (State Level) ---
                        # Aggregate to State level for the map (uses filtered view to reflect selection)
                        state_map_data = filtered_view.groupby('state')['risk_score_norm'].mean().reset_index()
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if GEOJSON_HELPER_AVAILABLE:
                                india_geojson = load_india_geojson()
                                if india_geojson:
                                    # Create choropleth
                                    fig_map = px.choropleth(
                                        state_map_data,
                                        geojson=india_geojson,
                                        locations='state',
                                        featureidkey=f"properties.{get_state_name_field(india_geojson)}",
                                        color='risk_score_norm',
                                        color_continuous_scale='Reds',
                                        title=f"Forensic Signal Intensity by State - {selected_label}",
                                        labels={'risk_score_norm': 'Signal Intensity (Avg)'}
                                    )
                                    # Zoom to data bounds (filters)
                                    fig_map.update_geos(fitbounds="locations", visible=False)
                                    fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
                                    st.plotly_chart(fig_map, use_container_width=True)
                                else:
                                    create_marker_fallback_map(state_map_data, 'risk_score_norm', 'Signal Intensity')
                            else:
                                create_marker_fallback_map(state_map_data, 'risk_score_norm', 'Signal Intensity')
                                
                        with col2:
                            st.markdown(f"**{selected_label} Summary**")
                            # Metrics based on FILTERED view
                            total_adults = filtered_view['adult_enrollment'].sum()
                            avg_signal = filtered_view['risk_score_norm'].mean()
                            max_signal = filtered_view['risk_score_norm'].max()
                            loc_count = len(filtered_view)
                            
                            st.metric("Total 18+ Enrollments", f"{int(total_adults):,}", help="Total adult enrollments in selected scope")
                            st.metric("Avg Signal", f"{avg_signal:.1f}")
                            st.metric("Max Signal", f"{max_signal:.1f}")
                            st.metric("Areas Count", f"{loc_count}")
                            
                            st.markdown("---")
                            if sel_state == "All":
                                st.markdown("**Top Risk States**")
                                top_items = state_map_data.nlargest(5, 'risk_score_norm')
                                st.table(top_items.set_index('state')[['risk_score_norm']].style.format("{:.1f}"))
                            elif sel_dist == "All":
                                st.markdown(f"**Top Districts in {sel_state}**")
                                dist_agg = filtered_view.groupby('district')['risk_score_norm'].mean().reset_index()
                                top_items = dist_agg.nlargest(5, 'risk_score_norm')
                                st.table(top_items.set_index('district')[['risk_score_norm']].style.format("{:.1f}"))
                            else:
                                st.markdown(f"**Pincodes in {sel_dist}**")
                                top_items = filtered_view.nlargest(5, 'risk_score_norm')
                                st.table(top_items.set_index('pincode')[['risk_score_norm']].style.format("{:.1f}"))

                        # --- HIERARCHICAL AREA MAP (Treemap) ---
                        st.subheader(f"🏘️ Area Implementation Analysis")
                        st.caption("Hierarchical breakdown: State → District → Pincode (Size = Enrollment Volume, Color = Signal Intensity)")
                        
                        # Path for Treemap
                        path_cols = ['state', 'district']
                        if 'pincode' in filtered_view.columns:
                            # Convert pincode to string for categorical plotting
                            filtered_view['pincode_str'] = filtered_view['pincode'].astype(str)
                            path_cols.append('pincode_str')
                        
                        # For Treemap, we need positive values for size. Use total_enrollment or 1 if 0.
                        filtered_view['display_size'] = filtered_view['total_enrollment'].clip(lower=1)
                        
                        fig_tree = px.treemap(
                            filtered_view,
                            path=path_cols,
                            values='display_size',
                            color='risk_score_norm',
                            color_continuous_scale='Reds',
                            hover_data=['adult_enrollment', 'algo1_score', 'algo5_score'],
                            title=f"Signal Intensity Distribution: {sel_state if sel_state != 'All' else 'All States'}"
                        )
                        fig_tree.update_layout(height=500)
                        st.plotly_chart(fig_tree, use_container_width=True)

                        # --- DETAILED LOCATION ANALYSIS ---
                        st.subheader(f"📍 Detailed Forensic Data ({selected_label})")
                        
                        display_cols = ['state', 'district', 'adult_enrollment', 'risk_score_norm', 
                                       'algo1_score', 'algo2_score', 'algo5_score']
                        if 'pincode' in filtered_view.columns:
                            display_cols.insert(2, 'pincode')
                            
                        detailed_view = filtered_view[display_cols].sort_values('risk_score_norm', ascending=False)
                        
                        # Rename columns for display (Safe Language)
                        detailed_view_display = detailed_view.rename(columns={
                            'risk_score_norm': 'Signal Intensity',
                            'adult_enrollment': 'Enrollment Vol',
                            'algo1_score': 'Temporal Dev',
                            'algo2_score': 'Spatial Anom',
                            'algo5_score': 'Demographic Ratio'
                        })
                        
                        st.dataframe(
                            detailed_view_display.head(1000).style.background_gradient(subset=['Signal Intensity'], cmap='Reds'),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        csv_period = detailed_view_display.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            f"Download Report ({selected_label})",
                            csv_period,
                            f"forensic_report_{selected_label.replace(' ', '_')}.csv",
                            "text/csv",
                            key=f'dl_{selected_idx}'
                        )
                    else:
                        st.warning("Not enough data to generate timeline.")

                    st.markdown("---")
                    
                    # --- ALGORITHM BREAKDOWN (Aggregated) ---
                    st.subheader("Algorithm Contribution (All Time)")
                    with st.expander("View Algorithm Performance Stats"):
                        avg_scores = {
                            'Temporal Deviation': results_df['algo1_score'].mean(),
                            'Spatial Anomaly': results_df['algo2_score'].mean(),
                            'Forecast Violation': results_df['algo3_score'].mean(),
                            'Cross-Signal Integrity': results_df['algo4_score'].mean(),
                            'Demographic Ratio': results_df['algo5_score'].mean()
                        }
                        
                        fig = px.bar(
                            x=list(avg_scores.values()),
                            y=list(avg_scores.keys()),
                            orientation='h',
                            labels={'x': 'Avg Contribution', 'y': 'Algorithm'},
                            title="Average Signal Contribution by Algorithm"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("No data available for analysis.")
            else:
                st.warning("Granular data (enrolment, biometric, demographic) not available for forensic analysis.")

def create_marker_fallback_map(state_map_data, map_metric_col, map_metric_choice):
    """Fallback marker-based map when GeoJSON is not available"""
    # Add coordinates for each state
    state_map_data['lat'] = state_map_data['state'].apply(lambda x: get_state_coordinates(x)[0])
    state_map_data['lon'] = state_map_data['state'].apply(lambda x: get_state_coordinates(x)[1])
    
    # Create Indian map with state markers
    fig_map = go.Figure()
    
    # Add state markers with colors based on metric value
    fig_map.add_trace(go.Scattergeo(
        lat=state_map_data['lat'],
        lon=state_map_data['lon'],
        text=state_map_data['state'],
        mode='markers+text',
        marker=dict(
            size=state_map_data[map_metric_col] / state_map_data[map_metric_col].max() * 60 + 15,
            color=state_map_data[map_metric_col],
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(
                title=dict(text=map_metric_choice, font=dict(size=14)),
                len=0.7,
                thickness=20,
                x=1.02
            ),
            line=dict(width=2, color='darkgray'),
            opacity=0.8,
            sizemode='diameter'
        ),
        name=map_metric_choice,
        textfont=dict(size=10, color='black', family='Arial Black'),
        textposition='middle center',
        hovertemplate='<b>%{text}</b><br>' + 
                     map_metric_choice + ': %{marker.color:,.0f}<extra></extra>',
    ))
    
    # Configure map for India
    fig_map.update_geos(
        center=dict(lon=78.9629, lat=20.5937),
        projection_scale=4.8,
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor='black',
        countrywidth=2,
        showcoastlines=True,
        coastlinecolor='darkblue',
        coastlinewidth=1.5,
        showland=True,
        landcolor='lightgray',
        showocean=True,
        oceancolor='lightblue',
        lonaxis_range=[68, 97],
        lataxis_range=[6, 37],
        bgcolor='white'
    )
    
    fig_map.update_layout(
        title=dict(
            text=f"🗺️ Indian States Visualization: {map_metric_choice}",
            font=dict(size=20, color='darkblue'),
            x=0.5
        ),
        height=750,
        geo=dict(bgcolor='rgba(0,0,0,0)', subunitwidth=1, showframe=False),
        margin=dict(l=0, r=0, t=60, b=0)
    )
    
    st.plotly_chart(fig_map, use_container_width=True)


if __name__ == "__main__":
    main()

display_chatbot()