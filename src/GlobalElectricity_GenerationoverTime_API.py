import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ssl
import urllib.request

# Download data directly from Our World in Data
print("Downloading data from Our World in Data...")
print("This may take 30-60 seconds as the file is ~50MB...")

# Create an SSL context that doesn't verify certificates (workaround for Mac SSL issue)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

url = 'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv'

# Download with SSL workaround
try:
    df = pd.read_csv(url, storage_options={'client_kwargs': {'context': ssl_context}})
except:
    # Alternative method using urllib
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ssl_context) as response:
        df = pd.read_csv(response)

print(f"✓ Data downloaded! Total rows: {len(df)}")

# Filter for World data only
print("Processing global data...")
world_data = df[df['country'] == 'World'].copy()
print(f"✓ Filtered to World data: {len(world_data)} years")

# Set Year as index
world_data = world_data.set_index('year')

# Use primary energy consumption for historical data (goes back to 1965)
# This gives us a more complete picture than electricity-only data
energy_cols = {
    'coal_cons_change_twh': 'Coal',  # Try consumption first
    'oil_cons_change_twh': 'Oil',
    'gas_cons_change_twh': 'Gas',
    'nuclear_cons_change_twh': 'Nuclear',
    'hydro_cons_change_twh': 'Hydro',
    'wind_cons_change_twh': 'Wind',
    'solar_cons_change_twh': 'Solar',
    'biofuel_cons_change_twh': 'Bioenergy',
    'other_renewable_cons_change_twh': 'Other Renewables'
}

# Actually, let's use the electricity generation columns but check what's available
# Check which columns exist in the data
available_elec_cols = [col for col in world_data.columns if 'electricity' in col or 'elec' in col]
print(f"\nAvailable electricity columns: {len(available_elec_cols)}")

# Use the main electricity generation columns
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

# Extract relevant columns and rename them
electricity_data = world_data[[col for col in electricity_cols.keys() if col in world_data.columns]].copy()
electricity_data.columns = [electricity_cols[col] for col in electricity_data.columns]

# Remove rows with all NaN values
electricity_data = electricity_data.dropna(how='all')

# Fill NaN with 0 (for years where certain sources didn't exist yet)
electricity_data = electricity_data.fillna(0)

# Check the data range
print(f"\nData range before filtering: {electricity_data.index.min()} to {electricity_data.index.max()}")
print(f"Non-zero coal data starts: {electricity_data[electricity_data['Coal'] > 0].index.min()}")

# The issue is that the electricity data only goes back to 1985 for coal
# Let's check if we should start from 1985 or if there's better data
print("\nNote: Electricity generation data from Ember starts in 1985.")
print("For historical accuracy before 1985, consider using primary energy consumption data instead.")

# Calculate total electricity generation
total = electricity_data.sum(axis=1)

# Convert to shares (proportions)
shares = electricity_data.div(total, axis=0)

# Filter for years with meaningful data
shares = shares[shares.index >= 1985]  # Start from 1985 where we have reliable coal data

print(f"\nVisualization period: {shares.index.min()} to {shares.index.max()}")

# Define colors matching the original visualization style
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

# Order of stacking (bottom to top) - similar to US chart
energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Bioenergy', 'Other Renewables']
# Filter to only sources that exist in our data
energy_sources = [s for s in energy_sources if s in shares.columns]

# Create the figure
print("Creating visualization...")
fig, ax = plt.subplots(figsize=(14, 8))

# Create stacked area chart
ax.stackplot(shares.index, 
             [shares[source] for source in energy_sources],
             labels=energy_sources,
             colors=[colors[source] for source in energy_sources],
             alpha=0.9)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Electricity Generation', fontsize=12, fontweight='bold')
ax.set_title('Energy Source Shares in Global Electricity Generation, 1985-2024', 
             fontsize=14, fontweight='bold', pad=20)

# Set y-axis to percentage
ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

# Add grid for readability
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

# Add Source Info
ax.text(0.5, -0.12, 'Source: Our World in Data - https://ourworldindata.org/energy', 
        transform=ax.transAxes, ha='center', va='top', fontsize=10, color='#555555')

# Create legend
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), 
          frameon=True, fontsize=10)

# Tight layout to prevent label cutoff
plt.tight_layout()

# Save the figure
print("Saving figure...")
plt.savefig('global_electricity_generation.png', dpi=300, bbox_inches='tight')
print("✓ Figure saved!")

# Display the plot
plt.show()

print("\n" + "="*60)
print("Graph created successfully!")
print("="*60)
print(f"\nNote: This visualization starts in 1985 because that's when")
print(f"comprehensive global electricity generation data becomes available.")
print(f"\nFor pre-1985 data, the Our World in Data dataset relies on")
print(f"primary energy consumption figures rather than electricity-specific data.")
print("\nSummary statistics for most recent year:")
latest_year = shares.index.max()
print(f"\nYear: {latest_year}")
print(shares.loc[latest_year].sort_values(ascending=False))

# Optional: Save the processed data to CSV for reference
shares.to_csv('global_electricity_shares.csv')
print("\nProcessed data saved to 'global_electricity_shares.csv'")