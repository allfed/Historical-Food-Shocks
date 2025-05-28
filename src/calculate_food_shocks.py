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

        # Set the filter window length to 11 if the country is Sudan or South Sudan
        # this is a workaround for the fact that these countries have very few data points
        if country in ["Sudan", "South Sudan"]:
            window_length = 11

        # Apply Savitzky-Golay filter to get the smoothed baseline
        smoothed_yields = savgol_filter(yields, window_length, polyorder)

        # Calculate percentage changes
        pct_change = ((yields - smoothed_yields) / smoothed_yields) * 100

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
