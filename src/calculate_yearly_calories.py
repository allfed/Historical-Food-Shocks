"""
Calculate total calories from crop production for each country and year.

This script processes FAO crop production data to calculate the total calories
produced by each country for each year based on a list of key crops and their
calorie values.
"""

import os
import pandas as pd

# Define paths
DATA_DIR = "data"
RESULTS_DIR = "results"
INPUT_FILE = "fao_crop_production_comprehensive.csv"
OUTPUT_FILE = "calories_by_countries.csv"

# Define calorie values for each crop (kcal per 100g)
CALORIE_VALUES = {
    # Cereals
    "Maize (corn)": 356,
    "Rice": 360,
    "Wheat": 334,
    "Barley": 332,
    "Sorghum": 343,
    # Sugar crops
    "Sugar cane": 30,
    "Sugar beet": 70,
    # Roots and tubers
    "Potatoes": 67,
    "Cassava, fresh": 109,
    "Sweet potatoes": 92,
    "Yams": 101,
    "Taro": 86,
    # Fruits
    "Bananas": 60,
    "Apples": 48,
    "Oranges": 34,
    "Grapes": 53,
    "Watermelons": 17,
    # Vegetables
    "Tomatoes": 17,
    "Onions and shallots, green": 31,
    "Cucumbers and gherkins": 13,
    "Cabbages": 19,
    "Eggplants (aubergines)": 21,
}


def calculate_calories(df):
    """
    Calculate calories for each crop based on production weight.

    Args:
        df (pandas.DataFrame): Filtered production data

    Returns:
        tuple: (DataFrame with calorie calculations, list of calorie column names)
    """
    # Add calorie value column
    df["Calorie_Value"] = df["Item"].map(CALORIE_VALUES)

    # Get year columns (those starting with 'Y')
    year_cols = [col for col in df.columns if col.startswith("Y")]

    # Calculate calories for each year
    for year_col in year_cols:
        # Convert tonnes to grams and multiply by calorie value per 100g
        df[year_col + "_calories"] = (
            df[year_col] * 1_000_000 * df["Calorie_Value"] / 100
        )

    return df, [col for col in df.columns if col.endswith("_calories")]


def aggregate_calories_by_country(df, calorie_cols):
    """
    Aggregate calories by country and year.

    Args:
        df (pandas.DataFrame): Data with calorie calculations
        calorie_cols (list): List of column names containing calorie values

    Returns:
        pandas.DataFrame: Aggregated calories by country and year
    """
    # Group by country and sum calories
    df_agg = df.groupby("Area")[calorie_cols].sum().reset_index()

    # Clean up column names
    column_mapping = {
        col: col.replace("Y", "").replace("_calories", "") for col in calorie_cols
    }

    # If a country has 0 production for a year, set it to nan
    # Because if a country has 0 production, it means no data for that year
    # And we don't to confuse it with 0 calories
    # Also print all the countries that have 0 production
    for col in calorie_cols:
        df_agg[col] = df_agg[col].replace(0, pd.NA)
        if df_agg[col].isna().all():
            print(f"Country {df_agg['Area'].unique()} has 0 production for {col}")

    # Convert all columns to numeric, so we can do the interpolation
    df_agg[calorie_cols] = df_agg[calorie_cols].apply(pd.to_numeric, errors="coerce")

    # Rename/remove some of the countries for clarity
    # Remove "China" beccause this refers to Taiwan and the mainland China
    df_agg = df_agg[df_agg["Area"] != "China"]
    # Rename "China; Taiwan Province of" to "Taiwan"
    df_agg.loc[df_agg["Area"] == "China, Taiwan Province of", "Area"] = "Taiwan"
    # Rename China, mainland to "China"
    df_agg.loc[df_agg["Area"] == "China, mainland", "Area"] = "China"
    # Remove Singapore, because the data is not reliable
    df_agg = df_agg[df_agg["Area"] != "Singapore"]

    # Make the index the country names
    df_agg.set_index("Area", inplace=True)

    # South Sudan and Sudan only have data for the last 13 years. 
    # So we need to fill the missing years with the data from Sudan (former)
    # This is not perfect, but it's better than leaving them empty
    # Add the data from Sudan (former) to South Sudan
    df_agg.loc["South Sudan"] = df_agg.loc["Sudan (former)"].copy()
    # Add the data from Sudan (former) to Sudan
    df_agg.loc["Sudan"] = df_agg.loc["Sudan (former)"].copy()
    # Remove the data from Sudan (former)
    df_agg = df_agg[df_agg.index != "Sudan (former)"]
    return df_agg.rename(columns=column_mapping)


