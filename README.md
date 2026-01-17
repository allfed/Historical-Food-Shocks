# Historical-Food-Shocks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) ![Testing](https://github.com/allfed/Historical-Food-Shocks/actions/workflows/testing.yml/badge.svg)

## What this is and what it can be used for

Historical-Food-Shocks analyzes the frequency and magnitude of food production shocks at the country level. This project aims to demonstrate that food production shocks meeting the requirements of a the Global Catastrophic Food Failure (GCFF) regularly at national scales, suggesting that global-scale events of similar magnitude are plausible and require preparation.

The analysis uses data from the Food and Agriculture Organization of the United Nations (FAO) to estimate how much each year's yield deviates from expected trends, focusing on the majority of feed and food crops that account for >85% of global calorie production.

By visualizing historical shock patterns through choropleth maps, this project grounds future catastrophic food security risks in historical data, challenging the perception that GCFF-scale events are merely theoretical.

## Installation

To install the Historical-Food-Shocks package, set up a virtual environment using uv with the following steps:

Create a virtual environment by running `uv venv` in the main folder of the repository. This creates an environment in the `.venv` directory. 

Activate the environment using `source .venv/bin/activate` on Unix/macOS or `.venv\Scripts\activate` on Windows. 

Install the package in editable mode by running `uv pip install -e .` in the main folder. This installs the package and all its dependencies.

To run the Jupyter notebooks, create a kernel for the environment. First install ipykernel with `uv pip install ipykernel`, then create the kernel using `python -m ipykernel install --user --name=food-shocks`. You can now select the "food-shocks" kernel in Jupyter to run the example notebooks or analyze the data yourself.

## How this works
The main implementation of the analysis is provided in the `src` directory. The analysis process consists of:

### Determining the largest shock

1. Loading and preprocessing the FAO data
2. Aggregating crops on a calorie basis to evaluate total calorie production
3. Calculating smoothed yield baselines using a Savitzky-Golay filter
4. Identifying irregular fluctuations (shocks) by comparing actual yields to the smoothed baseline

The `scripts` directory contains Jupyter notebooks with visualization examples and use cases for the analysis.
### Finding the reasons for the largest shocks

We used Claude 4 Sonnet to look for reasons for food shocks with the prompt saved in the docs folder. The results from Claude were verified by hand and sorted into a number of categories. The result file was then used to create the figures that display the shock categories. 

### Running the analysis with custom parameters

You can customize the analysis by modifying parameters such as:

- Window length and polynomial order for the Savitzky-Golay filter
- Shock threshold values (default is 5%)
- Specific crops to include in the analysis
- Date range for the analysis

You can also just execute `run_everything.py` to run everything in the right order.

## Getting the data

The repository comes with recent versions of the FAO data, but if you need the most up-to-date information, you can download the data from the FAO:
- [Production data](http://www.fao.org/faostat/en/#data/QC)

## Having problems?

If you encounter any issues, feel free to open an issue in the repository or contact the maintainers.

## Flowchart for shock detection

```mermaid
%%{ init: { 'flowchart': { 'curve': 'natural' } } }%%
flowchart TD
    subgraph id_pre [Pre-processing]
    direction TB
    id_pre_1[Import FAO data] --> id_pre_2[Clean and format data]
    id_pre_2 --> id_pre_3[Calculate total calories]
    end
    subgraph id_mod [Shock Detection]
    direction TB
    id_mod_1[Apply Savitzky-Golay filter] --> id_mod_2[Create smoothed baseline]
    id_mod_2 --> id_mod_3[Calculate % difference from baseline]
    id_mod_3 --> id_mod_4[Identify shocks > 5%]
    end
    
    FAO[(FAO data)] ==> id_pre
    id_pre ==> id_mod

    style id_pre fill:None,stroke:red,stroke-width:4px,stroke-dasharray: 5 5
    style id_mod fill:None,stroke:green,stroke-width:4px,stroke-dasharray: 5 5
    style FAO stroke:yellow,stroke-width:4px
```
