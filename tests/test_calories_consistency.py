import pandas as pd
import numpy as np

crop_dict = {
    "Apples": 15100,
    "Barley": 378000,
    "Grapes": 225000,
    "Maize (corn)": 700000,
    "Oranges": 10100,
    "Potatoes": 130000,
    "Rice": 319000,
    "Sugar beet": 42400,
    "Sugar cane": 45000,
    "Watermelons": 63000,
    "Wheat": 2279000,
}

CALORIE_VALUES = {
    # Cereals
    "Maize (corn)": 356,
    "Rice": 360,
    "Wheat": 334,
    "Barley": 332,
    "Sorghum": 343,
    # Sugar crops
    "Sugar cane": 30,
    "Sugar beet": 70,
    # Roots and tubers
    "Potatoes": 67,
    "Cassava, fresh": 109,
    "Sweet potatoes": 92,
    "Yams": 101,
    "Taro": 86,
    # Fruits
    "Bananas": 60,
    "Apples": 48,
    "Oranges": 34,
    "Grapes": 53,
    "Watermelons": 17,
    # Vegetables
    "Tomatoes": 17,
    "Onions and shallots, green": 31,
    "Cucumbers and gherkins": 13,
    "Cabbages": 19,
    "Eggplants (aubergines)": 21,
}


def test_calories_values():
    # Read in the calories data from the CSV file in results
    df = pd.read_csv("results/calories.csv", index_col=0)
    # Filter for Afghanistan and the 1961 column
    afghanistan_data = df.loc["Afghanistan", "1961"]

    # Calculate expected values
    # Go through all crops and compare the sum of the calories with afghanistan_data
    expected_calories = 0
    for crop, production in crop_dict.items():
        if crop in CALORIE_VALUES:
            expected_calories += ((production * 1000000) * CALORIE_VALUES[crop]) / 100
    # Compare the expected calories with the actual data
    assert np.isclose(
        afghanistan_data, expected_calories, rtol=1e-5
    ), f"Expected {expected_calories}, but got {afghanistan_data}"

    # Check if the values for the United States in 1961 are larger than Afghanistan
    us_data = df.loc["United States of America", "1961"]
    afghanistan_data = df.loc["Afghanistan", "1961"]
    assert (
        us_data > afghanistan_data
    ), f"Expected US calories in 1961 to be larger than Afghanistan, but got {us_data} and {afghanistan_data}"

    # Check if the values values for the United States in 2023 are in a reasonable range
    us_data_2023 = df.loc["United States of America", "2023"]
    assert (
        us_data_2023 > 1000000000
    ), f"Expected US calories in 2023 to be larger than 1 billion, but got {us_data_2023}"

    # Should also not be larger than 1.8 × 10¹⁵ kcal
    assert (
        us_data_2023 < 1.8e15
    ), f"Expected US calories in 2023 to be smaller than 1.8 × 10¹⁵ kcal, but got {us_data_2023}"


if __name__ == "__main__":
    # Run the test
    test_calories_values()
    print("Test passed!")
