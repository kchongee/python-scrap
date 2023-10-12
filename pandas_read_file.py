import pandas as pd

# Specify the file name
file_name = 'output2.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(file_name)

# Now df contains the data from the CSV file
print(df)

# ------------------------------------------------------

# Convert DataFrame to a List of Dictionaries (exp: [{'Name': 'Alice', 'Age': 25, 'City': 'New York'}, {'Name': 'Bob', 'Age': 30, 'City': 'Chicago'},...])
dict_list = df.to_dict('records')

# Now dict_list contains list of dictionaries
print(dict_list)

# ------------------------------------------------------

# Convert DataFrame to a Dictionary that contain List (exp: {'Items': ['apple', 'banana', 'cherry', 'orange', 'grape', 'kiwi', 'melon', 'pear', 'pineapple']})
list_dict = df.to_dict('list')

# Now dict_list contains list of dictionaries
print(list_dict)
