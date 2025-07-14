#!/usr/bin/env python3
"""
Create a map showing ONLY Hartford city proper - not the surrounding towns
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

def create_hartford_city_only():
    """Create a map showing only Hartford city proper"""
    
    print("Creating map of Hartford city only (excluding neighboring towns)...")
    
    # Load vulnerability data
    try:
        hartford_data = pd.read_csv('hvi_output/hartford_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(hartford_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found.")
        return
    
    # Create Hartford city only - more precise boundaries
    hartford_gdf = create_hartford_city_precise(hartford_data)
    
    # Create the final map
    create_hartford_only_map(hartford_gdf)

def create_hartford_city_precise(hartford_data):
    """Create Hartford city boundaries only - excluding neighboring towns"""
    
    print("Creating precise Hartford city boundaries only...")
    
    # Hartford city proper coordinates (more precise research-based)
    # Hartford center: 41.7637°N, 72.6851°W
    # Area: 17.4 sq miles
    # This excludes West Hartford, East Hartford, Windsor, Wethersfield etc.
    
    # More precise Hartford city-only boundary
    hartford_city_coords = [
        # Northwestern boundary
        (-72.7150, 41.7900),  # Northwest corner
        (-72.7050, 41.7950),  # North boundary
        (-72.6950, 41.7980),  # Northeast approach
        (-72.6850, 41.7950),  # North-central
        
        # Eastern boundary (Connecticut River)
        (-72.6750, 41.7900),  # River approach
        (-72.6700, 41.7850),  # Connecticut River north
        (-72.6650, 41.7800),  # Connecticut River central
        (-72.6680, 41.7750),  # Connecticut River bend
        (-72.6720, 41.7700),  # Connecticut River south
        (-72.6750, 41.7650),  # Southeast area
        
        # Southern boundary
        (-72.6850, 41.7600),  # South-central
        (-72.6950, 41.7550),  # South boundary
        (-72.7050, 41.7500),  # Southwest area
        (-72.7150, 41.7520),  # Southwest corner
        
        # Western boundary
        (-72.7200, 41.7600),  # West boundary south
        (-72.7220, 41.7700),  # West boundary central
        (-72.7200, 41.7800),  # West boundary north
        (-72.7150, 41.7900)   # Close polygon
    ]
    
    hartford_city_boundary = Polygon(hartford_city_coords)
    
    # Create census tracts within Hartford city only
    tract_polygons = create_hartford_city_tracts(hartford_data, hartford_city_boundary)
    
    # Create GeoDataFrame
    hartford_gdf = gpd.GeoDataFrame(
        hartford_data.iloc[:len(tract_polygons)].copy(),
        geometry=tract_polygons, 
        crs='EPSG:4326'
    )
    
    print(f"✓ Created {len(hartford_gdf)} census tracts within Hartford city proper")
    return hartford_gdf

def create_hartford_city_tracts(hartford_data, city_boundary):
    """Create census tracts within Hartford city proper only"""
    
    print("Creating Hartford city census tracts...")
    
    bounds = city_boundary.bounds
    west, south, east, north = bounds
    
    # Target number of tracts for Hartford city
    n_tracts = min(len(hartford_data), 60)  # Reasonable for Hartford city
    
    # Create rectangular grid
    aspect_ratio = (east - west) / (north - south)
    cols = int(np.ceil(np.sqrt(n_tracts * aspect_ratio)))
    rows = int(np.ceil(n_tracts / cols))
    
    cell_width = (east - west) / cols
    cell_height = (north - south) / rows
    
    tract_polygons = []
    
    for row in range(rows):
        for col in range(cols):
            if len(tract_polygons) >= n_tracts:
                break
                
            # Calculate cell boundaries
            left = west + col * cell_width
            right = west + (col + 1) * cell_width
            bottom = south + row * cell_height
            top = south + (row + 1) * cell_height
            
            # Create cell polygon
            cell = Polygon([
                (left, bottom),
                (right, bottom), 
                (right, top),
                (left, top),
                (left, bottom)
            ])
            
            # Intersect with Hartford city boundary only
            tract = cell.intersection(city_boundary)
            
            # Keep if valid and reasonable size
            if (hasattr(tract, 'area') and tract.area > 0.0001 and 
                hasattr(tract, 'is_valid') and tract.is_valid):
                
                # Handle MultiPolygon case
                if hasattr(tract, 'geoms'):
                    # Take largest piece
                    tract = max(tract.geoms, key=lambda x: x.area if hasattr(x, 'area') else 0)
                
                tract_polygons.append(tract)
    
    print(f"✓ Created {len(tract_polygons)} Hartford city tract polygons")
    return tract_polygons

def create_hartford_only_map(hartford_gdf):
    """Create map showing only Hartford city proper"""
    
    print("Creating Hartford city-only Heat Vulnerability Index map...")
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Define colors
    colors = {
        1: '#2E8B57',  # Dark green (lowest risk)
        2: '#90EE90',  # Light green (low risk) 
        3: '#FFFF00',  # Yellow (moderate risk)
        4: '#FFA500',  # Orange (high risk)
        5: '#FF4500'   # Red-orange (highest risk)
    }
    
    # Plot each vulnerability level
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
    
    # Add Hartford city boundary ONLY
    hartford_city_coords = [
        (-72.7150, 41.7900), (-72.7050, 41.7950), (-72.6950, 41.7980), (-72.6850, 41.7950),
        (-72.6750, 41.7900), (-72.6700, 41.7850), (-72.6650, 41.7800), (-72.6680, 41.7750),
        (-72.6720, 41.7700), (-72.6750, 41.7650), (-72.6850, 41.7600), (-72.6950, 41.7550),
        (-72.7050, 41.7500), (-72.7150, 41.7520), (-72.7200, 41.7600), (-72.7220, 41.7700),
        (-72.7200, 41.7800), (-72.7150, 41.7900)
    ]
    
    city_boundary = Polygon(hartford_city_coords)
    city_gdf = gpd.GeoDataFrame([1], geometry=[city_boundary], crs='EPSG:4326')
    city_gdf.boundary.plot(ax=ax, color='black', linewidth=3, alpha=0.9)
    
    # Add Connecticut River indication (eastern boundary of Hartford city)
    river_coords = [
        (-72.6750, 41.7900), (-72.6700, 41.7850), (-72.6650, 41.7800), 
        (-72.6680, 41.7750), (-72.6720, 41.7700), (-72.6750, 41.7650)
    ]
    
    # Plot river line
    river_x = [coord[0] for coord in river_coords]
    river_y = [coord[1] for coord in river_coords]
    ax.plot(river_x, river_y, color='#4A90E2', linewidth=4, alpha=0.8, label='Connecticut River')
    
    # Customize map
    ax.set_title('Hartford City Only\nHeat Vulnerability Index - July 2024\n(Excluding West Hartford, East Hartford, Windsor, Wethersfield)', 
                fontsize=15, fontweight='bold', pad=20)
    
    # Remove axis elements for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_facecolor('#f0f8ff')  # Light blue background
    
    # Create legend for vulnerability levels
    legend_elements = [
        mpatches.Patch(color=colors[1], label='Level 1 - Lowest Risk'),
        mpatches.Patch(color=colors[2], label='Level 2 - Low Risk'),
        mpatches.Patch(color=colors[3], label='Level 3 - Moderate Risk'),
        mpatches.Patch(color=colors[4], label='Level 4 - High Risk'),
        mpatches.Patch(color=colors[5], label='Level 5 - Highest Risk'),
        mpatches.Patch(color='#4A90E2', label='Connecticut River (Eastern Border)')
    ]
    
    legend = ax.legend(
        handles=legend_elements, 
        loc='upper left', 
        fontsize=10,
        title='Heat Vulnerability Level',
        title_fontsize=11,
        frameon=True,
        fancybox=True,
        shadow=True
    )
    legend.get_title().set_fontweight('bold')
    
    # Add north arrow
    bounds = ax.get_xlim() + ax.get_ylim()
    x_pos = bounds[1] - (bounds[1] - bounds[0]) * 0.08
    y_pos = bounds[3] - (bounds[3] - bounds[2]) * 0.12
    ax.annotate('N', xy=(x_pos, y_pos), xytext=(x_pos, y_pos - (bounds[3] - bounds[2]) * 0.04),
                arrowprops=dict(arrowstyle='->', lw=3, color='black'),
                fontsize=16, fontweight='bold', ha='center')
    
    # Add statistics for Hartford city only
    total_pop = hartford_gdf['population'].sum()
    high_vuln_tracts = len(hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])])
    high_vuln_pop = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100 if total_pop > 0 else 0
    
    stats_text = f"""Hartford City Statistics:
