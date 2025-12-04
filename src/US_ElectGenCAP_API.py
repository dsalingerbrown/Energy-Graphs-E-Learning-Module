import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import sys
import time

# --- CONFIGURATION ---
# REPLACE THIS WITH YOUR ACTUAL API KEY
API_KEY = "OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU" 

def get_capacity_data():
    """
    Fetches Annual Net Summer Capacity data by looping through years.
    Route: electricity/operating-generator-capacity
    
    Uses specific technology facets provided by the user.
    Fetches 'December' snapshot for each year to represent annual capacity.
    """
    url = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data"
    
    # List of technologies to filter by (Matched to user's successful query)
    technologies = [
        "Coal Integrated Gasification Combined Cycle",
        "Conventional Hydroelectric",
        "Conventional Steam Coal",
        "Geothermal",
        "Hydroelectric Pumped Storage",
        "Natural Gas Fired Combined Cycle",
        "Natural Gas Fired Combustion Turbine",
        "Natural Gas Internal Combustion Engine",
        "Natural Gas Steam Turbine",
        "Natural Gas with Compressed Air Storage",
        "Nuclear",
        "Offshore Wind Turbine",
        "Onshore Wind Turbine",
        "Petroleum Coke",
        "Petroleum Liquids",
        "Solar Photovoltaic",
        "Solar Thermal with Energy Storage",
        "Solar Thermal without Energy Storage",
        "Wood/Wood Waste Biomass",
        "Battery Energy Storage", # Added to capture 'Battery' category from original graph
        "Batteries" # Alternate label just in case
    ]

    all_data = []
    
    # Range of years to fetch
    start_year = 2008
    end_year = 2025 
    
    print(f"Fetching capacity data from {start_year} to {end_year}...")
    print("This may take 30-60 seconds...")

    for year in range(start_year, end_year + 1):
        # Fetch December data to serve as the Annual snapshot
        period = f"{year}-12"
        
        params = {
            "api_key": API_KEY,
            "frequency": "monthly",
            "data[0]": "net-summer-capacity-mw", # Updated to match user's working URL
            "start": period,               # FIX: Use start/end for date filtering
            "end": period,                 # FIX: Use start/end for date filtering
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000 
        }
        
        # Add technology facets dynamically
        # The API expects multiple 'facets[technology][]' keys
        params["facets[technology][]"] = technologies
        
        year_data = []
        page_count = 0
        
        while True:
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 400:
                    print(f"  API Error 400 for {year}: {response.text}")
                    break
                
                response.raise_for_status()
                payload = response.json()
                
                if 'response' not in payload or 'data' not in payload['response']:
                    break
                    
                batch = payload['response']['data']
                if not batch:
                    break
                    
                year_data.extend(batch)
                
                if len(batch) < params['length']:
                    break
                params['offset'] += params['length']
                page_count += 1
                
            except Exception as e:
                print(f"Error fetching {period} (page {page_count}): {e}")
                break
        
        if year_data:
            print(f"  Got {len(year_data)} generators for {year}")
            all_data.extend(year_data)
        else:
            print(f"  No data found for {year}")

    return pd.DataFrame(all_data)

