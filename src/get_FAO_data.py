"""
Download FAO data from the FAO website and save it to a CSV file.
"""

import pandas as pd
import os
import sys
from tqdm.auto import tqdm
from pathlib import Path

def load_local_fao_crop_production(data_path):
    """
    Load FAO crop production data from a local CSV file.
    
    Args:
        data_path (Path): Path to the FAOSTAT crop production CSV file
        
    Returns:
        DataFrame: Complete crop production dataset
    """
    print(f"Loading crop production data from: {data_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found at: {data_path}")
        
        # Load the CSV file
        df = pd.read_csv(data_path)
        
        print(f"Data loaded successfully: {len(df):,} rows, {len(df.columns)} columns")
        return df
    
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None

def filter_crops_of_interest(df, crop_list):
    """
    Filter the raw production dataset to include only crops of interest.
    
    Args:
        df (DataFrame): Complete FAOSTAT crop production dataset
        crop_list (dict): Dictionary of crop categories and their names
        
    Returns:
        DataFrame: Filtered dataset containing only crops of interest
    """
    # Flatten the crop list for filtering
    flat_crop_list = [crop_name for category, crops in crop_list.items() 
                    for crop_name in crops]
    
    # Create a copy of the dataframe to avoid modifying the original
    filtered_df = df.copy()
    
    # Filter to include only the crops of interest
    # Using partial matching because FAO item names might not match exactly
    mask = filtered_df['Item'].apply(lambda x: any(crop.lower() in x.lower() for crop in flat_crop_list))
    filtered_df = filtered_df[mask]
    
    # Add crop category information
    filtered_df['Crop Category'] = 'Other'
    for category, crops in crop_list.items():
        for crop_name in crops:
            crop_mask = filtered_df['Item'].str.contains(crop_name, case=False)
            filtered_df.loc[crop_mask, 'Crop Category'] = category
            
            # Also standardize the crop name
            filtered_df.loc[crop_mask, 'Crop Name'] = crop_name
    
    print(f"Filtered to {len(filtered_df):,} rows for the specified crops")
    
    # Report which crops were found and which weren't
    found_crops = filtered_df['Crop Name'].unique()
    print(f"Found data for {len(found_crops)} crops: {', '.join(sorted(found_crops))}")
    
    missing_crops = [crop for crop in flat_crop_list if crop not in found_crops]
    if missing_crops:
        print(f"Warning: No data found for {len(missing_crops)} crops: {', '.join(missing_crops)}")
        print("Check if these crops use different names in the FAO dataset")
    
    return filtered_df

def clean_and_format_dataframe(df):
    """
    Clean and format the FAOSTAT DataFrame.
    
    Args:
        df (DataFrame): FAOSTAT data
        
    Returns:
        DataFrame: Cleaned and formatted data
    """
    # Select and rename relevant columns
    try:
        # Create a new cleaned DataFrame with standardized column names
        cleaned_df = pd.DataFrame()
        
        # Add standardized columns
        cleaned_df['Area'] = df['Area']
        
        if 'Area Code' in df.columns:
            cleaned_df['Area Code'] = df['Area Code']
            
        cleaned_df['Item'] = df['Item']
            
        if 'Item Code' in df.columns:
            cleaned_df['Item Code'] = df['Item Code']
            
        # Extract Element information (Production, Area harvested, etc.)
        if 'Element' in df.columns:
            # Only keep "Production" rows (not Area harvested or Yield)
            if 'Production' in df['Element'].unique():
                # We'll add this filter only if we're certain it won't remove all data
                production_mask = df['Element'].str.contains('Production', case=False)
                if production_mask.sum() > 0:
                    df = df[production_mask]
                    cleaned_df['Element'] = df['Element']
        
        # Extract Year and Value
        cleaned_df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
        cleaned_df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
            
        if 'Unit' in df.columns:
            cleaned_df['Unit'] = df['Unit']
            
        if 'Flag' in df.columns:
            cleaned_df['Flag'] = df['Flag']
            
        # Copy crop category and name
        if 'Crop Category' in df.columns:
            cleaned_df['Crop Category'] = df['Crop Category']
        
        if 'Crop Name' in df.columns:
            cleaned_df['Crop Name'] = df['Crop Name']
        
        # Sort by Area, Year, and Item
        cleaned_df = cleaned_df.sort_values(by=['Area', 'Year', 'Item'])
        
        # Report on data years
        year_range = cleaned_df['Year'].dropna().astype(int)
        if not year_range.empty:
            print(f"Data spans from {year_range.min()} to {year_range.max()}")
        
        # Report on countries
        country_count = cleaned_df['Area'].nunique()
        print(f"Data includes {country_count} countries/regions")
        
        return cleaned_df
    
    except Exception as e:
        print(f"Error in cleaning dataframe: {str(e)}")
        print("Returning original dataframe")
        return df

