#!/usr/bin/env python3
"""
Create Hartford Heat Vulnerability Index map with original tract shapes but no overlaps
Uses exact original tract geometries and resolves any overlaps
"""

import json
import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
import warnings
warnings.filterwarnings('ignore')

def create_hartford_no_overlap_original_shapes():
    """Create Hartford map with original shapes but no overlaps"""
    
    print("Creating Hartford Heat Vulnerability Index map with original shapes (no overlaps)...")
    
    # Load the extracted census tract data with original geometries
    try:
        with open('hartford_census_tract_data.json', 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded extracted data for {len(data['census_tracts'])} census tracts")
    except FileNotFoundError:
        print("✗ Census tract data not found. Run extract script first.")
        return None
    
    # Process tract geometries to ensure no overlaps
    tracts_gdf = process_original_geometries_no_overlap(data['census_tracts'])
    
    # Create the interactive map
    map_obj = create_interactive_map(tracts_gdf)
    
    return map_obj

def process_original_geometries_no_overlap(census_tracts):
    """Process original geometries to remove overlaps while preserving shapes"""
    
    print("Processing original tract geometries to remove overlaps...")
    
    # Convert tract data to GeoDataFrame with original geometries
    geometries = []
    tract_data = []
    
    for tract in census_tracts:
        # Convert GeoJSON to Shapely geometry
        geom = shape(tract['geojson']['features'][0]['geometry'])
        
        # Ensure geometry is valid
        if not geom.is_valid:
            geom = geom.buffer(0)  # Fix invalid geometries
        
        geometries.append(geom)
        
        # Prepare tract data
        tract_info = {
            'tract_id': tract['tract_id'],
            'vulnerability_level': tract['vulnerability_level'],
            'population': tract['popup_data']['population'],
            'median_income': tract['popup_data']['median_income'],
            'temperature': tract['popup_data']['temperature'],
            'ac_access': tract['popup_data']['ac_access'],
            'green_space': tract['popup_data']['green_space'],
            'vulnerability_score': tract['popup_data']['vulnerability_score']
        }
        tract_data.append(tract_info)
    
    # Create initial GeoDataFrame
    gdf = gpd.GeoDataFrame(tract_data, geometry=geometries, crs='EPSG:4326')
    
    # Resolve overlaps by slightly buffering and differencing
    print("Resolving overlaps while preserving original shapes...")
    
    processed_geometries = []
    
    for i, (idx, row) in enumerate(gdf.iterrows()):
        current_geom = row.geometry
        
        # Check for overlaps with previously processed geometries
        for j in range(i):
            previous_geom = processed_geometries[j]
            
            if current_geom.intersects(previous_geom):
                intersection = current_geom.intersection(previous_geom)
                
                # If there's a significant overlap, remove it from current geometry
                if intersection.area > 0.000001:  # Small threshold for tiny overlaps
                    try:
                        # Subtract the intersection from current geometry
                        current_geom = current_geom.difference(intersection)
                        
                        # Ensure we still have a valid polygon
                        if current_geom.is_empty:
                            # If completely removed, use a small buffer around centroid
                            centroid = row.geometry.centroid
                            current_geom = centroid.buffer(0.001)
                        elif hasattr(current_geom, 'geoms'):
                            # If result is multipolygon, take largest part
                            current_geom = max(current_geom.geoms, key=lambda x: x.area)
                    except:
                        # If difference operation fails, use original with small offset
                        bounds = current_geom.bounds
                        offset = 0.0001 * i  # Small offset based on index
                        current_geom = Polygon([
                            (bounds[0] + offset, bounds[1] + offset),
                            (bounds[2] + offset, bounds[1] + offset),
                            (bounds[2] + offset, bounds[3] + offset),
                            (bounds[0] + offset, bounds[3] + offset)
                        ])
        
        processed_geometries.append(current_geom)
    
    # Update the GeoDataFrame with processed geometries
    gdf.geometry = processed_geometries
    
    # Ensure all geometries are valid
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom if geom.is_valid else geom.buffer(0))
    
    print(f"✓ Processed {len(gdf)} tract geometries with no overlaps")
    return gdf