def main():
    """
    Main function to process data and calculate calories.

    This function orchestrates the entire process:
    1. Loads the raw production data
    2. Filters for relevant crops
    3. Calculates calories for each crop and year
    4. Aggregates calories by country and year
    5. Saves the results to a CSV file
    """
    # Create results directory if needed
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Load and process data
    input_path = os.path.join(DATA_DIR, INPUT_FILE)
    df = pd.read_csv(input_path)

    df_calories, calorie_cols = calculate_calories(df)

    df_agg = aggregate_calories_by_country(df_calories, calorie_cols)

    # Remove countries with less than 1 million population
    # or an area below 10.000 km2, because the data is not reliable
    # This is optinal, seems to be fine if we keep them
    countries_to_remove = []
    # countries_to_remove = [
    #     "Antigua and Barbuda",
    #     "Vanuatu",
    #     "Micronesia",
    #     "Micronesia (Federated States of)",
    #     "Saint Kitts and Nevis",
    #     "Bahamas",
    #     "Barbados",
    #     "China, Hong Kong SAR",
    #     "China, Macao SAR",
    #     "Bahrain",
    #     "Belize",
    #     "Bhutan",
    #     "Brunei Darussalam",
    #     "Cabo Verde",
    #     "Comoros",
    #     "Cook Islands",
    #     "Djibouti",
    #     "Dominica",
    #     "Eswatini",
    #     "Faroe Islands",
    #     "Fiji",
    #     "French Guiana",
    #     "French Polynesia",
    #     "Grenada",
    #     "Guadeloupe",
    #     "Kiribati",
    #     "Kuwait",
    #     "Luxembourg",
    #     "Maldives",
    #     "Malta",
    #     "Martinique",
    #     "Mauritius",
    #     "Melanesia",
    #     "Montenegro",
    #     "Nauru",
    #     "New Caledonia",
    #     "Niue",
    #     "Réunion",
    #     "Saint Lucia",
    #     "Saint Vincent and the Grenadines",
    #     "Samoa",
    #     "Sao Tome and Principe",
    #     "Seychelles",
    #     "Solomon Islands",
    #     "Trinidad and Tobago",
    #     "Tuvalu",
    #     "Tokelau",
    #     "Tonga",
    # ]
    # Remove countries with clearly incorrect data
    df_agg = df_agg[~df_agg.index.isin(countries_to_remove)]

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
        "Northern America",
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
    regions_df = df_agg[df_agg.index.isin(regions)]
    groups_df = df_agg[df_agg.index.isin(groups_of_countries)]
    # Save the regions and groups of countries in separate files
    regions_df.to_csv(os.path.join("results", "calories_by_regions.csv"))
    groups_df.to_csv(os.path.join("results", "calories_by_groups_of_countries.csv"))
    # Remove regions and groups of countries from the data
    df_agg = df_agg[~df_agg.index.isin(regions)]
    df_agg = df_agg[~df_agg.index.isin(groups_of_countries)]

    # Save results
    output_path = os.path.join(RESULTS_DIR, OUTPUT_FILE)
    df_agg.to_csv(output_path)


if __name__ == "__main__":
    main()
