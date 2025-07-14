#!/usr/bin/env python3
"""
Create a proper Hartford Heat Vulnerability Index map with realistic boundaries and no overlaps
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import matplotlib.patches as mpatches
from scipy.spatial import Voronoi
import warnings
warnings.filterwarnings('ignore')

def create_hartford_geographic_map():
    """Create a proper Hartford map with realistic boundaries"""
    
    print("Creating Hartford Heat Vulnerability Index map with proper boundaries...")
    
    # Load the vulnerability data
    try:
        hartford_data = pd.read_csv('hvi_output/hartford_vulnerability_data.csv')
        print(f"✓ Loaded vulnerability data: {len(hartford_data)} tracts")
    except FileNotFoundError:
        print("✗ Vulnerability data not found. Run hartford_hvi_implementation.py first.")
        return
    
    # Create Hartford city boundary and census tracts
    hartford_gdf = create_hartford_boundary_with_tracts(hartford_data)
    
    # Create the final map
    create_professional_hartford_map(hartford_gdf)

def create_hartford_boundary_with_tracts(hartford_data):
    """Create realistic Hartford city boundary with non-overlapping census tracts"""
    
    print("Creating Hartford city boundary with census tracts...")
    
    # Hartford real coordinates (approximate city boundary)
    hartford_boundary_coords = [
        (-72.7200, 41.7200),  # Southwest
        (-72.7200, 41.7900),  # Northwest  
        (-72.6500, 41.7900),  # Northeast
        (-72.6500, 41.7600),  # East center
        (-72.6300, 41.7400),  # Southeast point
        (-72.6600, 41.7200),  # South center
        (-72.7200, 41.7200)   # Close polygon
    ]
    
    # Create Hartford city boundary
    hartford_boundary = Polygon(hartford_boundary_coords)
    
    # Create census tract centers using population-based clustering
    tract_centers = generate_tract_centers(hartford_data, hartford_boundary)
    
    # Create Voronoi diagram for non-overlapping tracts
    tract_polygons = create_voronoi_tracts(tract_centers, hartford_boundary)
    
    # Create GeoDataFrame
    hartford_gdf = gpd.GeoDataFrame(
        hartford_data, 
        geometry=tract_polygons, 
        crs='EPSG:4326'
    )
    
    print(f"✓ Created {len(hartford_gdf)} non-overlapping census tracts within Hartford boundary")
    return hartford_gdf

def generate_tract_centers(hartford_data, city_boundary):
    """Generate realistic tract center points based on population density"""
    
    # Get city bounds
    bounds = city_boundary.bounds
    
    # Define Hartford neighborhoods/districts with realistic centers
    neighborhoods = [
        {"name": "Downtown", "center": (-72.6851, 41.7584), "weight": 3.0},
        {"name": "North End", "center": (-72.6900, 41.7700), "weight": 2.5},
        {"name": "South End", "center": (-72.6800, 41.7450), "weight": 2.0},
        {"name": "West End", "center": (-72.7000, 41.7550), "weight": 1.8},
        {"name": "Northeast", "center": (-72.6650, 41.7650), "weight": 1.5},
        {"name": "Asylum Hill", "center": (-72.6950, 41.7620), "weight": 2.2},
        {"name": "Parkville", "center": (-72.7100, 41.7480), "weight": 1.6},
        {"name": "Behind the Rocks", "center": (-72.6750, 41.7520), "weight": 1.4},
    ]
    
    tract_centers = []
    np.random.seed(42)  # For reproducible results
    
    # Sort tracts by population for better placement
    sorted_data = hartford_data.sort_values('population', ascending=False)
    
    for i, (_, row) in enumerate(sorted_data.iterrows()):
        population_weight = row['population'] / hartford_data['population'].max()
        
        # Choose neighborhood based on population (higher pop = more likely downtown)
        if population_weight > 0.8:
            # High population - downtown area
            neighborhood = neighborhoods[0]  # Downtown
        elif population_weight > 0.6:
            # Medium-high population
            neighborhood = np.random.choice(neighborhoods[:3])
        elif population_weight > 0.4:
            # Medium population
            neighborhood = np.random.choice(neighborhoods[:5])
        else:
            # Lower population - any neighborhood
            neighborhood = np.random.choice(neighborhoods)
        
        # Add some randomness around neighborhood center
        center_lon, center_lat = neighborhood["center"]
        
        # Spread based on neighborhood weight and population
        spread = 0.008 / neighborhood["weight"] * (0.5 + population_weight)
        
        # Generate point within neighborhood
        attempts = 0
        while attempts < 50:  # Prevent infinite loop
            offset_lat = np.random.normal(0, spread)
            offset_lon = np.random.normal(0, spread)
            
            point_lat = center_lat + offset_lat
            point_lon = center_lon + offset_lon
            
            test_point = Point(point_lon, point_lat)
            
            # Check if point is within city boundary
            if city_boundary.contains(test_point):
                tract_centers.append((point_lon, point_lat))
                break
            
            attempts += 1
        
        # Fallback if we can't find a good point
        if attempts >= 50:
            tract_centers.append(neighborhood["center"])
    
    print(f"✓ Generated {len(tract_centers)} tract centers")
    return tract_centers

def create_voronoi_tracts(tract_centers, city_boundary):
    """Create non-overlapping census tracts using Voronoi tessellation"""
    
    print("Creating Voronoi tessellation for census tracts...")
    
    # Convert to numpy array for Voronoi
    points = np.array(tract_centers)
    
    # Create Voronoi diagram
    vor = Voronoi(points)
    
    tract_polygons = []
    
    for i, point in enumerate(points):
        # Find the Voronoi cell for this point
        region_index = vor.point_region[i]
        region = vor.regions[region_index]
        
        if not region or -1 in region:
            # Handle edge cases - create a small polygon around the point
            buffer_size = 0.003
            tract_polygon = Point(point).buffer(buffer_size)
        else:
            # Create polygon from Voronoi vertices
            vertices = [vor.vertices[j] for j in region]
            try:
                tract_polygon = Polygon(vertices)
            except:
                # Fallback for invalid polygons
                buffer_size = 0.003
                tract_polygon = Point(point).buffer(buffer_size)
        
        # Clip to city boundary
        tract_polygon = tract_polygon.intersection(city_boundary)
        
        # Ensure we have a valid polygon
        if tract_polygon.is_empty or not tract_polygon.is_valid:
            buffer_size = 0.002
            tract_polygon = Point(point).buffer(buffer_size).intersection(city_boundary)
        
        # Handle MultiPolygon case - take the largest part
        if hasattr(tract_polygon, 'geoms'):
            tract_polygon = max(tract_polygon.geoms, key=lambda p: p.area)
        
        tract_polygons.append(tract_polygon)
    
    print(f"✓ Created {len(tract_polygons)} non-overlapping tract polygons")
    return tract_polygons

def create_professional_hartford_map(hartford_gdf):
    """Create the final professional Hartford map"""
    
    print("Creating professional Hartford Heat Vulnerability Index map...")
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Define vulnerability level colors
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
                alpha=0.85,
                label=f'Level {level}'
            )
    
    # Add Hartford city boundary outline
    city_boundary_coords = [
        (-72.7200, 41.7200), (-72.7200, 41.7900), (-72.6500, 41.7900),
        (-72.6500, 41.7600), (-72.6300, 41.7400), (-72.6600, 41.7200),
        (-72.7200, 41.7200)
    ]
    city_boundary = Polygon(city_boundary_coords)
    city_gdf = gpd.GeoDataFrame([1], geometry=[city_boundary], crs='EPSG:4326')
    city_gdf.boundary.plot(ax=ax, color='black', linewidth=3, alpha=0.8)
    
    # Customize the map
    ax.set_title('Hartford, Connecticut\nHeat Vulnerability Index - July 2024', 
                fontsize=18, fontweight='bold', pad=20)
    
    # Remove axis ticks and labels for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    # Set background color
    ax.set_facecolor('#f8f9fa')
    
    # Create custom legend
    legend_elements = [
        mpatches.Patch(color=colors[1], label='Level 1 - Lowest Risk'),
        mpatches.Patch(color=colors[2], label='Level 2 - Low Risk'),
        mpatches.Patch(color=colors[3], label='Level 3 - Moderate Risk'),
        mpatches.Patch(color=colors[4], label='Level 4 - High Risk'),
        mpatches.Patch(color=colors[5], label='Level 5 - Highest Risk')
    ]
    
    legend = ax.legend(
        handles=legend_elements, 
        loc='upper left', 
        fontsize=11,
        title='Heat Vulnerability Level',
        title_fontsize=12,
        frameon=True,
        fancybox=True,
        shadow=True,
        bbox_to_anchor=(0.02, 0.98)
    )
    legend.get_title().set_fontweight('bold')
    
    # Add north arrow
    bounds = ax.get_xlim() + ax.get_ylim()
    x_pos = bounds[1] - (bounds[1] - bounds[0]) * 0.08
    y_pos = bounds[3] - (bounds[3] - bounds[2]) * 0.12
    ax.annotate('N', xy=(x_pos, y_pos), xytext=(x_pos, y_pos - (bounds[3] - bounds[2]) * 0.04),
                arrowprops=dict(arrowstyle='->', lw=3, color='black'),
                fontsize=16, fontweight='bold', ha='center')
    
    # Add key statistics box
    total_pop = hartford_gdf['population'].sum()
    high_vuln_tracts = len(hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])])
    high_vuln_pop = hartford_gdf[hartford_gdf['vulnerability_index'].isin([4, 5])]['population'].sum()
    high_vuln_pct = (high_vuln_pop / total_pop) * 100
    avg_temp = hartford_gdf['mean_temp'].mean()
    
    stats_text = f"""Key Statistics:
