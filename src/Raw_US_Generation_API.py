import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import requests
import sys

# --- CONFIGURATION ---
API_KEY = "OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU" 

def get_eia_data():
    """
    Fetches monthly Net Generation data for the Total US (All Sectors)
    from the EIA API v2.
    """
    url = "https://api.eia.gov/v2/electricity/electric-power-operational-data/data"
    
    # We request 'generation' for Total US (US) and All Sectors (99)
    params = {
        "api_key": API_KEY,
        "frequency": "monthly",
        "data[0]": "generation",
        "facets[location][]": "US",
        "facets[sectorid][]": "99", # 99 = Total Electric Power Industry
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000 
    }
    
    all_data = []
    
    # Loop to handle pagination
    while True:
        try:
            print(f"Fetching data offset {params['offset']}...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            
            if 'response' not in payload or 'data' not in payload['response']:
                break
                
            batch = payload['response']['data']
            if not batch:
                break
                
            all_data.extend(batch)
            
            if len(batch) < params['length']:
                break
            params['offset'] += params['length']
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            sys.exit(1)
            
    return pd.DataFrame(all_data)

def process_data(df):
    """
    Cleans EIA data and groups it into the requested categories.
    Returns RAW generation figures (not shares).
    """
    # Convert 'generation' to numeric
    df['generation'] = pd.to_numeric(df['generation'], errors='coerce').fillna(0)
    
    # Extract Year
    df['Year'] = df['period'].astype(str).str[:4].astype(int)
    
    # Define mapping from EIA 'fueltypeid' to User Categories
    fuel_map = {
        'COW': 'Coal',
        'NG': 'Gas',
        'OOG': 'Gas',
        'PEL': 'Oil',
        'PC': 'Oil',
        'NUC': 'Nuclear',
        'WAT': 'Hydro',
        'WND': 'Wind',
        'SUN': 'Solar',
        'GEO': 'Geothermal',
        'WDS': 'Wood/Waste',
        'WAS': 'Wood/Waste',
        'LFG': 'Wood/Waste',
        'MSW': 'Wood/Waste',
        'BIO': 'Wood/Waste',
        'OTH': 'Wood/Waste'
    }
    
    df['Category'] = df['fueltypeid'].map(fuel_map)
    df = df.dropna(subset=['Category'])
    
    # Pivot: Summing monthly data into annual totals
    df_pivot = df.pivot_table(index='Year', columns='Category', values='generation', aggfunc='sum')
    
    # Ensure all user categories exist
    energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Wood/Waste', 'Geothermal']
    for source in energy_sources:
        if source not in df_pivot.columns:
            df_pivot[source] = 0
            
    # Sort columns by user list
    df_pivot = df_pivot[energy_sources]
    
    # NOTE: We are NOT calculating shares here. We return raw MWh.
    return df_pivot

# --- MAIN EXECUTION ---

print("Starting API download...")
raw_df = get_eia_data()

if raw_df.empty:
    print("No data returned. Check your API Key.")
    sys.exit(1)

print("Processing data...")
df = process_data(raw_df)

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
    'Geothermal': '#D4A5A5'
}

energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Wood/Waste', 'Geothermal']

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# PLOT LINES instead of Stackplot
for source in energy_sources:
    ax.plot(df.index, df[source], 
            label=source, 
            color=colors[source], 
            linewidth=2.5, 
            marker='o',      # Add dots for data points
            markersize=4)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Net Generation (Megawatthours)', fontsize=12, fontweight='bold')

# Dynamic Title
min_year = df.index.min()
max_year = df.index.max()
ax.set_title(f'United States Electricity Generation by Source, {min_year}-{max_year}', 
             fontsize=14, fontweight='bold', pad=20)

# Add Source Info
ax.text(0.5, -0.12, 'Source: U.S. Energy Information Administration (EIA) - https://www.eia.gov/', 
        transform=ax.transAxes, ha='center', va='top', fontsize=10, color='#555555')

# Format Y-Axis to Billions (B) for readability
def billions_formatter(x, pos):
    return f'{x*1e-9:.1f}B'

ax.yaxis.set_major_formatter(ticker.FuncFormatter(billions_formatter))

# Add grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Legend
ax.legend(loc='upper left', bbox_to_anchor=(1, 1), frameon=True, fontsize=10)

plt.tight_layout()

# Save
plt.savefig('us_electricity_generation_raw.png', dpi=300, bbox_inches='tight')
plt.show()

print("Graph created successfully!")
print(f"\nSummary statistics for {max_year} (MWh):")
print(df.loc[max_year].sort_values(ascending=False))