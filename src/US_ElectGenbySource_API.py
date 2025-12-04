import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import sys

# --- CONFIGURATION ---
# REPLACE THIS WITH YOUR ACTUAL API KEY
API_KEY = "OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU" 

def get_eia_data():
    """
    Fetches monthly Net Generation data for the Total US (All Sectors)
    from the EIA API v2.
    """
    url = "https://api.eia.gov/v2/electricity/electric-power-operational-data/data"
    
    # We request 'generation' for Total US (US) and All Sectors (99)
    # This avoids double counting individual plants.
    params = {
        "api_key": API_KEY,
        "frequency": "monthly",
        "data[0]": "generation",
        "facets[location][]": "US",
        "facets[sectorid][]": "99", # 99 = Total Electric Power Industry
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000 # Max rows per call. We might need to loop if data > 5000 rows
    }
    
    all_data = []
    
    # Loop to handle pagination (data > 5000 rows)
    # 20+ years of monthly data * ~12 fuel types = ~3000 rows, so one call usually suffices,
    # but looping is safer for robustness.
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
            
            # Check if we need to fetch more
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
    """
    # Convert 'generation' to numeric, forcing errors to NaN (then 0)
    df['generation'] = pd.to_numeric(df['generation'], errors='coerce').fillna(0)
    
    # Extract Year from the 'period' column (format YYYY-MM)
    df['Year'] = df['period'].astype(str).str[:4].astype(int)
    
    # Define mapping from EIA 'fueltypeid' to User Categories
    # EIA Codes: COW(Coal), NG(Gas), PEL(Oil), PC(PetCoke), NUC(Nuclear), 
    # WAT(Hydro), WND(Wind), SUN(Solar), GEO(Geothermal), 
    # WDS(Wood), WAS(Waste/Biomass), OTH(Other), HPS(Pumped Storage - usually negative/load)
    
    fuel_map = {
        'COW': 'Coal',
        'NG': 'Gas',
        'OOG': 'Gas', # Other Gases
        'PEL': 'Oil',
        'PC': 'Oil',
        'NUC': 'Nuclear',
        'WAT': 'Hydro',
        'WND': 'Wind',
        'SUN': 'Solar',
        'GEO': 'Geothermal',
        'WDS': 'Wood/Waste',
        'WAS': 'Wood/Waste', # Agricultural by-products/Landfill gas often here
        'LFG': 'Wood/Waste', # Landfill Gas
        'MSW': 'Wood/Waste', # Municipal Solid Waste
        'BIO': 'Wood/Waste', # Biogenic Municipal Solid Waste
        'OTH': 'Wood/Waste'  # Grouping 'Other' into Wood/Waste to keep categories consistent
    }
    
    # Map the fuel types
    df['Category'] = df['fueltypeid'].map(fuel_map)
    
    # Drop rows that didn't map (e.g., Total or Unknown)
    df = df.dropna(subset=['Category'])
    
    # Pivot to get Years as Index and Categories as Columns
    # Summing monthly data into annual totals
    df_pivot = df.pivot_table(index='Year', columns='Category', values='generation', aggfunc='sum')
    
    # Ensure all user categories exist, fill missing with 0
    energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Wood/Waste', 'Geothermal']
    for source in energy_sources:
        if source not in df_pivot.columns:
            df_pivot[source] = 0
            
    # Sort columns by user list
    df_pivot = df_pivot[energy_sources]
    
    # CONVERT TO SHARES (PERCENTAGE 0-1)
    # Row sum is the total generation for that year
    df_pivot['Total'] = df_pivot.sum(axis=1)
    
    # Divide each column by the total to get the share
    for source in energy_sources:
        df_pivot[source] = df_pivot[source] / df_pivot['Total']
        
    return df_pivot[energy_sources]

# --- MAIN EXECUTION ---

print("Starting API download...")
raw_df = get_eia_data()

if raw_df.empty:
    print("No data returned. Check your API Key.")
    sys.exit(1)

print("Processing data...")
df = process_data(raw_df)

# --- PLOTTING (Exact code from user, adjusted inputs) ---

# Define colors matching the original visualization
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

# Order of stacking (bottom to top)
energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Wood/Waste', 'Geothermal']

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# Create stacked area chart
ax.stackplot(df.index, 
             [df[source] for source in energy_sources],
             labels=energy_sources,
             colors=[colors[source] for source in energy_sources],
             alpha=0.9)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Electricity Generation', fontsize=12, fontweight='bold')

# Add Source Info below x-axis
ax.text(0.5, -0.12, 'Source: U.S. Energy Information Administration (EIA) - https://www.eia.gov/', 
        transform=ax.transAxes, ha='center', va='top', fontsize=10, color='#555555')

# Dynamic Title with Date Range
min_year = df.index.min()
max_year = df.index.max()
ax.set_title(f'Energy Source Shares in United States Electricity Generation, {min_year}-{max_year}', 
             fontsize=14, fontweight='bold', pad=20)

# Set y-axis to percentage
ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

# Add grid for readability
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

# Create legend
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), 
          frameon=True, fontsize=10)

# Tight layout to prevent label cutoff
plt.tight_layout()

# Save the figure
plt.savefig('us_electricity_generation_api.png', dpi=300, bbox_inches='tight')

# Display the plot
plt.show()

print("Graph created successfully!")
print(f"\nSummary statistics for {max_year}:")
print(df.loc[max_year].sort_values(ascending=False))