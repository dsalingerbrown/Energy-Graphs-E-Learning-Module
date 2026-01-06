import pandas as pd
import matplotlib.pyplot as plt
import requests

# 1. SETUP
# ---------------------------------------------------------
API_KEY = 'OuVPsef3oTE0qu7LRhyGikO8aLGz2VTWQCWutOPU' 

GLOBAL_URL = "https://api.eia.gov/v2/international/data/"
US_URL = "https://api.eia.gov/v2/total-energy/data/"

# 2. FETCH GLOBAL DATA
# ---------------------------------------------------------
print("--- Step 1: Fetching Global Data ---")

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
    
    # --- UPDATE 1: Filter to include 1980 through 2024 ONLY ---
    df_global = df_global[(df_global['Date'].dt.year >= 1980) & (df_global['Date'].dt.year <= 2024)]

    # Pivot
    global_pivot = df_global.pivot(index='Date', columns='productName', values='value')
    print("✓ Global data loaded (1980-2024).")
    
except Exception as e:
    print(f"Global Data Failed: {e}")
    global_pivot = pd.DataFrame()

# 3. FETCH US DATA
# ---------------------------------------------------------
print("--- Step 2: Fetching US Data ---")

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
    
    # Pivot (Raw Monthly Data in Trillion BTU)
    us_pivot = df_us.pivot(index='Date', columns='msn', values='value')
    
    # 1. Resample Monthly to Annual (Sum)
    us_annual = us_pivot.resample('YS').sum()
    
    # 2. CONVERSION: Trillion BTU -> Quadrillion BTU
    us_annual = us_annual / 1000.0

    # --- UPDATE 2: Drop any rows after 2024 ---
    # This removes the incomplete 2025 sum
    us_annual = us_annual[us_annual.index.year <= 2024]
    
    print("✓ US data loaded, aggregated, converted, and trimmed to 2024.")

    # ---------------------------------------------------------
    # --- VERIFICATION BLOCK ---
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("      DATA VERIFICATION CHECK")
    print("="*50)

    # Check 2020 (Still safe, as it is <= 2024)
    check_year = '2020'
    check_col = 'NNTCBUS' 

    if check_year in us_pivot.index.strftime('%Y'):
        print(f"INSPECTING: Year {check_year} | Column '{check_col}' (Natural Gas)")

        # A. Show the 12 Monthly values from the RAW pivot
        monthly_data = us_pivot.loc[check_year, check_col]
        print(f"\n1. Raw Monthly Data (Trillion BTU):\n{monthly_data}")

        # B. Calculate manual sum of those 12 months
        manual_sum_trillion = monthly_data.sum()
        print(f"\n2. Manual Sum of Months: {manual_sum_trillion:,.2f} Trillion BTU")

        # C. Calculate manual conversion
        manual_quad = manual_sum_trillion / 1000.0
        print(f"3. Manual Conversion (/1000): {manual_quad:,.4f} Quadrillion BTU")

        # D. Compare to what is inside your final 'us_annual' DataFrame
        code_result = us_annual.loc[f'{check_year}-01-01', check_col]
        print(f"4. Your Code's Final Value:   {code_result:,.4f} Quadrillion BTU")

        # E. Verdict
        if abs(manual_quad - code_result) < 0.0001:
            print("\n>> STATUS: SUCCESS. The aggregation and unit conversion are correct.")
        else:
            print("\n>> STATUS: FAILURE. The values do not match.")
    else:
        print("Verification skipped (Year 2020 not in data).")
    print("="*50 + "\n")
    # ---------------------------------------------------------

except Exception as e:
    print(f"US Data Failed: {e}")
    us_annual = pd.DataFrame()

# 4. PLOT GENERATION
# ---------------------------------------------------------

if not global_pivot.empty and not us_annual.empty:
    
    graphs = [
        {"fuel": "Coal", "global_col": "Coal", "us_col": "CLTCBUS", "color": "red"},
        {"fuel": "Natural Gas", "global_col": "Dry natural gas", "us_col": "NNTCBUS", "color": "blue"},
        {"fuel": "Oil", "global_col": "Petroleum and other liquids", "us_col": "PMTCBUS", "color": "green"}
    ]

    print("\n--- Generating 3 Graphs ---")
    
    for g in graphs:
        plt.figure(figsize=(10, 6))
        
        if g['global_col'] in global_pivot.columns:
            plt.plot(global_pivot.index, global_pivot[g['global_col']], 
                     label='Global (Solid)', color=g['color'], linestyle='-', linewidth=2)

        if g['us_col'] in us_annual.columns:
            plt.plot(us_annual.index, us_annual[g['us_col']], 
                     label='US (Dashed)', color=g['color'], linestyle='--', linewidth=2)

        plt.title(f"Annual {g['fuel']} Consumption: Global vs US (1980-2024)", fontsize=16)
        plt.ylabel("Consumption (Quadrillion BTU)", fontsize=12)
        plt.xlabel("Year", fontsize=12)
        
        # --- UPDATE 3: Explicitly lock the axis to 2024 ---
        plt.xlim(pd.Timestamp('1980-01-01'), pd.Timestamp('2024-01-01'))
        
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Footer
        plt.figtext(0.99, 0.01, 'Source: EIA International & Total Energy Data', 
                    horizontalalignment='right', fontsize=9, color='gray', style='italic')

        plt.tight_layout()
        
        filename = f"compare_{g['fuel'].replace(' ', '_').lower()}.png"
        plt.savefig(filename, dpi=300)
        print(f"Saved: {filename}")

else:
    print("Error: One or both datasets failed to load.")