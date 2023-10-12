import pandas as pd

# Sample list of dictionaries (TYPE 1: List of dictionaries, each key is COLUMN NAME and value is ROWs)
data = [{'Name': 'Alice', 'Age': 25, 'City': 'New York'},
        {'Name': 'Bob', 'Age': 30, 'City': 'Chicago'},
        {'Name': 'Eve', 'Age': 22, 'City': 'Los Angeles'}]
# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(data)
# Display the DataFrame
print(df)
# Specify the file name
file_name = 'output1.csv'
# Export the DataFrame to a CSV file
df.to_csv(file_name, index=False)  # Set index=False to exclude row numbers in the CSV

# ----------------------------------------------------------------------------------------------------------------

# Sample list of items (TYPE 2: List of item, 1 COLUMN only)
item_list = ['apple', 'banana', 'cherry', 'orange', 'grape', 'kiwi', 'melon', 'pear', 'pineapple']
# Create a DataFrame with a column containing the list of items
df = pd.DataFrame({'Items': item_list})
# Display the DataFrame
print(df)
# Specify the file name
file_name = 'output2.csv'
# Export the DataFrame to a CSV file
df.to_csv(file_name, index=False)  # Set index=False to exclude row numbers in the CSV