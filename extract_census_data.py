#!/usr/bin/env python3
"""
Extract census tract data from Hartford Heat Vulnerability Interactive Map HTML file.
This script parses the HTML to extract all GeoJSON coordinates, styling, and popup data.
"""

import re
import json
import html
from typing import Dict, List, Any

def extract_census_data(html_file_path: str) -> Dict[str, Any]:
    """Extract all census tract data from the HTML file."""
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract map configuration
    map_config = extract_map_config(content)
    
    # Extract color scheme and vulnerability levels
    color_scheme = extract_color_scheme(content)
    
    # Extract all census tracts
    census_tracts = extract_all_tracts(content)
    
    return {
        'map_config': map_config,
        'color_scheme': color_scheme,
        'census_tracts': census_tracts,
        'total_tracts': len(census_tracts)
    }

def extract_map_config(content: str) -> Dict[str, Any]:
    """Extract map center, zoom level, and other configuration."""
    
    # Extract center coordinates
    center_match = re.search(r'center: \[([^]]+)\]', content)
    center = None
    if center_match:
        coords = center_match.group(1).split(',')
        center = [float(coord.strip()) for coord in coords]
    
    # Extract zoom level
    zoom_match = re.search(r'"zoom": (\d+)', content)
    zoom = int(zoom_match.group(1)) if zoom_match else None
    
    # Extract map settings
    config = {
        'center': center,
        'zoom': zoom,
        'crs': 'EPSG3857',
        'base_map_url': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    }
    
    return config

def extract_color_scheme(content: str) -> Dict[str, Any]:
    """Extract vulnerability levels and their corresponding colors."""
    
    # Define the color scheme based on the legend
    color_scheme = {
        'level_1': {
            'color': '#2E8B57',
            'name': 'Level 1 - Lowest Risk',
            'fillOpacity': 0.6
        },
        'level_2': {
            'color': '#90EE90', 
            'name': 'Level 2 - Low Risk',
            'fillOpacity': 0.7
        },
        'level_3': {
            'color': '#FFFF00',
            'name': 'Level 3 - Moderate Risk', 
            'fillOpacity': 0.8
        },
        'level_4': {
            'color': '#FFA500',
            'name': 'Level 4 - High Risk',
            'fillOpacity': 0.9
        },
        'level_5': {
            'color': '#FF4500',
            'name': 'Level 5 - Highest Risk',
            'fillOpacity': 1.0
        }
    }
    
    # Common styling parameters
    common_style = {
        'stroke_color': 'white',
        'opacity': 0.8,
        'weight': 1
    }
    
    return {
        'levels': color_scheme,
        'common_style': common_style
    }

def extract_all_tracts(content: str) -> List[Dict[str, Any]]:
    """Extract data for all census tracts."""
    
    tracts = []
    
    # Find all geo_json variable declarations
    geo_json_pattern = r'var (geo_json_[a-f0-9]+) = L\.geoJson\(null, \{'
    geo_json_matches = re.finditer(geo_json_pattern, content)
    
    for match in geo_json_matches:
        var_name = match.group(1)
        tract_data = extract_single_tract(content, var_name)
        if tract_data:
            tracts.append(tract_data)
    
    return tracts