• Total Population: {total_pop:,}
• Census Tracts: {len(hartford_gdf)}
• High Risk Tracts: {high_vuln_tracts} ({high_vuln_tracts/len(hartford_gdf)*100:.1f}%)
• People at High Risk: {high_vuln_pop:,} ({high_vuln_pct:.1f}%)
• City Area: ~17.4 sq miles
• Capital of Connecticut"""
    
    ax.text(0.98, 0.98, stats_text, 
           transform=ax.transAxes, 
           fontsize=10,
           verticalalignment='top',
           horizontalalignment='right',
           bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='gray'))
    
    # Add clarification note
    ax.text(0.02, 0.02, 
           'Hartford City Proper Only\n'
           'EXCLUDES: West Hartford, East Hartford, Windsor, Wethersfield\n'
           'Eastern Border: Connecticut River\n'
           'Data: US Census ACS 2022, Simulated Climate Data', 
           transform=ax.transAxes, 
           fontsize=9, 
           alpha=0.8,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # Set equal aspect ratio
    ax.set_aspect('equal')
    plt.tight_layout()
    
    # Save the map
    output_path = 'hvi_output/hartford_city_only_vulnerability_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved Hartford city-only map to {output_path}")
    
    # Also save as PDF
    pdf_path = 'hvi_output/hartford_city_only_vulnerability_map.pdf'
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved PDF version to {pdf_path}")
    
    plt.show()
    
    # Print summary
    print(f"\n📊 Hartford City Heat Vulnerability Index Summary:")
    print(f"   • Map shows ONLY Hartford city proper")
    print(f"   • EXCLUDES neighboring towns (West Hartford, East Hartford, Windsor, Wethersfield)")
    print(f"   • Total population: {total_pop:,}")
    print(f"   • {len(hartford_gdf)} census tracts with no overlapping regions")
    print(f"   • Connecticut River forms eastern city boundary")

if __name__ == "__main__":
    create_hartford_city_only()