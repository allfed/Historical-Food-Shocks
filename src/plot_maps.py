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
    # Load and plot border
    border_geojson = gpd.read_file('https://raw.githubusercontent.com/ALLFED/ALLFED-map-border/main/border.geojson', engine='fiona')
    border_geojson.plot(ax=ax, edgecolor='black', linewidth=0.1, facecolor='none')

    ax.set_axis_off()


def convert_country_names(df):
    """
    Convert country names in the DataFrame to name_short format using country_converter. Assumes that 
    the DataFrame has the countries in the index.

    Args:
        df (pd.DataFrame): DataFrame with countries in the index.

    Returns:
        pd.DataFrame: DataFrame with countries converted to name_short format.
    """
    # Convert country names to name_short format
    df.index = coco.convert(df.index, to='name_short', not_found=None)
    return df


def merge_data_with_map(df, map_df):
    """
    Merge the DataFrame with the map DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with countries in name_short format.
        map_df (gpd.GeoDataFrame): GeoDataFrame with country geometries.

    Returns:
        gpd.GeoDataFrame: Merged GeoDataFrame.
    """
    # Create a new column name_short in the map DataFrame
    map_df['name_short'] = coco.convert(map_df['ADMIN'], to='name_short', not_found=None)

    # Get the largest food shock for each country
    df = pd.DataFrame(df.min(axis=1))

    # Merge the data with the map
    merged = map_df.merge(df, left_on='name_short', right_index=True, how='left')
    # Rename the column to 'food_shock'
    merged.rename(columns={0: 'food_shock'}, inplace=True)
    return merged


def plot_map(merged, title, filename):
    """
    Plot the map with the merged data.
    Args:
        merged (gpd.GeoDataFrame): Merged GeoDataFrame.
        title (str): Title for the plot.
        filename (str): Filename to save the plot.
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    # Set the map to the Winkel Tripel projection
    merged = merged.to_crs('+proj=wintri')
    merged.plot(column='food_shock', ax=ax, legend=True,
                legend_kwds={'label': "Food Shock [%]", 
                            'orientation': "horizontal",
                            'pad': 0.02,        # Distance from map
                            'shrink': 0.6},      # Overall size
                cmap='magma', missing_kwds={"color": "lightgrey"})
    plot_winkel_tripel_map(ax)
    ax.set_title(title)
    plt.savefig(filename, bbox_inches='tight')
    plt.close()


def main():
    """
    Main function to create all food shock maps.
    """
    spatial_extent = "countries"
    # Load the data
    data_path = Path("results") / f"yield_changes_by_{spatial_extent}.csv"
    df = pd.read_csv(data_path, index_col=0)
    # Convert country names to name_short format
    df = convert_country_names(df)
    print(df.head())

    # Force use of Fiona instead of pyogrio
    shapefile_path = Path("data") / "ne_110m_admin_0_countries.shp"
    admin_map = gpd.read_file(shapefile_path, engine='fiona')
    print(f"Successfully loaded {len(admin_map)} countries using Fiona")
    print(admin_map.head())

    # Merge the data with the map
    merged = merge_data_with_map(df, admin_map)
    print(merged.head())

    # Plot the map
    plot_map(merged, "Food Shock by Country", "results/food_shock_by_country.png")
    

if __name__ == "__main__":
    main()