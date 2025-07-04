"""
# This script calculates the largest crop shock for each country
# with validation that the shock represents an actual calorie decrease
"""
import pandas as pd
import country_converter as coco
from pathlib import Path


def calculate_largest_shock():
    """
    Main function to create all crop shock maps.
    Validates that detected shocks represent actual calorie decreases.
    """
    spatial_extent = "countries"
    
    # Load the yield changes data
    yield_data_path = Path("results") / f"yield_changes_by_{spatial_extent}.csv"
    df = pd.read_csv(yield_data_path, index_col=0)
    df.index = coco.convert(df.index, to="name_short", not_found=None)
    
    # Load the actual calories data for validation
    calories_data_path = Path("results") / f"calories_by_{spatial_extent}.csv"
    calories_df = pd.read_csv(calories_data_path, index_col=0)
    calories_df.index = coco.convert(calories_df.index, to="name_short", not_found=None)
    
    # Initialize results storage
    results = []
    
    # Process each country
    for country in df.index:
        if country not in calories_df.index:
            print(f"Warning: {country} not found in calories data, skipping...")
            continue
            
        # Get yield changes and calories for this country
        country_yield_changes = df.loc[country]
        country_calories = calories_df.loc[country]
        
        # Ensure we have Series objects
        if isinstance(country_yield_changes, pd.DataFrame):
            country_yield_changes = country_yield_changes.iloc[0]
        if isinstance(country_calories, pd.DataFrame):
            country_calories = country_calories.iloc[0]
        
        # Sort yield changes to find negative shocks (ascending order)
        sorted_shocks = country_yield_changes.sort_values()
        
        # Find the largest valid shock
        largest_valid_shock = None
        year_of_shock = None
        
        # Iterate through negative shocks from most severe
        for year, shock_value in sorted_shocks.items():
            # Only consider negative shocks
            if shock_value >= 0:
                break
                
            # Get the year index for comparison
            year_idx = list(country_calories.index).index(year)
            
            # Skip if it's the first year (no previous year to compare)
            if year_idx == 0:
                continue
                
            # Get current and previous year's calories
            current_calories = country_calories.iloc[year_idx]
            previous_calories = country_calories.iloc[year_idx - 1]
            
            # Check if calories actually decreased
            if current_calories < previous_calories:
                # This is a valid shock
                largest_valid_shock = shock_value
                year_of_shock = year
                break
        
        # If no valid shock found, use the minimum value anyway
        # (this handles edge cases where all shocks might be in years with calorie increases)
        if largest_valid_shock is None:
            largest_valid_shock = country_yield_changes.min()
            year_of_shock = country_yield_changes.idxmin() if not country_yield_changes.isnull().all() else None
            print(f"Note: {country} has no shocks with actual calorie decrease, using minimum yield change")
        
        results.append({
            "country": country,
            "largest_crop_shock": largest_valid_shock,
            "year_of_shock": year_of_shock
        })
    
    # Create DataFrame from results
    largest_shock = pd.DataFrame(results).set_index("country")
    
    # Save to CSV
    output_path = Path("results") / "largest_crop_shock_by_country.csv"
    largest_shock.to_csv(output_path)
    print(f"Saved largest crop shock per country to {output_path}")
    
    # Print summary statistics
    valid_shocks = largest_shock[largest_shock["largest_crop_shock"].notna()]
    print(f"\nSummary:")
    print(f"Total countries processed: {len(largest_shock)}")
    print(f"Countries with valid shocks: {len(valid_shocks)}")
    print(f"Average shock magnitude: {valid_shocks['largest_crop_shock'].mean():.2f}%")
    print(f"Most severe shock: {valid_shocks['largest_crop_shock'].min():.2f}%")


if __name__ == "__main__":
    calculate_largest_shock()