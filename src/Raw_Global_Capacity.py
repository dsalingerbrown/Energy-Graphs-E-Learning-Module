import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read CSV
# Ensure the path is correct for your local machine
df = pd.read_csv('/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/data/ember_yearly_electricity-capacity - All electricity sources - World - breakdown.csv')

# Safety: Clean column headers (remove extra spaces if any exist)
df.columns = df.columns.str.strip()

# Filter for World only and exclude total row
# We use 'is_aggregate_series' to exclude totals like 'Total Thermal' if they exist in your dataset
df = df[(df['entity'] == 'World') & (df['is_aggregate_series'] == False)].copy()

# Set the value column based on your screenshot
value_column = 'capacity_gw'

# Pivot data to have years as rows, energy sources as columns
capacity_raw = df.pivot(index='date', columns='series', values=value_column)

# Sort columns for consistent plotting
energy_sources = [
    'Coal', 'Gas', 'Oil', 'Nuclear', 'Hydro', 'Wind', 'Solar', 
    'Bioenergy', 'Other fossil', 'Other renewables'
]
# Ensure we only try to plot columns that actually exist in the data
energy_sources = [s for s in energy_sources if s in capacity_raw.columns]
capacity_raw = capacity_raw[energy_sources]

# --- Filter from 2000 onward ---
capacity_raw = capacity_raw[capacity_raw.index >= 2000]

# Define colors
colors = {
    'Coal': '#5B8DB8',
    'Gas': '#A8D35E',
    'Oil': '#E89CAE',
    'Nuclear': '#9AC7C4',
    'Hydro': '#F4B042',
    'Wind': '#F79646',
    'Solar': '#FDC576',
    'Bioenergy': '#C9A5D6',
    'Other fossil': '#D4A5A5',
    'Other renewables': '#B8A8D8'
}

# Create figure
fig, ax = plt.subplots(figsize=(14, 8))

# Line Plot Loop
for source in energy_sources:
    if source in capacity_raw.columns:
        ax.plot(
            capacity_raw.index, 
            capacity_raw[source], 
            label=source, 
            color=colors.get(source, '#CCCCCC'),
            linewidth=2.5,  # Thicker lines for better visibility
            marker='o',     # Adds dots at data points
            markersize=4
        )

# Customize plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Installed Capacity (GW)', fontsize=12, fontweight='bold')
ax.set_title(
    f'Global Installed Electricity Capacity (GW), {capacity_raw.index.min()}-{capacity_raw.index.max()}',
    fontsize=14, fontweight='bold', pad=20
)

# Adjust Axis Limits
ax.set_ylim(bottom=0)

# Grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Legend
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=True, fontsize=10)

# Add Source
fig.text(0.5, 0.02, 'Source: Ember (https://ember-energy.org/data/)', ha='center', fontsize=10, style='italic', color='#555555')

plt.tight_layout()

# Adjust bottom margin to ensure source text isn't cut off (must be after tight_layout)
plt.subplots_adjust(bottom=0.1)
plt.savefig('global_installed_capacity_lines.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nGraph created successfully!")