import pandas as pd

# Specify the file name
file_name = 'vendors_name_contact.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(file_name, dtype=str)

# Now df contains the data from the CSV file
print(df)

# Read the CSV file into a pandas DataFrame
df = df.dropna(subset=df.columns, how='all', inplace=False)

# Now df contains the data from the CSV file
print(df)

# Read the CSV file into a pandas DataFrame
df = df.drop_duplicates(subset=df.columns, keep='first')

# Now df contains the data from the CSV file
print(df)

# ------------------------------------------------------

# # Convert DataFrame to a List of Dictionaries (exp: [{'Name': 'Alice', 'Age': 25, 'City': 'New York'}, {'Name': 'Bob', 'Age': 30, 'City': 'Chicago'},...])
# dict_list = df.to_dict('records')

# # Now dict_list contains list of dictionaries
# print(dict_list)

# # ------------------------------------------------------

# # Convert DataFrame to a Dictionary that contain List (exp: {'Items': ['apple', 'banana', 'cherry', 'orange', 'grape', 'kiwi', 'melon', 'pear', 'pineapple']})
# list_dict = df.to_dict('list')

# # Now dict_list contains list of dictionaries
# print(list_dict)
