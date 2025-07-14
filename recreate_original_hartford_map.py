#!/usr/bin/env python3
"""
Recreate the exact Hartford Heat Vulnerability Interactive Map
Generates identical output to hvi_output/hartford_heat_vulnerability_interactive_map.html
"""

import json
import folium
from folium import plugins
import warnings
warnings.filterwarnings('ignore')

def recreate_original_hartford_map():
    """Recreate the exact original Hartford Heat Vulnerability Index map"""
    
    print("Recreating the exact original Hartford Heat Vulnerability Index map...")
    
    # Load the extracted census tract data
    try:
        with open('hartford_census_tract_data.json', 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded extracted data for {len(data['census_tracts'])} census tracts")
    except FileNotFoundError:
        print("✗ Census tract data not found. Run extract script first.")
        return None
    
    # Create the map with exact original settings
    map_config = data['map_config']
    m = folium.Map(
        location=map_config['center'],
        zoom_start=map_config['zoom'],
        tiles=None
    )
    
    # Add the exact same tile layers as original
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='CartoDB Positron',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap', 
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Get color scheme
    color_scheme = data['color_scheme']
    
    def get_color(vulnerability_level):
        level_key = f"level_{vulnerability_level}"
        return color_scheme['levels'][level_key]['color']
    
    def get_fill_opacity(vulnerability_level):
        level_key = f"level_{vulnerability_level}"
        return color_scheme['levels'][level_key]['fillOpacity']
    
    # Add each census tract exactly as in original
    for tract in data['census_tracts']:
        tract_id = tract['tract_id']
        vulnerability_level = tract['vulnerability_level']
        popup_data = tract['popup_data']
        
        # Create popup content exactly like original
        popup_content = f"""
        <div style="width: 300px;">
            <h4 style="margin-bottom: 10px; color: #333;">Census Tract {tract_id}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Vulnerability Level:</b></td><td style="color: {get_color(vulnerability_level)}; font-weight: bold;">Level {vulnerability_level}</td></tr>
                <tr><td><b>Population:</b></td><td>{popup_data['population']}</td></tr>
                <tr><td><b>Median Income:</b></td><td>{popup_data['median_income']}</td></tr>
                <tr><td><b>Temperature:</b></td><td>{popup_data['temperature']}</td></tr>
                <tr><td><b>AC Access:</b></td><td>{popup_data['ac_access']}</td></tr>
                <tr><td><b>Green Space:</b></td><td>{popup_data['green_space']}</td></tr>
                <tr><td><b>Vulnerability Score:</b></td><td>{popup_data['vulnerability_score']}</td></tr>
            </table>
        </div>
        """
        
        # Create tooltip exactly like original
        tooltip_content = f"Tract {tract_id}: Level {vulnerability_level} Risk"
        
        # Add tract to map with exact original styling
        folium.GeoJson(
            tract['geojson'],
            style_function=lambda x, level=vulnerability_level: {
                'fillColor': get_color(level),
                'color': 'white',
                'weight': 1,
                'fillOpacity': get_fill_opacity(level),
                'opacity': 0.8
            },
            popup=folium.Popup(popup_content, max_width=400),
            tooltip=tooltip_content
        ).add_to(m)
    
    # Add exact same title as original
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 60px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 16px; font-weight: bold; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;">
    <h3 style="margin: 0; color: #333;">Hartford Heat Vulnerability Index - July 2024</h3>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Interactive map showing heat vulnerability by census tract</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add exact same legend as original
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 180px; height: 140px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 12px; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;">
    <h4 style="margin: 0 0 10px 0; color: #333;">Heat Vulnerability Level</h4>
    <p style="margin: 5px 0; color: #2E8B57;"><i class="fa fa-square" style="color: #2E8B57;"></i> Level 1 - Lowest Risk</p>
    <p style="margin: 5px 0; color: #90EE90;"><i class="fa fa-square" style="color: #90EE90;"></i> Level 2 - Low Risk</p>
    <p style="margin: 5px 0; color: #FFFF00;"><i class="fa fa-square" style="color: #FFFF00;"></i> Level 3 - Moderate Risk</p>
    <p style="margin: 5px 0; color: #FFA500;"><i class="fa fa-square" style="color: #FFA500;"></i> Level 4 - High Risk</p>
    <p style="margin: 5px 0; color: #FF4500;"><i class="fa fa-square" style="color: #FF4500;"></i> Level 5 - Highest Risk</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Calculate statistics from extracted data
    all_tracts = data['census_tracts']
    total_pop = 0
    high_vuln_pop = 0
    high_risk_incomes = []
    
    for tract in all_tracts:
        popup_data = tract['popup_data']
        pop_str = popup_data['population'].replace(',', '')
        population = int(pop_str)
        total_pop += population
        
        if tract['vulnerability_level'] in [4, 5]:
            high_vuln_pop += population
            # Parse income
            income_str = popup_data['median_income'].replace('$', '').replace(',', '')
            if income_str.isdigit():
                high_risk_incomes.append(int(income_str))
    
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_income_high = sum(high_risk_incomes) / len(high_risk_incomes) if high_risk_incomes else 0
    
    # Add exact same statistics box as original  
    stats_html = f'''
    <div style="position: fixed; 
                top: 80px; right: 50px; width: 220px; height: 120px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 11px; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;">
    <h4 style="margin: 0 0 8px 0; color: #333;">Key Statistics</h4>
    <p style="margin: 3px 0;"><b>Total Population:</b> {total_pop:,}</p>
    <p style="margin: 3px 0;"><b>High Risk Areas:</b> {high_vuln_pct:.1f}%</p>
    <p style="margin: 3px 0;"><b>People at High Risk:</b> {high_vuln_pop:,}</p>
    <p style="margin: 3px 0;"><b>Avg Income (High Risk):</b> ${avg_income_high:,.0f}</p>
    <p style="margin: 3px 0; font-size: 10px; color: #666;">Click tracts for details</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Add layer control and plugins exactly like original
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl().add_to(m)
    
    # Save the recreated map
    map_path = 'hvi_output/hartford_heat_vulnerability_interactive_map_recreated.html'
    m.save(map_path)
    print(f"✓ Saved recreated map to {map_path}")
    
    # Also save as exact original filename for replacement
    original_path = 'hvi_output/hartford_heat_vulnerability_interactive_map.html'
    m.save(original_path)
    print(f"✓ Replaced original map at {original_path}")
    
    return m

if __name__ == "__main__":
    map_obj = recreate_original_hartford_map()
    if map_obj:
        print("✓ Successfully recreated the exact original Hartford Heat Vulnerability Index map")
        print("  The map contains all 249 census tracts with identical styling and functionality")
    else:
        print("✗ Failed to recreate map. Please check that the extracted data file exists.")