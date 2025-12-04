import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read CSV
df = pd.read_csv('/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/data/ember_yearly_electricity-capacity - All electricity sources - World - breakdown.csv')

# Filter for World only and exclude total row
df = df[(df['entity'] == 'World') & (df['is_aggregate_series'] == False)].copy()

# Convert share to decimal
df['capacity_share'] = df['capacity_share_pct'] / 100

# Pivot data to have years as rows, energy sources as columns
capacity_shares = df.pivot(index='date', columns='series', values='capacity_share')

# Sort columns for consistent plotting
energy_sources = [
    'Coal', 'Gas', 'Oil', 'Nuclear', 'Hydro', 'Wind', 'Solar', 
    'Bioenergy', 'Other fossil', 'Other renewables'
]
energy_sources = [s for s in energy_sources if s in capacity_shares.columns]
capacity_shares = capacity_shares[energy_sources]

# --- Filter from 2000 onward ---
capacity_shares = capacity_shares[capacity_shares.index >= 2000]

# Define colors (similar style to US graph)
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

# Stackplot
ax.stackplot(
    capacity_shares.index,
    [capacity_shares[source] for source in energy_sources],
    labels=energy_sources,
    colors=[colors.get(source, '#CCCCCC') for source in energy_sources],
    alpha=0.9
)

# Customize plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Installed Capacity', fontsize=12, fontweight='bold')
ax.set_title(
    f'Global Electricity Capacity Shares, {capacity_shares.index.min()}-{capacity_shares.index.max()}',
    fontsize=14, fontweight='bold', pad=20
)

# Y-axis as percentages
ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

# Grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

# Legend
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=True, fontsize=10)

# Add Source
fig.text(0.5, 0.02, 'Source: Ember (https://ember-energy.org/data/)', ha='center', fontsize=10, style='italic', color='#555555')

plt.tight_layout()

# Adjust bottom margin to ensure source text isn't cut off (must be after tight_layout)
plt.subplots_adjust(bottom=0.1)
plt.savefig('global_installed_capacity.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nGraph created successfully!")
