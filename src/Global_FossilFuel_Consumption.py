import pandas as pd
import matplotlib.pyplot as plt
import requests

# 1. SETUP
# ---------------------------------------------------------
API_KEY = 'OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU' 
DATA_URL = "https://api.eia.gov/v2/international/data/"
FACET_URL = "https://api.eia.gov/v2/international/data/facet/productId"

# The fuels we want to find
TARGET_FUELS = ['Coal', 'Natural gas', 'Petroleum and other liquids']
selected_ids = []

# ---------------------------------------------------------
# 2. DISCOVERY (Find IDs)
# ---------------------------------------------------------
print("--- Step 1: Discovering IDs ---")
try:
    # Ask API what products exist
    r = requests.get(FACET_URL, params={
        "api_key": API_KEY, 
        "facets[activityId][]": "2", 
        "facets[countryRegionId][]": "WORL"
    })
    r.raise_for_status()
    
    df_products = pd.DataFrame(r.json().get('response', {}).get('facets', []))
    
    # Match our targets to the API list
    for target in TARGET_FUELS:
        match = df_products[df_products['name'].str.contains(target, case=False, na=False)]
        if not match.empty:
            fid = match.iloc[0]['id']
            fname = match.iloc[0]['name']
            selected_ids.append(fid)
            print(f"  ✓ Found '{fname}' (ID: {fid})")
            
except Exception as e:
    print(f"Discovery Failed: {e}. Using defaults.")
    selected_ids = ["7", "26", "5"] # Defaults if discovery fails

# ---------------------------------------------------------
# 3. FETCH DATA
# ---------------------------------------------------------
print(f"\n--- Step 2: Fetching Data (IDs: {selected_ids}) ---")
params = {
    "api_key": API_KEY,
    "frequency": "annual",
    "data[0]": "value",
    "facets[activityId][]": "2",
    "facets[countryRegionId][]": "WORL",
    "facets[unit][]": "QBTU",             # Requesting Quadrillion Btu
    "facets[productId][]": selected_ids,
    "sort[0][column]": "period",
    "sort[0][direction]": "asc",
    "offset": 0,
    "length": 5000            
}

try:
    response = requests.get(DATA_URL, params=params)
    response.raise_for_status()
    df = pd.DataFrame(response.json()['response']['data'])
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    df = pd.DataFrame()

# ---------------------------------------------------------
# 4. *** THE VERIFICATION REPORT ***
# ---------------------------------------------------------
if not df.empty:
    print("\n" + "="*60)
    print("      DATA VERIFICATION REPORT (Source of Truth)")
    print("="*60)
    print("The following variables were successfully retrieved:")
    
    # We grab the unique combinations of Name, Unit, and Activity from the actual data
    # This proves exactly what units are in the dataframe.
    verify_cols = ['productName', 'unit', 'activityName', 'countryRegionName']
    
    # Filter for columns that actually exist in response
    cols_to_show = [c for c in verify_cols if c in df.columns]
    
    # Print the unique rows (drop duplicates)
    report = df[cols_to_show].drop_duplicates().sort_values('productName')
    print(report.to_string(index=False))
    print("="*60 + "\n")

    # ---------------------------------------------------------
    # 5. CLEAN & PLOT
    # ---------------------------------------------------------
    df['Date'] = pd.to_datetime(df['period'].astype(str), format='%Y')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df_pivot = df.pivot(index='Date', columns='productName', values='value')

    plt.figure(figsize=(12, 7))
    
    # Smart Plotting Loop
    for col_name in df_pivot.columns:
        c_lower = col_name.lower()
        color = 'gray'
        if 'coal' in c_lower: color = 'red'
        elif 'gas' in c_lower: color = 'blue'
        elif 'petroleum' in c_lower or 'oil' in c_lower: color = 'green'
        
        plt.plot(df_pivot.index, df_pivot[col_name], label=col_name, color=color, linewidth=2)

    plt.xlim(df_pivot.index.min(), df_pivot.index.max())
    plt.title('Global Fossil Fuel Consumption (Annual)', fontsize=16)
    
    # Use the unit found in the verification step for the label
    current_unit = report['unit'].iloc[0] if 'unit' in report.columns else "Unknown"
    plt.ylabel(f'Consumption (Quadrillion BTU)', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.figtext(0.99, 0.01, 'Source: U.S. Energy Information Administration (EIA) - https://www.eia.gov/opendata/', 
                horizontalalignment='right', fontsize=10, color='gray', style='italic')
    
    plt.tight_layout()

    # Save the figure
    plt.savefig('global_fossilfuel_consumption.png', dpi=300, bbox_inches='tight')

    plt.show()
    print("Graph generated.")
else:
    print("No data retrieved.")