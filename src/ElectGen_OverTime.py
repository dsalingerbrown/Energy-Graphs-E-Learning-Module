import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file, skipping the header information lines
# Adjust skiprows based on how many info lines you have before the data
df = pd.read_csv('/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/ve26.04_energysourcesharesuselectricitygeneration19202021.csv', skiprows=19)  # Skip the info lines

# Set Year as index
df = df.set_index('Year')

# Define colors matching the original visualization
colors = {
    'Coal': '#5B8DB8',
    'Hydro': '#F4B042',
    'Gas': '#A8D35E',
    'Oil': '#E89CAE',
    'Nuclear': '#9AC7C4',
    'Wind': '#F79646',
    'Solar': '#FDC576',
    'Wood/Waste': '#C9A5D6',
    'Geothermal': '#D4A5A5'
}

# Order of stacking (bottom to top)
energy_sources = ['Coal', 'Hydro', 'Gas', 'Oil', 'Nuclear', 'Wind', 'Solar', 'Wood/Waste', 'Geothermal']

# Create the figure
fig, ax = plt.subplots(figsize=(14, 8))

# Create stacked area chart
ax.stackplot(df.index, 
             [df[source] for source in energy_sources],
             labels=energy_sources,
             colors=[colors[source] for source in energy_sources],
             alpha=0.9)

# Customize the plot
ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Share of Electricity Generation', fontsize=12, fontweight='bold')
ax.set_title('Energy Source Shares in United States Electricity Generation, 1920-2021', 
             fontsize=14, fontweight='bold', pad=20)

# Set y-axis to percentage
ax.set_ylim(0, 1)
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels([f'{int(i*100)}%' for i in np.arange(0, 1.1, 0.1)])

# Add grid for readability
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_axisbelow(True)

# Create legend
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), 
          frameon=True, fontsize=10)

# Tight layout to prevent label cutoff
plt.tight_layout()

# Save the figure
plt.savefig('us_electricity_generation.png', dpi=300, bbox_inches='tight')

# Display the plot
plt.show()

print("Graph created successfully!")
print("\nSummary statistics for 2021:")
print(df.loc[2021].sort_values(ascending=False))