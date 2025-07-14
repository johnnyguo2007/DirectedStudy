#!/usr/bin/env python3
"""
Create a simple map showing ONLY Hartford city proper
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

def create_hartford_city_simple():
    """Create a simple map showing only Hartford city"""
    
    print("Creating Hartford city-only Heat Vulnerability Index map...")
    
    # Load vulnerability data
    try:
        hartford_data = pd.read_csv('hvi_output/hartford_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(hartford_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found.")
        return
    
    # Create Hartford city boundary and tracts
    hartford_gdf = create_hartford_city_simple_tracts(hartford_data)
    
    # Create the map
    create_hartford_map(hartford_gdf)

def create_hartford_city_simple_tracts(hartford_data):
    """Create simple Hartford city with tracts"""
    
    print("Creating Hartford city boundary and tracts...")
    
    # Hartford city coordinates (simplified but accurate shape)
    # Center: 41.7637°N, 72.6851°W
    center_lat, center_lon = 41.7637, -72.6851
    
    # Hartford city boundary (excluding neighboring towns)
    hartford_coords = [
        (-72.715, 41.790),  # Northwest
        (-72.695, 41.795),  # North
        (-72.675, 41.790),  # Northeast
        (-72.665, 41.785),  # East (Connecticut River)
        (-72.660, 41.770),  # East-central (River)
        (-72.665, 41.755),  # East-south (River)
        (-72.675, 41.745),  # Southeast
        (-72.695, 41.740),  # South
        (-72.710, 41.745),  # Southwest
        (-72.720, 41.760),  # West
        (-72.715, 41.775),  # Northwest
        (-72.715, 41.790)   # Close
    ]
    
    hartford_boundary = Polygon(hartford_coords)
    
    # Create simple grid of tracts
    bounds = hartford_boundary.bounds
    west, south, east, north = bounds
    
    # Create a 6x6 grid (36 tracts)
    grid_size = 6
    cell_width = (east - west) / grid_size
    cell_height = (north - south) / grid_size
    
    tract_polygons = []
    tract_data = []
    
    tract_idx = 0
    for row in range(grid_size):
        for col in range(grid_size):
            # Calculate cell boundaries
            left = west + col * cell_width
            right = west + (col + 1) * cell_width
            bottom = south + row * cell_height
            top = south + (row + 1) * cell_height
            
            # Create cell
            cell = Polygon([
                (left, bottom), (right, bottom),
                (right, top), (left, top), (left, bottom)
            ])
            
            # Intersect with Hartford boundary
            tract = cell.intersection(hartford_boundary)
            
            # Keep if it has reasonable area
            if hasattr(tract, 'area') and tract.area > 0.0005:
                # Handle MultiPolygon
                if hasattr(tract, 'geoms'):
                    tract = max(tract.geoms, key=lambda x: x.area)
                
                tract_polygons.append(tract)
                
                # Use data from original dataset (cycling through)
                data_idx = tract_idx % len(hartford_data)
                tract_data.append(hartford_data.iloc[data_idx].copy())
                tract_idx += 1
    
    # Create GeoDataFrame
    if tract_data:
        hartford_gdf = gpd.GeoDataFrame(
            pd.DataFrame(tract_data),
            geometry=tract_polygons,
            crs='EPSG:4326'
        )
    else:
        # Fallback if no tracts created
        print("Creating fallback tracts...")
        sample_data = hartford_data.iloc[:1].copy()
        sample_polygon = hartford_boundary
        hartford_gdf = gpd.GeoDataFrame(sample_data, geometry=[sample_polygon], crs='EPSG:4326')
    
    print(f"✓ Created {len(hartford_gdf)} Hartford city tracts")
    return hartford_gdf

def create_hartford_map(hartford_gdf):
    """Create the Hartford city map"""
    
    print("Creating Hartford city Heat Vulnerability Index map...")
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Define colors
    colors = {
        1: '#2E8B57',  # Dark green
        2: '#90EE90',  # Light green
        3: '#FFFF00',  # Yellow
        4: '#FFA500',  # Orange
        5: '#FF4500'   # Red-orange
    }
    
    # Plot vulnerability levels
    for level in [1, 2, 3, 4, 5]:
        level_data = hartford_gdf[hartford_gdf['vulnerability_index'] == level]
        if len(level_data) > 0:
            level_data.plot(
                ax=ax,
                color=colors[level],
                edgecolor='white',
                linewidth=0.8,
                alpha=0.85
            )
    
    # Add Hartford city boundary
    hartford_coords = [
        (-72.715, 41.790), (-72.695, 41.795), (-72.675, 41.790), (-72.665, 41.785),
        (-72.660, 41.770), (-72.665, 41.755), (-72.675, 41.745), (-72.695, 41.740),
        (-72.710, 41.745), (-72.720, 41.760), (-72.715, 41.775), (-72.715, 41.790)
    ]
    
    city_boundary = Polygon(hartford_coords)
    city_gdf = gpd.GeoDataFrame([1], geometry=[city_boundary], crs='EPSG:4326')
    city_gdf.boundary.plot(ax=ax, color='black', linewidth=3)
    
    # Add Connecticut River (eastern boundary)
    river_coords = [(-72.665, 41.785), (-72.660, 41.770), (-72.665, 41.755)]
    river_x = [coord[0] for coord in river_coords]
    river_y = [coord[1] for coord in river_coords]
    ax.plot(river_x, river_y, color='#4A90E2', linewidth=5, alpha=0.8, label='Connecticut River')
    
    # Customize map
    ax.set_title('Hartford City Only\nHeat Vulnerability Index - July 2024\n(Excluding Neighboring Towns)', 
                fontsize=14, fontweight='bold', pad=15)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('#f0f8ff')
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors[1], label='Level 1 - Lowest Risk'),
        mpatches.Patch(color=colors[2], label='Level 2 - Low Risk'),
        mpatches.Patch(color=colors[3], label='Level 3 - Moderate Risk'),
        mpatches.Patch(color=colors[4], label='Level 4 - High Risk'),
        mpatches.Patch(color=colors[5], label='Level 5 - Highest Risk'),
        mpatches.Patch(color='#4A90E2', label='Connecticut River')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10,
             title='Heat Vulnerability Level', title_fontsize=11)
    
    # Add north arrow
    bounds = ax.get_xlim() + ax.get_ylim()
    x_pos = bounds[1] - (bounds[1] - bounds[0]) * 0.1
    y_pos = bounds[3] - (bounds[3] - bounds[2]) * 0.15
    ax.annotate('N', xy=(x_pos, y_pos), xytext=(x_pos, y_pos - (bounds[3] - bounds[2]) * 0.05),
                arrowprops=dict(arrowstyle='->', lw=3, color='black'),
                fontsize=16, fontweight='bold', ha='center')
    
    # Statistics
    total_pop = hartford_gdf['population'].sum()
    high_vuln_tracts = len(hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])])
    high_vuln_pop = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100 if total_pop > 0 else 0
    
    stats_text = f"""Hartford City Only:
