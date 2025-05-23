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


def convert_country_names(df):
    """
    Convert country names in the DataFrame to ISO3 format using country_converter. Assumes that 
    the DataFrame has the countries in the index.

    Args:
        df (pd.DataFrame): DataFrame with countries in the index.

    Returns:
        pd.DataFrame: DataFrame with countries converted to ISO3 format.
    """
    # Convert country names to ISO3 format
    df.index = coco.convert(df.index, to='ISO3', not_found=None)
    # Remove countries that could not be converted
    df = df.dropna()
    return df




def main():
    """
    Main function to create all food shock maps.
    """
    spatial_extent = "countries"
    # Load the data
    data_path = Path("results") / f"yield_changes_by_{spatial_extent}.csv"
    df = pd.read_csv(data_path, index_col=0)
    # Convert country names to ISO3 format
    df = convert_country_names(df)
    print(df.head())

    # Force use of Fiona instead of pyogrio
    shapefile_path = Path("data") / "ne_110m_admin_0_countries.shp"
    admin_map = gpd.read_file(shapefile_path, engine='fiona')
    print(f"Successfully loaded {len(admin_map)} countries using Fiona")


if __name__ == "__main__":
    main()