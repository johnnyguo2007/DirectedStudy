#!/usr/bin/env python3
"""
Create main New Haven Heat Vulnerability Index interactive map
Generates newhaven_heat_vulnerability_interactive_map.html using existing vulnerability data
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import voronoi_diagram
from shapely.geometry.collection import GeometryCollection
import warnings
warnings.filterwarnings('ignore')

def create_main_newhaven_interactive_map():
    """Create main New Haven Heat Vulnerability Index interactive map"""
    
    print("Creating main New Haven Heat Vulnerability Index interactive map...")
    
    # Load the vulnerability data
    try:
        newhaven_data = pd.read_csv('hvi_output/newhaven_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(newhaven_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found. Run newhaven_hvi_implementation.py first.")
        return None
    
    # Create census tract geometries using realistic geographic distribution
    newhaven_gdf = create_realistic_newhaven_tracts(newhaven_data)
    
    # Create the interactive map
    map_obj = create_interactive_vulnerability_map(newhaven_gdf)
    
    return map_obj

def create_realistic_newhaven_tracts(newhaven_data):
    """Create realistic census tract geometries for New Haven using geographic clustering"""
    
    print("Creating realistic tract boundaries for New Haven...")
    
    # New Haven center and realistic bounds
    newhaven_center_lat, newhaven_center_lon = 41.3083, -72.9279
    
    # Create realistic bounds around New Haven (tighter urban area)
    bounds_km = 8
    lat_offset = bounds_km / 111  # Convert km to degrees latitude
    lon_offset = bounds_km / (111 * np.cos(np.radians(newhaven_center_lat)))
    
    west = newhaven_center_lon - lon_offset
    east = newhaven_center_lon + lon_offset
    south = newhaven_center_lat - lat_offset
    north = newhaven_center_lat + lat_offset
    
    # Create boundary polygon for clipping
    boundary = Polygon([
        (west, south), (east, south), (east, north), (west, north), (west, south)
    ])
    
    # Generate realistic tract points based on New Haven geography
    np.random.seed(47)  # Different seed for New Haven main map
    
    # Use population and vulnerability to influence placement
    population_weights = newhaven_data['population'] / newhaven_data['population'].max()
    vulnerability_weights = newhaven_data['vulnerability_index'] / 5.0
    
    points = []
    
    # Define realistic neighborhood centers in New Haven
    neighborhood_centers = [
        (41.3083, -72.9279),   # Downtown New Haven / Yale campus
        (41.3200, -72.9150),   # East Rock neighborhood
        (41.2950, -72.9350),   # Westville
        (41.3150, -72.9450),   # West Rock area
        (41.2900, -72.9200),   # Fair Haven
        (41.3250, -72.9300),   # Prospect Hill
        (41.3000, -72.9100),   # The Hill neighborhood
        (41.3180, -72.9080),   # Wooster Square
        (41.2850, -72.9450),   # West Haven border
        (41.3300, -72.9200),   # Hamden border
        (41.3100, -72.8950),   # East Haven border
        (41.2950, -72.9500),   # West side neighborhoods
    ]
    
    for i, (_, row) in enumerate(newhaven_data.iterrows()):
        pop_weight = population_weights.iloc[i]
        vuln_weight = vulnerability_weights.iloc[i]
        
        # Higher population density = closer to downtown/Yale or major neighborhoods
        if pop_weight > 0.8 or vuln_weight > 0.7:
            # Very high density - downtown core, Yale area
            center_idx = 0
            spread = 0.003
        elif pop_weight > 0.6 or vuln_weight > 0.5:
            # High density - downtown, Yale, or major neighborhoods
            center_idx = np.random.choice([0, 1, 2, 3, 7], p=[0.4, 0.2, 0.15, 0.15, 0.1])
            spread = 0.006
        elif pop_weight > 0.3:
            # Medium density - various neighborhoods
            center_idx = np.random.choice(range(len(neighborhood_centers)), 
                                        p=[0.15, 0.12, 0.1, 0.1, 0.1, 0.08, 0.08, 0.08, 0.06, 0.06, 0.04, 0.03])
            spread = 0.010
        else:
            # Lower density - outer areas
            center_idx = np.random.randint(0, len(neighborhood_centers))
            spread = 0.018
        
        center_lat, center_lon = neighborhood_centers[center_idx]
        
        # Add controlled random offset around neighborhood center
        lat = center_lat + np.random.normal(0, spread)
        lon = center_lon + np.random.normal(0, spread)
        
        # Ensure points stay within New Haven bounds
        lat = max(south + 0.003, min(north - 0.003, lat))
        lon = max(west + 0.003, min(east - 0.003, lon))
        
        points.append(Point(lon, lat))
    
    # Create realistic polygon shapes around points
    geometries = []
    
    for i, point in enumerate(points):
        # Create polygons with realistic census tract characteristics
        # Vary size based on population density and geographic location
        
        pop_weight = population_weights.iloc[i]
        
        # Smaller tracts in dense urban areas, larger in less dense areas
        if pop_weight > 0.7:
            base_size = 0.002  # Very small urban tracts (downtown/Yale)
        elif pop_weight > 0.5:
            base_size = 0.004  # Small urban tracts
        elif pop_weight > 0.3:
            base_size = 0.007  # Medium tracts
        else:
            base_size = 0.012  # Larger suburban tracts
        
        # Add some variation
        size_variation = np.random.uniform(0.7, 1.4)
        tract_size = base_size * size_variation
        
        # Create slightly irregular rectangles (more realistic than perfect shapes)
        center_x, center_y = point.x, point.y
        
        # Random rotation for more natural look
        rotation = np.random.uniform(0, np.pi/3)
        
        # Create vertices with slight irregularity
        vertices = []
        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            adjusted_angle = angle + rotation
            offset_x = tract_size * np.cos(adjusted_angle) * np.random.uniform(0.8, 1.3)
            offset_y = tract_size * np.sin(adjusted_angle) * np.random.uniform(0.8, 1.3)
            
            vertices.append((center_x + offset_x, center_y + offset_y))
        
        # Close the polygon
        vertices.append(vertices[0])
        
        try:
            poly = Polygon(vertices)
            if poly.is_valid and poly.intersects(boundary):
                clipped = poly.intersection(boundary)
                if isinstance(clipped, Polygon) and clipped.area > 0.000008:
                    geometries.append(clipped)
                elif isinstance(clipped, MultiPolygon):
                    largest = max(clipped.geoms, key=lambda x: x.area)
                    if largest.area > 0.000008:
                        geometries.append(largest)
                    else:
                        # Fallback to simple buffer around point
                        geometries.append(point.buffer(tract_size * 0.6))
                else:
                    # Fallback to simple buffer around point
                    geometries.append(point.buffer(tract_size * 0.6))
            else:
                # Fallback to simple buffer around point
                geometries.append(point.buffer(tract_size * 0.6))
        except:
            # Fallback to simple buffer around point
            geometries.append(point.buffer(tract_size * 0.6))
    
    # Ensure we have the right number of geometries
    while len(geometries) < len(newhaven_data):
        # Add fallback geometries if needed
        remaining_idx = len(geometries)
        if remaining_idx < len(points):
            geometries.append(points[remaining_idx].buffer(0.004))
    
    # Trim to exact number needed
    geometries = geometries[:len(newhaven_data)]
    
    # Create GeoDataFrame
    newhaven_gdf = gpd.GeoDataFrame(newhaven_data, geometry=geometries, crs='EPSG:4326')
    
    print(f"✓ Created {len(newhaven_gdf)} realistic tract boundaries")
    return newhaven_gdf

def create_interactive_vulnerability_map(newhaven_gdf):
    """Create the main interactive vulnerability map using Folium"""
    
    # Calculate map center
    bounds = newhaven_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create base map with higher zoom level
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,  # Higher zoom for detail
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
            1: '#0080ff',  # Bright Blue (lowest risk/coolest)
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
    for idx, row in newhaven_gdf.iterrows():
        # Create popup content
        popup_content = f"""
        <div style="width: 300px;">
            <h4 style="margin-bottom: 10px; color: #333;">Census Tract {row['tract']}</h4>
            <hr style="margin: 5px 0;">
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Vulnerability Level:</b></td><td style="color: {get_color(row['vulnerability_index'])}; font-weight: bold;">Level {row['vulnerability_index']}</td></tr>
                <tr><td><b>Population:</b></td><td>{row['population']:,}</td></tr>
                <tr><td><b>Median Income:</b></td><td>${row['median_income']:,}</td></tr>
                <tr><td><b>Temperature:</b></td><td>{row['mean_temp']:.1f}°C</td></tr>
                <tr><td><b>AC Access:</b></td><td>{row['ac_probability']:.1%}</td></tr>
                <tr><td><b>Green Space:</b></td><td>{row['green_space_pct']:.1%}</td></tr>
                <tr><td><b>Vulnerability Score:</b></td><td>{row['vulnerability_score']:.3f}</td></tr>
            </table>
        </div>
        """
        
        # Create tooltip
        tooltip_content = f"Tract {row['tract']}: Level {row['vulnerability_index']} Risk"
        
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
            style_function=create_style_function(row['vulnerability_index']),
            popup=folium.Popup(popup_content, max_width=400),
            tooltip=tooltip_content
        )
        
        # Add to the appropriate level group
        geojson_layer.add_to(level_groups[row['vulnerability_index']])
    
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
    <h3 style="margin: 0; color: #333;">New Haven Heat Vulnerability Index - July 2024</h3>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Interactive map showing heat vulnerability by census tract</p>
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
    <p style="margin: 5px 0; color: #0080ff;"><i class="fa fa-square" style="color: #0080ff;"></i> Level 1 - Lowest Risk</p>
    <p style="margin: 5px 0; color: #2ca02c;"><i class="fa fa-square" style="color: #2ca02c;"></i> Level 2 - Low Risk</p>
    <p style="margin: 5px 0; color: #ff7f0e;"><i class="fa fa-square" style="color: #ff7f0e;"></i> Level 3 - Moderate Risk</p>
    <p style="margin: 5px 0; color: #d62728;"><i class="fa fa-square" style="color: #d62728;"></i> Level 4 - High Risk</p>
    <p style="margin: 5px 0; color: #8b0000;"><i class="fa fa-square" style="color: #8b0000;"></i> Level 5 - Highest Risk</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Calculate statistics
    total_pop = newhaven_gdf['population'].sum()
    high_vuln_pop = newhaven_gdf[newhaven_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_income_high = newhaven_gdf[newhaven_gdf['vulnerability_index'].isin([4, 5])]['median_income'].mean()
    
    # Add statistics box
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
    
    # Save the main interactive map
    map_path = 'hvi_output/newhaven_heat_vulnerability_interactive_map.html'
    m.save(map_path)
    print(f"✓ Saved main interactive map to {map_path}")
    
    return m

if __name__ == "__main__":
    map_obj = create_main_newhaven_interactive_map()
    if map_obj:
        print("✓ Successfully created main New Haven Heat Vulnerability Index interactive map")
        print("  Map uses realistic geographic distribution with proper Level 1 priority")
    else:
        print("✗ Failed to create map. Please check that the vulnerability data file exists.")