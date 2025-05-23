"""
Create maps showing the largest food shocks per country, region, and group of countries.

This script reads the calculated yield changes and creates choropleth maps
visualizing the most severe food production shocks for each geographic entity.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import country_converter as coco
from pathlib import Path
import warnings
import os

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set PROJ_LIB environment variable to fix PROJ issues
os.environ['PROJ_LIB'] = '/home/florian/local/anaconda3/envs/food_shocks/share/proj'

# Set up ALLFED plotting style
plt.style.use("https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle")


def plot_winkel_tripel_map(ax):
    """
    Add border to map and remove gridlines and ticks for ALLFED style.
    
    Args:
        ax: matplotlib axis object
    """
    try:
        # Load and plot border
        border_geojson = gpd.read_file('https://raw.githubusercontent.com/ALLFED/ALLFED-map-border/main/border.geojson')
        border_geojson.plot(ax=ax, edgecolor='black', linewidth=0.1, facecolor='none')
    except:
        # If border fails to load, continue without it
        pass
    ax.set_axis_off()


def load_shock_data(shock_type):
    """
    Load yield change data for a specific geographic type.
    
    Args:
        shock_type (str): Type of geographic entity ('countries', 'regions', 'groups_of_countries')
        
    Returns:
        pd.DataFrame: Yield change data
    """
    file_path = Path(f"results/yield_changes_by_{shock_type}.csv")
    return pd.read_csv(file_path, index_col=0)


def calculate_largest_shocks(df):
    """
    Calculate the largest negative shock (most severe food production decline) for each entity.
    
    Args:
        df (pd.DataFrame): Yield change data with entities as rows and years as columns
        
    Returns:
        pd.Series: Largest negative shock for each entity
    """
    # Find the minimum value (most negative) for each row
    # This represents the worst food production shock
    return df.min(axis=1)


def prepare_country_geodata(shock_data):
    """
    Prepare geographic data for countries with shock values.
    
    Args:
        shock_data (pd.Series): Largest shocks by country
        
    Returns:
        gpd.GeoDataFrame: Geographic data with shock values
    """
    # Load world shapefile with explicit encoding
    world = gpd.read_file("data/ne_110m_admin_0_countries.shp", encoding='utf-8')
    
    # Convert country names using country_converter
    cc = coco.CountryConverter()
    
    # Create mapping from shock data country names to standard names
    shock_countries = shock_data.index.tolist()
    standard_names = cc.convert(names=shock_countries, to='name_short', not_found=None)
    
    # Create a mapping dictionary
    name_mapping = dict(zip(shock_countries, standard_names))
    
    # Map shock data to standard names
    shock_data_mapped = shock_data.rename(index=name_mapping)
    
    # Merge shock data with world geodata
    # Try different name columns in the shapefile
    for name_col in ['NAME', 'NAME_EN', 'SOVEREIGNT']:
        if name_col in world.columns:
            world = world.merge(
                shock_data_mapped.to_frame('largest_shock'),
                left_on=name_col,
                right_index=True,
                how='left'
            )
            break
    
    # Project to Winkel Tripel - use try/except in case of PROJ issues
    try:
        world = world.to_crs('+proj=wintri')
    except:
        print("Warning: Could not project to Winkel Tripel, using original projection")
    
    return world


def prepare_region_geodata(shock_data):
    """
    Prepare geographic data for regions with shock values.
    
    Args:
        shock_data (pd.Series): Largest shocks by region
        
    Returns:
        gpd.GeoDataFrame: Geographic data with shock values
    """
    # Load world shapefile
    world = gpd.read_file("data/ne_110m_admin_0_countries.shp", encoding='utf-8')
    
    # Use country converter to get region assignments
    cc = coco.CountryConverter()
    
    # Add region information to world data
    world['region'] = world['ISO_A3'].apply(
        lambda x: cc.convert(names=x, to='continent', not_found=None) if pd.notna(x) else None
    )
    
    # For more specific regions, use UN region classification
    world['un_region'] = world['ISO_A3'].apply(
        lambda x: cc.convert(names=x, to='UN_region', not_found=None) if pd.notna(x) else None
    )
    
    # Initialize largest_shock column with NaN
    world['largest_shock'] = pd.NA
    
    # Map shock data to countries based on their regions
    for region, shock_value in shock_data.items():
        if region in ['Africa', 'Americas', 'Asia', 'Europe', 'Oceania']:
            # Continental regions
            world.loc[world['region'] == region, 'largest_shock'] = shock_value
        else:
            # Sub-regions - use UN classification
            world.loc[world['un_region'] == region, 'largest_shock'] = shock_value
    
    # Convert to float to avoid plotting issues
    world['largest_shock'] = pd.to_numeric(world['largest_shock'], errors='coerce')
    
    # Project to Winkel Tripel - use try/except in case of PROJ issues
    try:
        world = world.to_crs('+proj=wintri')
    except:
        print("Warning: Could not project to Winkel Tripel, using original projection")
    
    return world


def create_map(geodata, shock_type, output_filename):
    """
    Create and save a choropleth map of food shocks.
    
    Args:
        geodata (gpd.GeoDataFrame): Geographic data with shock values
        shock_type (str): Type of map ('countries', 'regions', 'groups')
        output_filename (str): Name of output file
    """
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    
    # Plot the choropleth map
    geodata.plot(
        column='largest_shock',
        ax=ax,
        cmap='Reds_r',  # Reverse Reds so darker = more severe shock
        legend=True,
        legend_kwds={
            'label': 'Largest Food Production Shock (%)',
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        },
        missing_kwds={
            'color': 'lightgray',
            'label': 'No data'
        },
        vmin=-50,  # Set consistent scale
        vmax=0
    )
    
    # Add ALLFED map styling
    plot_winkel_tripel_map(ax)
    
    # Add title
    title_map = {
        'countries': 'Largest Food Production Shocks by Country',
        'regions': 'Largest Food Production Shocks by Region',
        'groups': 'Largest Food Production Shocks by Country Groups'
    }
    ax.set_title(title_map.get(shock_type, 'Food Production Shocks'), fontsize=16, pad=20)
    
    # Save the figure
    output_path = Path('results') / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_groups_visualization(shock_data):
    """
    Create a bar chart for groups of countries since they don't map geographically.
    
    Args:
        shock_data (pd.Series): Largest shocks by country group
    """
    # Sort by shock severity
    shock_data_sorted = shock_data.sort_values()
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Plot bars
    bars = ax.barh(range(len(shock_data_sorted)), shock_data_sorted.values, color='darkred')
    
    # Customize appearance
    ax.set_yticks(range(len(shock_data_sorted)))
    ax.set_yticklabels(shock_data_sorted.index)
    ax.set_xlabel('Largest Food Production Shock (%)', fontsize=12)
    ax.set_title('Largest Food Production Shocks by Country Groups', fontsize=14, pad=20)
    
    # Add value labels on bars
    for i, (value, name) in enumerate(zip(shock_data_sorted.values, shock_data_sorted.index)):
        ax.text(value - 1, i, f'{value:.1f}%', ha='right', va='center', color='white', fontweight='bold')
    
    # Add zero line
    ax.axvline(x=0, color='black', linewidth=0.5)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    output_path = Path('results') / 'largest_shocks_groups.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """
    Main function to create all food shock maps.
    """
    # Create results directory if it doesn't exist
    Path('results').mkdir(exist_ok=True)
    
    try:
        # 1. Create country-level shock map
        print("Creating country-level shock map...")
        country_shocks = load_shock_data('countries')
        largest_country_shocks = calculate_largest_shocks(country_shocks)
        country_geodata = prepare_country_geodata(largest_country_shocks)
        create_map(country_geodata, 'countries', 'largest_shocks_countries.png')
        print("Country map created successfully.")
    except Exception as e:
        print(f"Error creating country map: {e}")
    
    try:
        # 2. Create region-level shock map
        print("Creating region-level shock map...")
        region_shocks = load_shock_data('regions')
        largest_region_shocks = calculate_largest_shocks(region_shocks)
        region_geodata = prepare_region_geodata(largest_region_shocks)
        create_map(region_geodata, 'regions', 'largest_shocks_regions.png')
        print("Region map created successfully.")
    except Exception as e:
        print(f"Error creating region map: {e}")
    
    try:
        # 3. Create groups visualization (bar chart instead of map)
        print("Creating country groups bar chart...")
        groups_shocks = load_shock_data('groups_of_countries')
        largest_groups_shocks = calculate_largest_shocks(groups_shocks)
        create_groups_visualization(largest_groups_shocks)
        print("Groups bar chart created successfully.")
    except Exception as e:
        print(f"Error creating groups chart: {e}")
    
    print("\nAll visualizations completed. Check the results folder.")


if __name__ == "__main__":
    main()