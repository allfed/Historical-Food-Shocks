"""
Download FAO data from the FAO website and save it to a CSV file.
"""

import pandas as pd
import os
import zipfile
from pathlib import Path

def extract_and_load_fao_data(zip_path, csv_filename):
    """
    Extract and load FAO crop production data from a ZIP file.
    
    Args:
        zip_path (Path): Path to the FAOSTAT ZIP file
        csv_filename (str): Name of the CSV file within the ZIP to extract
        
    Returns:
        DataFrame: Complete crop production dataset
    """
    print(f"Extracting {csv_filename} from {zip_path}")
    
    try:
        # Extract the CSV file from the ZIP archive
        with zipfile.ZipFile(zip_path) as z:
            # Check if the specified file exists in the ZIP
            if csv_filename not in z.namelist():
                # Try to find a similar file
                available_files = [f for f in z.namelist() if f.endswith('.csv')]
                if available_files:
                    print(f"{csv_filename} not found. Using {available_files[0]} instead.")
                    csv_filename = available_files[0]
                else:
                    raise FileNotFoundError(f"No CSV files found in ZIP.")
            
            # Read the CSV into a pandas DataFrame
            with z.open(csv_filename) as f:
                df = pd.read_csv(f)
        
        print(f"Data loaded: {len(df):,} rows")
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
    
    # Find the column containing crop/item names (usually 'Item')
    item_col = next((col for col in df.columns if col.lower() in ['item', 'item_name', 'item_code_name', 'commodity']), None)
    
    if not item_col:
        print("Warning: Could not find item column. Columns available:", df.columns.tolist())
        return None
    
    # Filter to include only the crops of interest
    mask = df[item_col].apply(lambda x: any(crop.lower() in str(x).lower() for crop in flat_crop_list))
    filtered_df = df[mask].copy()
    
    # No reformatting, just add crop category information
    filtered_df['Crop Category'] = 'Other'
    for category, crops in crop_list.items():
        for crop_name in crops:
            crop_mask = filtered_df[item_col].str.contains(crop_name, case=False)
            filtered_df.loc[crop_mask, 'Crop Category'] = category
            filtered_df.loc[crop_mask, 'Crop Name'] = crop_name

    # Only keep the rows with "t" as Unit
    filtered_df = filtered_df[filtered_df['Unit'] == 't'].copy()
    
    print(f"Filtered to {len(filtered_df):,} rows for specified crops")    
    return filtered_df

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
    # Setup paths relative to script location
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    # Define input file path - adjust filename as needed
    zip_file = data_dir / "Production_Crops_Livestock_E_All_Data.zip"
    csv_in_zip = "Production_Crops_Livestock_E_All_Data_NOFLAG.csv"
    
    # Define output file path
    output_file = data_dir / "fao_crop_production_comprehensive.csv"
    
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
    
    # Load the data directly from the ZIP file
    full_production_data = extract_and_load_fao_data(zip_file, csv_in_zip)
    
    if full_production_data is None or len(full_production_data) == 0:
        print("Failed to load data or data is empty.")
        return None
    
    # Filter to crops of interest (no reformatting)
    filtered_data = filter_crops_of_interest(full_production_data, crop_list)
    
    if filtered_data is None:
        print("Failed to filter data.")
        return None
    
    # Save the data (original format preserved)
    save_data_to_csv(filtered_data, output_file)
    
    return filtered_data

if __name__ == "__main__":
    # Run the main function
    crop_data = main()

    print(crop_data.describe(include='all'))
    print(crop_data.head())
