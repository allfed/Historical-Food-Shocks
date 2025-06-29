"""
Create comparative plots analyzing crop shocks by their reasons/categories.

This script reads the calculated largest crop shocks with their categorized reasons
and creates visualizations comparing shock magnitudes and distributions across
categories, continents, and decades.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import country_converter as coco


# Set up ALLFED plotting style
plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


def load_shock_data_with_continents():
    """
    Load the shock data and add continent information without removing historical countries.

    Returns:
        pd.DataFrame: Shock data with continent information added
    """
    # Load shock data
    shock_data = pd.read_csv("results/largest_crop_shock_by_country_with_reasons.csv")

    # Load shapefile to get continent information
    shapefile_path = Path("data") / "ne_110m_admin_0_countries.shp"
    world_map = gpd.read_file(shapefile_path, engine="fiona")

    # Convert country names to name_short format for matching
    shock_data["name_short"] = coco.convert(
        shock_data["country"], to="name_short", not_found=None
    )
    world_map["name_short"] = coco.convert(
        world_map["ADMIN"], to="name_short", not_found=None
    )

    # Create a continent lookup dictionary from the shapefile
    continent_lookup = dict(zip(world_map["name_short"], world_map["CONTINENT"]))

    # Add continent information using the lookup (preserves all rows)
    shock_data["CONTINENT"] = shock_data["name_short"].map(continent_lookup)

    # Handle historical countries that aren't in the modern shapefile
    # by manually mapping them to their historical continent
    historical_continent_mapping = {
        # European historical countries
        "USSR": "Europe",  # Most of USSR was in Europe
        "Yugoslav SFR": "Europe",
        "Yugoslavia": "Europe",
        "Serbia and Montenegro": "Europe",
        "Belgium-Luxembourg": "Europe",
        "Czechoslovakia": "Europe",
        "Czechia": "Europe",  # When it appears as historical reference
        # African historical countries
        "Ethiopia": "Africa",  # For the pre-1993 entries (before Eritrea independence)
        "Sudan": "Africa",  # For pre-2011 entries (before South Sudan independence)
        # Asian historical countries
        "Democratic People's Republic of Korea": "Asia",  # Full name for North Korea
        "North Korea": "Asia",
        # Pacific historical countries
        "Micronesia, Fed. Sts.": "Oceania",  # Federated States of Micronesia
        # Note: Some entries appear multiple times in the data due to:
        # - Ethiopia: pre/post Eritrea independence (1993)
        # - Sudan: pre/post South Sudan independence (2011)
        # - Czechia: represents Czechoslovakia in earlier years
        # - Micronesia, Fed. Sts.: appears twice in the data
    }

    # Apply historical mappings where continent is missing
    for country, continent in historical_continent_mapping.items():
        mask = (shock_data["country"] == country) & (shock_data["CONTINENT"].isna())
        shock_data.loc[mask, "CONTINENT"] = continent

    # Alternative approach: Use country_converter's continent conversion
    # for any remaining countries without continent data
    missing_continent_mask = shock_data["CONTINENT"].isna()
    if missing_continent_mask.any():
        # Try to get continent from country_converter
        shock_data.loc[missing_continent_mask, "CONTINENT"] = coco.convert(
            shock_data.loc[missing_continent_mask, "country"],
            to="continent",
            not_found=None,
        )

    # Drop the temporary name_short column
    shock_data = shock_data.drop("name_short", axis=1)

    # Print summary of continent assignment
    print(f"Total countries: {len(shock_data)}")
    print(f"Countries with continent data: {shock_data['CONTINENT'].notna().sum()}")
    print(f"Countries missing continent data: {shock_data['CONTINENT'].isna().sum()}")

    if shock_data["CONTINENT"].isna().any():
        print("\nCountries still missing continent data:")
        missing = shock_data[shock_data["CONTINENT"].isna()][
            ["country", "year_of_shock"]
        ].values.tolist()
        for country, year in missing:
            print(f"  - {country} ({year})")

    return shock_data


def get_category_colors():
    """
    Get the consistent pastel color palette for categories.

    Returns:
        dict: Category to color mapping
    """
    return {
        "Economic": "#F0B323",         # Warm amber (kept original - works well)
        "Policy": "#755549",           # Deep brown (your specified color)
        "Climate": "#e67f54",          # Coral orange (your specified color)
        "Conflict": "#C41E3A",         # Deep red (kept original - fits perfectly)
        "Natural Disaster": "#6197d0", # Sky blue (your specified color)
        "Pest/Disease": "#006B3C",     # Dark teal green (kept original)
        "Infrastructure": "#8B7355",   # Tan brown
        "Mismanagement": "#9B5A75",    # Dusty rose
        "Unknown": "#808080",          # Medium gray (kept original)
    }


def plot_swarm_by_category(data):
    """
    Create a swarm plot comparing shock sizes by main category.

    Args:
        data (pd.DataFrame): Shock data with categories
    """
    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Get color palette
    category_colors = get_category_colors()

    # Order categories by median shock size (most severe first)
    category_order = (
        data.groupby("Category (main)")["largest_food_shock"]
        .median()
        .sort_values()
        .index.tolist()
    )

    # Create color palette in the correct order
    palette = [category_colors.get(cat, "#E6E6FA") for cat in category_order]

    # Create swarm plot
    sns.swarmplot(
        data=data,
        x="Category (main)",
        y="largest_food_shock",
        order=category_order,
        palette=palette,
        size=10,
        alpha=0.9,
        ax=ax,
    )

    # Add median lines
    for i, category in enumerate(category_order):
        cat_data = data[data["Category (main)"] == category]["largest_food_shock"]
        median_val = cat_data.median()

        # Draw median line
        ax.hlines(
            median_val,
            i - 0.4,
            i + 0.4,
            colors="black",
            linestyles="solid",
            linewidth=2,
        )

    # Customize plot
    ax.set_xlabel("Shock Category", fontsize=12)
    ax.set_ylabel("Largest crop Production Shock (%)", fontsize=12)
    ax.set_title("Distribution of Largest crop Shocks by Category", fontsize=14, pad=20)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha="right")

    # Add grid for easier reading
    ax.grid(True, axis="y", alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path = Path("results/figures/shock_swarm_by_category.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved swarm plot to {output_path}")


def plot_stacked_bar_by_continent(data):
    """
    Create a stacked bar plot showing category distribution by continent.

    Args:
        data (pd.DataFrame): Shock data with categories and continents
    """
    # Remove rows with missing continent data
    data_clean = data.dropna(subset=["CONTINENT"])

    # Create crosstab for stacked bar
    crosstab = (
        pd.crosstab(
            data_clean["CONTINENT"], data_clean["Category (main)"], normalize="index"
        )
        * 100
    )  # Convert to percentages

    # Sort continents by total number of countries
    continent_counts = data_clean["CONTINENT"].value_counts()
    continent_order = continent_counts.index.tolist()
    crosstab = crosstab.reindex(continent_order)

    # Get color palette
    category_colors = get_category_colors()

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create stacked bar plot
    crosstab.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[category_colors.get(cat, "#E6E6FA") for cat in crosstab.columns],
        width=0.8,
    )

    # Customize plot
    ax.set_xlabel("Continent", fontsize=12)
    ax.set_ylabel("Percentage of Countries (%)", fontsize=12)
    ax.set_title("Distribution of Shock Categories by Continent", fontsize=14, pad=20)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    # Move legend outside plot
    ax.legend(
        title="Category", bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0
    )

    # Add grid
    ax.grid(True, axis="y", alpha=0.3)

    # Set y-axis to 0-100
    ax.set_ylim(0, 100)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path = Path("results/figures/shock_categories_by_continent.png")
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved continent stacked bar plot to {output_path}")


def plot_stacked_bar_by_continent_absolute(data):
    """
    Create a stacked bar plot showing category distribution by continent in absolute counts.

    Args:
        data (pd.DataFrame): Shock data with categories and continents
    """
    # Remove rows with missing continent data
    data_clean = data.dropna(subset=["CONTINENT"])

    # Create crosstab for stacked bar (absolute counts)
    crosstab = pd.crosstab(data_clean["CONTINENT"], data_clean["Category (main)"])

    # Sort continents by total number of countries
    continent_counts = data_clean["CONTINENT"].value_counts()
    continent_order = continent_counts.index.tolist()
    crosstab = crosstab.reindex(continent_order)

    # Get color palette
    category_colors = get_category_colors()

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create stacked bar plot
    crosstab.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[category_colors.get(cat, "#E6E6FA") for cat in crosstab.columns],
        width=0.8,
    )

    # Customize plot
    ax.set_xlabel("Continent", fontsize=12)
    ax.set_ylabel("Number of Countries", fontsize=12)
    ax.set_title(
        "Number of Countries with Largest Shock by Category and Continent",
        fontsize=14,
        pad=20,
    )

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    # Move legend outside plot
    ax.legend(
        title="Category", bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0
    )

    # Add grid
    ax.grid(True, axis="y", alpha=0.3)
    ax.xaxis.grid(False)  # Disable x-axis grid for cleaner look

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path = Path("results/figures/shock_categories_by_continent_absolute.png")
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved continent absolute counts stacked bar plot to {output_path}")


def plot_stacked_bar_by_decade(data):
    """
    Create a stacked bar plot showing category distribution by decade.

    Args:
        data (pd.DataFrame): Shock data with categories and years
    """
    # Extract decade from year
    data["decade"] = data["year_of_shock"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )

    # Create crosstab for stacked bar
    crosstab = (
        pd.crosstab(data["decade"], data["Category (main)"], normalize="index") * 100
    )  # Convert to percentages

    # Sort decades chronologically
    decade_order = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020-2023"]
    # Only include decades that exist in the data
    decade_order = [d for d in decade_order if d in crosstab.index]
    crosstab = crosstab.reindex(decade_order)

    # Get color palette
    category_colors = get_category_colors()

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create stacked bar plot
    crosstab.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[category_colors.get(cat, "#E6E6FA") for cat in crosstab.columns],
        width=0.8,
    )

    # Customize plot
    ax.set_xlabel("Decade", fontsize=12)
    ax.set_ylabel("Percentage of Countries (%)", fontsize=12)
    ax.set_title("Distribution of Shock Categories by Decade", fontsize=14, pad=20)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    # Move legend outside plot
    ax.legend(
        title="Category", bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0
    )

    # Add grid
    ax.grid(True, axis="y", alpha=0.3)

    # Set y-axis to 0-100
    ax.set_ylim(0, 100)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path = Path("results/figures/shock_categories_by_decade.png")
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved decade stacked bar plot to {output_path}")


def plot_stacked_bar_by_decade_absolute(data):
    """
    Create a stacked bar plot showing category distribution by decade in absolute counts.

    Args:
        data (pd.DataFrame): Shock data with categories and years
    """
    # Extract decade from year
    data["decade"] = data["year_of_shock"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )

    # Create crosstab for stacked bar (absolute counts)
    crosstab = pd.crosstab(data["decade"], data["Category (main)"])

    # Sort decades chronologically
    decade_order = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020-2023"]
    # Only include decades that exist in the data
    decade_order = [d for d in decade_order if d in crosstab.index]
    crosstab = crosstab.reindex(decade_order)

    # Get color palette
    category_colors = get_category_colors()

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create stacked bar plot
    crosstab.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=[category_colors.get(cat, "#E6E6FA") for cat in crosstab.columns],
        width=0.8,
    )

    # Customize plot
    ax.set_xlabel("Decade", fontsize=12)
    ax.set_ylabel("Number of Countries", fontsize=12)
    ax.set_title(
        "Number of Countries with Largest Shock by Category and Decade",
        fontsize=14,
        pad=20,
    )

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    # Move legend outside plot
    ax.legend(
        title="Category", bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0
    )

    # Add grid
    ax.grid(True, axis="y", alpha=0.3)
    ax.xaxis.grid(False)  # Disable x-axis grid for cleaner look

    # Adjust layout
    plt.tight_layout()

    # Save figure
    output_path = Path("results/figures/shock_categories_by_decade_absolute.png")
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved decade absolute counts stacked bar plot to {output_path}")


def print_summary_statistics(data):
    """
    Print summary statistics about the shock data.

    Args:
        data (pd.DataFrame): Shock data with categories
    """
    print("\n=== SHOCK ANALYSIS SUMMARY ===\n")

    # Overall statistics
    print(f"Total countries analyzed: {len(data)}")
    print(f"Average shock magnitude: {data['largest_food_shock'].mean():.1f}%")
    print(f"Most severe shock: {data['largest_food_shock'].min():.1f}%")

    # Category statistics
    print("\nShocks by category:")
    category_stats = data.groupby("Category (main)")["largest_food_shock"].agg(
        ["count", "mean", "median", "min"]
    )
    category_stats.columns = ["Count", "Mean (%)", "Median (%)", "Most Severe (%)"]
    print(category_stats.round(1))

    # Continent statistics
    print("\nShocks by continent:")
    continent_stats = data.groupby("CONTINENT")["largest_food_shock"].agg(
        ["count", "mean", "min"]
    )
    continent_stats.columns = ["Count", "Mean (%)", "Most Severe (%)"]
    print(continent_stats.round(1))

    # Decade statistics
    data["decade"] = data["year_of_shock"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )
    print("\nShocks by decade:")
    decade_stats = data.groupby("decade")["largest_food_shock"].agg(
        ["count", "mean", "min"]
    )
    decade_stats.columns = ["Count", "Mean (%)", "Most Severe (%)"]
    print(decade_stats.round(1))


def plot_swarm_by_decade(data):
    """
    Create a swarm plot comparing shock sizes by decade with median lines.

    This function visualizes the distribution of crop production shocks across decades,
    showing individual data points as a swarm with median values highlighted.

    Args:
        data (pd.DataFrame): Shock data containing 'year_of_shock' and 'largest_crop_shock' columns
    """
    # Extract decade from year of shock
    # Handle years before 2020 as regular decades (e.g., 1990s)
    # Years 2020 and after as "2020-2023" since the data ends at 2023
    data["decade"] = data["year_of_shock"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )

    # Define the chronological order of decades
    # This ensures x-axis is sorted by time, not by median shock size
    decade_order = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020-2023"]

    # Filter to only include decades that exist in the data
    decade_order = [d for d in decade_order if d in data["decade"].values]

    # Set up the figure with appropriate size for readability
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create swarm plot
    # Using a single color (dimgrey) for consistency with ALLFED style
    # alpha=0.7 provides some transparency to see overlapping points
    sns.swarmplot(
        data=data,
        x="decade",
        y="largest_food_shock",
        order=decade_order,  # This ensures chronological ordering
        color="dimgrey",
        size=8,
        alpha=0.7,
        ax=ax,
    )

    # Calculate and add median lines for each decade
    for i, decade in enumerate(decade_order):
        # Extract data for current decade
        decade_data = data[data["decade"] == decade]["largest_food_shock"]

        # Calculate median value
        median_val = decade_data.median()

        # Draw horizontal line representing median
        # Line extends 0.4 units on each side of the decade position
        ax.hlines(
            median_val,  # y-position (median value)
            i - 0.4,  # x-start position
            i + 0.4,  # x-end position
            colors="red",  # Red color for visibility
            linestyles="solid",  # Solid line style
            linewidth=2.5,  # Thick line for emphasis
            label="Median" if i == 0 else "",  # Only label once for legend
        )

        # Add text label showing the median value
        # Position slightly to the right of the median line
        ax.text(
            i + 0.45,  # x-position (slightly right of line end)
            median_val,  # y-position (at median value)
            f"{median_val:.1f}%",  # Text showing median with 1 decimal
            va="center",  # Vertical alignment
            ha="left",  # Horizontal alignment
            fontsize=9,  # Slightly smaller font
            color="red",  # Match line color
        )

    # Customize plot appearance
    ax.set_xlabel("Decade", fontsize=12)
    ax.set_ylabel("Largest Crop Production Shock (%)", fontsize=12)
    ax.set_title("Distribution of Largest Crop Shocks by Decade", fontsize=14, pad=20)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha="right")

    # Add grid for easier value reading
    # Only on y-axis to avoid cluttering
    ax.grid(True, axis="y", alpha=0.3)
    ax.xaxis.grid(False)

    # Add a subtle box around the plot area
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)

    # Add legend if median lines were drawn
    if len(decade_order) > 0:
        ax.legend(loc="upper right", frameon=False)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save figure with high resolution
    output_path = Path("results/figures/shock_swarm_by_decade.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()

    print(f"Saved decade swarm plot to {output_path}")

    # Print summary statistics for each decade
    print("\nSummary statistics by decade:")
    for decade in decade_order:
        decade_data = data[data["decade"] == decade]["largest_food_shock"]
        print(f"\n{decade}:")
        print(f"  Count: {len(decade_data)}")
        print(f"  Median: {decade_data.median():.1f}%")
        print(f"  Mean: {decade_data.mean():.1f}%")
        print(f"  Min (most severe): {decade_data.min():.1f}%")
        print(f"  Max (least severe): {decade_data.max():.1f}%")


def main():
    """
    Main function to create all comparative shock analysis plots.
    """
    print("Loading shock data with continent information...")
    data = load_shock_data_with_continents()

    print("Creating swarm plot by category...")
    plot_swarm_by_category(data)

    print("Creating swarm plot by decade...")
    plot_swarm_by_decade(data)

    print("Creating stacked bar plot by continent (percentage)...")
    plot_stacked_bar_by_continent(data)

    print("Creating stacked bar plot by continent (absolute counts)...")
    plot_stacked_bar_by_continent_absolute(data)

    print("Creating stacked bar plot by decade (percentage)...")
    plot_stacked_bar_by_decade(data)

    print("Creating stacked bar plot by decade (absolute counts)...")
    plot_stacked_bar_by_decade_absolute(data)

    # Print summary statistics
    print_summary_statistics(data)

    print("\nAll plots saved successfully!")


if __name__ == "__main__":
    main()
