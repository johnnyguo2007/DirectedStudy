Based on the NYC Heat Vulnerability Index, here's what you'll need to create a similar system for a Connecticut city:

  Core Data Requirements:

  1. Surface Temperature Data - NASA satellite data for daytime summer temperatures
  2. Green Space Coverage - Percentage of area with vegetation/parks
  3. Air Conditioning Access - Household AC availability (from Census/ACS)
  4. Income Data - Median neighborhood income (Census/ACS)

  Technical Components:

  - Interactive map interface with neighborhood boundaries
  - Scoring system (1-5 scale) for vulnerability assessment
  - Data visualization showing comparative metrics
  - Neighborhood lookup functionality

  Data Sources You'll Need:

  - American Community Survey for demographic/income data
  - NASA satellite imagery for surface temperature
  - Local housing surveys for AC availability
  - Municipal GIS data for green space mapping

  Implementation Architecture:

  - JavaScript-based interactive interface
  - Client-side data loading (likely from static files)
  - Map visualization library (likely Leaflet or similar)
  - Data processing to calculate composite vulnerability scores

  The key insight is that this combines multiple datasets into a single vulnerability index, emphasizing how structural inequities create heat risk disparities across neighborhoods.
