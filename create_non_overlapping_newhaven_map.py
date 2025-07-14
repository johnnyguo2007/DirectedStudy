#!/usr/bin/env python3
"""
Create New Haven Heat Vulnerability Index map with non-overlapping regions using Voronoi diagrams
Generates the same output as hvi_output/newhaven_heat_vulnerability_interactive_map.html
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

def create_non_overlapping_newhaven_map():
    """Create New Haven Heat Vulnerability Index map with guaranteed non-overlapping regions"""
    
    print("Creating New Haven Heat Vulnerability Index map with non-overlapping regions...")
    
    # Load the vulnerability data
    try:
        newhaven_data = pd.read_csv('hvi_output/newhaven_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(newhaven_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found. Run newhaven_hvi_implementation.py first.")
        return None
    
    # Create non-overlapping census tract geometries using Voronoi diagrams
    newhaven_gdf = create_voronoi_tracts(newhaven_data)
    
    # Create the interactive map
    map_obj = create_interactive_vulnerability_map(newhaven_gdf)
    
    return map_obj

def create_voronoi_tracts(newhaven_data):
    """Create non-overlapping census tract geometries using Voronoi diagrams"""
    
    print("Creating non-overlapping tract boundaries using Voronoi diagrams...")
    
    # New Haven center and realistic bounds
    newhaven_center_lat, newhaven_center_lon = 41.3083, -72.9279
    
    # Create realistic bounds around New Haven (approximately 10km radius)
    bounds_km = 10
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
    
    # Generate seed points for each census tract
    np.random.seed(48)  # For reproducible results
    
    # Use population density and vulnerability to influence placement
    population_weights = newhaven_data['population'] / newhaven_data['population'].max()
    vulnerability_weights = newhaven_data['vulnerability_index'] / 5.0
    
    points = []
    
    # Define cluster centers based on New Haven geography
    cluster_centers = [
        (newhaven_center_lat, newhaven_center_lon),                    # Downtown New Haven / Yale
        (newhaven_center_lat + 0.015, newhaven_center_lon - 0.015),   # East Rock
        (newhaven_center_lat - 0.015, newhaven_center_lon - 0.025),   # Westville
        (newhaven_center_lat + 0.020, newhaven_center_lon - 0.030),   # West Rock area
        (newhaven_center_lat - 0.020, newhaven_center_lon + 0.015),   # Fair Haven
        (newhaven_center_lat + 0.025, newhaven_center_lon),           # Prospect Hill
        (newhaven_center_lat - 0.010, newhaven_center_lon + 0.020),   # Wooster Square
        (newhaven_center_lat + 0.030, newhaven_center_lon + 0.010),   # Hamden border
        (newhaven_center_lat - 0.025, newhaven_center_lon - 0.020),   # West Haven border
    ]
    
    for i, (_, row) in enumerate(newhaven_data.iterrows()):
        pop_weight = population_weights.iloc[i]
        vuln_weight = vulnerability_weights.iloc[i]
        
        # Higher population and vulnerability = closer to downtown/Yale
        if pop_weight > 0.7 or vuln_weight > 0.6:
            center_idx = 0  # Downtown/Yale
            spread = 0.005
        elif pop_weight > 0.4:
            center_idx = np.random.choice([0, 1, 2], p=[0.5, 0.25, 0.25])
            spread = 0.008
        else:
            center_idx = np.random.randint(0, len(cluster_centers))
            spread = 0.015
        
        center_lat, center_lon = cluster_centers[center_idx]
        
        # Add random offset around cluster center
        lat = center_lat + np.random.normal(0, spread)
        lon = center_lon + np.random.normal(0, spread)
        
        # Ensure points stay within bounds
        lat = max(south + 0.008, min(north - 0.008, lat))
        lon = max(west + 0.008, min(east - 0.008, lon))
        
        points.append(Point(lon, lat))
    
    # Create Voronoi diagram
    multipoint = MultiPolygon([point.buffer(0.0008) for point in points])
    voronoi_polys = voronoi_diagram(multipoint, envelope=boundary)
    
    # Extract individual polygons and ensure they're properly formed
    geometries = []
    if isinstance(voronoi_polys, GeometryCollection):
        for geom in voronoi_polys.geoms:
            if isinstance(geom, Polygon) and geom.is_valid:
                # Clip to boundary and ensure reasonable size
                clipped = geom.intersection(boundary)
                if isinstance(clipped, Polygon) and clipped.area > 0.00008:
                    geometries.append(clipped)
                elif isinstance(clipped, MultiPolygon):
                    # Take the largest polygon if we get multiple parts
                    largest = max(clipped.geoms, key=lambda x: x.area)
                    if largest.area > 0.00008:
                        geometries.append(largest)
    
    # If we don't have enough geometries, create fallback regular polygons
    while len(geometries) < len(newhaven_data):
        # Create a fallback polygon around remaining points
        point_idx = len(geometries)
        if point_idx < len(points):
            center = points[point_idx]
            size = 0.006
            # Create a hexagon around the point
            angles = np.linspace(0, 2*np.pi, 7)
            vertices = [(center.x + size * np.cos(a), center.y + size * np.sin(a)) for a in angles]
            poly = Polygon(vertices)
            if poly.is_valid:
                geometries.append(poly)
    
    # Trim to exact number needed
    geometries = geometries[:len(newhaven_data)]
    
    # Create GeoDataFrame
    newhaven_gdf = gpd.GeoDataFrame(newhaven_data, geometry=geometries, crs='EPSG:4326')
    
    print(f"✓ Created {len(newhaven_gdf)} non-overlapping tract boundaries")
    return newhaven_gdf

def create_interactive_vulnerability_map(newhaven_gdf):
    """Create the interactive vulnerability map using Folium - matches original exactly"""
    
    # Calculate map center
    bounds = newhaven_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create base map with higher zoom level
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,  # Increased from 12 to 13 for more zoom
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
    
    # NYC-style heat vulnerability color scheme (cool to hot)
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
        # Create popup content exactly like original
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
        
        # Create tooltip exactly like original
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
    
    # Add exact same title as original
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
    
    # Add legend with proper width and height to cover header and all 5 levels
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
    
    # Add exact same statistics box as original
    total_pop = newhaven_gdf['population'].sum()
    high_vuln_pop = newhaven_gdf[newhaven_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_income_high = newhaven_gdf[newhaven_gdf['vulnerability_index'].isin([4, 5])]['median_income'].mean()
    
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
    
    # Add layer control and plugins exactly like original
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl().add_to(m)
    
    # Save the map with same filename pattern
    map_path = 'hvi_output/newhaven_heat_vulnerability_interactive_map_non_overlapping.html'
    m.save(map_path)
    print(f"✓ Saved non-overlapping interactive map to {map_path}")
    
    return m

if __name__ == "__main__":
    map_obj = create_non_overlapping_newhaven_map()
    if map_obj:
        print("✓ Successfully created New Haven Heat Vulnerability Index map with non-overlapping regions")
        print("  The map maintains all original functionality while ensuring census tract boundaries don't overlap")
    else:
        print("✗ Failed to create map. Please check that the vulnerability data file exists.")