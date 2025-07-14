#!/usr/bin/env python3
"""
Example script showing how to recreate the Hartford Heat Vulnerability Map
using the extracted census tract data.
"""

import json
import folium
from typing import Dict, Any

def load_extracted_data(json_file: str) -> Dict[str, Any]:
    """Load the extracted census tract data."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_hartford_map(data: Dict[str, Any]) -> folium.Map:
    """Create the Hartford Heat Vulnerability map using extracted data."""
    
    # Initialize map with extracted configuration
    map_config = data['map_config']
    m = folium.Map(
        location=map_config['center'],
        zoom_start=map_config['zoom'],
        tiles=map_config['base_map_url'],
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    )
    
    # Add census tracts
    for tract in data['census_tracts']:
        add_census_tract(m, tract)
    
    # Add legend
    add_legend(m, data['color_scheme'])
    
    # Add title
    add_title(m)
    
    return m

def add_census_tract(map_obj: folium.Map, tract: Dict[str, Any]) -> None:
    """Add a single census tract to the map."""
    
    if not tract['geojson'] or 'features' not in tract['geojson']:
        return
    
    # Extract styling
    style = tract['style']
    
    # Create GeoJSON layer
    geojson_layer = folium.GeoJson(
        tract['geojson'],
        style_function=lambda feature, style=style: {
            'fillColor': style['fill_color'],
            'color': style['stroke_color'],
            'weight': style['weight'],
            'fillOpacity': style['fill_opacity'],
            'opacity': style['opacity']
        }
    )
    
    # Add tooltip
    tooltip_text = f"Tract {tract['tract_id']}: Level {tract['vulnerability_level']} Risk"
    geojson_layer.add_child(folium.Tooltip(tooltip_text, sticky=True))
    
    # Add popup with detailed information
    if tract['popup_data']:
        popup_html = create_popup_html(tract['tract_id'], tract['popup_data'], tract['vulnerability_level'])
        geojson_layer.add_child(folium.Popup(popup_html, max_width=400))
    
    # Add to map
    geojson_layer.add_to(map_obj)

def create_popup_html(tract_id: str, popup_data: Dict[str, Any], level: int) -> str:
    """Create HTML content for tract popup."""
    
    level_colors = {
        1: '#2E8B57',
        2: '#90EE90', 
        3: '#FFFF00',
        4: '#FFA500',
        5: '#FF4500'
    }
    
    color = level_colors.get(level, '#CCCCCC')
    
    html = f"""
    <div style="width: 300px;">
        <h4 style="margin-bottom: 10px; color: #333;">Census Tract {tract_id}</h4>
        <hr style="margin: 5px 0;">
        <table style="width: 100%; font-size: 12px;">
            <tr><td><b>Vulnerability Level:</b></td><td style="color: {color}; font-weight: bold;">Level {level}</td></tr>
            <tr><td><b>Population:</b></td><td>{popup_data.get('population', 'N/A')}</td></tr>
            <tr><td><b>Median Income:</b></td><td>{popup_data.get('median_income', 'N/A')}</td></tr>
            <tr><td><b>Temperature:</b></td><td>{popup_data.get('temperature', 'N/A')}</td></tr>
            <tr><td><b>AC Access:</b></td><td>{popup_data.get('ac_access', 'N/A')}</td></tr>
            <tr><td><b>Green Space:</b></td><td>{popup_data.get('green_space', 'N/A')}</td></tr>
            <tr><td><b>Vulnerability Score:</b></td><td>{popup_data.get('vulnerability_score', 'N/A')}</td></tr>
        </table>
    </div>
    """
    return html

def add_legend(map_obj: folium.Map, color_scheme: Dict[str, Any]) -> None:
    """Add legend to the map."""
    
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0; color: #333;">Heat Vulnerability Level</h4>
    """
    
    for level_key, level_data in color_scheme['levels'].items():
        color = level_data['color']
        name = level_data['name']
        legend_html += f'<p style="margin: 5px 0; color: {color};"><i class="fa fa-square" style="color: {color};"></i> {name}</p>'
    
    legend_html += "</div>"
    
    map_obj.get_root().html.add_child(folium.Element(legend_html))

def add_title(map_obj: folium.Map) -> None:
    """Add title to the map."""
    
    title_html = """
    <div style="position: fixed; 
                top: 10px; left: 50%; transform: translateX(-50%); 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 16px; padding: 10px; text-align: center;">
        <h3 style="margin: 0; color: #333;">Hartford Heat Vulnerability Index - July 2024</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Interactive map showing heat vulnerability by census tract</p>
    </div>
    """
    
    map_obj.get_root().html.add_child(folium.Element(title_html))

def main():
    """Main function to recreate the map."""
    
    # Load extracted data
    data_file = '/home/jguo/projects/DS/hartford_census_tract_data.json'
    print("Loading extracted census tract data...")
    data = load_extracted_data(data_file)
    
    # Create map
    print(f"Creating map with {len(data['census_tracts'])} census tracts...")
    m = create_hartford_map(data)
    
    # Save map
    output_file = '/home/jguo/projects/DS/recreated_hartford_map.html'
    m.save(output_file)
    
    print(f"Map saved to: {output_file}")
    print("\nMap recreation complete!")
    print("The recreated map should be identical to the original with:")
    print(f"- {data['total_tracts']} census tracts")
    print("- 5 vulnerability levels with correct colors")
    print("- Interactive tooltips and popups")
    print("- Legend and title")

if __name__ == '__main__':
    main()