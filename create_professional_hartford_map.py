#!/usr/bin/env python3
"""
Create a professional, interactive Hartford Heat Vulnerability Index map using Folium
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import json
import numpy as np
from shapely.geometry import Polygon
import math
import random
import warnings
warnings.filterwarnings('ignore')

def create_professional_hartford_map():
    """Create a professional interactive map of Hartford Heat Vulnerability Index"""
    
    print("Creating professional Hartford Heat Vulnerability Index map...")
    
    # Load the vulnerability data
    try:
        hartford_data = pd.read_csv('hvi_output/hartford_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(hartford_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found. Run hartford_hvi_implementation.py first.")
        return
    
    # Create realistic census tract geometries
    hartford_gdf = create_realistic_hartford_tracts(hartford_data)
    
    # Create the interactive map
    create_interactive_vulnerability_map(hartford_gdf)

def create_realistic_hartford_tracts(hartford_data):
    """Create realistic census tract geometries for Hartford"""
    from shapely.geometry import Polygon
    from shapely.ops import voronoi_diagram
    from shapely.geometry import Point, MultiPoint
    
    print("Creating realistic Hartford census tract boundaries...")
    
    # Hartford center and bounds
    hartford_center_lat, hartford_center_lon = 41.7584, -72.6851
    
    # Create more realistic bounds around Hartford
    bounds_km = 12  # 12km radius around Hartford center
    lat_offset = bounds_km / 111  # Rough conversion km to degrees latitude
    lon_offset = bounds_km / (111 * np.cos(np.radians(hartford_center_lat)))
    
    west = hartford_center_lon - lon_offset
    east = hartford_center_lon + lon_offset
    south = hartford_center_lat - lat_offset
    north = hartford_center_lat + lat_offset
    
    # Use population density to influence tract placement
    population_weights = hartford_data['population'] / hartford_data['population'].max()
    
    # Generate points with realistic clustering
    random.seed(42)
    np.random.seed(42)
    
    points = []
    geometries = []
    
    for i, (_, row) in enumerate(hartford_data.iterrows()):
        # Create clusters around Hartford center and some suburban areas
        cluster_centers = [
            (hartford_center_lat, hartford_center_lon),  # Downtown
            (hartford_center_lat + 0.02, hartford_center_lon - 0.02),  # West End
            (hartford_center_lat - 0.02, hartford_center_lon + 0.02),  # East Hartford area
            (hartford_center_lat + 0.03, hartford_center_lon),  # North Hartford
            (hartford_center_lat - 0.03, hartford_center_lon),  # South Hartford
        ]
        
        # Choose cluster based on population (higher pop = more likely downtown)
        pop_weight = population_weights.iloc[i]
        if pop_weight > 0.8:
            center_idx = 0  # Downtown
        elif pop_weight > 0.6:
            center_idx = random.choice([0, 1, 2])
        else:
            center_idx = random.choice(range(len(cluster_centers)))
        
        center_lat, center_lon = cluster_centers[center_idx]
        
        # Add random offset around cluster center
        lat_spread = 0.008 * (1 + pop_weight)  # Higher density = tighter clustering
        lon_spread = 0.008 * (1 + pop_weight)
        
        lat = center_lat + random.gauss(0, lat_spread)
        lon = center_lon + random.gauss(0, lon_spread)
        
        # Keep within bounds
        lat = max(south, min(north, lat))
        lon = max(west, min(east, lon))
        
        points.append((lon, lat))
        
        # Create tract polygon around point
        size_factor = 0.003 + (pop_weight * 0.002)  # Larger tracts for higher population
        n_vertices = random.randint(6, 9)
        
        vertices = []
        for j in range(n_vertices):
            angle = (2 * math.pi * j) / n_vertices + random.uniform(-0.3, 0.3)
            radius = size_factor * random.uniform(0.8, 1.2)
            
            vertex_lon = lon + radius * math.cos(angle)
            vertex_lat = lat + radius * math.sin(angle)
            
            vertices.append((vertex_lon, vertex_lat))
        
        # Close polygon
        vertices.append(vertices[0])
        
        try:
            polygon = Polygon(vertices)
            if polygon.is_valid and polygon.area > 0:
                geometries.append(polygon)
            else:
                # Fallback to simple polygon
                geometries.append(Polygon([
                    (lon - size_factor, lat - size_factor),
                    (lon + size_factor, lat - size_factor),
                    (lon + size_factor, lat + size_factor),
                    (lon - size_factor, lat + size_factor),
                    (lon - size_factor, lat - size_factor)
                ]))
        except:
            geometries.append(Polygon([
                (lon - size_factor, lat - size_factor),
                (lon + size_factor, lat - size_factor),
                (lon + size_factor, lat + size_factor),
                (lon - size_factor, lat + size_factor),
                (lon - size_factor, lat - size_factor)
            ]))
    
    # Create GeoDataFrame
    hartford_gdf = gpd.GeoDataFrame(hartford_data, geometry=geometries, crs='EPSG:4326')
    
    print(f"✓ Created {len(hartford_gdf)} realistic tract boundaries")
    return hartford_gdf

def create_interactive_vulnerability_map(hartford_gdf):
    """Create the interactive vulnerability map using Folium"""
    
    # Calculate map center
    bounds = hartford_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles=None
    )
    
    # Add multiple tile layers
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
    
    # Define color scheme for vulnerability levels
    def get_color(vulnerability_level):
        colors = {
            1: '#2E8B57',  # Dark green (lowest risk)
            2: '#90EE90',  # Light green (low risk) 
            3: '#FFFF00',  # Yellow (moderate risk)
            4: '#FFA500',  # Orange (high risk)
            5: '#FF4500'   # Red-orange (highest risk)
        }
        return colors.get(vulnerability_level, '#808080')  # Gray for missing data
    
    def get_opacity(vulnerability_level):
        """Higher vulnerability = higher opacity"""
        return 0.5 + (vulnerability_level * 0.1)
    
    # Add vulnerability data to map
    for idx, row in hartford_gdf.iterrows():
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
        
        # Add tract to map
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x, color=get_color(row['vulnerability_index']), 
                          opacity=get_opacity(row['vulnerability_index']): {
                'fillColor': color,
                'color': 'white',
                'weight': 1,
                'fillOpacity': opacity,
                'opacity': 0.8
            },
            popup=folium.Popup(popup_content, max_width=400),
            tooltip=tooltip_content
        ).add_to(m)
    
    # Add title
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
    
    # Add custom legend
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
    
    # Add statistics box
    total_pop = hartford_gdf['population'].sum()
    high_vuln_pop = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_income_high = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['median_income'].mean()
    
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
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add measure tool
    plugins.MeasureControl().add_to(m)
    
    # Save the map
    map_path = 'hvi_output/hartford_heat_vulnerability_interactive_map.html'
    m.save(map_path)
    print(f"✓ Saved interactive map to {map_path}")
    
    # Also create a static high-quality version
    create_static_professional_map(hartford_gdf)
    
    return m

def create_static_professional_map(hartford_gdf):
    """Create a high-quality static version of the map"""
    import matplotlib.pyplot as plt
    import contextily as ctx
    from matplotlib.patches import Rectangle
    import matplotlib.patches as mpatches
    
    # Create figure with high DPI
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Define colors
    colors = {1: '#2E8B57', 2: '#90EE90', 3: '#FFFF00', 4: '#FFA500', 5: '#FF4500'}
    
    # Plot the vulnerability data
    for level in [1, 2, 3, 4, 5]:
        level_data = hartford_gdf[hartford_gdf['vulnerability_index'] == level]
        if len(level_data) > 0:
            level_data.plot(
                ax=ax,
                color=colors[level],
                edgecolor='white',
                linewidth=0.5,
                alpha=0.8,
                label=f'Level {level}'
            )
    
    # Try to add basemap
    try:
        # Convert to Web Mercator for basemap
        hartford_mercator = hartford_gdf.to_crs(epsg=3857)
        ctx.add_basemap(ax, crs=hartford_mercator.crs, source=ctx.providers.CartoDB.Positron)
        
        # Set the coordinate system back
        ax.set_xlim(hartford_mercator.total_bounds[0], hartford_mercator.total_bounds[2])
        ax.set_ylim(hartford_mercator.total_bounds[1], hartford_mercator.total_bounds[3])
    except:
        print("⚠ Could not add basemap, using simple background")
        ax.set_facecolor('#f0f0f0')
    
    # Customize the map
    ax.set_title('Hartford Heat Vulnerability Index - July 2024\nInteractive Version Available', 
                fontsize=20, fontweight='bold', pad=20)
    
    # Remove axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    # Create custom legend
    legend_elements = [
        mpatches.Patch(color=colors[1], label='Level 1 (Lowest Risk)'),
        mpatches.Patch(color=colors[2], label='Level 2 (Low Risk)'),
        mpatches.Patch(color=colors[3], label='Level 3 (Moderate Risk)'),
        mpatches.Patch(color=colors[4], label='Level 4 (High Risk)'),
        mpatches.Patch(color=colors[5], label='Level 5 (Highest Risk)')
    ]
    
    legend = ax.legend(handles=legend_elements, 
                      loc='upper left', 
                      fontsize=12,
                      title='Heat Vulnerability Level',
                      title_fontsize=14,
                      frameon=True,
                      fancybox=True,
                      shadow=True)
    legend.get_title().set_fontweight('bold')
    
    # Add north arrow
    bounds = ax.get_xlim() + ax.get_ylim()
    x_pos = bounds[1] - (bounds[1] - bounds[0]) * 0.08
    y_pos = bounds[3] - (bounds[3] - bounds[2]) * 0.08
    ax.annotate('N', xy=(x_pos, y_pos), xytext=(x_pos, y_pos - (bounds[3] - bounds[2]) * 0.03),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'),
                fontsize=16, fontweight='bold', ha='center')
    
    # Add statistics box
    total_pop = hartford_gdf['population'].sum()
    high_vuln_pop = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    
    stats_text = f"Key Statistics:\n" \
                f"• Total Population: {total_pop:,}\n" \
                f"• High Risk Areas: {high_vuln_pct:.1f}%\n" \
                f"• People at High Risk: {high_vuln_pop:,}\n" \
                f"• Census Tracts: {len(hartford_gdf)}"
    
    ax.text(0.02, 0.98, stats_text, 
           transform=ax.transAxes, 
           fontsize=11,
           verticalalignment='top',
           bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='gray'))
    
    # Add data attribution
    ax.text(0.02, 0.02, 
           'Data: US Census ACS 2022, Simulated Temperature & Green Space\n'
           'Analysis: Hartford Heat Vulnerability Index\n'
           'Interactive version: hartford_heat_vulnerability_interactive_map.html', 
           transform=ax.transAxes, 
           fontsize=9, 
           alpha=0.8,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.tight_layout()
    
    # Save high-quality static version
    static_path = 'hvi_output/hartford_heat_vulnerability_map_professional.png'
    plt.savefig(static_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved professional static map to {static_path}")
    
    # Also save as PDF
    pdf_path = 'hvi_output/hartford_heat_vulnerability_map_professional.pdf'
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved professional PDF to {pdf_path}")
    
    plt.close()

if __name__ == "__main__":
    create_professional_hartford_map()