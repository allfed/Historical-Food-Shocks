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
    create_heatmap,
    create_map_visualization,
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
        with patch("country_world_correlations.pd.read_csv") as mock_read:
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
            "country_world_correlations.calculate_changes_savgol"
        ) as mock_savgol:
            # Mock the savgol function to return predictable yield changes
            mock_savgol.return_value = pd.DataFrame(
                np.random.normal(-1.0, 2.0, (1, 63)),
                columns=sample_yield_changes_countries.columns,
                index=pd.Index(["World_minus_Country_1"]),
            )

            with patch("country_world_correlations.pd.Series.to_csv") as mock_csv:
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

    def test_calculate_correlation_matrix_without_rmt(
        self, sample_yield_changes_countries, sample_yield_changes_world
    ):
        """Test correlation matrix calculation without RMT filtering."""
        corr_matrix = calculate_correlation_matrix(
            sample_yield_changes_countries.copy(), sample_yield_changes_world, RMT=False
        )

        # Check matrix properties
        assert corr_matrix.shape == (6, 6)  # 5 countries + World
        assert "World" in corr_matrix.index
        assert "World" in corr_matrix.columns
        # Diagonal should be 1.0
        assert np.allclose(np.diag(corr_matrix.values), 1.0, atol=1e-10)
        # Matrix should be symmetric
        assert corr_matrix.equals(corr_matrix.T)

    def test_calculate_correlation_matrix_with_rmt(
        self, sample_yield_changes_countries, sample_yield_changes_world
    ):
        """Test correlation matrix calculation with RMT filtering."""
        with patch("country_world_correlations.clipped") as mock_clipped:
            # Mock the RMT clipping function
            mock_clipped.return_value = np.random.normal(0, 0.1, (6, 6))

            corr_matrix = calculate_correlation_matrix(
                sample_yield_changes_countries.copy(),
                sample_yield_changes_world,
                RMT=True,
            )

            # Check that RMT was applied
            assert mock_clipped.called
            assert corr_matrix.shape == (6, 6)
            assert "World" in corr_matrix.index
            assert "World" in corr_matrix.columns

    def test_create_heatmap(
        self, sample_yield_changes_countries, sample_yield_changes_world
    ):
        """Test heatmap creation."""
        # Create a sample correlation matrix
        corr_matrix = calculate_correlation_matrix(
            sample_yield_changes_countries.copy(), sample_yield_changes_world, RMT=False
        )

        with patch("country_world_correlations.plt.savefig") as mock_save:
            with patch("country_world_correlations.plt.show") as mock_show:
                create_heatmap(corr_matrix, sortby="World")

                # Check that plot was saved and shown
                assert mock_save.called
                assert mock_show.called

    def test_create_map_visualization(self):
        """Test map visualization creation."""
        # Create sample correlation series
        corr_series = pd.Series(
            {
                "United States": 0.8,
                "China": 0.6,
                "India": 0.4,
                "Brazil": 0.2,
                "Russia": -0.1,
            }
        )

        with patch("country_world_correlations.convert_country_names") as mock_convert:
            mock_convert.return_value = corr_series

            with patch("country_world_correlations.gpd.read_file") as mock_read_file:
                # Mock the shapefile reading
                mock_map = MagicMock()
                mock_map.__len__ = lambda x: 5
                mock_read_file.return_value = mock_map

                with patch("country_world_correlations.coco.convert") as mock_coco:
                    mock_coco.return_value = [
                        "United States",
                        "China",
                        "India",
                        "Brazil",
                        "Russia",
                    ]

                    with patch("country_world_correlations.plt.savefig") as mock_save:
                        with patch("country_world_correlations.plt.show") as mock_show:
                            create_map_visualization(corr_series)

                            # Check that map was created and saved
                            assert mock_save.called
                            assert mock_show.called

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

    def test_correlation_matrix_edge_cases(self):
        """Test correlation matrix with edge cases."""
        # Test with single country
        single_country_data = pd.DataFrame(
            {"1961": [1.0], "1962": [2.0]}, index=["Single_Country"]
        )
        world_data = pd.Series({"1961": 1.5, "1962": 2.5}, name="World")

        corr_matrix = calculate_correlation_matrix(
            single_country_data, world_data, RMT=False
        )

        assert corr_matrix.shape == (2, 2)  # Single country + World
        assert "Single_Country" in corr_matrix.index
        assert "World" in corr_matrix.index

    def test_integration_with_real_data_structure(self):
        """Test that functions work with realistic data structures."""
        # Create realistic test data
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        np.random.seed(42)

        # Create realistic calorie data
        realistic_calories = pd.DataFrame(
            np.random.normal(1000, 200, (10, len(years))),
            index=pd.Index([f"Country_{i}" for i in range(1, 11)]),
            columns=years,
        )

        # Create realistic yield changes with some correlation
        base_changes = np.random.normal(-1.0, 2.0, len(years))
        realistic_yield_changes = pd.DataFrame(
            np.array(
                [base_changes + np.random.normal(0, 1.0, len(years)) for _ in range(10)]
            ),
            index=realistic_calories.index,
            columns=years,
        )

        world_calories = realistic_calories.sum()
        world_yield_changes = pd.Series(base_changes, index=years, name="World")

        # Test correlation calculation
        with patch(
            "country_world_correlations.calculate_changes_savgol"
        ) as mock_savgol:
            mock_savgol.return_value = pd.DataFrame(
                np.random.normal(-1.0, 2.0, (1, len(years))),
                columns=years,
                index=pd.Index(["World_minus_Country_1"]),
            )

            with patch("country_world_correlations.pd.Series.to_csv"):
                corr_series = calculate_country_world_correlations(
                    realistic_calories, realistic_yield_changes, world_calories
                )

                assert len(corr_series) == 10
                assert all(corr_series >= -1) and all(corr_series <= 1)
                assert set(corr_series.index) == set(realistic_calories.index)

        # Test correlation matrix
        corr_matrix = calculate_correlation_matrix(
            realistic_yield_changes.copy(), world_yield_changes, RMT=False
        )

        assert corr_matrix.shape == (11, 11)  # 10 countries + World
        assert "World" in corr_matrix.index
        assert np.allclose(np.diag(corr_matrix.values), 1.0, atol=1e-10)