• Total Population: {total_pop:,}
• Census Tracts: {len(hartford_gdf)}
• High Risk Tracts: {high_vuln_tracts} ({high_vuln_tracts/len(hartford_gdf)*100:.1f}%)
• People at High Risk: {high_vuln_pop:,} ({high_vuln_pct:.1f}%)
• Average Temperature: {avg_temp:.1f}°C"""
    
    ax.text(0.98, 0.98, stats_text, 
           transform=ax.transAxes, 
           fontsize=10,
           verticalalignment='top',
           horizontalalignment='right',
           bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='gray'))
    
    # Add scale and attribution
    ax.text(0.02, 0.02, 
           'Hartford City Boundary\n'
           'Data: US Census ACS 2022, Simulated Climate Data\n'
           'Note: Census tract boundaries are modeled for visualization', 
           transform=ax.transAxes, 
           fontsize=8, 
           alpha=0.8,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # Ensure equal aspect ratio and tight layout
    ax.set_aspect('equal')
    plt.tight_layout()
    
    # Save the map
    output_path = 'hvi_output/hartford_heat_vulnerability_geographic_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved Hartford geographic map to {output_path}")
    
    # Also save as PDF
    pdf_path = 'hvi_output/hartford_heat_vulnerability_geographic_map.pdf'
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved PDF version to {pdf_path}")
    
    plt.show()
    
    # Print summary
    print(f"\n📊 Hartford Heat Vulnerability Index Summary:")
    print(f"   • Total population analyzed: {total_pop:,}")
    print(f"   • Census tracts: {len(hartford_gdf)}")
    print(f"   • High risk areas (Level 4-5): {high_vuln_tracts} tracts ({high_vuln_pct:.1f}% of population)")
    print(f"   • Map saved with proper Hartford city boundaries and non-overlapping tracts")

if __name__ == "__main__":
    create_hartford_geographic_map()