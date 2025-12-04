import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

# 1. SETUP
# ---------------------------------------------------------
# (Your API Key is preserved here, though it is good practice to keep it private)
API_KEY = 'OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU' 

# API Endpoint for Total Energy (Monthly Energy Review)
url = "https://api.eia.gov/v2/total-energy/data/"

# 2. DEFINE PARAMETERS
params = {
    "api_key": API_KEY,
    "frequency": "monthly",
    "data[0]": "value",
    "facets[msn][]": ["CLTCBUS", "NNTCBUS", "PMTCBUS"],
    "start": "1973-01",     
    "sort[0][column]": "period",
    "sort[0][direction]": "asc",
    "offset": 0,
    "length": 5000            
}

print("--- Fetching Data from EIA API ---")
try:
    response = requests.get(url, params=params)
    response.raise_for_status() 
    data = response.json()
    
    records = data['response']['data']
    df = pd.DataFrame(records)
    # Check the unique units associated with these MSNs
    if 'unit' in df.columns:
        print("--- Verified Units ---")
        print(df[['msn', 'unit']].drop_duplicates())
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    df = pd.DataFrame()

if not df.empty:
    # 3. CLEAN & PIVOT
    df['Date'] = pd.to_datetime(df['period'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    df_pivot = df.pivot(index='Date', columns='msn', values='value')
    
    name_map = {
        'CLTCBUS': 'Coal Consumption',
        'NNTCBUS': 'Natural Gas Consumption',
        'PMTCBUS': 'Petroleum (Oil) Consumption'
    }
    df_pivot.rename(columns=name_map, inplace=True)
    
    print("--- First 5 rows of clean data ---")
    print(df_pivot.head())

    # 4. PLOT
    plt.figure(figsize=(12, 7)) # Increased height slightly for the footer
    
    plt.plot(df_pivot.index, df_pivot['Natural Gas Consumption'], label='Natural Gas', color='blue', linewidth=1.5)
    plt.plot(df_pivot.index, df_pivot['Coal Consumption'], label='Coal', color='red', linewidth=1.5)
    plt.plot(df_pivot.index, df_pivot['Petroleum (Oil) Consumption'], label='Petroleum (Oil)', color='green', linewidth=1.5)

    plt.xlim(df_pivot.index.min(), df_pivot.index.max())

    plt.title('US Primary Energy Consumption (Monthly): Coal vs Gas vs Oil', fontsize=16)
    plt.ylabel('Consumption (Trillion Btu)', fontsize=12)
    plt.xlabel('Date', fontsize=12)

    # --- THE FIX ---
    # Create a list of dates starting EXACTLY at your first data point (1973),
    # stepping every 5 years ('5YS'). 
    my_ticks = pd.date_range(start=df_pivot.index.min(), end=df_pivot.index.max(), freq='5YS')
    
    # Apply these specific ticks to the axis
    plt.xticks(my_ticks, my_ticks.strftime('%Y'))
    plt.legend()
    
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # --- NEW: ADD SOURCE TEXT ---
    # (x=0.99, y=0.01) puts it in the bottom right corner
    plt.figtext(0.99, 0.01, 'Source: U.S. Energy Information Administration (EIA) - https://www.eia.gov/opendata/', 
                horizontalalignment='right', fontsize=10, color='gray', style='italic')
    
    # Adjust layout to make room for the footer text (bottom=0.05)
    plt.tight_layout(rect=[0, 0.03, 1, 1])

    # Save the figure
    plt.savefig('us_fossilfuel_consumption.png', dpi=300, bbox_inches='tight')
    
    plt.show()
    print("Graph generated.")
else:
    print("No data retrieved. Please check your API Key.")