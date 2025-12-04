import pandas as pd
import matplotlib.pyplot as plt
import requests

# 1. SETUP
# ---------------------------------------------------------
API_KEY = 'OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU' 

GLOBAL_URL = "https://api.eia.gov/v2/international/data/"
US_URL = "https://api.eia.gov/v2/total-energy/data/"

# 2. FETCH GLOBAL DATA (Already in Quadrillion BTU)
# ---------------------------------------------------------
print("--- Step 1: Fetching Global Data ---")

# IDs: 7=Coal, 26=Natural Gas, 5=Petroleum
global_params = {
    "api_key": API_KEY,
    "frequency": "annual",
    "data[0]": "value",
    "facets[activityId][]": "2",          
    "facets[countryRegionId][]": "WORL",  
    "facets[unit][]": "QBTU",             
    "facets[productId][]": ["7", "26", "5"], 
    "start": "1980",                      
    "sort[0][column]": "period",
    "sort[0][direction]": "asc",
    "length": 5000            
}

try:
    r_global = requests.get(GLOBAL_URL, params=global_params)
    r_global.raise_for_status()
    df_global = pd.DataFrame(r_global.json()['response']['data'])
    
    # Process Dates
    df_global['Date'] = pd.to_datetime(df_global['period'].astype(str), format='%Y')
    df_global['value'] = pd.to_numeric(df_global['value'], errors='coerce')
    df_global = df_global[df_global['Date'].dt.year >= 1980]

    # Pivot
    global_pivot = df_global.pivot(index='Date', columns='productName', values='value')
    
    print(f"[DEBUG] Global Columns found: {global_pivot.columns.tolist()}")
    print("✓ Global data loaded (Quadrillion BTU).")
    
except Exception as e:
    print(f"Global Data Failed: {e}")
    global_pivot = pd.DataFrame()

# 3. FETCH US DATA (In Trillion BTU -> Needs Conversion)
# ---------------------------------------------------------
print("--- Step 2: Fetching US Data ---")

# MSNs: CLTCBUS (Coal), NNTCBUS (Gas), PMTCBUS (Oil)
us_params = {
    "api_key": API_KEY,
    "frequency": "monthly",
    "data[0]": "value",
    "facets[msn][]": ["CLTCBUS", "NNTCBUS", "PMTCBUS"],
    "start": "1980-01",                   
    "sort[0][column]": "period",
    "sort[0][direction]": "asc",
    "length": 5000            
}

try:
    r_us = requests.get(US_URL, params=us_params)
    r_us.raise_for_status()
    df_us = pd.DataFrame(r_us.json()['response']['data'])
    
    # Process Dates
    df_us['Date'] = pd.to_datetime(df_us['period'])
    df_us['value'] = pd.to_numeric(df_us['value'], errors='coerce')
    
    # Pivot
    us_pivot = df_us.pivot(index='Date', columns='msn', values='value')
    
    # 1. Resample Monthly to Annual (Sum)
    us_annual = us_pivot.resample('YS').sum()
    
    # 2. CONVERSION: Trillion BTU -> Quadrillion BTU
    us_annual = us_annual / 1000.0
    
    print("✓ US data loaded, aggregated to annual, and converted to Quadrillion BTU.")

except Exception as e:
    print(f"US Data Failed: {e}")
    us_annual = pd.DataFrame()

# 4. PLOT GENERATION
# ---------------------------------------------------------

if not global_pivot.empty and not us_annual.empty:
    
    # Configuration - UPDATED 'global_col' for Natural Gas
    graphs = [
        {
            "fuel": "Coal", 
            "global_col": "Coal", 
            "us_col": "CLTCBUS", 
            "color": "red"
        },
        {
            "fuel": "Natural Gas", 
            "global_col": "Dry natural gas", # <--- UPDATED HERE
            "us_col": "NNTCBUS", 
            "color": "blue"
        },
        {
            "fuel": "Oil", 
            "global_col": "Petroleum and other liquids", 
            "us_col": "PMTCBUS", 
            "color": "green"
        }
    ]

    print("\n--- Generating 3 Graphs ---")
    
    for g in graphs:
        plt.figure(figsize=(10, 6))
        
        # Plot Global (Solid Line)
        if g['global_col'] in global_pivot.columns:
            plt.plot(global_pivot.index, global_pivot[g['global_col']], 
                     label='Global (Solid)', color=g['color'], linestyle='-', linewidth=2)
        else:
            print(f"WARNING: Could not find '{g['global_col']}' in Global Data.")

        # Plot US (Dashed Line)
        if g['us_col'] in us_annual.columns:
            plt.plot(us_annual.index, us_annual[g['us_col']], 
                     label='US (Dashed)', color=g['color'], linestyle='--', linewidth=2)

        # Formatting
        plt.title(f"{g['fuel']} Consumption: Global vs US (Annual)", fontsize=16)
        plt.ylabel("Consumption (Quadrillion BTU)", fontsize=12)
        plt.xlabel("Year", fontsize=12)
        
        plt.xlim(pd.Timestamp('1980-01-01'), max(global_pivot.index.max(), us_annual.index.max()))

        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        
        plt.figtext(0.99, 0.01, 'Source: EIA International & Total Energy Data', 
                    horizontalalignment='right', fontsize=9, color='gray', style='italic')

        plt.tight_layout()
        
        filename = f"compare_{g['fuel'].replace(' ', '_').lower()}.png"
        plt.savefig(filename, dpi=300)
        # plt.show() 
        print(f"Saved: {filename}")

else:
    print("Error: One or both datasets failed to load.")