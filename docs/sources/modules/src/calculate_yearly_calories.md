#


### calculate_calories
[source](https://github.com/allfed/My-Super-Cool-Respository/blob/master/src/calculate_yearly_calories.py/#L50)
```python
.calculate_calories(
   df
)
```

---
Calculate calories for each crop based on production weight.


**Args**

* **df** (pandas.DataFrame) : Filtered production data


**Returns**

* **tuple**  : (DataFrame with calorie calculations, list of calorie column names)


----


### aggregate_calories_by_country
[source](https://github.com/allfed/My-Super-Cool-Respository/blob/master/src/calculate_yearly_calories.py/#L75)
```python
.aggregate_calories_by_country(
   df, calorie_cols
)
```

---
Aggregate calories by country and year.


**Args**

* **df** (pandas.DataFrame) : Data with calorie calculations
* **calorie_cols** (list) : List of column names containing calorie values


**Returns**

* **DataFrame**  : Aggregated calories by country and year

