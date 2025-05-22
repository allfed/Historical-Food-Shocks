#!/usr/bin/env python3
"""
Pytest tests for calorie calculation script.
This module provides tests to verify the accuracy of calorie calculations,
focusing on unit conversions and aggregation logic.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO


# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

# Import the module to test (assuming it's in the src directory)
from calculate_yearly_calories import (
    calculate_calories,
    aggregate_calories_by_country,
    CALORIE_VALUES,
    main,
)


class TestCalorieCalculations:
    """Test suite for calorie calculation functions."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe for testing."""
        data = """Area,Item,Y2020,Y2021
USA,Maize (corn),300,400
USA,Rice,100,120
China,Maize (corn),800,850
China,Potatoes,500,520
"""
        return pd.read_csv(pd.io.common.StringIO(data))

    @pytest.fixture
    def data_dir(self):
        """Return the data directory path."""
        return project_root / "data"

    @pytest.fixture
    def results_dir(self):
        """Return the results directory path."""
        return project_root / "results"

    def test_calorie_calculation_formula(self, sample_df):
        """Test the correctness of the calorie calculation formula and unit conversion."""
        result_df, _ = calculate_calories(sample_df)

        # Test for USA Maize in 2020: 300 tonnes
        expected_calories_usa_maize_2020 = 300 * 1_000_000 * 356 / 100
        actual_calories = result_df[
            (result_df["Area"] == "USA") & (result_df["Item"] == "Maize (corn)")
        ]["Y2020_calories"].values[0]
        assert actual_calories == pytest.approx(
            expected_calories_usa_maize_2020
        ), "Calorie calculation for USA Maize 2020 is incorrect"

        # Test for China Potatoes in 2021: 520 tonnes
        expected_calories_china_potatoes_2021 = 520 * 1_000_000 * 67 / 100
        actual_calories = result_df[
            (result_df["Area"] == "China") & (result_df["Item"] == "Potatoes")
        ]["Y2021_calories"].values[0]
        assert actual_calories == pytest.approx(
            expected_calories_china_potatoes_2021
        ), "Calorie calculation for China Potatoes 2021 is incorrect"

    def test_aggregation_by_country(self, sample_df):
        """Test that calories are correctly aggregated by country."""
        df_with_calories, calorie_cols = calculate_calories(sample_df)
        result_df = aggregate_calories_by_country(df_with_calories, calorie_cols)

        # Calculate expected values for USA in 2020
        # USA Maize: 300 * 1,000,000 * 356 / 100 = 1,068,000,000
        # USA Rice: 100 * 1,000,000 * 360 / 100 = 360,000,000
        # Total: 1,428,000,000
        expected_usa_2020 = (300 * 1_000_000 * 356 / 100) + (
            100 * 1_000_000 * 360 / 100
        )

        # Get actual value
        usa_row = result_df.loc["USA"]
        assert usa_row["2020"] == pytest.approx(
            expected_usa_2020
        ), "Aggregated calories for USA in 2020 are incorrect"

        # Check column renaming
        assert (
            "2020" in result_df.columns
        ), "Year column '2020' not found in aggregated data"
        assert (
            "Y2020_calories" not in result_df.columns
        ), "Original column name not properly replaced"
