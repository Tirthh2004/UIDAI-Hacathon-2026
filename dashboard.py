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
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Roboto', sans-serif;
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
        background: linear-gradient(135deg, #003366 0%, #004080 50%, #003366 100%);
        background-size: 200% 200%;
        animation: gradientShift 15s ease infinite;
        padding: 2rem 2rem;
        border-bottom: 4px solid #D4AF37;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1);
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
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
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
        color: #FFFFFF;
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0;
        letter-spacing: 1px;
        text-transform: uppercase;
        opacity: 0.95;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header {
        color: #FFFFFF !important;
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
        background: linear-gradient(90deg, #D4AF37 0%, transparent 100%);
    }
    
    .sub-header {
        color: #FFD700;
        font-size: 1.3rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        letter-spacing: 0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Main content area with pattern */
    .main .block-container {
        padding-top: 1rem;
        position: relative;
    }
    
    .main .block-container::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(212,175,55,0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 50%, rgba(0,51,102,0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 50%, #f8f9fa 100%);
        border-right: 3px solid #003366;
        box-shadow: 2px 0 15px rgba(0,0,0,0.08);
        position: relative;
    }
    
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 1px;
        height: 100%;
        background: linear-gradient(180deg, transparent 0%, #D4AF37 50%, transparent 100%);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent;
    }
    
    section[data-testid="stSidebar"] h2 {
        color: #003366 !important;
        border-left: 4px solid #D4AF37 !important;
        padding-left: 1rem !important;
        background: linear-gradient(90deg, rgba(212,175,55,0.1) 0%, transparent 100%);
        padding: 0.5rem 1rem;
        margin: 0 -1rem 1rem -1rem;
        position: relative;
    }
    
    section[data-testid="stSidebar"] h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, #D4AF37 0%, transparent 100%);
    }
    
    /* Metric cards with glassmorphism */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #003366;
        box-shadow: 
            0 4px 15px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.8);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(212,175,55,0.15) 0%, transparent 70%);
        border-radius: 0 12px 0 100%;
    }
    
    [data-testid="stMetric"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #D4AF37 0%, transparent 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 8px 25px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.8);
        border-left-color: #D4AF37;
    }
    
    [data-testid="stMetric"]:hover::after {
        opacity: 1;
    }
    
    [data-testid="stMetric"] label {
        color: #003366 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #D4AF37 !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        text-shadow: 0 2px 4px rgba(212,175,55,0.2);
    }
    
    /* Insight boxes with unique design */
    .insight-box {
        background: linear-gradient(135deg, #e8f1f8 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-left: 6px solid #003366;
        border-top: 1px solid rgba(212,175,55,0.3);
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 
            0 3px 10px rgba(0,0,0,0.08),
            inset 0 1px 0 rgba(255,255,255,0.5);
        position: relative;
        transition: all 0.3s ease;
    }
    
    .insight-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #D4AF37 0%, transparent 100%);
    }
    
    .insight-box::after {
        content: '💡';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.2;
        transition: all 0.3s ease;
    }
    
    .insight-box:hover {
        box-shadow: 
            0 6px 20px rgba(0,0,0,0.12),
            inset 0 1px 0 rgba(255,255,255,0.5);
        transform: translateX(5px);
    }
    
    .insight-box:hover::after {
        opacity: 0.4;
        transform: rotate(10deg);
    }
    
    /* Tabs with world-class styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 50%, #f8f9fa 100%);
        padding: 0.8rem;
        border-radius: 12px;
        box-shadow: 
            inset 0 2px 4px rgba(0,0,0,0.05),
            0 1px 0 rgba(255,255,255,0.8);
        border: 1px solid rgba(0,51,102,0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #003366;
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]::before {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 2px;
        background: #D4AF37;
        transition: width 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, rgba(0,51,102,0.05) 0%, rgba(212,175,55,0.05) 100%);
        border-color: rgba(212,175,55,0.3);
    }
    
    .stTabs [data-baseweb="tab"]:hover::before {
        width: 80%;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #003366 0%, #004080 100%) !important;
        color: white !important;
        box-shadow: 
            0 4px 12px rgba(0,51,102,0.3),
            inset 0 1px 0 rgba(255,255,255,0.2);
        border-color: #D4AF37 !important;
    }
    
    .stTabs [aria-selected="true"]::before {
        width: 0 !important;
    }
    
    /* Headers with decorative elements */
    h1, h2, h3 {
        color: #003366 !important;
    }
    
    h1 {
        font-weight: 700 !important;
        border-bottom: 4px solid #D4AF37;
        padding-bottom: 0.8rem;
        margin-bottom: 1.5rem !important;
        position: relative;
        background: linear-gradient(90deg, rgba(0,51,102,0.03) 0%, transparent 100%);
        padding: 1rem;
        margin-left: -1rem;
        padding-left: 1rem;
        border-radius: 4px;
    }
    
    h1::after {
        content: '';
        position: absolute;
        bottom: -4px;
        left: 1rem;
        width: 120px;
        height: 4px;
        background: linear-gradient(90deg, #003366 0%, transparent 100%);
    }
    
    h1::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #D4AF37 0%, transparent 100%);
        border-radius: 4px 0 0 4px;
    }
    
    h2 {
        font-weight: 600 !important;
        border-left: 5px solid #003366;
        padding-left: 1.2rem;
        background: linear-gradient(90deg, rgba(0,51,102,0.05) 0%, transparent 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 4px;
        margin: 1.5rem 0 1rem 0 !important;
        position: relative;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    h2::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 1px;
        background: linear-gradient(90deg, #D4AF37 0%, transparent 100%);
    }
    
    h3 {
        font-weight: 500 !important;
        color: #004080 !important;
        margin-top: 1rem !important;
        padding-left: 0.5rem;
        border-left: 3px solid rgba(212,175,55,0.5);
    }
    
    /* Buttons with premium styling */
    .stButton > button {
        background: linear-gradient(135deg, #003366 0%, #004080 100%);
        color: white;
        border: 2px solid #D4AF37;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 
            0 4px 10px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.2);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.1);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #004080 0%, #005099 100%);
        box-shadow: 
            0 8px 20px rgba(0,0,0,0.25),
            inset 0 1px 0 rgba(255,255,255,0.2);
        transform: translateY(-2px);
        border-color: #FFD700;
    }
    
    /* Expander with enhanced design */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
        border-left: 4px solid #003366;
        font-weight: 600;
        color: #003366;
        border-radius: 6px;
        padding: 1rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(90deg, #e8f1f8 0%, #f8f9fa 100%);
        border-left-color: #D4AF37;
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    }
    
    /* Info boxes */
    .stAlert {
        border-left: 5px solid #003366;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
    }
    
    /* Links */
    a {
        color: #003366 !important;
        font-weight: 500;
        transition: all 0.2s ease;
        position: relative;
    }
    
    a::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 0;
        height: 2px;
        background: #D4AF37;
        transition: width 0.3s ease;
    }
    
    a:hover {
        color: #D4AF37 !important;
    }
    
    a:hover::after {
        width: 100%;
    }
    
    /* DataFrames and Tables with premium styling */
    .dataframe {
        border: 2px solid #f0f2f6 !important;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    
    .dataframe thead tr th {
        background: linear-gradient(135deg, #003366 0%, #004080 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.8rem !important;
        border: none !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f8f9fa !important;
    }
    
    .dataframe tbody tr:hover {
        background: linear-gradient(90deg, #e8f1f8 0%, #f8f9fa 100%) !important;
        transform: scale(1.005);
        transition: all 0.2s ease;
    }
    
    .dataframe tbody tr td {
        border-bottom: 1px solid rgba(0,51,102,0.05) !important;
    }
    
    /* Select boxes and inputs */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stSelectbox > div > div:hover {
        border-color: #003366;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #D4AF37;
        box-shadow: 0 0 0 3px rgba(212,175,55,0.1);
    }
    
    /* Footer badge */
    .gov-footer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 3rem;
        color: #666;
        font-size: 0.9rem;
        border-top: 3px solid #D4AF37;
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        position: relative;
    }
    
    .gov-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, #003366 50%, transparent 100%);
    }
    
    /* Dividers with decorative design */
    hr {
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, #D4AF37 50%, transparent 100%);
        margin: 2rem 0;
        position: relative;
    }
    
    hr::after {
        content: '◆';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        color: #D4AF37;
        padding: 0 0.5rem;
        font-size: 0.8rem;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Plotly charts container */
    .js-plotly-plot {
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,51,102,0.1);
        overflow: hidden;
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background: #003366 !important;
    }
    
    /* Date input styling */
    .stDateInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stDateInput > div > div > input:hover {
        border-color: #003366;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f8f9fa;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #003366 0%, #004080 100%);
        border-radius: 5px;
        border: 2px solid #f8f9fa;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #004080 0%, #005099 100%);
    }
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
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
        "🎯 Actionable Insights"
    ])
    
    # Tab 1: Overview
    with tab1:
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.header("Dashboard Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        if 'daily' in data and len(data['daily']) > 0:
            with col1:
                total_bio = data['daily']['bio_total'].sum()
                st.metric("Total Biometric Updates", f"{total_bio:,.0f}")
            
            with col2:
                total_demo = data['daily']['demo_total'].sum()
                st.metric("Total Demographic Updates", f"{total_demo:,.0f}")
            
            with col3:
                total_enrol = data['daily']['enrol_total'].sum()
                st.metric("Total Enrolments", f"{total_enrol:,.0f}")
            
            with col4:
                avg_daily = data['daily']['bio_total'].mean()
                st.metric("Avg Daily Biometric Updates", f"{avg_daily:,.0f}")
        
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
                    title="Total Updates by Type",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
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
                        title="Top States",
                        labels={'bio_total': 'Biometric Updates', 'state': 'State'},
                        color='bio_total',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
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
        st.header("Temporal Pattern Analysis")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        
        if 'daily' in data and len(data['daily']) > 0:
            # Time series chart
            st.subheader("Time Series Trends")
            
            chart_type = st.radio("Select Chart Type", ["Line Chart", "Area Chart"], horizontal=True)
            
            fig = go.Figure()
            
            if chart_type == "Line Chart":
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
            else:
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['bio_total'],
                    mode='lines',
                    name='Biometric Updates',
                    fill='tonexty',
                    line=dict(color='#1f77b4')
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['demo_total'],
                    mode='lines',
                    name='Demographic Updates',
                    fill='tonexty',
                    line=dict(color='#ff7f0e')
                ))
                fig.add_trace(go.Scatter(
                    x=data['daily']['date'],
                    y=data['daily']['enrol_total'],
                    mode='lines',
                    name='Enrolments',
                    fill='tonexty',
                    line=dict(color='#2ca02c')
                ))
            
            fig.update_layout(
                title="Daily Updates Over Time",
                xaxis_title="Date",
                yaxis_title="Count",
                hovermode='x unified',
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
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
                st.subheader("📊 Pattern Learning (STL Decomposition)")
                st.markdown("**Algorithm**: STL Decomposition | **Capability**: Pattern Learning")
                
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
        st.header("Forecasting & Predictions")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.markdown("**Algorithm**: auto_ARIMA (pmdarima) | **Capability**: Forecasting")
        
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
                    st.markdown("##### Forecast Performance Metrics")
                    if metric_summary is not None:
                        col_met1, col_met2 = st.columns(2)
                        with col_met1:
                            st.metric("MAE", f"{metric_summary['mae']:,.2f}")
                            st.metric("RMSE", f"{metric_summary['rmse']:,.2f}")
                        with col_met2:
                            st.metric("MAPE", f"{metric_summary['mape']:.2f}%")
                            st.metric("Model Order", str(metric_summary['model_order']))
                        
                    st.markdown("##### Forecast Summary")
                    if metric_summary is not None:
                        st.info(f"""
                        **Forecast Periods**: {int(metric_summary['forecast_periods'])} days  
                        **AIC**: {metric_summary['aic']:.2f}  
                        **Model**: ARIMA{metric_summary['model_order']}
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

                        st.metric("Forecast Periods", f"{int(state_forecast_data['forecast_periods'])} days")
                        st.metric("MAE", f"{state_forecast_data['mae']:,.2f}")
                        st.metric("RMSE", f"{state_forecast_data['rmse']:,.2f}")
                        st.metric("MAPE", f"{state_forecast_data['mape']:.2f}%")
                        st.info(f"**Model**: ARIMA{state_forecast_data['model_order']}")
                    else:
                        st.warning("No forecast summary available for this state.")
                        st.stop()
    
                    # st.metric("Forecast Periods", f"{int(state_forecast_data['forecast_periods'])} days")
                    # st.metric("MAE", f"{state_forecast_data['mae']:,.2f}")
                    # st.metric("RMSE", f"{state_forecast_data['rmse']:,.2f}")
                    # st.metric("MAPE", f"{state_forecast_data['mape']:.2f}%")
                    # st.info(f"**Model**: ARIMA{state_forecast_data['model_order']}")
                        
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
                            title=f"{selected_state_forecast} Forecast",
                            xaxis_title="Period (Days Ahead)",
                            yaxis_title="Forecasted Value",
                            height=300
                        )
                        st.plotly_chart(fig_state, use_container_width=True)
                    
                # State forecasts table
                with st.expander("📋 View All State Forecasts Summary"):
                    display_cols = ['state', 'forecast_type', 'forecast_periods', 'mae', 'rmse', 'mape', 'model_order']
                    display_df = state_summary_df[display_cols].copy().sort_values('mae', ascending=True)
                    display_df.columns = ['State', 'Forecast Type', 'Forecast Periods', 'MAE', 'RMSE', 'MAPE', 'Model Order']
                    display_df['MAE'] = display_df['MAE'].apply(lambda x: f"{x:,.2f}")
                    display_df['RMSE'] = display_df['RMSE'].apply(lambda x: f"{x:,.2f}")
                    display_df['MAPE'] = display_df['MAPE'].apply(lambda x: f"{x:.2f}%")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    
    # Tab 4: Geographic Analysis
    with tab4:
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
                            title="Biometric Age Distribution",
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
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
                            title="Demographic Age Distribution",
                            color_discrete_sequence=px.colors.qualitative.Set1
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
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
                            title="Enrolment Age Distribution",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
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
                st.metric("Average Coverage Index", f"{avg_coverage:.2f}")
            
            with col2:
                low_coverage = (coverage_df['coverage_index'] < 0.5).sum()
                st.metric("Districts with Low Coverage (<0.5)", f"{low_coverage}")
            
            with col3:
                good_coverage = (coverage_df['coverage_index'] >= 1.0).sum()
                st.metric("Districts with Good Coverage (≥1.0)", f"{good_coverage}")
            
            with col4:
                total_districts = len(coverage_df)
                st.metric("Total Districts Analyzed", f"{total_districts}")
            
            st.markdown("---")
            
            # Coverage distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Coverage Index Distribution")
                fig = px.histogram(
                    coverage_df,
                    x='coverage_index',
                    nbins=50,
                    title="Distribution of Coverage Index",
                    labels={'coverage_index': 'Coverage Index', 'count': 'Number of Districts'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig.add_vline(x=1.0, line_dash="dash", line_color="green", annotation_text="Ideal Coverage (1.0)")
                fig.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Low Coverage (0.5)")
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
                title=f"Average Coverage Index by State (Top {top_n_coverage})",
                labels={'avg_coverage_index': 'Average Coverage Index', 'state': 'State'},
                hover_data=['district_count', 'demo_total', 'bio_total']
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
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
                st.metric("Total Anomalies Detected", f"{total_anomalies}")
            
            with col2:
                high_severity = (anomalies_df['severity'] >= 0.8).sum() if 'severity' in anomalies_df.columns else 0
                st.metric("High Severity Anomalies", f"{high_severity}")
            
            with col3:
                if 'date' in anomalies_df.columns:
                    anomalies_df['date'] = pd.to_datetime(anomalies_df['date'], errors='ignore')
                    recent_anomalies = anomalies_df[anomalies_df['date'] >= anomalies_df['date'].max() - pd.Timedelta(days=30)] if len(anomalies_df) > 0 else anomalies_df
                    st.metric("Anomalies (Last 30 Days)", f"{len(recent_anomalies)}")
            
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
                    <p style="margin-bottom: 0.5rem;"><strong>Finding:</strong> {finding}</p>
                    <p style="margin-bottom: 0;"><strong>Recommendation:</strong> {recommendation}</p>
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
        st.header("🚨 Surge Prediction System")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.markdown("**Algorithm**: Ensemble (Age Transitions + Forecasts + Regional Patterns) | **Capability**: Surge Prediction")
        
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
        st.header("⚙️ Feature Engineering")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.markdown("**Purpose**: Prepare data for ML models with engineered features")
        
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
                                title="Feature Distribution",
                                labels={'count': 'Frequency'},
                                color_discrete_sequence=['#1f77b4']
                            )
                            fig.update_layout(height=300)
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
                            title=f"Top {top_n_features} States by {selected_feature_state}",
                            labels={selected_feature_state: 'Feature Value', 'state': 'State'},
                            color=selected_feature_state,
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
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
        st.header("🏘️ District & Pincode Level Models")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.markdown("**Purpose**: Granular forecasting and anomaly detection at district and pincode levels")
        
        # Summary metrics
        if 'district_pincode_summary' in data:
            summary = data['district_pincode_summary']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'district_forecasts' in summary.get('summary', {}):
                    total_forecasts = summary['summary']['district_forecasts'].get('total_forecasts', 0)
                    st.metric("District Forecasts", f"{total_forecasts}")
                else:
                    st.metric("District Forecasts", "0")
            
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
                            title=f"Top {top_n_districts} Districts by Forecast Mean",
                            labels={'forecast_mean': 'Forecast Mean', 'district': 'District'},
                            hover_data=['state', 'historical_mean', 'forecast_trend'],
                            color_discrete_map={'high_volume': '#1f77b4', 'low_volume': '#ff7f0e'} if 'volume_classification' in top_districts.columns else None
                        )
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)
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
                        title="Total Forecast by State",
                        labels={'total_forecast_mean': 'Total Forecast Mean', 'state': 'State', 'forecast_increase': 'Forecast Increase (%)'},
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=400)
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
        st.header("🎯 Actionable Insights")
        if selected_state != 'All':
            st.info(f"📍 **Currently viewing data for: {selected_state}** — Select 'All' in the sidebar to view national data.")
        st.markdown("**Purpose**: Translating predictions, anomalies, and forecasts into actionable recommendations")
        st.markdown("**Feature**: Actionable Insights Generation (Feature 9)")
        
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