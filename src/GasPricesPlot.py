import pandas as pd
import matplotlib.pyplot as plt

# 1. LOAD THE DATA
# Note: Ensure this path points to the file containing the Monthly sheet.
# If you downloaded a separate file for monthly data, update the filename below.
file_path = '/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/data/CMO-Historical-Data-Monthly (1).xlsx' 

print("--- Loading File ---")
try:
    # The monthly data is usually on a sheet named 'Monthly Prices'
    # The image shows headers on Row 7, which is index 6 in Python
    df = pd.read_excel(file_path, sheet_name='Monthly Prices', header=6)
except ValueError:
    # Fallback if specific sheet name fails
    print("Sheet 'Monthly Prices' not found. Trying the first sheet...")
    df = pd.read_excel(file_path, sheet_name=0, header=6)

# 2. SELECT & CLEAN DATA BY POSITION
# Based on your image:
# Column 0 = Date (e.g., 1960M01)
# Column 1 = Crude oil, average ($/bbl) <-- NEW
# Column 7 = Natural gas, US
# Column 8 = Natural gas, Europe
df_clean = df.iloc[:, [0, 1, 7, 8]].copy()
df_clean.columns = ['Date', 'Oil_Avg', 'Gas_US', 'Gas_EU']

print("--- First 5 rows of raw data (to check if we grabbed the right columns) ---")
print(df_clean.head())

# 3. PARSE DATES (The tricky part!)
# The format '1960M01' is special. We convert it to standard datetime objects.
# errors='coerce' turns titles/units/codes (rows that aren't dates) into NaT (Not a Time)
df_clean['Date'] = pd.to_datetime(df_clean['Date'], format='%YM%m', errors='coerce')

# Drop rows where Date conversion failed (this removes the Units row and Codes row automatically)
df_clean = df_clean.dropna(subset=['Date'])

# Convert price columns to numbers
df_clean['Gas_US'] = pd.to_numeric(df_clean['Gas_US'], errors='coerce')
df_clean['Gas_EU'] = pd.to_numeric(df_clean['Gas_EU'], errors='coerce')
df_clean['Oil_Avg'] = pd.to_numeric(df_clean['Oil_Avg'], errors='coerce')

# --- CONVERT OIL TO MMBtu ---
# 1 Barrel of Oil ≈ 5.8 MMBtu
df_clean['Oil_MMBtu'] = df_clean['Oil_Avg'] / 5.8

# Filter for year 2000+
# We access the year part of the date using .dt.year
# df_clean = df_clean[df_clean['Date'].dt.year >= 2000]

print(f"--- Data points found after cleaning: {len(df_clean)} ---")

# 4. PLOT
if df_clean.empty:
    print("CRITICAL ERROR: No data found. Check if the sheet name or header row is correct.")
else:
    plt.figure(figsize=(12, 6))
    
    # We plot against 'Date' now, which gives a nice time-series axis
    plt.plot(df_clean['Date'], df_clean['Gas_US'], label='US Natural Gas Price', color='blue', linewidth=1.5)
    plt.plot(df_clean['Date'], df_clean['Gas_EU'], label='Europe Natural Gas Price', color='red', linewidth=1.5)
    plt.plot(df_clean['Date'], df_clean['Oil_MMBtu'], label='Price of Oil ($/MMBtu eq)', color='green', linewidth=1.5)

    plt.title('Energy Prices (Monthly): US Gas vs Europe Gas vs Oil', fontsize=16)
    plt.ylabel('Price ($/MMBtu)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()
    print("Graph generated.")