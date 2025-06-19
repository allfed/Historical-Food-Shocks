"""
Create a bar plot showing the proportion of countries with food shocks per decade,
adjusted for the changing number of countries over time.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set up ALLFED plotting style
plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


def main():
    """Create bar plot of shock proportions adjusted for country counts."""

    # Load the shock data
    shock_data = pd.read_csv("results/largest_food_shock_by_country_with_reasons.csv")

    # Load country count data
    country_counts = pd.read_csv("data/number-of-countries.csv")

    # Filter for World entity and years 1961-2023
    world_counts = country_counts[
        (country_counts["Entity"] == "World")
        & (country_counts["Year"] >= 1961)
        & (country_counts["Year"] <= 2023)
    ].copy()

    # Extract decade from shock year
    shock_data["decade"] = shock_data["year_of_shock"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )

    # Count countries with shocks per decade
    shocks_per_decade = shock_data.groupby("decade").size()

    # Calculate average country count per decade
    world_counts["decade"] = world_counts["Year"].apply(
        lambda x: f"{int(x//10)*10}s" if x < 2020 else "2020-2023"
    )

    # Average number of countries per decade using Butcher and Griffiths data
    avg_countries_per_decade = (
        world_counts.groupby("decade")[
            "Number of states in a region (Butcher and Griffiths)"
        ]
        .mean()
        .round()
        .astype(int)
    )

    # Create DataFrame with both shock counts and country counts
    decade_data = pd.DataFrame(
        {
            "Countries with shocks": shocks_per_decade,
            "Total countries": avg_countries_per_decade,
        }
    )

    # Calculate proportion
    decade_data["Proportion"] = (
        decade_data["Countries with shocks"] / decade_data["Total countries"]
    )

    # Define decade order
    decade_order = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020-2023"]
    decade_data = decade_data.reindex(decade_order)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create bar plot
    bars = ax.bar(
        decade_data.index,
        decade_data["Proportion"] * 100,  # Convert to percentage
        color="dimgrey",
        edgecolor="white",
        linewidth=0.5,
    )

    # Add value labels on bars
    for i, (bar, total, shocks) in enumerate(
        zip(bars, decade_data["Total countries"], decade_data["Countries with shocks"])
    ):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{shocks}/{total}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # Customize plot
    ax.set_xlabel("Decade", fontsize=12)
    ax.set_ylabel("Percentage of Countries with Largest Shock (%)", fontsize=12)
    ax.set_title(
        "Proportion of Countries Experiencing Their Largest Food Shock by Decade",
        fontsize=14,
        pad=20,
    )

    # Set y-axis limits
    ax.set_ylim(0, max(decade_data["Proportion"] * 100) * 1.15)

    # Add grid
    ax.grid(True, axis="y", alpha=0.3)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")

    # Save figure
    output_path = Path("results/figures/shock_proportion_by_decade.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()


if __name__ == "__main__":
    main()
