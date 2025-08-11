import pandas as pd
import os
from scipy.signal import savgol_filter


def calculate_changes_savgol(data, window_length=15, polyorder=3):
    """
    Calculate changes in yield for each year using a Savitzky-Golay filter

    Arguments:
        data (pd.DataFrame): DataFrame with countries as rows and years as columns
        window_length (int): The length of the filter window (must be positive odd integer)
        polyorder (int): The order of the polynomial used to fit the samples
                         (must be less than window_length)

    Returns:
        pd.DataFrame: DataFrame with percentage changes for each country and year
    """
    if polyorder >= window_length:
        raise ValueError("polyorder must be less than window_length")

    # Create empty DataFrame to store results
    pct_changes = pd.DataFrame(index=data.index, columns=data.columns)

    # For each country, calculate percentage changes
    for country in data.index:
        # Extract yield data for the country
        yields = data.loc[country]
        # Only process non-NaN values
        valid_mask = yields.notna()
        valid_yields = yields[valid_mask]

        # If the nan dropping removes all data entries, skip this country
        if len(valid_yields) <= 2:
            print(f"Skipping {country} due to lack of valid data")
            continue

        # If the length of the data is smaller than the window length, make the window smaller
        # This should be the first odd integer which is smaller then the window length
        if len(valid_yields) < window_length:
            window_length = len(valid_yields) if len(valid_yields) % 2 == 1 else len(valid_yields) - 1
            print(f"Adjusted window length for {country}: {window_length}")

        # Apply Savitzky-Golay filter to get the smoothed baseline
        smoothed_yields = savgol_filter(valid_yields, window_length, polyorder)

        # Calculate percentage changes
        pct_change = ((valid_yields - smoothed_yields) / smoothed_yields) * 100

        # Store in results DataFrame
        pct_changes.loc[country] = pct_change

    return pct_changes


def main():
    """
    Main function to run the analysis
    """
    for selection in ["countries", "regions", "groups_of_countries"]:
        # Set path to input file
        input_file = os.path.join("results", "calories_by_" + selection + ".csv")

        # Load data
        print(f"Loading data from {input_file}...")
        data = pd.read_csv(input_file, index_col=0)

        print("Calculating yield changes using Savitzky-Golay filter...")
        # Set the window length and polynomial order for the Savitzky-Golay filter
        # Using 15 years, because this is similar to the approach in Anderson et al. (2023)
        # This way we can smooth out the data and get a better estimate of the changes
        window_length = 15
        polyorder = 3  # Must be less than window_length
        # Calculate percentage changes
        pct_changes = calculate_changes_savgol(
            data, window_length=window_length, polyorder=polyorder
        )

        # Save results
        output_file = os.path.join("results", "yield_changes_by_" + selection + ".csv")
        pct_changes.to_csv(output_file)
        print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
    print("Analysis complete.")
