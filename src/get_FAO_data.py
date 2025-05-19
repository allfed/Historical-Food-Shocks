"""
Download FAO data from the FAO website and save it to a CSV file.
"""

import pandas as pd
import requests
import io
import zipfile
from tqdm.auto import tqdm
import os

def download_fao_crop_production_bulk():
    """
    Download FAO crop production data from the bulk download files.
    This is more reliable than using the API when it's experiencing issues.
    
    Returns:
        DataFrame: Complete crop production dataset
    """
    # URL for bulk download of crop production data
    url = "https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_E_All_Data.zip"
    
    print(f"Downloading crop production data from FAOSTAT bulk files...")
    print(f"URL: {url}")
    print("This may take a few minutes depending on your internet connection...")
    
    try:
        # Download the zip file
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        
        # Check if the download was successful
        if response.status_code != 200:
            raise Exception(f"Failed to download data: Status code {response.status_code}")
        
        # Download with progress bar
        content = io.BytesIO()
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            content.write(data)
        progress_bar.close()
        
        content.seek(0)
        
        # Extract the CSV file from the ZIP archive
        print("Extracting data from zip file...")
        z = zipfile.ZipFile(content)
        csv_filename = [f for f in z.namelist() if f.endswith('.csv')][0]
        
        # Read the CSV into a pandas DataFrame
        print(f"Processing file: {csv_filename}")
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)
        
        print(f"Data loaded successfully: {len(df)} rows")
        return df
    
    except Exception as e:
        print(f"Error downloading bulk data: {str(e)}")
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
    
    print(f"Filtered to {len(filtered_df)} rows for the specified crops")
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
        # Handle different column naming patterns in FAOSTAT data
        if 'Area' in df.columns:
            area_col = 'Area'
        elif 'Country' in df.columns:
            area_col = 'Country'
        else:
            area_col = df.columns[0]  # First column is typically the country
            
        if 'Item' in df.columns:
            item_col = 'Item'
        elif 'Crop' in df.columns:
            item_col = 'Crop'
        else:
            # Try to find a column that might contain crop names
            for col in df.columns:
                if any(crop_term in col.lower() for crop_term in ['item', 'crop', 'commodity']):
                    item_col = col
                    break
            else:
                item_col = None
                print("Warning: Could not identify the crop/item column")
            
        if 'Element' in df.columns:
            element_col = 'Element'
        else:
            # Try to find a column that might identify the element (production, yield, etc.)
            for col in df.columns:
                if any(term in col.lower() for term in ['element', 'measure', 'metric']):
                    element_col = col
                    break
            else:
                element_col = None
                print("Warning: Could not identify the element column")
                
        if 'Value' in df.columns:
            value_col = 'Value'
        else:
            # Sometimes the value is in a column called something else
            numeric_cols = df.select_dtypes(include=['number']).columns
            # Exclude year column
            numeric_cols = [col for col in numeric_cols if 'year' not in col.lower()]
            if numeric_cols:
                value_col = numeric_cols[0]
            else:
                value_col = None
                print("Warning: Could not identify the value column")
        
        # Only keep rows related to production (not area harvested or yield)
        if element_col and 'Production' in df[element_col].unique():
            df = df[df[element_col].str.contains('Production', case=False)]
        
        # Create a new cleaned DataFrame with standardized column names
        cleaned_df = pd.DataFrame()
        
        # Add standardized columns
        if area_col:
            cleaned_df['Area'] = df[area_col]
        
        if 'Area Code' in df.columns:
            cleaned_df['Area Code'] = df['Area Code']
        elif 'Country Code' in df.columns:
            cleaned_df['Area Code'] = df['Country Code']
            
        if item_col:
            cleaned_df['Item'] = df[item_col]
            
        if 'Item Code' in df.columns:
            cleaned_df['Item Code'] = df['Item Code']
            
        # Extract the Year and Value columns
        if 'Year' in df.columns:
            cleaned_df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
        else:
            # Sometimes years are part of column names in wide format data
            # For now we'll assume long format, but this could be expanded
            print("Warning: Could not find 'Year' column")
            
        if value_col:
            cleaned_df['Value'] = pd.to_numeric(df[value_col], errors='coerce')
            
        if 'Unit' in df.columns:
            cleaned_df['Unit'] = df['Unit']
        elif 'Element Unit' in df.columns:
            cleaned_df['Unit'] = df['Element Unit']
            
        if 'Flag' in df.columns:
            cleaned_df['Flag'] = df['Flag']
        elif 'Flag Description' in df.columns:
            cleaned_df['Flag'] = df['Flag Description']
            
        # Copy crop category and name if they exist
        if 'Crop Category' in df.columns:
            cleaned_df['Crop Category'] = df['Crop Category']
        
        if 'Crop Name' in df.columns:
            cleaned_df['Crop Name'] = df['Crop Name']
        
        # Sort by Area, Year, and Item
        cleaned_df = cleaned_df.sort_values(by=['Area', 'Year', 'Item'])
        
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

def save_data_to_csv(df, filename="fao_crop_production_data.csv"):
    """
    Save the DataFrame to a CSV file.
    
    Args:
        df (DataFrame): Data to save
        filename (str): Name of the CSV file
    """
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


def main():
    """
    Main function to retrieve and process all crop production data.

    Download the FAO data for the most produced
    Cereals (Maize, Rice, Wheat, Barley, Sorghum),
    Sugar crops (Sugar cane, Sugar beet)
    Roots and tubers (Potatoes, Cassava, Sweet potatoes, Yams, Taro),
    Fruits (Bananas, Apples, Oranges, Grapes, Watermelons),
    Vegetables (Tomatoes, Onions, Cucumbers and gherkins, Cabbages, Eggplants)

    These are the top crops according to FAO data 
    https://openknowledge.fao.org/server/api/core/bitstreams/df90e6cf-4178-4361-97d4-5154a9213877/content
    """
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
    
    # Try to download from bulk files first
    print("Attempting to download data from FAOSTAT bulk files...")
    full_production_data = download_fao_crop_production_bulk()
    
    if full_production_data is None or len(full_production_data) == 0:
        print("Bulk download failed or returned empty data.")
        return None
    
    # Filter to crops of interest
    filtered_data = filter_crops_of_interest(full_production_data, crop_list)
    
    # Clean and format the data
    cleaned_data = clean_and_format_dataframe(filtered_data)
    
    # If you want to save the data
    if not cleaned_data.empty:
        save_data_to_csv(cleaned_data, "fao_crop_production_comprehensive.csv")
        
        # Create a wide-format version for analysis
        wide_data = reshape_for_analysis(cleaned_data)
        save_data_to_csv(wide_data, "fao_crop_production_wide_format.csv")
        
        # Display sample of the data
        print("\nSample of the retrieved data:")
        print(cleaned_data.head())
        
        # Display some basic statistics
        print("\nData summary:")
        if 'Crop Name' in cleaned_data.columns:
            summary = cleaned_data.groupby('Crop Name')['Value'].describe()
        else:
            summary = cleaned_data.groupby('Item')['Value'].describe()
        print(summary)
    
    return cleaned_data

if __name__ == "__main__":
    # Run the main function
    crop_data = main()