def process_data(df):
    """
    Cleans EIA capacity data and groups it into the requested categories.
    """
    if df.empty:
        return df

    # Convert values to numeric
    val_col = 'net-summer-capacity-mw'
    if val_col not in df.columns:
        # Fallback if the API returns the old column name
        val_col = 'net-summer-capacity'
        if val_col not in df.columns:
            print(f"Warning: Capacity column not found. Available: {df.columns.tolist()}")
            return pd.DataFrame()
    
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
    
    # Extract Year
    df['Year'] = df['period'].astype(str).str[:4].astype(int)
    
    # Map Technologies to General Categories
    tech_map = {
        "Coal Integrated Gasification Combined Cycle": "Coal",
        "Conventional Steam Coal": "Coal",
        
        "Conventional Hydroelectric": "Hydro",
        
        "Natural Gas Fired Combined Cycle": "Gas",
        "Natural Gas Fired Combustion Turbine": "Gas",
        "Natural Gas Internal Combustion Engine": "Gas",
        "Natural Gas Steam Turbine": "Gas",
        "Natural Gas with Compressed Air Storage": "Gas",
        
        "Petroleum Coke": "Oil",
        "Petroleum Liquids": "Oil",
        
        "Nuclear": "Nuclear",
        
        "Offshore Wind Turbine": "Wind",
        "Onshore Wind Turbine": "Wind",
        
        "Solar Photovoltaic": "Solar",
        "Solar Thermal with Energy Storage": "Solar",
        "Solar Thermal without Energy Storage": "Solar",
        
        "Wood/Wood Waste Biomass": "Wood/Waste",
        
        "Geothermal": "Geothermal",
        
        "Hydroelectric Pumped Storage": "Pumped Storage",
        
        "Battery Energy Storage": "Battery",
        "Batteries": "Battery"
    }
    
    # Apply mapping
    if 'technology' in df.columns:
        df['Category'] = df['technology'].map(tech_map)
    else:
        print("Error: 'technology' column missing.")
        return pd.DataFrame()
    
    # Fill unmapped with 'Other'
    df['Category'] = df['Category'].fillna('Other')
    
    # Pivot: Year vs Category (SUMMING all generators)
    df_pivot = df.pivot_table(index='Year', columns='Category', values=val_col, aggfunc='sum')
    
    # Define Target Categories
    energy_sources = [
        'Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar',
        'Wood/Waste', 'Geothermal', 'Pumped Storage', 'Battery'
    ]
    
    # Ensure all user categories exist
    for source in energy_sources:
        if source not in df_pivot.columns:
            df_pivot[source] = 0
            
    # Sort columns
    df_pivot = df_pivot[energy_sources]
    
    # Calculate Shares
    df_pivot['Total'] = df_pivot.sum(axis=1)
    df_pivot = df_pivot[df_pivot['Total'] > 0]
    
    for source in energy_sources:
        df_pivot[source] = df_pivot[source] / df_pivot['Total']
        
    return df_pivot[energy_sources]

# --- MAIN EXECUTION ---

print("Starting API download (Capacity)...")
raw_df = get_capacity_data()

if raw_df.empty:
    print("No data returned.")
    sys.exit(1)

print("Processing data...")
df = process_data(raw_df)

if df.empty:
    print("Data processing resulted in empty dataframe.")
    sys.exit(1)

# --- PLOTTING ---

# Define colors
colors = {
    'Coal': '#5B8DB8',
    'Hydro': '#F4B042',
    'Gas': '#A8D35E',
    'Oil': '#E89CAE',
    'Nuclear': '#9AC7C4',
    'Wind': '#F79646',
    'Solar': '#FDC576',
    'Wood/Waste': '#C9A5D6',
    'Geothermal': '#D4A5A5',
    'Pumped Storage': '#B8A8D8',
    'Battery': '#AAAAAA',
    'Other': '#CCCCCC'
}

energy_sources = [col for col in df.columns if col in colors]

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# Stacked area chart
ax.stackplot(df.index, 
             [df[source] for source in energy_sources],
             labels=energy_sources,
             colors=[colors.get(source, '#CCCCCC') for source in energy_sources],
             alpha=0.9)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Installed Capacity', fontsize=12, fontweight='bold')

# Add Source Info below x-axis
ax.text(0.5, -0.12, 'Source: U.S. Energy Information Administration (EIA) - https://www.eia.gov/', 
        transform=ax.transAxes, ha='center', va='top', fontsize=10, color='#555555')

# Dynamic Title
min_year = df.index.min()
max_year = df.index.max()
ax.set_title(f'Energy Source Shares in United States Installed Capacity, {min_year}-{max_year}', 
             fontsize=14, fontweight='bold', pad=20)

ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=True, fontsize=10)

plt.tight_layout()
plt.savefig('us_installed_capacity_api.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nGraph created successfully!")
print(f"\nSummary statistics for {max_year}:")
print(df.loc[max_year].sort_values(ascending=False))