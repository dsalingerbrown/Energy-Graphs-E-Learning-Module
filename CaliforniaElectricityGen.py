import pandas as pd
import matplotlib.pyplot as plt

# 1. Configuration
INPUT_FILE = '/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/data/CASystemGeneration.csv' 
YEARS = [str(year) for year in range(2012, 2025)] # 2012 to 2024 as requested

# Fuel stacking order: Carbon-heavy at the bottom, Renewables at the top
FUEL_TYPES_ORDER = [
    'Coal', 
    'Oil', 
    'Oil/Other', 
    'Other (Waste Heat / Petroleum Coke)', 
    'Unspecified',
    'Unspecified Imports',
    'Natural Gas', 
    'Nuclear', 
    'Biomass', 
    'Geothermal', 
    'Large Hydro', 
    'Small Hydro', 
    'Solar', 
    'Wind'
]

# UPDATE: Changed Unspecified to Purple to distinguish from Oil (Grey)
COLOR_MAP = {
    'Wind': '#54a24b',                      # Green
    'Solar': '#ffed6f',                     # Yellow
    'Small Hydro': '#00204d',               # Dark Blue
    'Large Hydro': '#80b1d3',               # Light Blue
    'Natural Gas': '#8c564b',               # Brown
    'Nuclear': '#4e79a7',                   # Steel Blue/Teal
    'Geothermal': '#f28e2b',                # Orange
    'Biomass': '#bab0ac',                   # Warm Grey
    'Oil': '#d3d3d3',                       # Light Grey
    'Oil/Other': '#d3d3d3',                 # Light Grey
    'Coal': '#000000',                      # Black
    'Unspecified': '#b07aa1',               # Purple (New Distinct Color)
    'Unspecified Imports': '#b07aa1',       # Purple (New Distinct Color)
    'Other (Waste Heat / Petroleum Coke)': '#76b7b2' # Cyan/Teal
}

def load_and_clean_data(file_path):
    # Place 'skiprows=1' here to skip that first empty row
    try:
        df = pd.read_csv(file_path, skiprows=1, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, skiprows=1, encoding='cp1252')

    # Immediately clean the headers to remove invisible spaces
    df.columns = df.columns.str.strip()
    
    # Strip whitespace from data cells in the Region and Fuel Type columns
    df['Region'] = df['Region'].astype(str).str.strip()
    df['Fuel Type'] = df['Fuel Type'].astype(str).str.strip()

    # Clean numeric data for the years 2012-2024
    for col in YEARS:
        if col in df.columns:
            # Handle commas, dashes, and empty values
            df[col] = df[col].astype(str).str.replace(',', '').replace('-', '0').replace('nan', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

def create_stacked_area_chart(data, title, filename):
    # Prepare data for plotting (Transpose: Years become index)
    plot_data = data.set_index('Fuel Type')[YEARS].T
    
    # Filter and sort columns based on our defined order
    existing_fuels = [f for f in FUEL_TYPES_ORDER if f in plot_data.columns]
    plot_data = plot_data[existing_fuels]
    
    colors = [COLOR_MAP.get(fuel, '#333333') for fuel in existing_fuels]
    
    plt.figure(figsize=(12, 7))
    plt.stackplot(plot_data.index, plot_data.T, labels=plot_data.columns, colors=colors)
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('Generation (GWh)', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), reverse=True)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

def main():
    try:
        df = load_and_clean_data(INPUT_FILE)
        
        # 1. California Generation
        # Filter Region "California" but exclude the summary row "California Total"
        ca_data = df[(df['Region'] == 'California') & (~df['Fuel Type'].str.contains('Total'))].copy()
        create_stacked_area_chart(ca_data, 'California In-State Generation by Fuel Type (2012-2024)', 'ca_generation.png')
        
        # 2. Total Imported Generation (Northwest + Southwest)
        imports_raw = df[df['Region'].isin(['Northwest', 'Southwest'])]
        # Exclude summary rows like "Northwest Total"
        imports_clean = imports_raw[~imports_raw['Fuel Type'].str.contains('Total')].copy()
        imports_grouped = imports_clean.groupby('Fuel Type')[YEARS].sum().reset_index()
        create_stacked_area_chart(imports_grouped, 'Total Imported Generation by Fuel Type (2012-2024)', 'imported_generation.png')
        
        # 3. Combined CA + Total Imported
        # Use the "Total" region rows at the bottom of the dataset
        total_data = df[df['Region'] == 'Total'].copy()
        create_stacked_area_chart(total_data, 'Combined CA In-State+ Imported Generation by Fuel Type (2012-2024)', 'grand_total_generation.png')
        
        print("Success: Three graphs generated in your project folder.")
        
    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    main()