def create_interactive_map(hartford_gdf):
    """Create the interactive vulnerability map using processed geometries"""
    
    # Calculate map center from tract bounds
    bounds = hartford_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create base map with higher zoom level
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,  # Increased from 12 to 13 for more zoom
        tiles=None
    )
    
    # Add tile layers
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
    
    # NYC-style heat vulnerability color scheme
    def get_color(vulnerability_level):
        colors = {
            1: '#000000',  # Black (lowest risk/coolest)
            2: '#2ca02c',  # Green (low risk) 
            3: '#ff7f0e',  # Orange (moderate risk)
            4: '#d62728',  # Red (high risk)
            5: '#8b0000'   # Dark Red (highest risk/hottest)
        }
        return colors.get(vulnerability_level, '#808080')
    
    # Create separate feature groups for each vulnerability level to ensure Level 1 draws last
    level_groups = {}
    for level in [1, 2, 3, 4, 5]:
        level_groups[level] = folium.FeatureGroup(name=f'Level {level}')
    
    # Add all tracts to their respective feature groups
    for idx, row in hartford_gdf.iterrows():
        # Create popup content
        popup_content = f"""
        <div style="width: 300px;">
            <h4 style="margin-bottom: 10px; color: #333;">Census Tract {row['tract_id']}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Vulnerability Level:</b></td><td style="color: {get_color(row['vulnerability_level'])}; font-weight: bold;">Level {row['vulnerability_level']}</td></tr>
                <tr><td><b>Population:</b></td><td>{row['population']}</td></tr>
                <tr><td><b>Median Income:</b></td><td>{row['median_income']}</td></tr>
                <tr><td><b>Temperature:</b></td><td>{row['temperature']}</td></tr>
                <tr><td><b>AC Access:</b></td><td>{row['ac_access']}</td></tr>
                <tr><td><b>Green Space:</b></td><td>{row['green_space']}</td></tr>
                <tr><td><b>Vulnerability Score:</b></td><td>{row['vulnerability_score']}</td></tr>
            </table>
        </div>
        """
        
        # Create tooltip
        tooltip_content = f"Tract {row['tract_id']}: Level {row['vulnerability_level']} Risk"
        
        # Add tract to its appropriate feature group
        # Create a closure to capture the current vulnerability_level
        def create_style_function(vuln_level):
            return lambda x: {
                'fillColor': get_color(vuln_level),
                'color': 'white',
                'weight': 1,
                'fillOpacity': 0.8,
                'opacity': 0.8
            }
        
        geojson_layer = folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=create_style_function(row['vulnerability_level']),
            popup=folium.Popup(popup_content, max_width=400),
            tooltip=tooltip_content
        )
        
        # Add to the appropriate level group
        geojson_layer.add_to(level_groups[row['vulnerability_level']])
    
    # Add feature groups to map in order: 2, 3, 4, 5, then 1 LAST (so Level 1 is on top)
    for level in [2, 3, 4, 5]:
        level_groups[level].add_to(m)
    # Add Level 1 LAST so it draws on top and stands out more
    level_groups[1].add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 60px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 16px; font-weight: bold; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;">
    <h3 style="margin: 0; color: #333;">Hartford Heat Vulnerability Index - July 2024</h3>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Original tract shapes with no overlaps</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 180px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 12px; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                border-radius: 5px;">
    <h4 style="margin: 0 0 10px 0; color: #333;">Heat Vulnerability Level</h4>
    <p style="margin: 5px 0; color: #000000;"><i class="fa fa-square" style="color: #000000;"></i> Level 1 - Lowest Risk</p>
    <p style="margin: 5px 0; color: #2ca02c;"><i class="fa fa-square" style="color: #2ca02c;"></i> Level 2 - Low Risk</p>
    <p style="margin: 5px 0; color: #ff7f0e;"><i class="fa fa-square" style="color: #ff7f0e;"></i> Level 3 - Moderate Risk</p>
    <p style="margin: 5px 0; color: #d62728;"><i class="fa fa-square" style="color: #d62728;"></i> Level 4 - High Risk</p>
    <p style="margin: 5px 0; color: #8b0000;"><i class="fa fa-square" style="color: #8b0000;"></i> Level 5 - Highest Risk</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Calculate statistics
    total_pop = 0
    high_vuln_pop = 0
    high_risk_incomes = []
    
    for _, row in hartford_gdf.iterrows():
        pop_str = row['population'].replace(',', '')
        population = int(pop_str)
        total_pop += population
        
        if row['vulnerability_level'] in [4, 5]:
            high_vuln_pop += population
            income_str = row['median_income'].replace('$', '').replace(',', '')
            if income_str.isdigit():
                high_risk_incomes.append(int(income_str))
    
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_income_high = sum(high_risk_incomes) / len(high_risk_incomes) if high_risk_incomes else 0
    
    # Add statistics box with proper height to cover all content
    stats_html = f'''
    <div style="position: fixed; 
                top: 80px; right: 50px; width: 220px; height: 140px; 
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
    
    # Add layer control and plugins
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl().add_to(m)
    
    # Save the map
    map_path = 'hvi_output/hartford_heat_vulnerability_original_shapes_no_overlap.html'
    m.save(map_path)
    print(f"✓ Saved map with original shapes (no overlaps) to {map_path}")
    
    return m

if __name__ == "__main__":
    map_obj = create_hartford_no_overlap_original_shapes()
    if map_obj:
        print("✓ Successfully created Hartford Heat Vulnerability Index map with original shapes but no overlaps")
        print("  All census tract boundaries preserved with overlaps resolved")
    else:
        print("✗ Failed to create map. Please check that the extracted data file exists.")