def reshape_for_analysis(df):
    """
    Reshape the long-format DataFrame to a wide format suitable for analysis.
    
    Args:
        df (DataFrame): Long-format FAOSTAT data
        
    Returns:
        DataFrame: Wide-format data with crops as columns
    """
    # Create a pivot table with countries and years as index and crops as columns
    try:
        crop_col = 'Crop Name' if 'Crop Name' in df.columns else 'Item'
        
        pivot_df = df.pivot_table(
            index=['Area', 'Year'],
            columns=crop_col,
            values='Value',
            aggfunc='sum'  # In case there are duplicate entries
        ).reset_index()
        
        return pivot_df
    except Exception as e:
        print(f"Error reshaping data: {str(e)}")
        return df

def save_data_to_csv(df, output_path):
    """
    Save the DataFrame to a CSV file.
    
    Args:
        df (DataFrame): Data to save
        output_path (Path): Path where to save the CSV file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the file
    df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")

def main():
    """
    Main function to process all crop production data.

    Download the FAO data for the most produced
    Cereals (Maize, Rice, Wheat, Barley, Sorghum),
    Sugar crops (Sugar cane, Sugar beet)
    Roots and tubers (Potatoes, Cassava, Sweet potatoes, Yams, Taro),
    Fruits (Bananas, Apples, Oranges, Grapes, Watermelons),
    Vegetables (Tomatoes, Onions, Cucumbers and gherkins, Cabbages, Eggplants)

    These are the top crops according to FAO data 
    https://openknowledge.fao.org/server/api/core/bitstreams/df90e6cf-4178-4361-97d4-5154a9213877/content
    """
    # Setup paths relative to script location using Path for cross-platform compatibility
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    # Define input file path - adjust filename as needed
    input_file = data_dir / "Production_Crops_Livestock_E_All_Data_NOFLAG.csv"
    
    # Define output file paths - saving to the data folder as requested
    output_file_long = data_dir / "fao_crop_production_comprehensive.csv"
    output_file_wide = data_dir / "fao_crop_production_wide_format.csv"
    
    # Print paths for verification
    print(f"Project structure:")
    print(f"- Script location: {script_dir}")
    print(f"- Project root: {project_root}")
    print(f"- Data directory: {data_dir}")
    print(f"- Input file: {input_file}")
    print(f"- Output files will be saved to: {data_dir}")
    
    # Define crops of interest
    crop_list = {
        "Cereals": [
            "Maize", "Rice", "Wheat", "Barley", "Sorghum"
        ],
        "Sugar crops": [
            "Sugar cane", "Sugar beet"
        ],
        "Roots and tubers": [
            "Potatoes", "Cassava", "Sweet potatoes", "Yams", "Taro"
        ],
        "Fruits": [
            "Bananas", "Apples", "Oranges", "Grapes", "Watermelons"
        ],
        "Vegetables": [
            "Tomatoes", "Onions", "Cucumbers", "Cabbages", "Eggplants"
        ]
    }
    
    # Load the data
    full_production_data = load_local_fao_crop_production(input_file)
    
    if full_production_data is None or len(full_production_data) == 0:
        print("Failed to load data or data is empty.")
        return None
    
    # Filter to crops of interest
    filtered_data = filter_crops_of_interest(full_production_data, crop_list)
    
    # Clean and format the data
    cleaned_data = clean_and_format_dataframe(filtered_data)
    
    # Save the data
    if not cleaned_data.empty:
        save_data_to_csv(cleaned_data, output_file_long)
        
        # Create a wide-format version for analysis
        wide_data = reshape_for_analysis(cleaned_data)
        save_data_to_csv(wide_data, output_file_wide)
        
        # Display sample of the data
        print("\nSample of the processed data:")
        print(cleaned_data.head())  
    return cleaned_data

if __name__ == "__main__":
    # Run the main function
    crop_data = main()
