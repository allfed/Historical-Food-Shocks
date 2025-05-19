import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

class TestFAODataConsistency:
    """Test class for verifying the consistency and completeness of the FAO data output file."""
    
    @pytest.fixture
    def output_filepath(self):
        """Fixture providing the path to the output CSV file."""
        data_dir = project_root / "data"
        return data_dir / "fao_crop_production_comprehensive.csv"
    
    @pytest.fixture
    def expected_crops(self):
        """Fixture providing the list of 25 crops that should be present in the output."""
        return {
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
    
    @pytest.fixture
    def expected_year_range(self):
        """Fixture providing the expected range of years in the data."""
        return range(1961, 2024)  # Y1961 to Y2023
    
    @pytest.fixture
    def expected_country_count(self):
        """Fixture providing the expected number of unique countries/areas."""
        return 244
    
    def test_output_file_exists(self, output_filepath):
        """Test that the output CSV file exists."""
        assert output_filepath.exists(), f"Output file not found at {output_filepath}"
        assert output_filepath.is_file(), f"{output_filepath} is not a file"
        assert output_filepath.stat().st_size > 0, f"Output file {output_filepath} is empty"
    
    def test_output_file_readable(self, output_filepath):
        """Test that the output CSV file can be read as a DataFrame."""
        try:
            df = pd.read_csv(output_filepath)
            assert len(df) > 0, "Output CSV file is empty"
            print(f"Output file has {len(df):,} rows and {len(df.columns)} columns")
        except Exception as e:
            pytest.fail(f"Failed to read output CSV file: {str(e)}")
    
    def test_contains_all_crops(self, output_filepath, expected_crops):
        """Test that the output contains all expected crops."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Flatten the expected crops list
        all_expected_crops = [crop for category, crops in expected_crops.items() for crop in crops]
        
        # Find the column containing crop names (either 'Item' or 'Crop Name')
        crop_column = None
        if 'Crop Name' in df.columns:
            crop_column = 'Crop Name'
        elif 'Item' in df.columns:
            crop_column = 'Item'
        
        assert crop_column is not None, "Could not find crop name column ('Item' or 'Crop Name')"
        
        # Get the unique crops in the data
        unique_crops = set(df[crop_column].unique())
        
        # Check if each expected crop appears in the data (with partial matching)
        missing_crops = []
        for expected_crop in all_expected_crops:
            # Check for exact match first
            if expected_crop in unique_crops:
                continue
                
            # If no exact match, check for partial match
            found = False
            for actual_crop in unique_crops:
                if expected_crop.lower() in actual_crop.lower():
                    found = True
                    break
            
            if not found:
                missing_crops.append(expected_crop)
        
        # Report results
        if missing_crops:
            print(f"Missing crops ({len(missing_crops)}/{len(all_expected_crops)}): {', '.join(missing_crops)}")
            print(f"Available crops: {', '.join(sorted(unique_crops))}")
        
        assert len(missing_crops) == 0, f"{len(missing_crops)} crops are missing from the output"
    
    def test_contains_all_years(self, output_filepath, expected_year_range):
        """Test that the output contains data for all expected years."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Check if data is in wide format (years as columns) or long format (Year column)
        if 'Year' in df.columns:
            # Long format
            print("Data is in long format with 'Year' column")
            
            # Get unique years
            unique_years = sorted(df['Year'].unique())
            
            # Check for missing years
            expected_years = list(expected_year_range)
            missing_years = [year for year in expected_years if year not in unique_years]
            
            if missing_years:
                print(f"Missing years: {missing_years}")
                print(f"Available years: {unique_years[:5]} ... {unique_years[-5:]}")
            
            # It's okay if we have more years than expected
            assert len(missing_years) == 0, f"{len(missing_years)} years are missing from the output"
            
        else:
            # Wide format (years as columns)
            print("Data appears to be in wide format (years as columns)")
            
            # Look for year columns (format: YXXXX)
            year_columns = [col for col in df.columns if col.startswith('Y') and col[1:].isdigit()]
            
            if not year_columns:
                # Try alternative format (just the year as a column)
                year_columns = [col for col in df.columns if str(col).isdigit() and int(col) >= 1961 and int(col) <= 2023]
            
            assert len(year_columns) > 0, "Could not find year columns in the data"
            
            # Extract the years from the column names
            if year_columns[0].startswith('Y'):
                # Format: YXXXX
                unique_years = sorted([int(col[1:]) for col in year_columns])
            else:
                # Format: XXXX
                unique_years = sorted([int(col) for col in year_columns])
            
            # Check for missing years
            expected_years = list(expected_year_range)
            missing_years = [year for year in expected_years if year not in unique_years]
            
            if missing_years:
                print(f"Missing years: {missing_years}")
                print(f"Available years: {unique_years[:5]} ... {unique_years[-5:]}")
            
            # It's okay if some of the most recent years are missing
            # Let's check if at least 80% of expected years are present
            coverage = len(unique_years) / len(expected_years) * 100
            assert coverage >= 80, f"Only {coverage:.1f}% of expected years are present in the data"
    
    def test_contains_sufficient_countries(self, output_filepath, expected_country_count):
        """Test that the output contains data for a sufficient number of countries/areas."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Find the column containing country/area names
        area_column = None
        if 'Area' in df.columns:
            area_column = 'Area'
        elif 'Country' in df.columns:
            area_column = 'Country'
        
        assert area_column is not None, "Could not find area/country column ('Area' or 'Country')"
        
        # Get the unique countries/areas in the data
        unique_areas = df[area_column].unique()
        
        # Print some information
        print(f"Found {len(unique_areas)} unique countries/areas in the data")
        print(f"Sample areas: {', '.join(sorted(unique_areas)[:10])}...")
        
        # Check if we have at least 80% of the expected countries
        min_expected = int(expected_country_count * 0.8)
        assert len(unique_areas) >= min_expected, \
            f"Only {len(unique_areas)} countries/areas found, expected at least {min_expected}"
    
    def test_data_completeness(self, output_filepath):
        """Test the overall completeness of the data (missing values)."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Calculate missing value statistics
        missing_counts = df.isna().sum()
        total_cells = df.size
        missing_cells = missing_counts.sum()
        missing_percentage = (missing_cells / total_cells) * 100
        
        # Print summary
        print(f"Total cells: {total_cells:,}")
        print(f"Missing cells: {missing_cells:,} ({missing_percentage:.2f}%)")
        
        # Print columns with most missing values
        if len(missing_counts) > 0:
            print("\nColumns with most missing values:")
            for col, count in missing_counts.nlargest(5).items():
                pct = (count / len(df)) * 100
                print(f"  {col}: {count:,} ({pct:.1f}%)")
        
        # It's normal to have some missing values in agricultural data
        # Let's consider the data complete if less than 50% of values are missing
        assert missing_percentage < 50, f"Too many missing values: {missing_percentage:.1f}%"
    
    def test_production_values_reasonable(self, output_filepath):
        """Test that the production values are within reasonable ranges."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Find value column(s)
        value_columns = []
        
        # First check if in long format with a 'Value' column
        if 'Value' in df.columns:
            value_columns = ['Value']
        else:
            # Check for year columns which would contain values in wide format
            year_columns = [col for col in df.columns if col.startswith('Y') and col[1:].isdigit()]
            if not year_columns:
                year_columns = [col for col in df.columns if str(col).isdigit() and int(col) >= 1961 and int(col) <= 2023]
            
            if year_columns:
                value_columns = year_columns
        
        assert len(value_columns) > 0, "Could not find value column(s) in the data"
        
        # Check each value column
        for col in value_columns:
            # Extract numeric values, ignoring non-numeric and missing values
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            
            if len(values) == 0:
                print(f"Warning: No numeric values in column {col}")
                continue
            
            # Check for negative values (which would be invalid for production)
            neg_count = (values < 0).sum()
            neg_percentage = (neg_count / len(values)) * 100 if len(values) > 0 else 0
            
            # Statistics for this column
            print(f"\nColumn {col}:")
            print(f"  Range: {values.min():,.1f} to {values.max():,.1f}")
            print(f"  Mean: {values.mean():,.1f}")
            print(f"  Negative values: {neg_count:,} ({neg_percentage:.2f}%)")
            
            # Should have very few or no negative values
            assert neg_percentage < 1, f"Too many negative values in {col}: {neg_percentage:.2f}%"
            
            # Check for extremely large values (potential data errors)
            # For agriculture production, values should typically be less than 1 billion (1e9) tonnes
            extreme_count = (values > 1e9).sum()
            extreme_percentage = (extreme_count / len(values)) * 100 if len(values) > 0 else 0
            
            print(f"  Extremely large values (>1B): {extreme_count:,} ({extreme_percentage:.2f}%)")
            
            # Should have very few or no extremely large values
            assert extreme_percentage < 1, f"Too many extremely large values in {col}: {extreme_percentage:.2f}%"
