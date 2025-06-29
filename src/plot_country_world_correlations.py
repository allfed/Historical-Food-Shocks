"""
Calculate correlations between each country's yield changes and world yield changes
(excluding that country's contribution) to avoid spurious correlations.

This script analyzes how each country's food production shocks correlate with
global food production shocks, excluding that country's own contribution to
avoid spurious correlations. It creates visualizations including bar plots,
maps, and clustermaps to show the correlation patterns.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import country_converter as coco
import geopandas as gpd
import seaborn as sns
from plot_maps import convert_country_names, plot_winkel_tripel_map
from calculate_food_shocks import calculate_changes_savgol
from pyRMT import clipped

# Set up ALLFED plotting style
plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


def load_data():
    """
    Load all required data files for the correlation analysis.

    Returns:
        tuple: A tuple containing:
            - calories_countries (pandas.DataFrame): Calorie production by country and year
            - world_calories (pandas.Series): World calorie production by year
            - yield_changes_countries (pandas.DataFrame): Percentage yield changes by country and year
            - yield_changes_regions (pandas.DataFrame): Percentage yield changes by region and year
            - yield_changes_world (pandas.Series): World percentage yield changes by year
    """
    print("Loading data files...")

    # Import FAO data
    calories_countries = pd.read_csv("./results/calories_by_countries.csv", index_col=0)
    calories_regions = pd.read_csv("./results/calories_by_regions.csv", index_col=0)
    world_calories = calories_regions.loc["World"]
    yield_changes_countries = pd.read_csv(
        "./results/yield_changes_by_countries.csv", index_col=0
    )
    yield_changes_regions = pd.read_csv(
        "./results/yield_changes_by_regions.csv", index_col=0
    )
    yield_changes_world = yield_changes_regions.loc["World"]

    print(f"Loaded calorie data for {len(calories_countries)} countries")

    return (
        calories_countries,
        world_calories,
        yield_changes_countries,
        yield_changes_regions,
        yield_changes_world,
    )


def calculate_country_world_correlations(
    calories_countries,
    yield_changes_countries,
    world_calories,
):
    """
    Calculate yield change Spearman correlations between each country and rest of the world
    (excluding that country's contribution) to avoid spurious correlations.

    Args:
        calories_countries (pandas.DataFrame): Calorie production data by country and year
        yield_changes_countries (pandas.DataFrame): Percentage yield changes by country and year
        world_calories (pandas.Series): World calorie production by year

    Returns:
        pandas.Series: Series with countries as index and correlation coefficients as values,
                      sorted in descending order
    """
    print("Calculating country-world correlations...")

    correlations = {}

    for country in calories_countries.index:
        if country == "World":
            continue

        # Get country's data
        country_calories = calories_countries.loc[country]
        country_yield_changes = yield_changes_countries.loc[country]

        # Calculate world minus this country
        # This avoids spurious correlation since a country's yield is part of world yield
        world_minus_country_calories = world_calories - country_calories

        # Create a DataFrame with the world minus country data for calculate_changes_savgol
        world_minus_country_df = pd.DataFrame(
            data=[world_minus_country_calories.values],
            columns=world_minus_country_calories.index,
            index=pd.Index([f"World_minus_{country}"], name="Area"),
        )

        # Calculate yield changes for world minus country using the same method
        world_minus_country_yield_changes = calculate_changes_savgol(
            world_minus_country_df, window_length=15, polyorder=3
        ).iloc[0]

        # Calculate correlation
        correlations[country] = world_minus_country_yield_changes.corr(
            country_yield_changes, method="spearman"
        )

    # Convert to Series and sort
    corr_series = pd.Series(correlations).sort_values(ascending=False).dropna()

    print(f"Calculated Spearman correlations for {len(corr_series)} countries")
    print(f"Mean correlation: {corr_series.mean():.4f}")
    print(f"Median correlation: {corr_series.median():.4f}")
    print(f"\nTop 10 countries: \n{corr_series.head(10)}")
    print(f"Bottom 10 countries: \n{corr_series.tail(10)}")

    corr_series.to_csv("./results/country_world_correlations.csv")
    return corr_series


def calculate_correlation_matrix(
    yield_changes_countries, yield_changes_world, RMT=True
):
    """
    Calculate correlation matrix between all countries and world yield changes.

    This function creates a correlation matrix from yield change data, optionally
    applying Random Matrix Theory (RMT) filtering to remove noise and spurious
    correlations from the correlation matrix.

    Args:
        yield_changes_countries (pandas.DataFrame): Percentage yield changes by country and year.
        yield_changes_world (pandas.Series): World percentage yield changes by year.
        RMT (bool, optional): Whether to apply Random Matrix Theory. Defaults to True.

    Returns:
        pandas.DataFrame: Correlation matrix with countries and world as both index and columns.
            If RMT=True, the matrix is filtered using the clipped function from pyRMT.
    """
    # Drop NAs and add world row
    yield_changes_countries.dropna(inplace=True)
    yield_changes_countries.loc["World"] = yield_changes_world

    corr = yield_changes_countries.T.corr()
    index = corr.index
    columns = corr.columns

    # Optionally apply Random Matrix Theory
    if RMT:
        corr = clipped(corr)
        # add country names back to corr_RMT
        corr = pd.DataFrame(corr, index=index, columns=columns)

    return corr


def create_heatmap(corr, sortby="World"):
    """
    Create and display a heatmap of the correlation matrix.

    Args:
        corr (pandas.DataFrame): Correlation matrix with countries/regions as index and columns.
        sortby (str, optional): Country/region name to sort the matrix by.
            Defaults to "World".

    Returns:
        None: Displays the heatmap and saves it to file.
    """
    sorted_indices = corr[sortby].sort_values(ascending=False).index
    sorted_corr = corr.loc[sorted_indices, sorted_indices]
    mean_corr = sorted_corr.drop("World").values.mean()

    # plot heatmap of corr_RMT
    plt.figure(figsize=(12, 8))
    sns.heatmap(sorted_corr, cmap="RdBu", vmin=-1, vmax=1, center=0)
    plt.xticks(fontsize=3)
    plt.xlabel("")
    plt.ylabel("")
    plt.yticks(fontsize=3)
    plt.title(
        f"Spearman correlation matrix sorted by {sortby} \n (Mean correlation: {mean_corr:.4f})"
    )
    plt.savefig(
        f"results/figures/correlation_matrix_{sortby}.png",
        dpi=300,
        bbox_inches="tight",
    )


def create_map_visualization(corr_series):
    """
    Create global map visualization of correlations between countries and the rest of the world.

    Args:
        corr_series (pandas.Series): Series with countries as index and correlation coefficients as values

    Returns:
        None: Displays and saves the map
    """
    print("Creating map visualization...")

    # Convert country names to short names for mapping
    plot_df = convert_country_names(corr_series)
    plot_df = plot_df.to_frame(name="Correlation")

    # Load map data
    shapefile_path = Path("./data") / "ne_110m_admin_0_countries.shp"
    admin_map = gpd.read_file(shapefile_path, engine="fiona")
    print(f"Successfully loaded {len(admin_map)} countries using Fiona")

    # Create a new column name_short in the map DataFrame
    admin_map["name_short"] = coco.convert(
        admin_map["ADMIN"], to="name_short", not_found=None
    )
    merged = admin_map.merge(
        plot_df, left_on="name_short", right_index=True, how="left"
    )

    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    # Set the map to the Winkel Tripel projection
    merged = merged.to_crs("+proj=wintri")

    merged.plot(
        column="Correlation",
        ax=ax,
        legend=True,
        legend_kwds={
            "label": "Spearman Correlation coefficient",
            "orientation": "horizontal",
            "pad": 0.02,
            "shrink": 0.6,
        },
        cmap="RdBu",
        vmin=-0.75,
        vmax=0.75,
        missing_kwds={"color": "lightgrey"},
        edgecolor="white",
        linewidth=0.4,
    )
    plot_winkel_tripel_map(ax)
    ax.set_title(
        "Correlation of yield changes between each country and the rest of the world"
    )
    plt.savefig(
        "./results/figures/country_world_correlations_map.png", dpi=300, bbox_inches="tight"
    )


def main():
    """
    Main function to run the country-world correlation analysis.
    """
    print("Country-World Correlation Analysis")
    print("=" * 50)

    # Load data
    (
        calories_countries,
        world_calories,
        yield_changes_countries,
        yield_changes_regions,
        yield_changes_world,
    ) = load_data()

    # Calculate correlations
    corr_series = calculate_country_world_correlations(
        calories_countries,
        yield_changes_countries,
        world_calories,
    )

    corr = calculate_correlation_matrix(
        yield_changes_countries, yield_changes_world, RMT=True
    )

    # Create visualizations
    create_heatmap(corr)
    create_map_visualization(corr_series)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
