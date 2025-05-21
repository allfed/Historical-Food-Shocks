#!/usr/bin/env python3
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
OUTPUT_FILE = "calories.csv"

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
    "Eggplants (aubergines)": 21
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
    df['Calorie_Value'] = df['Item'].map(CALORIE_VALUES)
    
    # Get year columns (those starting with 'Y')
    year_cols = [col for col in df.columns if col.startswith('Y')]
    
    # Calculate calories for each year
    for year_col in year_cols:
        # Convert tonnes to grams and multiply by calorie value per 100g
        df[year_col + '_calories'] = (
            df[year_col] * 1_000_000 * df['Calorie_Value'] / 100
        )
    
    return df, [col for col in df.columns if col.endswith('_calories')]

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
    df_agg = df.groupby('Area')[calorie_cols].sum().reset_index()
    
    # Clean up column names
    column_mapping = {col: col.replace('Y', '').replace('_calories', '') 
                     for col in calorie_cols}
    
    # If a country has 0 production for a year, set it to nan
    # Because if a country has 0 production, it means no data for that year
    # And we don't to confuse it with 0 calories
    # Also print all the countries that have 0 production
    for col in calorie_cols:
        df_agg[col] = df_agg[col].replace(0, pd.NA)
        if df_agg[col].isna().all():
            print(f"Country {df_agg['Area'].unique()} has 0 production for {col}")

    # Convert all columns to numeric, so we can do the interpolation
    df_agg[calorie_cols] = df_agg[calorie_cols].apply(pd.to_numeric, errors='coerce')
    # Make the index the country names
    df_agg.set_index('Area', inplace=True)
    # If a country has data gap between two years, do a linear interpolation
    # to fill the gap
    # This will only interpolate values that have at least one non-NaN value before and after
    df_agg = df_agg.interpolate(method='linear', limit_area='inside', axis=1)
    
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
    
    # Save results
    output_path = os.path.join(RESULTS_DIR, OUTPUT_FILE)
    df_agg.to_csv(output_path)

if __name__ == "__main__":
    main()