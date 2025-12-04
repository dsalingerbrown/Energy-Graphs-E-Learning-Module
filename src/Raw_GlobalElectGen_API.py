import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ssl
import urllib.request

# --- 1. DATA DOWNLOAD ---
print("Downloading data from Our World in Data (GitHub)...")
print("This may take 30-60 seconds as the file is ~50MB...")

# Create an SSL context that doesn't verify certificates (workaround for some Mac setups)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

url = 'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv'

try:
    # Try reading directly with pandas (easiest)
    df = pd.read_csv(url, storage_options={'client_kwargs': {'context': ssl_context}})
except:
    # Fallback method using urllib
    print("Direct download failed, trying urllib fallback...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ssl_context) as response:
        df = pd.read_csv(response)

print(f"✓ Data downloaded! Total rows: {len(df)}")

# --- 2. DATA PROCESSING ---
print("Processing global data...")

# Filter for World data only
world_data = df[df['country'] == 'World'].copy()
world_data = world_data.set_index('year')

# Map OWID columns to your categories
# Note: OWID electricity columns are already in TWh
electricity_cols = {
    'coal_electricity': 'Coal',
    'oil_electricity': 'Oil',
    'gas_electricity': 'Gas',
    'nuclear_electricity': 'Nuclear',
    'hydro_electricity': 'Hydro',
    'wind_electricity': 'Wind',
    'solar_electricity': 'Solar',
    'biofuel_electricity': 'Bioenergy',
    'other_renewable_exc_biofuel_electricity': 'Other Renewables'
}

# Extract and rename columns
df_plot = world_data[[col for col in electricity_cols.keys() if col in world_data.columns]].copy()
df_plot.columns = [electricity_cols[col] for col in df_plot.columns]

# Filter for relevant years (Ember data usually reliable from 1985 onwards)
df_plot = df_plot[df_plot.index >= 1985]

# Fill NaNs with 0 to allow plotting (e.g. Solar was 0 in 1985)
df_plot = df_plot.fillna(0)

# --- 3. PLOTTING ---

# Define colors (Matching your US chart)
colors = {
    'Coal': '#5B8DB8',
    'Hydro': '#F4B042',
    'Gas': '#A8D35E',
    'Oil': '#E89CAE',
    'Nuclear': '#9AC7C4',
    'Wind': '#F79646',
    'Solar': '#FDC576',
    'Bioenergy': '#C9A5D6',
    'Other Renewables': '#D4A5A5'
}

energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Bioenergy', 'Other Renewables']
# Only keep sources that actually exist in the dataframe
energy_sources = [s for s in energy_sources if s in df_plot.columns]

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# Plot Lines (Raw TWh)
for source in energy_sources:
    # Only plot if there is data
    if df_plot[source].max() > 0:
        ax.plot(df_plot.index, df_plot[source], 
                label=source, 
                color=colors.get(source, '#CCCCCC'), 
                linewidth=2.5, 
                marker='o', 
                markersize=4)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Electricity Generation (TWh)', fontsize=12, fontweight='bold')

# Dynamic Title
min_year = df_plot.index.min()
max_year = df_plot.index.max()
ax.set_title(f'Global Electricity Generation by Source, {min_year}-{max_year}', 
             fontsize=14, fontweight='bold', pad=20)

# Add Source Info
ax.text(0.5, -0.12, 'Source: Our World in Data - https://ourworldindata.org/energy', 
        transform=ax.transAxes, ha='center', va='top', fontsize=10, color='#555555')

# Grid and Legend
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_ylim(bottom=0)
ax.legend(loc='upper left', bbox_to_anchor=(1, 1), frameon=True, fontsize=10)

plt.tight_layout()

# Save
plt.savefig('global_electricity_generation_raw.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n" + "="*60)
print("Graph created successfully!")
print("="*60)
print(f"Summary statistics for {max_year} (TWh):")
print(df_plot.loc[max_year].sort_values(ascending=False))