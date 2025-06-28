"""
Test suite for calculate_historical_frequency.py

This test suite validates:
1. Data loading and preprocessing
2. Historical frequency calculations for different geographic levels
3. Threshold-based analysis accuracy
4. Output format and file generation
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch

# Add src directory to path to import the main script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from calculate_historical_frequency import (
    load_data,
    analyze_historical_frequency,
    save_summary_findings,
    CONTINENTS,
    THRESHOLD,
)


class TestHistoricalFrequency:
    """Test suite for historical frequency calculation functions."""

    @pytest.fixture
    def sample_countries_data(self):
        """Create sample country yield change data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            if year.year == 1990:
                data[year] = [-15.0, -2.0, -1.0]  # Major shock for country 1
            else:
                data[year] = [-1.0, -2.0, -1.0]  # Normal years
        return pd.DataFrame(
            data, index=pd.Index(["Test_Country_1", "Test_Country_2", "Test_Country_3"])
        )

    @pytest.fixture
    def sample_regions_data(self):
        """Create sample regional yield change data for testing."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        # 1961-2023 inclusive: 63 years
        data = {}
        for year in years:
            if year.year == 1985:
                data[year] = [
                    -8.0,
                    -1.0,
                    -2.0,
                    -1.0,
                    -1.0,
                    -1.0,
                    -1.0,
                ]  # Continental shock
            elif year.year == 1995:
                data[year] = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -12.0]  # World shock
            else:
                data[year] = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]  # Normal years
        return pd.DataFrame(
            data,
            index=pd.Index(
                [
                    "Africa",
                    "Asia",
                    "Europe",
                    "Northern America",
                    "South America",
                    "Oceania",
                    "World",
                ]
            ),
        )

    def test_load_data_success(self, sample_countries_data, sample_regions_data):
        """Test successful data loading with proper datetime conversion."""
        with patch("calculate_historical_frequency.pd.read_csv") as mock_read:
            mock_read.side_effect = [
                sample_countries_data.reset_index(drop=True),
                sample_regions_data.reset_index(drop=True),
            ]
            df_countries, df_regions = load_data()
            assert isinstance(df_countries.columns, pd.DatetimeIndex)
            assert isinstance(df_regions.columns, pd.DatetimeIndex)
            min_year = pd.Timestamp(str(df_countries.columns.min())).year
            max_year = pd.Timestamp(str(df_countries.columns.max())).year
            assert min_year == 1961
            assert max_year == 2023
            assert len(df_countries.columns) == 63  # 1961-2023 inclusive

    def test_analyze_historical_frequency_global(self, sample_regions_data):
        """Test historical frequency analysis for global data (Series)."""
        world_series = sample_regions_data.loc["World"]
        results = analyze_historical_frequency(
            world_series, "Global", thresholds=[5.0, 10.0], global_analysis=True
        )
        threshold_5_results = results[5.0]
        assert threshold_5_results["years_with_events"] == 1
        assert threshold_5_results["total_events"] == 1
        assert threshold_5_results["historical_frequency"] == 63.0  # 63 years / 1 event
        assert threshold_5_results["event_frequency"] == pytest.approx(1 / 63, rel=1e-3)
        threshold_10_results = results[10.0]
        assert threshold_10_results["years_with_events"] == 1
        assert threshold_10_results["total_events"] == 1

    def test_analyze_historical_frequency_continental(self, sample_regions_data):
        """Test historical frequency analysis for continental data (DataFrame)."""
        continental_data = sample_regions_data.loc[CONTINENTS]
        results = analyze_historical_frequency(
            continental_data, "Any Continent", thresholds=[5.0]
        )
        threshold_results = results[5.0]
        assert threshold_results["years_with_events"] == 1
        assert threshold_results["total_events"] == 1
        assert threshold_results["historical_frequency"] == 63.0
        assert threshold_results["event_frequency"] == pytest.approx(1 / 63, rel=1e-3)

    def test_analyze_historical_frequency_country(self, sample_countries_data):
        """Test historical frequency analysis for country data (DataFrame)."""
        results = analyze_historical_frequency(
            sample_countries_data, "Any Country", thresholds=[5.0, 10.0]
        )
        threshold_5_results = results[5.0]
        assert threshold_5_results["years_with_events"] == 1
        assert threshold_5_results["total_events"] == 1
        threshold_10_results = results[10.0]
        assert threshold_10_results["years_with_events"] == 1
        assert threshold_10_results["total_events"] == 1

    def test_analyze_historical_frequency_no_events(self):
        """Test historical frequency analysis when no events occur."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        stable_data = pd.DataFrame(
            {year: [-1.0, -1.0, -1.0] for year in years},
            index=pd.Index(["Country_1", "Country_2", "Country_3"]),
        )
        results = analyze_historical_frequency(
            stable_data, "Stable Countries", thresholds=[5.0]
        )
        threshold_results = results[5.0]
        assert threshold_results["years_with_events"] == 0
        assert threshold_results["total_events"] == 0
        assert threshold_results["historical_frequency"] == float("inf")
        assert threshold_results["event_frequency"] == 0

    def test_save_summary_findings(self, tmp_path):
        """Test saving summary findings to CSV."""
        global_results = {5.0: {"years_with_events": 2, "total_events": 2}}
        continental_results = {5.0: {"years_with_events": 3, "total_events": 3}}
        country_results = {5.0: {"years_with_events": 5, "total_events": 5}}
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        with patch("calculate_historical_frequency.RESULTS_DIR", str(results_dir)):
            save_summary_findings(global_results, continental_results, country_results)

            # Check that file was created
            output_file = results_dir / "historical_frequency_results.csv"
            assert output_file.exists()

            # Check file contents
            df = pd.read_csv(output_file, index_col=0)
            # The function creates a transposed DataFrame, so the original columns become the index
            assert "Global" in df.index
            assert "Any Continent" in df.index
            assert "Any Country" in df.index
            # Check that the data columns exist
            assert "years_with_events" in df.columns
            assert "total_events" in df.columns

    def test_constants_defined(self):
        """Test that required constants are properly defined."""
        assert THRESHOLD == 5.0
        assert isinstance(CONTINENTS, list)
        assert len(CONTINENTS) == 6
        assert "Africa" in CONTINENTS
        assert "Asia" in CONTINENTS
        assert "Europe" in CONTINENTS
        assert "Northern America" in CONTINENTS
        assert "South America" in CONTINENTS
        assert "Oceania" in CONTINENTS

    def test_integration_with_real_data_structure(self):
        """Test that the functions work with the expected data structure."""
        years = pd.date_range(start="1961", end="2023-12-31", freq="YE")
        np.random.seed(42)
        realistic_data = pd.DataFrame(
            np.random.normal(-1.0, 3.0, (10, len(years))),
            index=pd.Index([f"Country_{i}" for i in range(1, 11)]),
            columns=years,
        )
        realistic_data.loc["Country_1", "1990-12-31"] = -12.0  # Major shock
        realistic_data.loc["Country_2", "1985-12-31"] = -8.0  # Moderate shock
        results = analyze_historical_frequency(
            realistic_data, "Realistic Data", thresholds=[5.0, 10.0]
        )
        threshold_5_results = results[5.0]
        assert threshold_5_results["years_with_events"] >= 2
        assert threshold_5_results["total_events"] >= 2
        threshold_10_results = results[10.0]
        assert threshold_10_results["years_with_events"] >= 1
        assert threshold_10_results["total_events"] >= 1
