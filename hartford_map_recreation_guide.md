# Hartford Heat Vulnerability Interactive Map - Recreation Guide

This document provides all the extracted data and parameters needed to recreate the exact Hartford Heat Vulnerability Interactive Map.

## Map Configuration

### Center and Zoom
- **Map Center**: `[41.75528543647294, -72.68522108383712]` (Latitude, Longitude)
- **Zoom Level**: `12`
- **Coordinate Reference System**: `EPSG3857`
- **Base Map**: CartoDB Light (`https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`)

### Map Container Settings
- **Min Zoom**: 0
- **Max Zoom**: 18
- **Max Native Zoom**: 18
- **No Wrap**: false
- **Detect Retina**: false

## Color Scheme and Vulnerability Levels

### Level 1 - Lowest Risk
- **Color**: `#2E8B57` (Sea Green)
- **Fill Opacity**: `0.6`
- **Count**: 4 tracts

### Level 2 - Low Risk  
- **Color**: `#90EE90` (Light Green)
- **Fill Opacity**: `0.7`
- **Count**: 50 tracts

### Level 3 - Moderate Risk
- **Color**: `#FFFF00` (Yellow)
- **Fill Opacity**: `0.8`
- **Count**: 120 tracts

### Level 4 - High Risk
- **Color**: `#FFA500` (Orange)
- **Fill Opacity**: `0.9`
- **Count**: 66 tracts

### Level 5 - Highest Risk
- **Color**: `#FF4500` (Orange Red)
- **Fill Opacity**: `1.0`
- **Count**: 9 tracts

## Common Styling Parameters

All census tracts share these styling properties:
- **Stroke Color**: `white`
- **Stroke Opacity**: `0.8`
- **Stroke Weight**: `1`

## Census Tract Data Structure

Each census tract contains the following data fields:

### Geographic Data
- **GeoJSON Coordinates**: Polygon coordinates defining tract boundaries
- **Tract ID**: Census tract identifier (e.g., "400101")

### Styling Information
- **Fill Color**: Based on vulnerability level
- **Fill Opacity**: Varies by level (0.6 to 1.0)
- **Stroke properties**: Consistent white border

### Popup Data (Detailed Information)
Each tract popup contains:
- **Vulnerability Level**: 1-5 scale
- **Population**: Total population count
- **Median Income**: In USD format (e.g., "$58,792")
- **Temperature**: In Celsius (e.g., "29.8°C") 
- **AC Access**: Percentage with air conditioning access
- **Green Space**: Percentage of green space coverage
- **Vulnerability Score**: Numeric score (0-1 scale)

## Sample Tract Examples

### Tract 400101 (Level 3 - Moderate Risk)
- **Color**: #FFFF00 (Yellow)
- **Population**: 3,845
- **Median Income**: $58,792
- **Temperature**: 29.8°C
- **AC Access**: 91.7%
- **Green Space**: 28.1%
- **Vulnerability Score**: 0.422

### Tract 400102 (Level 3 - Moderate Risk)
- **Color**: #FFFF00 (Yellow)
- **Population**: 2,799
- **Median Income**: $30,194
- **Temperature**: 28.8°C
- **AC Access**: 47.1%
- **Green Space**: 44.9%
- **Vulnerability Score**: 0.512

## Total Dataset Summary

- **Total Census Tracts**: 249
- **Data Source**: Hartford Heat Vulnerability Interactive Map HTML file
- **Extracted Data**: `/home/jguo/projects/DS/hartford_census_tract_data.json`

## Leaflet.js Implementation Notes

To recreate this map programmatically:

1. **Initialize Map**: Use Leaflet.js with the specified center and zoom
2. **Add Base Layer**: CartoDB Light tile layer
3. **Load GeoJSON**: For each tract, create a GeoJSON layer with:
   - Polygon coordinates from the extracted data
   - Styling function based on vulnerability level
   - Popup with detailed tract information
   - Tooltip showing "Tract {ID}: Level {X} Risk"

4. **Legend**: Create HTML legend showing the 5 vulnerability levels with colors

## Map Interactivity

- **Tooltips**: Hover to show "Tract {ID}: Level {X} Risk"
- **Popups**: Click to show detailed information table
- **Styling**: Dynamic coloring based on vulnerability level

## Files Generated

1. **`/home/jguo/projects/DS/hartford_census_tract_data.json`**: Complete extracted data
2. **`/home/jguo/projects/DS/extract_census_data.py`**: Extraction script
3. **`/home/jguo/projects/DS/hartford_map_recreation_guide.md`**: This documentation

All data has been successfully extracted and is ready for programmatic recreation of the exact same interactive map.