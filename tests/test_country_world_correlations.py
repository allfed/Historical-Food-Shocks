"""
Test suite for country_world_correlations.py

This test suite validates:
1. Data loading and preprocessing
2. Country-world correlation calculations
3. Correlation matrix generation with and without RMT
4. Visualization functions
5. Output format and file generation
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from plot_country_world_correlations import (
    load_data,
    calculate_country_world_correlations,
    calculate_correlation_matrix,
)


class TestCountryWorldCorrelations:
    """Test suite for country-world correlation calculation functions."""

    @pytest.fixture
    def sample_calories_countries(self):
        """Create sample calorie production data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            # Create calorie data with some variation
            data[year] = [
                1000 + np.random.normal(0, 100),  # Country_1
                2000 + np.random.normal(0, 150),  # Country_2
                1500 + np.random.normal(0, 120),  # Country_3
                3000 + np.random.normal(0, 200),  # Country_4
                2500 + np.random.normal(0, 180),  # Country_5
            ]
        return pd.DataFrame(
            data,
            index=pd.Index(
                ["Country_1", "Country_2", "Country_3", "Country_4", "Country_5"]
            ),
        )

    @pytest.fixture
    def sample_yield_changes_countries(self):
        """Create sample yield change data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            # Create yield changes with some correlation patterns
            base_change = np.random.normal(-1.0, 3.0)
            data[year] = [
                base_change
                + np.random.normal(0, 1.0),  # Country_1 - correlated with world
                base_change
                + np.random.normal(0, 1.0),  # Country_2 - correlated with world
                np.random.normal(-1.0, 3.0),  # Country_3 - independent
                base_change
                + np.random.normal(0, 1.0),  # Country_4 - correlated with world
                np.random.normal(-1.0, 3.0),  # Country_5 - independent
            ]
        return pd.DataFrame(
            data,
            index=pd.Index(
                ["Country_1", "Country_2", "Country_3", "Country_4", "Country_5"]
            ),
        )

    @pytest.fixture
    def sample_world_calories(self):
        """Create sample world calorie data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            data[year] = 10000 + np.random.normal(0, 500)  # World total
        return pd.Series(data, name="World")

    @pytest.fixture
    def sample_yield_changes_world(self):
        """Create sample world yield change data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            data[year] = np.random.normal(-1.0, 2.0)  # World yield changes
        return pd.Series(data, name="World")

    def test_load_data_success(
        self,
        sample_calories_countries,
        sample_yield_changes_countries,
        sample_world_calories,
        sample_yield_changes_world,
    ):
        """Test successful data loading."""
        with patch("plot_country_world_correlations.pd.read_csv") as mock_read:
            # Mock the different CSV files with 'World' as index
            mock_read.side_effect = [
                sample_calories_countries.reset_index(
                    drop=True
                ),  # calories_by_countries.csv
                pd.DataFrame(
                    [sample_world_calories], index=pd.Index(["World"])
                ),  # calories_by_regions.csv
                sample_yield_changes_countries.reset_index(
                    drop=True
                ),  # yield_changes_by_countries.csv
                pd.DataFrame(
                    [sample_yield_changes_world], index=pd.Index(["World"])
                ),  # yield_changes_by_regions.csv
            ]

            (
                calories_countries,
                world_calories,
                yield_changes_countries,
                yield_changes_regions,
                yield_changes_world,
            ) = load_data()

            # Check that data is loaded correctly
            assert len(calories_countries) == 5
            assert len(yield_changes_countries) == 5
            assert len(world_calories) == 63  # 1961-2023 inclusive
            assert len(yield_changes_world) == 63

    def test_calculate_country_world_correlations(
        self,
        sample_calories_countries,
        sample_yield_changes_countries,
        sample_world_calories,
    ):
        """Test country-world correlation calculations."""
        with patch(
            "plot_country_world_correlations.calculate_changes_savgol"
        ) as mock_savgol:
            # Mock the savgol function to return predictable yield changes
            mock_savgol.return_value = pd.DataFrame(
                np.random.normal(-1.0, 2.0, (1, 63)),
                columns=sample_yield_changes_countries.columns,
                index=pd.Index(["World_minus_Country_1"]),
            )

            with patch("plot_country_world_correlations.pd.Series.to_csv") as mock_csv:
                corr_series = calculate_country_world_correlations(
                    sample_calories_countries,
                    sample_yield_changes_countries,
                    sample_world_calories,
                )

                # Check that correlations were calculated
                assert len(corr_series) == 5  # All 5 countries
                assert isinstance(corr_series, pd.Series)
                assert set(corr_series.index) == set(sample_calories_countries.index)
                # Correlations should be between -1 and 1
                assert all(corr_series >= -1) and all(corr_series <= 1)
                # Check that CSV was saved
                assert mock_csv.called

    def test_correlation_calculation_edge_cases(self):
        """Test correlation calculations with edge cases."""
        # Test with empty data
        empty_calories = pd.DataFrame()
        empty_yield_changes = pd.DataFrame()
        empty_world_calories = pd.Series()

        corr_series = calculate_country_world_correlations(
            empty_calories, empty_yield_changes, empty_world_calories
        )
        assert corr_series.empty
