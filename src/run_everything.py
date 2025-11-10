"""
This script runs all the main components of the Historical Food Shocks project in sequence.

The sequence is as follows:
1) Get FAO data for selected crops (in src/get_FAO_data.py)
2) Calculate the calories per country and year (in src/calculate_yearly_calories.py)
3) Calculate food shocks based on the calories data (in src/calculate_food_shocks.py)
4) Calculate the largest shocks per country (in src/calculate_largest_shocks.py)
5) Plot the results. This includes multiple plots in different scripts:
   - src/plot_maps.py
   - src/plot_country_world_correlations.py
   - src/plot_countries_by_countries_per_decade.py
   - src/plot_compare_shock_reasons.py
"""
import os
from pathlib import Path
import subprocess
import sys

def main():
    """Run all main components of the project in sequence."""
    scripts = [
        "get_FAO_data.py",
        "calculate_yearly_calories.py",
        "calculate_food_shocks.py",
        "calculate_largest_shock.py",
        "plot_maps.py",
        "plot_country_world_correlations.py",
        "plot_countries_by_countries_per_decade.py",
        "plot_compare_shock_reasons.py",
    ]

    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    src_dir = script_dir

    for script in scripts:
        script_path = src_dir / script
        print(f"Running {script}...")
        result = subprocess.run([sys.executable, str(script_path)])
        if result.returncode != 0:
            print(f"Error running {script}. Exiting.")
            sys.exit(result.returncode)
        print(f"Finished {script}.\n")

if __name__ == "__main__":
    main()