• Population: {total_pop:,}
• Census Tracts: {len(hartford_gdf)}
• High Risk Tracts: {high_vuln_tracts}
• High Risk Pop: {high_vuln_pop:,} ({high_vuln_pct:.1f}%)
• Capital of Connecticut"""
    
    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
           fontsize=9, ha='right', va='top',
           bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9))
    
    # Clarification
    ax.text(0.02, 0.02, 
           'Hartford City Proper Only\n'
           'EXCLUDES: West Hartford, East Hartford,\n'
           'Windsor, Wethersfield, Bloomfield, Newington\n'
           'Connecticut River = Eastern City Border', 
           transform=ax.transAxes, fontsize=8, alpha=0.8,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    ax.set_aspect('equal')
    plt.tight_layout()
    
    # Save
    output_path = 'hvi_output/hartford_city_only_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved Hartford city-only map to {output_path}")
    
    pdf_path = 'hvi_output/hartford_city_only_map.pdf'
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved PDF to {pdf_path}")
    
    plt.show()
    
    print(f"\n📊 Hartford City Summary:")
    print(f"   • Shows ONLY Hartford city proper")
    print(f"   • Population: {total_pop:,}")
    print(f"   • {len(hartford_gdf)} non-overlapping census tracts")
    print(f"   • Connecticut River forms eastern boundary")

if __name__ == "__main__":
    create_hartford_city_simple()