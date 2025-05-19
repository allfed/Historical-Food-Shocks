import os
import sys
import pytest
import pandas as pd
import tempfile
import zipfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

# Import the script we're testing - adjust name to match your actual script filename
# Instead of relying on directly importing the module which seems to be failing
# we'll import the functions separately in each test as needed

class TestFAODataExtraction:
    """Test class for FAO data extraction functionality."""
    
    @pytest.fixture
    def sample_crop_list(self):
        """Fixture providing a sample crop list for testing."""
        return {
            "Cereals": ["Maize", "Wheat"],
            "Fruits": ["Bananas", "Apples"]
        }
    
    @pytest.fixture
    def sample_fao_data(self):
        """Fixture providing sample FAO data for testing."""
        # Include all columns that might be accessed by the code
        return pd.DataFrame({
            'Area': ['USA', 'Brazil', 'India', 'China', 'France', 'Germany'],
            'Item': ['Maize', 'Wheat', 'Rice', 'Apples', 'Bananas', 'Potatoes'],
            'Element': ['Production', 'Production', 'Production', 'Production', 'Production', 'Production'],
            'Unit': ["t", "t", "t", "t", "t", "t"],
            'Y2000': [100, 200, 300, 400, 500, 600],
            'Y2001': [110, 220, 330, 440, 550, 660]
        })
    
    @pytest.fixture
    def temp_zip_file(self, sample_fao_data):
        """Fixture creating a temporary ZIP file with sample FAO data."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = Path(temp_dir) / "test_fao_data.zip"
        
        # Create a CSV file from the sample data
        csv_path = Path(temp_dir) / "test_data.csv"
        sample_fao_data.to_csv(csv_path, index=False)
        
        # Create a ZIP file containing the CSV
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(csv_path, arcname="test_data.csv")
        
        yield zip_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_extract_and_load_fao_data(self, temp_zip_file, monkeypatch):
        """Test extracting and loading data from a ZIP file."""
        # Import the function directly to avoid module import issues
        # We'll use monkeypatch to mock sys.path temporarily for this import
        monkeypatch.syspath_prepend(str(project_root / "src"))
        
        # Now try to import the specific function we want to test
        from get_FAO_data import extract_and_load_fao_data
        
        # Test with existing file
        df = extract_and_load_fao_data(temp_zip_file, "test_data.csv")
        assert df is not None
        assert len(df) == 6  # Should match our sample data
        
        # Test with non-existent file, should fall back to available CSV
        df = extract_and_load_fao_data(temp_zip_file, "nonexistent.csv")
        assert df is not None
        assert len(df) == 6  # Should match our sample data
        
        # Instead of expecting an exception, let's test that None is returned for a non-existent ZIP
        # This aligns with the error handling in your function
        non_existent_zip = Path(temp_zip_file.parent) / "nonexistent.zip"
        result = extract_and_load_fao_data(non_existent_zip, "test_data.csv")
        assert result is None
    
    def test_filter_crops_of_interest(self, sample_fao_data, sample_crop_list, monkeypatch):
        """Test filtering data for crops of interest."""
        # Import the function directly
        monkeypatch.syspath_prepend(str(project_root / "src"))
        from get_FAO_data import filter_crops_of_interest
        
        filtered_df = filter_crops_of_interest(sample_fao_data, sample_crop_list)
        
        # Check that only the selected crops are included
        assert len(filtered_df) == 4  # Maize, Wheat, Apples, Bananas
        assert set(filtered_df['Item'].unique()) == {'Maize', 'Wheat', 'Apples', 'Bananas'}
        
        # Check that crop categories are correctly assigned
        assert all(filtered_df.loc[filtered_df['Item'] == 'Maize', 'Crop Category'] == 'Cereals')
        assert all(filtered_df.loc[filtered_df['Item'] == 'Wheat', 'Crop Category'] == 'Cereals')
        assert all(filtered_df.loc[filtered_df['Item'] == 'Apples', 'Crop Category'] == 'Fruits')
        assert all(filtered_df.loc[filtered_df['Item'] == 'Bananas', 'Crop Category'] == 'Fruits')
        
        # Check that crop names are standardized
        assert all(filtered_df.loc[filtered_df['Item'] == 'Maize', 'Crop Name'] == 'Maize')
        assert all(filtered_df.loc[filtered_df['Item'] == 'Wheat', 'Crop Name'] == 'Wheat')

   
    def test_filter_crops_partial_match(self, sample_fao_data, monkeypatch):
        """Test filtering with partial name matching."""
        # Import the function directly
        monkeypatch.syspath_prepend(str(project_root / "src"))
        from get_FAO_data import filter_crops_of_interest

        # Test with partial names that should match
        crop_list = {"Cereals": ["Mai", "Wh"]}  # Should match Maize and Wheat
        filtered_df = filter_crops_of_interest(sample_fao_data, crop_list)
        assert len(filtered_df) == 2
        assert set(filtered_df['Item'].unique()) == {'Maize', 'Wheat'}


    def test_save_data_to_csv(self, sample_fao_data, tmp_path, monkeypatch):
        """Test saving data to CSV file."""
        # Import the function directly
        monkeypatch.syspath_prepend(str(project_root / "src"))
        from get_FAO_data import save_data_to_csv
        
        output_path = tmp_path / "test_output.csv"
        save_data_to_csv(sample_fao_data, output_path)
        
        # Check that file exists
        assert output_path.exists()
        
        # Check that data was saved correctly
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(sample_fao_data)
        assert list(saved_df.columns) == list(sample_fao_data.columns)
    
    def test_main_function(self, monkeypatch):
        """Test the main function with mocked dependencies."""
        # Import the module for patching
        monkeypatch.syspath_prepend(str(project_root / "src"))
        import get_FAO_data
        
        # Setup mock DataFrame
        sample_df = pd.DataFrame({
            'Area': ['USA', 'Brazil'],
            'Item': ['Maize', 'Wheat'],
            'Y2000': [100, 200]
        })
        
        # Setup mocks using monkeypatch
        monkeypatch.setattr(get_FAO_data, "extract_and_load_fao_data", lambda *args: sample_df)
        monkeypatch.setattr(get_FAO_data, "filter_crops_of_interest", lambda *args: sample_df)
        monkeypatch.setattr(get_FAO_data, "save_data_to_csv", lambda *args: None)
        
        # Call main function
        result = get_FAO_data.main()
        
        # Verify the result
        assert result is not None
        assert len(result) == 2  # Should match our mock DataFrame
    
    def test_main_function_with_extract_error(self, monkeypatch):
        """Test the main function when extraction fails."""
        # Import the module for patching
        monkeypatch.syspath_prepend(str(project_root / "src"))
        import get_FAO_data
        
        # Setup mocks using monkeypatch
        monkeypatch.setattr(get_FAO_data, "extract_and_load_fao_data", lambda *args: None)
        
        # Call main function
        result = get_FAO_data.main()
        
        # Verify result
        assert result is None
    
    def test_main_function_with_filter_error(self, monkeypatch):
        """Test the main function when filtering fails."""
        # Import the module for patching
        monkeypatch.syspath_prepend(str(project_root / "src"))
        import get_FAO_data
        
        # Setup mock DataFrame
        sample_df = pd.DataFrame({
            'Area': ['USA', 'Brazil'],
            'Item': ['Maize', 'Wheat'],
            'Y2000': [100, 200]
        })
        
        # Setup mocks using monkeypatch
        monkeypatch.setattr(get_FAO_data, "extract_and_load_fao_data", lambda *args: sample_df)
        monkeypatch.setattr(get_FAO_data, "filter_crops_of_interest", lambda *args: None)
        
        # Call main function
        result = get_FAO_data.main()
        
        # Verify result
        assert result is None

    def test_item_column_not_found(self, monkeypatch):
        """Test behavior when Item column is not found."""
        # Import the function directly
        monkeypatch.syspath_prepend(str(project_root / "src"))
        from get_FAO_data import filter_crops_of_interest
        
        # Create a dataframe without an Item column
        df = pd.DataFrame({
            'Area': ['USA', 'Brazil'],
            'Product': ['Maize', 'Wheat'],  # Not named 'Item'
            'Y2000': [100, 200]
        })
        
        # Test with a sample crop list
        crop_list = {"Cereals": ["Maize", "Wheat"]}
        
        # Should return None when Item column not found
        result = filter_crops_of_interest(df, crop_list)
        assert result is None

    def test_case_insensitive_matching(self, sample_fao_data, monkeypatch):
        """Test that crop matching is case-insensitive."""
        # Import the function directly
        monkeypatch.syspath_prepend(str(project_root / "src"))
        from get_FAO_data import filter_crops_of_interest
        
        # Mixed case crop list
        crop_list = {"Cereals": ["maIZe", "WHEat"]}
        filtered_df = filter_crops_of_interest(sample_fao_data, crop_list)
        
        # Should still match despite case differences
        assert len(filtered_df) == 2
        assert set(filtered_df['Item'].unique()) == {'Maize', 'Wheat'}