def extract_single_tract(content: str, var_name: str) -> Dict[str, Any]:
    """Extract data for a single census tract."""
    
    # Extract styling function
    style_function_pattern = rf'function {var_name}_styler\(feature\) \{{[^}}]+return \{{([^}}]+)\}};[^}}]+\}}'
    style_match = re.search(style_function_pattern, content)
    
    style_data = {}
    if style_match:
        style_str = style_match.group(1)
        # Parse individual style properties
        color_match = re.search(r'"color": "([^"]+)"', style_str)
        fill_color_match = re.search(r'"fillColor": "([^"]+)"', style_str)
        fill_opacity_match = re.search(r'"fillOpacity": ([^,}]+)', style_str)
        opacity_match = re.search(r'"opacity": ([^,}]+)', style_str)
        weight_match = re.search(r'"weight": ([^,}]+)', style_str)
        
        if color_match:
            style_data['stroke_color'] = color_match.group(1)
        if fill_color_match:
            style_data['fill_color'] = fill_color_match.group(1)
        if fill_opacity_match:
            style_data['fill_opacity'] = float(fill_opacity_match.group(1))
        if opacity_match:
            style_data['opacity'] = float(opacity_match.group(1))
        if weight_match:
            style_data['weight'] = int(weight_match.group(1))
    
    # Extract GeoJSON data
    geojson_pattern = f'{var_name}_add\\((.+?)\\);'
    geojson_match = re.search(geojson_pattern, content)
    
    geojson_data = {}
    if geojson_match:
        try:
            geojson_str = geojson_match.group(1)
            geojson_data = json.loads(geojson_str)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse GeoJSON for {var_name}")
    
    # Extract tooltip (tract ID and level)
    tooltip_pattern = rf'{var_name}\.bindTooltip\(\s*`<div>\s*Tract ([^:]+): Level (\d+) Risk\s*</div>`'
    tooltip_match = re.search(tooltip_pattern, content)
    
    tract_id = None
    vulnerability_level = None
    if tooltip_match:
        tract_id = tooltip_match.group(1)
        vulnerability_level = int(tooltip_match.group(2))
    
    # Extract popup data (detailed information)
    if tract_id:
        popup_pattern = f'<h4[^>]*>Census Tract {re.escape(tract_id)}</h4>.*?</table>'
    else:
        popup_pattern = r'<h4[^>]*>Census Tract (\d+)</h4>.*?</table>'
    popup_match = re.search(popup_pattern, content, re.DOTALL)
    
    popup_data = {}
    if popup_match:
        popup_html = popup_match.group(0)
        popup_data = parse_popup_data(popup_html)
    
    # Determine vulnerability level from color if not found in tooltip
    if vulnerability_level is None and style_data.get('fill_color'):
        color_to_level = {
            '#2E8B57': 1,
            '#90EE90': 2, 
            '#FFFF00': 3,
            '#FFA500': 4,
            '#FF4500': 5
        }
        vulnerability_level = color_to_level.get(style_data['fill_color'])
    
    return {
        'variable_name': var_name,
        'tract_id': tract_id,
        'vulnerability_level': vulnerability_level,
        'style': style_data,
        'geojson': geojson_data,
        'popup_data': popup_data
    }

def parse_popup_data(popup_html: str) -> Dict[str, Any]:
    """Parse the popup HTML to extract tract details."""
    
    data = {}
    
    # Extract table rows
    row_patterns = [
        (r'Vulnerability Level:</b></td><td[^>]*>Level (\d+)</td>', 'vulnerability_level'),
        (r'Population:</b></td><td>([^<]+)</td>', 'population'),
        (r'Median Income:</b></td><td>([^<]+)</td>', 'median_income'),
        (r'Temperature:</b></td><td>([^<]+)</td>', 'temperature'),
        (r'AC Access:</b></td><td>([^<]+)</td>', 'ac_access'),
        (r'Green Space:</b></td><td>([^<]+)</td>', 'green_space'),
        (r'Vulnerability Score:</b></td><td>([^<]+)</td>', 'vulnerability_score')
    ]
    
    for pattern, key in row_patterns:
        match = re.search(pattern, popup_html)
        if match:
            value = match.group(1).strip()
            if key == 'vulnerability_level':
                data[key] = int(value)
            elif key == 'population':
                data[key] = value.replace(',', '')
            elif key == 'vulnerability_score':
                data[key] = float(value)
            else:
                data[key] = value
    
    return data

def main():
    """Main function to extract and save census data."""
    
    html_file = '/home/jguo/projects/DS/hvi_output/hartford_heat_vulnerability_interactive_map.html'
    
    print("Extracting census tract data from HTML file...")
    data = extract_census_data(html_file)
    
    print(f"Successfully extracted data for {data['total_tracts']} census tracts")
    
    # Save to JSON file
    output_file = '/home/jguo/projects/DS/hartford_census_tract_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to: {output_file}")
    
    # Print summary
    print("\nMap Configuration:")
    print(f"  Center: {data['map_config']['center']}")
    print(f"  Zoom: {data['map_config']['zoom']}")
    
    print("\nVulnerability Level Distribution:")
    level_counts = {}
    for tract in data['census_tracts']:
        level = tract.get('vulnerability_level')
        if level:
            level_counts[level] = level_counts.get(level, 0) + 1
    
    for level in sorted(level_counts.keys()):
        count = level_counts[level]
        level_info = data['color_scheme']['levels'][f'level_{level}']
        print(f"  {level_info['name']}: {count} tracts")
    
    print(f"\nFirst few tract examples:")
    for i, tract in enumerate(data['census_tracts'][:3]):
        print(f"  Tract {tract['tract_id']}: Level {tract['vulnerability_level']} - {tract['style']['fill_color']}")
        if tract['popup_data']:
            print(f"    Population: {tract['popup_data'].get('population', 'N/A')}")
            print(f"    Median Income: {tract['popup_data'].get('median_income', 'N/A')}")

if __name__ == '__main__':
    main()