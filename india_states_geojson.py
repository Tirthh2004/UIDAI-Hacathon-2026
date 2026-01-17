"""
Indian States GeoJSON Data
Coordinates and boundaries for Indian states for map visualizations
"""

# Simplified state center coordinates (latitude, longitude) for Indian states
INDIA_STATE_COORDINATES = {
    'Andhra Pradesh': (15.9129, 79.7400),
    'Arunachal Pradesh': (28.2180, 94.7278),
    'Assam': (26.2006, 92.9376),
    'Bihar': (25.0961, 85.3131),
    'Chhattisgarh': (21.2787, 81.8661),
    'Goa': (15.2993, 74.1240),
    'Gujarat': (23.0225, 72.5714),
    'Haryana': (29.0588, 76.0856),
    'Himachal Pradesh': (31.1048, 77.1734),
    'Jammu And Kashmir': (34.0837, 74.7973),
    'Jharkhand': (23.6102, 85.2799),
    'Karnataka': (15.3173, 75.7139),
    'Kerala': (10.8505, 76.2711),
    'Madhya Pradesh': (22.9734, 78.6569),
    'Maharashtra': (19.7515, 75.7139),
    'Manipur': (24.6637, 93.9063),
    'Meghalaya': (25.4670, 91.3662),
    'Mizoram': (23.1645, 92.9376),
    'Nagaland': (26.1584, 94.5624),
    'Odisha': (20.9517, 85.0985),
    'Punjab': (31.1471, 75.3412),
    'Rajasthan': (27.0238, 74.2179),
    'Sikkim': (27.5330, 88.5122),
    'Tamil Nadu': (11.1271, 78.6569),
    'Telangana': (18.1124, 79.0193),
    'Tripura': (23.9408, 91.9882),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Uttarakhand': (30.0668, 79.0193),
    'West Bengal': (22.9868, 87.8550),
    'Delhi': (28.6139, 77.2090),
    'Puducherry': (11.9416, 79.8083),
    'Ladakh': (34.1526, 77.5770),
    'Andaman And Nicobar Islands': (11.7401, 92.6586),
    'Dadra And Nagar Haveli And Daman And Diu': (20.1809, 73.0169),
    'Lakshadweep': (10.5667, 72.6417),
    'Chandigarh': (30.7333, 76.7794)
}

# State name mappings (to handle variations in data)
STATE_NAME_MAPPING = {
    'Jammu and Kashmir': 'Jammu And Kashmir',
    'Jammu And Kashmir': 'Jammu And Kashmir',
    'Andaman and Nicobar Islands': 'Andaman And Nicobar Islands',
    'Andaman And Nicobar Islands': 'Andaman And Nicobar Islands',
    'Dadra and Nagar Haveli': 'Dadra And Nagar Haveli And Daman And Diu',
    'Daman and Diu': 'Dadra And Nagar Haveli And Daman And Diu',
    'Dadra And Nagar Haveli And Daman And Diu': 'Dadra And Nagar Haveli And Daman And Diu'
}


def get_state_coordinates(state_name):
    """Get coordinates for a state name (with fuzzy matching)"""
    # Try exact match first
    if state_name in INDIA_STATE_COORDINATES:
        return INDIA_STATE_COORDINATES[state_name]
    
    # Try mapping
    mapped_name = STATE_NAME_MAPPING.get(state_name, state_name)
    if mapped_name in INDIA_STATE_COORDINATES:
        return INDIA_STATE_COORDINATES[mapped_name]
    
    # Try case-insensitive match
    for key, coords in INDIA_STATE_COORDINATES.items():
        if key.lower() == state_name.lower():
            return coords
    
    # Default to center of India if not found
    return (20.5937, 78.9629)
