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
                "Maize (corn)", "Rice", "Wheat", "Barley", "Sorghum"
            ],
            "Sugar crops": [
                "Sugar cane", "Sugar beet"
            ],
            "Roots and tubers": [
                "Potatoes", "Cassava, fresh", "Sweet potatoes", "Yams", "Taro"
            ],
            "Fruits": [
                "Bananas", "Apples", "Oranges", "Grapes", "Watermelons"
            ],
            "Vegetables": [
                "Tomatoes", "Onions and shallots, green", "Cucumbers and gherkins", "Cabbages", "Eggplants (aubergines)"
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
        
        crop_column = 'Item'

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

    def test_contains_only_expected_crops(self, output_filepath, expected_crops):
        """Test that the output contains only expected crops."""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Flatten the expected crops list
        all_expected_crops = [crop for category, crops in expected_crops.items() for crop in crops]
        
        crop_column = 'Item'
        
        # Get the unique crops in the data
        unique_crops = set(df[crop_column].unique())
        
        # Check if any unexpected crops are present
        unexpected_crops = [crop for crop in unique_crops if crop not in all_expected_crops]
        
        if unexpected_crops:
            print(f"Unexpected crops found: {', '.join(unexpected_crops)}")
            print(f"Expected crops: {', '.join(all_expected_crops)}")
        
        assert len(unexpected_crops) == 0, f"Found unexpected crops in the output: {', '.join(unexpected_crops)}"
    
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
            
            # Strict check: No missing years allowed
            assert len(missing_years) == 0, f"{len(missing_years)} years are missing from the output: {missing_years}"
            
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
            
            # Strict check: No missing years allowed
            assert len(missing_years) == 0, f"{len(missing_years)} years are missing from the output: {missing_years}"
    
    def test_contains_all_countries(self, output_filepath, expected_country_count):
        """Test that the output contains data for all expected countries/areas."""
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
        
        # Check area code column if it exists
        if 'Area Code' in df.columns:
            unique_area_codes = df['Area Code'].unique()
            print(f"Found {len(unique_area_codes)} unique area codes")
        
        # Print some information
        print(f"Found {len(unique_areas)} unique countries/areas in the data")
        print(f"Sample areas: {', '.join(sorted(unique_areas)[:10])}...")
        
        # Strict check: Must have all expected countries
        assert len(unique_areas) >= expected_country_count, \
            f"Only {len(unique_areas)} countries/areas found, expected {expected_country_count}"
        
        # If we have Area Code, check if we have all 244 unique codes
        if 'Area Code' in df.columns:
            assert len(unique_area_codes) >= expected_country_count, \
                f"Only {len(unique_area_codes)} unique area codes found, expected {expected_country_count}"
    
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
        
        # Some missing values are expected in agricultural data
        # Let's consider the data complete if less than 30% of values are missing (stricter threshold)
        assert missing_percentage < 30, f"Too many missing values: {missing_percentage:.1f}%"
    
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
            
            # Statistics for this column
            print(f"\nColumn {col}:")
            print(f"  Range: {values.min():,.1f} to {values.max():,.1f}")
            print(f"  Mean: {values.mean():,.1f}")
            print(f"  Negative values: {neg_count:,}")
            
            # Strict check: Zero tolerance for negative values
            assert neg_count == 0, f"Found {neg_count:,} negative values in {col}"
            
            # Check for extremely large values (potential data errors)
            # For agriculture production, values should typically be less than 1 billion (1e9) tonnes
            extreme_threshold = 2.5e9  # 2.5 billion (this should be the absolute max based on FAO data)
            extreme_count = (values > extreme_threshold).sum()
            
            if extreme_count > 0:
                print(f"  Values > {extreme_threshold:,.0f}: {extreme_count:,}")
                extreme_values = values[values > extreme_threshold]
                print(f"  Examples: {', '.join([f'{v:,.0f}' for v in extreme_values.head(3)])}")
            
            # Should have no extremely large values that might indicate data errors
            assert extreme_count == 0, f"Found {extreme_count:,} extremely large values (>{extreme_threshold:,.0f}) in {col}"
    
    def test_element_is_production(self, output_filepath):
        """Test that the data is for production (not area harvested, yield, etc.)"""
        # Load the data
        df = pd.read_csv(output_filepath)
        
        # Check if Element column exists
        if 'Element' not in df.columns:
            pytest.skip("Element column not found in the data")
        
        # Check that all rows are for Production
        non_production = df[~df['Element'].str.contains('Production', case=False)]
        
        if len(non_production) > 0:
            print(f"Found {len(non_production)} rows with Element not 'Production':")
            print(non_production['Element'].value_counts())
        
        assert len(non_production) == 0, \
            f"Found {len(non_production)} rows where Element is not Production"
