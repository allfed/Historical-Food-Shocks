"""
Create maps showing the largest crop shocks per country, region, and group of countries.

This script reads the calculated yield changes and creates choropleth maps
visualizing the most severe crop production shocks for each geographic entity.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import country_converter as coco
from pathlib import Path


# Set up ALLFED plotting style
plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


def plot_winkel_tripel_map(ax):
    """
    Add border to map and remove gridlines and ticks for ALLFED style.

    Args:
        ax: matplotlib axis object
    """
    # Load and plot border
    border_geojson = gpd.read_file(
        "https://raw.githubusercontent.com/ALLFED/ALLFED-map-border/main/border.geojson",
        engine="fiona",
    )
    border_geojson.plot(ax=ax, edgecolor="black", linewidth=0.1, facecolor="none")

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
    df.index = coco.convert(df.index, to="name_short", not_found=None)
    return df


def merge_data_with_map_shock(df, map_df):
    """
    Merge the DataFrame with the map DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with countries in name_short format.
        map_df (gpd.GeoDataFrame): GeoDataFrame with country geometries.

    Returns:
        gpd.GeoDataFrame: Merged GeoDataFrame.
    """
    # Create a new column name_short in the map DataFrame
    map_df["name_short"] = coco.convert(
        map_df["ADMIN"], to="name_short", not_found=None
    )

    # Get the largest crop shock for each country
    df = pd.DataFrame(df.min(axis=1))

    # Merge the data with the map
    merged = map_df.merge(df, left_on="name_short", right_index=True, how="left")
    # Rename the column to 'crop_shock'
    merged.rename(columns={0: "crop_shock"}, inplace=True)
    return merged


def plot_map_yield_shock_relative(merged, title, filename):
    """
    Plot the map with the merged data.
    Args:
        merged (gpd.GeoDataFrame): Merged GeoDataFrame.
        title (str): Title for the plot.
        filename (str): Filename to save the plot.
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    # Set the map to the Winkel Tripel projection
    merged = merged.to_crs("+proj=wintri")
    vmin = merged["crop_shock"].min()
    vmax = 0
    merged.plot(
        column="crop_shock",
        ax=ax,
        legend=True,
        legend_kwds={
            "label": "Crop Shock [%]",
            "orientation": "horizontal",
            "pad": 0.02,
            "shrink": 0.6,
        },
        cmap="magma",
        vmin=vmin,
        vmax=vmax,
        missing_kwds={"color": "lightgrey"},
        edgecolor="white",
        linewidth=0.4,
    )
    plot_winkel_tripel_map(ax)
    ax.set_title(title)
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def plot_map_yield_shock_count(merged, title, filename):
    """
    Plot map showing percentage of years with crop production shocks >5%.

    Args:
        merged (gpd.GeoDataFrame): Merged GeoDataFrame with shock percentages.
        title (str): Title for the plot.
        filename (str): Filename to save the plot.
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    # Set the map to the Winkel Tripel projection
    merged = merged.to_crs("+proj=wintri")

    # Plot with percentage values
    merged.plot(
        column="shock_percentage",
        ax=ax,
        legend=True,
        legend_kwds={
            "label": "Percentage of Years with Crop Shock >5%",
            "orientation": "horizontal",
            "pad": 0.02,
            "shrink": 0.6,
        },
        cmap="magma_r",
        vmin=0,  # Percentages range from 0 to 100
        vmax=50,
        missing_kwds={"color": "lightgrey"},
        edgecolor="white",
        linewidth=0.4,
    )
    plot_winkel_tripel_map(ax)
    ax.set_title(title)
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def merge_data_with_map_count(df, map_df):
    """
    Calculate percentage of years with crop shocks >5% for each country.

    Accounts for countries that didn't exist for the full time period by
    using only non-NaN values to determine existence period.

    Args:
        df (pd.DataFrame): DataFrame with countries in name_short format.
        map_df (gpd.GeoDataFrame): GeoDataFrame with country geometries.

    Returns:
        gpd.GeoDataFrame: Merged GeoDataFrame with shock percentages.
    """
    # Create a new column name_short in the map DataFrame
    map_df["name_short"] = coco.convert(
        map_df["ADMIN"], to="name_short", not_found=None
    )

    # Calculate shock statistics for each country
    # Count years with shocks larger than 5% (values < -5)
    shock_counts = (df < -5).sum(axis=1)

    # Count total years of existence (non-NaN values)
    years_existed = df.notna().sum(axis=1)

    # Calculate percentage (avoid division by zero)
    shock_percentage = (shock_counts / years_existed * 100).fillna(0)

    # Create DataFrame with the percentage
    shock_stats = pd.DataFrame({"shock_percentage": shock_percentage})

    # Merge the data with the map
    merged = map_df.merge(
        shock_stats, left_on="name_short", right_index=True, how="left"
    )

    return merged


def plot_map_shock_categories(
    map_df, data_path="results/largest_crop_shock_by_country_with_reasons.csv"
):
    """
    Create a map showing countries colored by their main crop shock category.

    Args:
        map_df (gpd.GeoDataFrame): GeoDataFrame with country geometries
        data_path (str): Path to CSV file containing shock categories
    """
    # Load the shock category data
    shock_data = pd.read_csv(data_path)

    # Convert country names to name_short format for matching
    shock_data["name_short"] = coco.convert(
        shock_data["country"], to="name_short", not_found=None
    )

    # Create name_short column in map DataFrame
    map_df_copy = map_df.copy()
    map_df_copy["name_short"] = coco.convert(
        map_df_copy["ADMIN"], to="name_short", not_found=None
    )

    # Merge the data
    merged = map_df_copy.merge(
        shock_data[["name_short", "Category (main)"]], on="name_short", how="left"
    )

    # Define pastel colors for each category
    # Using colorblind-friendly pastel palette
    category_colors = {
        "Economic": "#FFB6C1",  # Light pink
        "Policy": "#87CEEB",  # Sky blue
        "Climate": "#FFA07A",  # Light salmon (reddish)
        "Conflict": "#DDA0DD",  # Plum
        "Natural Disaster": "#F0E68C",  # Khaki/yellow
        "Pest/Disease": "#90EE90",  # Light green
        "Infrastructure": "#E6E6FA",  # Lavender
        "Mismanagement": "#D2B48C",  # Tan/brown
        "Unknown": "#D3D3D3",  # Light gray
    }

    # Get unique categories from the data to ensure we have all of them
    unique_categories = merged["Category (main)"].dropna().unique()

    # Add any missing categories with a default color
    for cat in unique_categories:
        if cat not in category_colors:
            category_colors[cat] = "#E6E6FA"  # Lavender as default

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))

    # Convert to Winkel Tripel projection
    merged = merged.to_crs("+proj=wintri")

    # Plot countries with no data in light gray
    merged.plot(
        ax=ax,
        color="#F5F5F5",  # Very light gray for missing data
        edgecolor="white",
        linewidth=5,
    )

    # Plot each category separately to ensure proper legend
    for category, color in category_colors.items():
        # Select countries with this category
        category_data = merged[merged["Category (main)"] == category]

        if not category_data.empty:
            category_data.plot(
                ax=ax, color=color, edgecolor="white", linewidth=0.5, label=category
            )

    # Add border and styling
    plot_winkel_tripel_map(ax)

    # Create custom legend
    # Get only categories that appear in the data
    present_categories = [
        cat for cat in category_colors.keys() if cat in merged["Category (main)"].values
    ]

    # Create legend handles
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=category_colors[cat], edgecolor="white", label=cat)
        for cat in present_categories
    ]

    # Add "No Data" to legend
    legend_elements.append(
        Patch(facecolor="#F5F5F5", edgecolor="white", label="No Data")
    )

    # Position legend
    ax.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=5,
        frameon=False,
        fontsize=10,
    )

    # Set title
    ax.set_title(
        "Reason for Largest Crop Production Shock by Country (1961-2023)",
        fontsize=14,
        pad=20,
    )

    # Save figure
    output_path = Path("results/figures/crop_shock_categories_by_country.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved shock category map to {output_path}")

    # Print summary statistics
    print("\nShock Category Summary:")
    category_counts = shock_data["Category (main)"].value_counts()
    for category, count in category_counts.items():
        print(f"  {category}: {count} countries")


def main():
    """
    Main function to create all crop shock maps.
    """
    spatial_extent = "countries"
    # Load the data
    data_path = Path("results") / f"yield_changes_by_{spatial_extent}.csv"
    df = pd.read_csv(data_path, index_col=0)
    # Convert country names to name_short format
    df = convert_country_names(df)

    # Force use of Fiona instead of pyogrio
    shapefile_path = Path("data") / "ne_110m_admin_0_countries.shp"
    admin_map = gpd.read_file(shapefile_path, engine="fiona")
    print(f"Successfully loaded {len(admin_map)} countries using Fiona")

    # Merge the data with the map
    merged_shock = merge_data_with_map_shock(df, admin_map)
    merged_count = merge_data_with_map_count(df, admin_map)
    print(f"Successfully merged data with map for {spatial_extent}")

    # Plot the map
    plot_map_yield_shock_relative(
        merged_shock,
        "Largest Crop Production Shock by Country (1961-2023)",
        "results/figures/crop_shock_by_country.png",
    )
    plot_map_yield_shock_count(
        merged_count,
        "Percentage of Years with Crop Production Shock by Country (1961-2023)",
        "results/figures/crop_shock_count_by_country.png",
    )

    print("\nCreating shock category map...")
    plot_map_shock_categories(admin_map)

    # Save the largest crop shock per country to a CSV file
    # Together with the year of the shock
    largest_shock = df.min(axis=1).reset_index()
    largest_shock.columns = ["country", "largest_crop_shock"]

    # Get the year of the shock, handling NaN values correctly
    # For each row, find the column (year) with the minimum value, ignoring NaNs
    def get_min_year(row):
        if row.isnull().all():
            return None
        return row.idxmin()

    # Reset index for alignment
    df_reset = df.reset_index(drop=True)
    largest_shock["year_of_shock"] = df_reset.apply(get_min_year, axis=1)
    largest_shock = largest_shock.set_index("country")
    largest_shock.to_csv("results/largest_crop_shock_by_country.csv")
    print(
        "Saved largest crop shock per country to results/largest_crop_shock_by_country.csv"
    )


if __name__ == "__main__":
    main()
