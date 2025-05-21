#


### extract_and_load_fao_data
[source](https://github.com/allfed/My-Super-Cool-Respository/blob/master/src/get_FAO_data.py/#L10)
```python
.extract_and_load_fao_data(
   zip_path, csv_filename
)
```

---
Extract and load FAO crop production data from a ZIP file.


**Args**

* **zip_path** (Path) : Path to the FAOSTAT ZIP file
* **csv_filename** (str) : Name of the CSV file within the ZIP to extract


**Returns**

* **DataFrame**  : Complete crop production dataset


----


### filter_crops_of_interest
[source](https://github.com/allfed/My-Super-Cool-Respository/blob/master/src/get_FAO_data.py/#L47)
```python
.filter_crops_of_interest(
   df, crop_list
)
```

---
Filter the dataset to include only crops in crop_list.


**Args**

* **df** (DataFrame) : FAOSTAT crop production dataset
* **crop_list** (dict) : Dictionary of crop categories and their names


**Returns**

* **DataFrame**  : Filtered dataset with only the crops of interest


----


### save_data_to_csv
[source](https://github.com/allfed/My-Super-Cool-Respository/blob/master/src/get_FAO_data.py/#L72)
```python
.save_data_to_csv(
   df, output_path
)
```

---
Save the DataFrame to a CSV file.


**Args**

* **df** (DataFrame) : Data to save
* **output_path** (Path) : Path where to save the CSV file

