import json

try:
    with open('india_states.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total features: {len(data['features'])}")
    
    state_names = []
    for feature in data['features']:
        props = feature['properties']
        # Try to find name field
        name = props.get('NAME_1') or props.get('ST_NM') or props.get('name') or props.get('Name')
        if name:
            state_names.append(name)
            
    print("State names found in GeoJSON:")
    for name in sorted(state_names):
        print(f"  - '{name}'")
        
except Exception as e:
    print(f"Error: {e}")
