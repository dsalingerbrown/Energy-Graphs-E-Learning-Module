import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
df = pd.read_csv('/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/MER_T07_07B.csv')

print("Initial data shape:", df.shape)
print("\nFirst few rows:")
print(df.head(10))
print("\nColumn names:", df.columns.tolist())
print("\nUnique descriptions:")
print(df['Description'].unique())

# Filter out "Not Available" values and "Total Electric Power Sector" rows
df = df[df['Value'] != 'Not Available'].copy()
df = df[~df['Description'].str.contains('Total', case=False, na=False)].copy()

# Convert Value to numeric (it's in Million Kilowatts)
df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

# Extract year from YYYYMM column
df['Year'] = df['YYYYMM'].astype(str).str[:4].astype(int)

# For each year, take only December data (or last month available) to avoid double counting
# Group by Year and Description, take the last entry for each year
df_yearly = df.sort_values('YYYYMM').groupby(['Year', 'Description']).last().reset_index()

print("\nAfter filtering - unique years:", sorted(df_yearly['Year'].unique()))
print("\nEnergy sources found:")
print(df_yearly['Description'].unique())

# Pivot the data to have years as rows and energy sources as columns
capacity_pivot = df_yearly.pivot(index='Year', columns='Description', values='Value')

print("\nPivot table shape:", capacity_pivot.shape)
print("\nColumns in pivot:", capacity_pivot.columns.tolist())

# Fill NaN values with 0 (for years where a source didn't exist)
capacity_pivot = capacity_pivot.fillna(0)

# Column renaming
column_mapping = {
    'Coal Electric Power Sector, Net Summer Capacity': 'Coal',
    'Natural Gas Electric Power Sector, Net Summer Capacity': 'Gas',
    'Petroleum Electric Power Sector, Net Summer Capacity': 'Oil',
    'Nuclear Electric Power Sector, Net Summer Capacity': 'Nuclear',
    'Conventional Hydroelectric Power Electric Power Sector, Net Summer Capacity': 'Hydro',
    'Wind Electric Power Sector, Net Summer Capacity': 'Wind',
    'Solar Electric Power Sector, Net Summer Capacity': 'Solar',
    'Wood Electric Power Sector, Net Summer Capacity': 'Wood/Waste',
    'Waste Electric Power Sector, Net Summer Capacity': 'Wood/Waste',
    'Geothermal Electric Power Sector, Net Summer Capacity ': 'Geothermal',
    'Hydroelectric Pumped Storage Electric Power Sector, Net Summer Capacity': 'Pumped Storage',
    'Battery Storage Electric Power Sector, Net Summer Capacity': 'Battery',
}

capacity_pivot = capacity_pivot.rename(columns=column_mapping)

# --- Collapse duplicate columns automatically ---
if capacity_pivot.columns.duplicated().any():
    for col in capacity_pivot.columns[capacity_pivot.columns.duplicated()].unique():
        dups = capacity_pivot.filter(regex=f'^{col}$')
        capacity_pivot[col] = dups.sum(axis=1)
    capacity_pivot = capacity_pivot.loc[:, ~capacity_pivot.columns.duplicated()]

# Combine solar if needed
if 'Solar' in capacity_pivot.columns and 'Solar Thermal' in capacity_pivot.columns:
    capacity_pivot['Solar'] += capacity_pivot['Solar Thermal']
    capacity_pivot = capacity_pivot.drop('Solar Thermal', axis=1)

# Combine biomass sources if needed
if 'Wood/Waste' in capacity_pivot.columns and 'Other Biomass' in capacity_pivot.columns:
    capacity_pivot['Wood/Waste'] += capacity_pivot['Other Biomass']
    capacity_pivot = capacity_pivot.drop('Other Biomass', axis=1)

print("\nFinal columns for plotting:", capacity_pivot.columns.tolist())

# Keep only the energy sources you want to plot
energy_sources = [
    'Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar',
    'Wood/Waste', 'Geothermal', 'Pumped Storage', 'Battery'
]
energy_sources = [s for s in energy_sources if s in capacity_pivot.columns]

# --- NORMALIZE ONLY PLOTTED COLUMNS ---
capacity_shares = capacity_pivot[energy_sources]
capacity_shares = capacity_shares.div(capacity_shares.sum(axis=1), axis=0)

# Start from 2000
capacity_shares = capacity_shares[capacity_shares.index >= 2000]

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

print("\nEnergy sources to plot:", energy_sources)

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# Stacked area chart
ax.stackplot(capacity_shares.index, 
             [capacity_shares[source] for source in energy_sources],
             labels=energy_sources,
             colors=[colors.get(source, '#CCCCCC') for source in energy_sources],
             alpha=0.9)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Installed Capacity', fontsize=12, fontweight='bold')
ax.set_title(f'Energy Source Shares in United States Installed Capacity, {capacity_shares.index.min()}-{capacity_shares.index.max()}', 
             fontsize=14, fontweight='bold', pad=20)

ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=True, fontsize=10)

plt.tight_layout()
plt.savefig('us_installed_capacity.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nGraph created successfully!")
print(f"\nSummary statistics for {capacity_shares.index.max()}:")
print(capacity_shares.loc[capacity_shares.index.max()].sort_values(ascending=False))
