"""
Test suite for calculate_food_shocks.py

This test suite validates:
1. Parameter validation and error handling
2. Integration with actual FAO calorie data
3. Shock detection accuracy with known patterns
4. Data consistency and output format validation
5. Realistic shock magnitude assessment
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from calculate_food_shocks import calculate_changes_savgol


class TestCalculateFoodShocks:
    """Test suite for food shock calculation functions."""

    @pytest.fixture
    def simple_test_data(self):
        """Create synthetic data with known shock patterns for testing."""
        years = [str(year) for year in range(1961, 2024)]  # 63 years like FAO data

        # Country 1: Stable baseline with one major shock
        country1_data = [2000] * len(years)
        country1_data[30] = 1400  # 30% drop in year 30 (around 1990)

        # Country 2: Gradual trend with periodic variation
        country2_data = []
        for i, year in enumerate(years):
            base = 1000 + 5 * i  # Gradual increase
            variation = 30 * np.sin(2 * np.pi * i / 8)  # 8-year cycle
            country2_data.append(base + variation)

        # Country 3: Multiple moderate shocks
        country3_data = [1500] * len(years)
        country3_data[15] = 1350  # 10% drop
        country3_data[25] = 1275  # 15% drop
        country3_data[45] = 1650  # 10% increase

        return pd.DataFrame(
            {
                year: [country1_data[i], country2_data[i], country3_data[i]]
                for i, year in enumerate(years)
            },
            index=["Major_Shock_Country", "Trend_Country", "Multiple_Shocks_Country"],
        )

    @pytest.fixture
    def actual_calorie_data(self):
        """Load actual calorie data if available for integration testing."""
        try:
            data_path = project_root / "results" / "calories_by_countries.csv"
            if data_path.exists():
                df = pd.read_csv(data_path, index_col=0)
                # Remove regions and groups for cleaner testing
                regions_to_remove = [
                    "Africa",
                    "Americas",
                    "Asia",
                    "Caribbean",
                    "Central America",
                    "Central Asia",
                    "Eastern Africa",
                    "Eastern Asia",
                    "Eastern Europe",
                    "Europe",
                    "Middle Africa",
                    "Northern Africa",
                    "Northern Europe",
                    "Oceania",
                    "Polynesia",
                    "South-eastern Asia",
                    "Southern Africa",
                    "Southern Asia",
                    "Southern Europe",
                    "Western Africa",
                    "Western Asia",
                    "Western Europe",
                    "World",
                    "South America",
                    "European Union (27)",
                    "Land Locked Developing Countries",
                    "Least Developed Countries",
                    "Low Income Food Deficit Countries",
                    "Net Food Importing Developing Countries",
                    "Australia and New Zealand",
                    "Small Island Developing States",
                ]
                return df[~df.index.isin(regions_to_remove)]
            else:
                return None
        except Exception:
            return None

    def test_major_shock_detection(self, simple_test_data):
        """Test that major shocks are correctly identified."""
        result = calculate_changes_savgol(
            simple_test_data, window_length=15, polyorder=3
        )

        # Test Major_Shock_Country: should detect the 30% drop in year 30
        major_shock_data = result.loc["Major_Shock_Country"]
        shock_year_index = 30
        shock_magnitude = major_shock_data.iloc[shock_year_index]

        # Should detect a significant negative shock (around -20% to -30%)
        assert (
            shock_magnitude < -15.0
        ), f"Should detect major negative shock, got {shock_magnitude:.2f}%"

        # Most other years should have smaller deviations
        other_years = major_shock_data.drop(major_shock_data.index[shock_year_index])
        assert (
            abs(other_years.mean()) < 3.0
        ), "Non-shock years should have small deviations"

        print(f"Detected major shock: {shock_magnitude:.1f}% (expected around -25%)")

    def test_gcff_threshold_detection(self, simple_test_data):
        """Test detection of shocks above GCFF 5% threshold."""
        result = calculate_changes_savgol(
            simple_test_data, window_length=15, polyorder=3
        )

        # Count shocks above 5% threshold (GCFF level)
        severe_negative_shocks = (result < -5.0).sum().sum()
        severe_positive_shocks = (result > 5.0).sum().sum()

        # Should detect at least the major shocks we built into the data
        assert (
            severe_negative_shocks >= 2
        ), f"Should detect multiple negative GCFF-level shocks, found {severe_negative_shocks}"

        # Count shocks above 10% threshold (major shocks)
        major_negative_shocks = (result < -10.0).sum().sum()
        major_positive_shocks = (result > 10.0).sum().sum()

        print(
            f"GCFF-level shocks (>5%): {severe_positive_shocks} positive, {severe_negative_shocks} negative"
        )
        print(
            f"Major shocks (>10%): {major_positive_shocks} positive, {major_negative_shocks} negative"
        )

        # Should have at least one major negative shock from our test data
        assert (
            major_negative_shocks >= 1
        ), "Should detect at least one major negative shock"

    def test_output_format_consistency(self, simple_test_data):
        """Test that output format matches input format and contains valid data."""
        result = calculate_changes_savgol(
            simple_test_data, window_length=15, polyorder=3
        )

        # Should have same shape
        assert (
            result.shape == simple_test_data.shape
        ), "Output shape should match input shape"

        # Should have same index and columns
        pd.testing.assert_index_equal(result.index, simple_test_data.index)
        pd.testing.assert_index_equal(result.columns, simple_test_data.columns)

        # All values should be numeric (no NaN in middle of data)
        assert not result.isna().any().any(), "Output should not contain NaN values"

        # Values should be reasonable percentage changes
        assert result.min().min() > -100, "No shock should be more than 100% negative"
        assert result.max().max() < 1000, "No shock should be more than 1000% positive"

    def test_moderate_shock_detection(self, simple_test_data):
        """Test detection of moderate shocks in Multiple_Shocks_Country."""
        result = calculate_changes_savgol(
            simple_test_data, window_length=15, polyorder=3
        )

        # Check Multiple_Shocks_Country for the moderate shocks we inserted
        multi_shock_data = result.loc["Multiple_Shocks_Country"]

        # Should detect some negative shocks around years 15 and 25
        # (exact positions may shift due to smoothing)
        shocks_around_year_15 = multi_shock_data.iloc[12:18]  # Window around year 15
        shocks_around_year_25 = multi_shock_data.iloc[22:28]  # Window around year 25

        min_shock_15 = shocks_around_year_15.min()
        min_shock_25 = shocks_around_year_25.min()

        assert (
            min_shock_15 < -3.0
        ), f"Should detect moderate shock around year 15, got {min_shock_15:.1f}%"
        assert (
            min_shock_25 < -5.0
        ), f"Should detect moderate shock around year 25, got {min_shock_25:.1f}%"

        print(f"Moderate shocks detected: {min_shock_15:.1f}% and {min_shock_25:.1f}%")

    def test_edge_cases(self):
        """Test behavior with edge cases and boundary conditions."""
        # Test with minimum viable data size
        min_data = pd.DataFrame(
            {"1990": [100, 200], "1991": [110, 190], "1992": [120, 180]},
            index=["Country1", "Country2"],
        )

        # Should work with window_length=3 (minimum odd number for 3 data points)
        result = calculate_changes_savgol(min_data, window_length=3, polyorder=1)
        assert result.shape == min_data.shape

        # Test with constant values (should produce near-zero changes)
        constant_data = pd.DataFrame(
            {
                "1990": [100] * 2,
                "1991": [100] * 2,
                "1992": [100] * 2,
                "1993": [100] * 2,
                "1994": [100] * 2,
            },
            index=["Constant1", "Constant2"],
        )

        result_constant = calculate_changes_savgol(
            constant_data, window_length=3, polyorder=1
        )
        # All percentage changes should be zero (or very close to zero)
        assert (
            abs(result_constant.values.max()) < 1e-10
        ), "Constant data should yield zero changes"

    def test_realistic_country_patterns(self, actual_calorie_data):
        """Test that results show realistic patterns for known countries."""
        if actual_calorie_data is None:
            pytest.skip("Actual calorie data not available")

        # Focus on major food producers that should be in the data
        major_producers = ["United States of America", "China", "India", "Brazil"]
        available_producers = [
            country
            for country in major_producers
            if country in actual_calorie_data.index
        ]

        if len(available_producers) < 2:
            pytest.skip("Not enough major producers in test data")

        # Test with a subset for performance
        test_countries = actual_calorie_data.loc[available_producers[:3]]
        result = calculate_changes_savgol(test_countries, window_length=15, polyorder=3)

        for country in test_countries.index:
            country_shocks = result.loc[country]

            # Major producers should show some variability (not completely smooth)
            shock_std = country_shocks.std()
            assert (
                shock_std > 0.5
            ), f"{country} shows unusually low variability: {shock_std:.2f}%"
            assert (
                shock_std < 50.0
            ), f"{country} shows unusually high variability: {shock_std:.2f}%"

            # Should have some years with notable shocks
            notable_shocks = ((country_shocks > 5.0) | (country_shocks < -5.0)).sum()
            total_years = len(country_shocks)
            shock_rate = notable_shocks / total_years

            print(
                f"{country}: {notable_shocks}/{total_years} years with >5% shocks ({shock_rate:.1%})"
            )

            # Expect some but not too many notable shocks
            assert (
                shock_rate > 0.02
            ), f"{country} has too few notable shocks: {shock_rate:.1%}"
            assert (
                shock_rate < 0.50
            ), f"{country} has too many notable shocks: {shock_rate:.1%}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
