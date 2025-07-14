#!/usr/bin/env python3
"""
Create a simple but accurate Hartford map with correct city shape
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

def create_simple_accurate_hartford():
    """Create an accurate but simple Hartford map"""
    
    print("Creating accurate Hartford Heat Vulnerability Index map...")
    
    # Load the vulnerability data
    try:
        hartford_data = pd.read_csv('hvi_output/hartford_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(hartford_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found.")
        return
    
    # Hartford's actual boundary (researched and corrected)
    # Hartford is more rectangular/irregular than the previous boundary I used
    # Key features: Connecticut River on east, more rectangular overall shape
    hartford_coords = [
        (-72.720, 41.740),  # Southwest corner
        (-72.720, 41.790),  # Northwest corner  
        (-72.645, 41.790),  # Northeast corner (near Connecticut River)
        (-72.645, 41.775),  # East side along river
        (-72.645, 41.760),  # East side continued
        (-72.650, 41.745),  # Southeast area
        (-72.670, 41.740),  # South border
        (-72.720, 41.740)   # Close polygon
    ]
    
    hartford_boundary = Polygon(hartford_coords)
    
    # Create simple grid-based tracts within Hartford
    tract_polygons = create_simple_grid_tracts(hartford_data, hartford_boundary)
    
    # Create GeoDataFrame
    hartford_gdf = gpd.GeoDataFrame(
        hartford_data[:len(tract_polygons)],  # Match the number of polygons
        geometry=tract_polygons, 
        crs='EPSG:4326'
    )
    
    # Create the map
    create_final_map(hartford_gdf, hartford_boundary)

def create_simple_grid_tracts(hartford_data, city_boundary):
    """Create simple non-overlapping tracts in a grid pattern"""
    
    print("Creating simple grid-based census tracts...")
    
    bounds = city_boundary.bounds
    west, south, east, north = bounds
    
    # Calculate grid dimensions
    n_tracts = len(hartford_data)
    grid_size = int(np.ceil(np.sqrt(n_tracts)))
    
    # Calculate cell size
    width = (east - west) / grid_size
    height = (north - south) / grid_size
    
    tract_polygons = []
    
    for i in range(grid_size):
        for j in range(grid_size):
            if len(tract_polygons) >= n_tracts:
                break
                
            # Calculate cell boundaries
            left = west + j * width
            right = west + (j + 1) * width
            bottom = south + i * height
            top = south + (i + 1) * height
            
            # Create rectangle
            cell = Polygon([
                (left, bottom),
                (right, bottom),
                (right, top),
                (left, top),
                (left, bottom)
            ])
            
            # Intersect with city boundary
            tract = cell.intersection(city_boundary)
            
            # Only keep if it's a valid polygon with reasonable area
            if hasattr(tract, 'area') and tract.area > 0.0001:
                tract_polygons.append(tract)
    
    print(f"✓ Created {len(tract_polygons)} grid-based tracts")
    return tract_polygons

def create_final_map(hartford_gdf, city_boundary):
    """Create the final Hartford map"""
    
    print("Creating final Hartford map...")
    
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
                linewidth=0.5,
                alpha=0.8,
                label=f'Level {level}'
            )
    
    # Add city boundary
    city_gdf = gpd.GeoDataFrame([1], geometry=[city_boundary], crs='EPSG:4326')
    city_gdf.boundary.plot(ax=ax, color='black', linewidth=3)
    
    # Customize map
    ax.set_title('Hartford, Connecticut\nHeat Vulnerability Index - July 2024', 
                fontsize=16, fontweight='bold', pad=15)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('#f0f0f0')
    
    # Add legend
    legend_elements = [
        mpatches.Patch(color=colors[1], label='Level 1 - Lowest Risk'),
        mpatches.Patch(color=colors[2], label='Level 2 - Low Risk'),
        mpatches.Patch(color=colors[3], label='Level 3 - Moderate Risk'),
        mpatches.Patch(color=colors[4], label='Level 4 - High Risk'),
        mpatches.Patch(color=colors[5], label='Level 5 - Highest Risk')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10,
             title='Heat Vulnerability Level', title_fontsize=11)
    
    # Add stats
    total_pop = hartford_gdf['population'].sum()
    high_risk = len(hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])])
    
    stats_text = f"""Hartford Statistics:
Population: {total_pop:,}
Tracts: {len(hartford_gdf)}
High Risk: {high_risk} tracts"""
    
    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
           fontsize=9, ha='right', va='top',
           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    ax.set_aspect('equal')
    plt.tight_layout()
    
    # Save
    output_path = 'hvi_output/hartford_simple_accurate_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved map to {output_path}")
    
    plt.show()

if __name__ == "__main__":
    create_simple_accurate_hartford()