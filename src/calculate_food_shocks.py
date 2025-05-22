import numpy as np
import pandas as pd
import os
from scipy.signal import savgol_filter


def calculate_changes_savgol(data, window_length=11, polyorder=3):
    """
    Calculate changes in yield for each year using a Savitzky-Golay filter
    
    Arguments:
        data (pd.DataFrame): DataFrame with countries as rows and years as columns
        window_length (int): The length of the filter window (must be positive odd integer)
        polyorder (int): The order of the polynomial used to fit the samples
                         (must be less than window_length)
    
    Returns:
        pd.DataFrame: DataFrame with percentage changes for each country and year
    """
    # Validate parameters
    if window_length % 2 == 0:
        raise ValueError("window_length must be an odd integer")
    if polyorder >= window_length:
        raise ValueError("polyorder must be less than window_length")
    
    # Create empty DataFrame to store results
    pct_changes = pd.DataFrame(index=data.index, columns=data.columns)
    
    # For each country, calculate percentage changes
    for country in data.index:
        # Extract yield data for the country
        yields = data.loc[country]
               
        # Apply Savitzky-Golay filter to get the smoothed baseline
        smoothed_yields = savgol_filter(yields, window_length, polyorder)
        
        # Calculate percentage changes
        pct_change = ((yields - smoothed_yields) / smoothed_yields) * 100
        
        # Store in results DataFrame
        pct_changes.loc[country] = pct_change
    
    return pct_changes

def main():
    """
    Main function to run the analysis
    """
    # Set path to input file
    print(os.getcwd())
    input_file = os.path.join("results", "calories.csv")
    
    # Load data
    print(f"Loading data from {input_file}...")
    data = pd.read_csv(input_file, index_col=0)

    # Countries with clearly incorrect data or so low production that they are not relevant
    countries_to_remove = [
        "Singapore",  # data says that they did only produce a few thousand calories in the 1990s
        "Antigua and Barbuda",  # too small production
        "Vanuatu",  # too small production
        "Micronesia",  # too small production
        "Micronesia (Federated States of)",  # too small production
        "Saint Kitts and Nevis",  # too small production
        "Bahamas",  # too small production
        "Barbados",  # too small production
        "China, Hong Kong SAR",  # too small production
        "China, Macao SAR",  # too small production
    ]
    # Remove countries with clearly incorrect data
    data = data[~data.index.isin(countries_to_remove)]

    # Also save the regions and groups of countries in separate files
    regions = [
        "Africa",
        "Americas",
        "Asia",
        "Caribbean",
        "Central America",
        "Central Asia",
        "Eastern Africa",
        "Eastern Asia",
        "Eastern Europe",
        "Europe",
        "Middle Africa",
        "Northern Africa",
        "Northern Europe",
        "Oceania",
        "Polynesia",
        "South-eastern Asia",
        "Southern Africa",
        "Southern Asia",
        "Southern Europe",
        "Western Africa",
        "Western Asia",
        "Western Europe",
        "World",
        "South America",
    ]

    groups_of_countries = [
        "European Union (27)",
        "Land Locked Developing Countries",
        "Least Developed Countries",
        "Low Income Food Deficit Countries",
        "Net Food Importing Developing Countries",
        "Australia and New Zealand",  # to avoid double counting
        "Small Island Developing States",
    ]
    # Create two seperate dataframes for regions and groups of countries
    regions_df = data[data.index.isin(regions)]
    groups_df = data[data.index.isin(groups_of_countries)]
    # Save the regions and groups of countries in separate files
    regions_df.to_csv(os.path.join("results", "calories_by_regions.csv"))
    groups_df.to_csv(os.path.join("results", "calories_by_groups_of_countries.csv"))
    # Remove regions and groups of countries from the data
    data = data[~data.index.isin(regions)]
    data = data[~data.index.isin(groups_of_countries)]
    
    # Calculate percentage changes using Savitzky-Golay filter
    print("Calculating yield changes using Savitzky-Golay filter...")
    pct_changes = calculate_changes_savgol(data)
    
    # Save results
    output_file = os.path.join("results", "yield_changes.csv")
    pct_changes.to_csv(output_file)
    print(f"Results saved to {output_file}")

    return pct_changes

if __name__ == "__main__":
    pct_changes = main()
    # Save a csv in the results folder
    print("Analysis complete.")