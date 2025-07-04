"""
# This script calculates the largest crop shock for each country
"""
import pandas as pd
import country_converter as coco
from pathlib import Path


def calculate_largest_shock():
    """
    Main function to create all crop shock maps.
    """
    spatial_extent = "countries"
    # Load the data
    data_path = Path("results") / f"yield_changes_by_{spatial_extent}.csv"
    df = pd.read_csv(data_path, index_col=0)
    df.index = coco.convert(df.index, to="name_short", not_found=None)
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
    calculate_largest_shock()