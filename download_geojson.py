"""
Script to download Indian states GeoJSON file
Run this script to download the GeoJSON file needed for proper choropleth maps
"""

from india_geojson_helper import download_india_geojson

if __name__ == "__main__":
    print("Downloading Indian states GeoJSON file...")
    print("=" * 60)
    
    if download_india_geojson('india_states.geojson'):
        print("\n✅ Success! GeoJSON file downloaded as 'india_states.geojson'")
        print("The dashboard will now use proper choropleth maps with state boundaries.")
    else:
        print("\n❌ Failed to download GeoJSON file.")
        print("\nYou can manually download from:")
        print("1. https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson")
        print("2. https://github.com/Subhash9325/GeoJson-Data-of-Indian-States")
        print("\nSave it as 'india_states.geojson' in the project directory.")
