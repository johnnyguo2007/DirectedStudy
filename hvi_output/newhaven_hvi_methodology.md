# New Haven Heat Vulnerability Index Methodology

## Data Sources
- Temperature: Simulated July 2024 data (NASA MODIS LST alternative)
- Demographics: US Census ACS 2022 5-year estimates
- Green Space: Simulated based on housing density patterns
- Housing: ACS housing structure data for AC access modeling

## Vulnerability Components (Weighted)
1. Temperature (30%): Mean July 2024 surface temperature
2. Income (25%): Inverse of median household income
3. AC Access (25%): Probability of air conditioning access
4. Green Space (20%): Percentage of green space coverage

## Calculation Method
- All components normalized to 0-1 scale
- Weighted composite score calculated
- Final index converted to 1-5 scale (1=lowest risk, 5=highest risk)

## New Haven-Specific Adjustments
- Moderate baseline AC access probability reflecting college town demographics
- Coastal temperature moderation effect considered
- Enhanced green space estimates reflecting East Rock Park and other natural areas
- Mixed income distribution reflecting university and urban characteristics

## Limitations
- Temperature data is simulated for demonstration
- Green space estimates based on housing density proxy
- AC access uses predictive model, not direct survey data
- Census tract geometries simplified to grid representation
