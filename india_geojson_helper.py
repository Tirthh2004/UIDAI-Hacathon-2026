"""
Helper functions for Indian States GeoJSON
Downloads and loads GeoJSON data for Indian states boundaries
"""

import json
import urllib.request
from pathlib import Path


def download_india_geojson(save_path='india_states.geojson'):
    """
    Download Indian states GeoJSON from GitHub
    Returns True if successful, False otherwise
    """
    urls = [
        'https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson',
        'https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States.json',
    ]
    
    for url in urls:
        try:
            print(f"Attempting to download from: {url}")
            with urllib.request.urlopen(url, timeout=10) as response:
                data = response.read()
                with open(save_path, 'wb') as f:
                    f.write(data)
            print(f"Successfully downloaded GeoJSON to {save_path}")
            return True
        except Exception as e:
            print(f"Failed to download from {url}: {e}")
            continue
    
    return False


def load_india_geojson(file_path='india_states.geojson'):
    """
    Load Indian states GeoJSON file
    Returns GeoJSON dict if successful, None otherwise
    """
    geojson_path = Path(file_path)
    
    if not geojson_path.exists():
        # Try to download
        print(f"GeoJSON file not found. Attempting to download...")
        if download_india_geojson(file_path):
            geojson_path = Path(file_path)
        else:
            return None
    
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        return geojson_data
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return None


def get_state_name_field(geojson_data):
    """
    Detect the state name field in GeoJSON properties
    Returns the field name if found, None otherwise
    """
    if not geojson_data or 'features' not in geojson_data:
        return None
    
    if len(geojson_data['features']) == 0:
        return None
    
    # Check first feature properties
    first_feature = geojson_data['features'][0]
    properties = first_feature.get('properties', {})
    
    # Common field names for state names
    possible_fields = ['ST_NM', 'st_nm', 'NAME_1', 'name', 'NAME', 'STATE', 'state', 'State']
    
    for field in possible_fields:
        if field in properties:
            return field
    
    return None


def create_state_name_mapping(geojson_data, state_name_field):
    """
    Create a mapping from GeoJSON state names to our data state names
    """
    mapping = {}
    
    if not geojson_data or 'features' not in geojson_data:
        return mapping
    
    for feature in geojson_data['features']:
        props = feature.get('properties', {})
        geojson_name = props.get(state_name_field, '')
        
        # Create variations for matching
        variations = [
            geojson_name,
            geojson_name.title(),
            geojson_name.upper(),
            geojson_name.lower()
        ]
        
        for variation in variations:
            mapping[variation] = geojson_name
    
    return mapping
