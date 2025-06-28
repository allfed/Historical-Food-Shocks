"""
Calculate historical frequency of yield shocks at different geographic levels.

This script analyzes the frequency and patterns of food production shocks at global,
continental, and country levels using yield change data. It calculates historical
frequency of shocks.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# Set up ALLFED plotting style
plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)

# Define constants
RESULTS_DIR = "results"
THRESHOLD = 5.0  # Default shock threshold in percentage
CONTINENTS = [
    "Africa",
    "Asia",
    "Europe",
    "Northern America",
    "South America",
    "Oceania",
]


def load_data():
    """
    Load yield change data for countries and regions.

    Returns:
        tuple: (DataFrame for countries, DataFrame for regions)
    """
    print("Loading data...")

    # Import yield shocks data at different levels
    df_countries = pd.read_csv("results/yield_changes_by_countries.csv", index_col=0)
    df_regions = pd.read_csv("results/yield_changes_by_regions.csv", index_col=0)

    # Convert years to datetime for easier handling
    df_countries.columns = pd.to_datetime(df_countries.columns, format="%Y")
    df_regions.columns = pd.to_datetime(df_regions.columns, format="%Y")

    min_year = df_countries.columns.min().year
    max_year = df_countries.columns.max().year
    print(f"Data spans: {min_year} to {max_year}")
    print(f"Total years: {len(df_countries.columns)}")

    return df_countries, df_regions


def analyze_historical_frequency(data, name, thresholds=None, global_analysis=False):
    """
    Analyze historical frequency of yield shocks for multiple entities.

    Args:
        data (pandas.DataFrame or pandas.Series): Data to analyze
        name (str): Name of the analysis level (e.g., "Global", "Any Country")
        thresholds (list): List of threshold percentages to analyze
        global_analysis (bool): Whether data is global (as opposed to continent or country level)

    Returns:
        dict: Dictionary with results for each threshold
    """
    if thresholds is None:
        thresholds = [THRESHOLD]

    print(f"\n=== Historical Frequency Analysis for {name} ===")

    results = {}

    for threshold in thresholds:
        if global_analysis:
            # Series analysis: count events for single entity over time
            events_below = (data < -threshold).sum()
            years_with_events = (data < -threshold).sum()
            total_events = events_below
            total_years = len(data)
        else:
            # DataFrame analysis: count events across all entities for each year
            events_below = (data < -threshold).sum(axis=0)  # Count per year
            years_with_events = (
                events_below > 0
            ).sum()  # Years with at least one event
            total_events = events_below.sum()  # Total number of events
            total_years = len(data.columns)

        # Calculate historical frequency
        if years_with_events > 0:
            historical_frequency = total_years / years_with_events
            event_frequency = years_with_events / total_years
        else:
            historical_frequency = float("inf")
            event_frequency = 0

        avg_events_per_year = total_events / years_with_events

        results[threshold] = {
            "years_with_events": years_with_events,
            "total_events": total_events,
            "historical_frequency": historical_frequency,
            "event_frequency": event_frequency,
            "avg_events_per_year": avg_events_per_year,
        }

        print(f"Threshold -{threshold}% (yield shock):")
        print(
            f"  Years with events: {years_with_events}/{total_years} ({event_frequency:.1%})"
        )
        print(f"  Total shocks: {total_events}")
        print(f"  Historical time between shocks: {historical_frequency:.1f} years")
        print(f"  Avg shocks per year: {avg_events_per_year:.1f}")

    return results


def print_summary_findings(
    global_results, continental_results, country_results, df_countries
):
    """
    Print summary of key findings from the analysis.

    Args:
        global_results (dict): Results from global analysis
        continental_results (dict): Results from continental analysis
        country_results (dict): Results from country analysis
        df_countries (pandas.DataFrame): Country yield change data
    """
    print("\nEmpirical analysis complete!")
    print("Key findings:")
    print(
        f"- Global {THRESHOLD}%+ shocks: {global_results[THRESHOLD]['years_with_events']} "
        f"events in {len(df_countries.columns)} years"
    )
    print(
        f"- Any continent {THRESHOLD}%+ shocks: {continental_results[THRESHOLD]['years_with_events']} "
        f"years with events"
    )
    print(
        f"- Any country {THRESHOLD}%+ shocks: {country_results[THRESHOLD]['years_with_events']} "
        f"years with events"
    )


def save_summary_findings(global_results, continental_results, country_results):
    """
    Save summary of key findings from the analysis.

    Args:
        global_results (dict): Results from global analysis
        continental_results (dict): Results from continental analysis
        country_results (dict): Results from country analysis
        df_countries (pandas.DataFrame): Country yield change data

    Returns:
    """
    # save all as one dataframe
    results = pd.DataFrame(global_results)
    # concatenate continental and country results and add column for level
    results = pd.concat([results, pd.DataFrame(continental_results)], axis=1)
    results = pd.concat([results, pd.DataFrame(country_results)], axis=1)
    results.columns = ["Global", "Any Continent", "Any Country"]
    # save to csv
    results.T.to_csv(os.path.join(RESULTS_DIR, "historical_frequency_results.csv"))


def main():

    print("=" * 80)
    print(f"HISTORICAL FREQUENCY ANALYSIS ({THRESHOLD}% THRESHOLD)")
    print("=" * 80)

    # Load data
    df_countries, df_regions = load_data()

    # Analyze different levels
    print("\n" + "=" * 80)
    print(f"HISTORICAL FREQUENCY ANALYSIS ({THRESHOLD}% THRESHOLD)")
    print("=" * 80)

    # 1. Global level
    world_series = df_regions.loc["World"]
    global_results = analyze_historical_frequency(
        world_series, "Global", global_analysis=True
    )

    # 2. Continental level - use only major continents
    continental_data = df_regions.loc[df_regions.index.intersection(CONTINENTS)]
    continental_results = analyze_historical_frequency(
        continental_data, "Any Continent"
    )

    # 3. Country level - pooled (any country experiencing a shock)
    country_results = analyze_historical_frequency(df_countries, "Any Country")

    # Save summary findings
    save_summary_findings(global_results, continental_results, country_results)


if __name__ == "__main__":
    main()
