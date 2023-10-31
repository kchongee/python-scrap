import re
import os
import sys
import copy
import time
import json
import logging
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

# Global variables
default_link = "https://www.recommend.my/services/all-services"
save_point_filename = "save_point"
save_point_header = ["link_index", "url", "desc"]
logging_filename = 'recommend.log'
logging.basicConfig(filename=logging_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# END: Global variables


# Global function
def reformat_data_list_to_records(headers, list_item_list):
    if len(headers) != len(list_item_list):
        print(f"[reformat_data_list_to_records] --> Unmatch columns length")
        logging.error(f"[reformat_data_list_to_records] --> Unmatch columns length", exc_info=True)
        exit()
    return {key: value for key, value in zip(headers, list_item_list)}

def reformat_data_records_to_list(headers, record_list):
    cols = {}
    for header in headers:
        cols[header] = []
    for record in record_list:
        if len(headers) != len(record):
            print(f"Headers length doesn't match with records key")
            logging.error(f"[reformat_data_records_to_list] --> Headers length doesn't match with records key", exc_info=True)
            exit()
        for index, (key,value) in enumerate(record.items()):
            cols[headers[index]].append(value)
    return cols  

def remove_url_parameters(url):
    return url.split('?',1)[0]

def remove_urls_parameters(urls):
    return [remove_url_parameters(url) for url in urls]

def is_data_a_list(data):
    return isinstance(data, list)

def list_extend_or_append_data(list, data):
    if is_data_a_list(data):
        list.extend(data)
    else:
        list.append(data)

def csv_filename_checker(filename):
    return (filename if ".csv" in filename else filename+".csv")
# END: Global function


# Classes
class CSVFileManager:

    def __init__(self)-> None:
        pass

    def read(self, filename, cols_name, format="list"):
        filename = csv_filename_checker(filename)
        if format in ["dict", "list", "series", "split", "tight", "records", "index"]:
            try:
                df = pd.read_csv(filename, usecols=cols_name)
            except Exception as e:
                print(f"Read csv file exception: {e}")
                return False
            else:
                data = df.to_dict(format)
            return data
        else:
            return False

    def write(self, data, headers, filename):
        df = pd.DataFrame(data)
        filename = csv_filename_checker(filename)
        try:
            # Export the DataFrame to a CSV file
            df.to_csv(filename, header=headers, index=False)  # Set index=False to exclude row numbers in the CSV
        except Exception as e:    
            logging.error(f"Write data into {filename} failed: {e}", exc_info=True)
            print(f"Write data into {filename} failed: {e}")

    def write_header(self, header, filename):
        df = pd.DataFrame(columns=header)
        filename = csv_filename_checker(filename)
        try:
            # Export the DataFrame to a CSV file
            df.to_csv(filename, index=False)  # Set index=False to exclude row numbers in the CSV
        except Exception as e: 
            logging.error(f"Write header {header} into {filename} failed: {e}", exc_info=True)
            print(f"Write header {header} into {filename} failed: {e}")

    def append(self, data, filename):
        df = pd.DataFrame(data)
        filename = csv_filename_checker(filename)
        try:
            # Append the DataFrame to a CSV file
            df.to_csv(filename, mode="a", index=False, header=False)  # Set index=False to exclude row numbers and header=False to exclude extra column names in the CSV
        except Exception as e:    
            logging.error(f"Append data into {filename} failed: {e}", exc_info=True)
            print(f"Append data into {filename} failed: {e}")    
    
    def is_file_exist(self, filename):
        return pd.io.common.file_exists(csv_filename_checker(filename))

    def remove_null_and_duplicates_from_csv(self, filename):
        filename = csv_filename_checker(filename)
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(filename, dtype=str)        
        # Remove rows with empty strings in any column
        df_cleaned = df.dropna(subset=df.columns, how='all', inplace=False)
        # Remove duplicate rows based on all columns
        df_cleaned_no_duplicates = df_cleaned.drop_duplicates(subset=df.columns, keep='first')
        # Save the cleaned DataFrame to a new CSV file
        df_cleaned_no_duplicates.to_csv(filename, index=False)
            

class Timer:
    def __init__(self)-> None:
        self.start_time = time.time()
        self.stop_time = self.start_time

    def start(self)-> None:
        self.start_time = time.time()

    def stop(self)-> None:
        self.stop_time = time.time()

    def get_execution_time(self):
        return self.stop_time-self.start_time
# END: Classes


# Classes Configurations
csv_file_manager = CSVFileManager()
# END: Classes Configurations


# Main Function
def main():
    read_filename = "vendors_name_contact"
    name_column = "name"
    whatsapp_column = "whatsapp_number"
    phone_column = "phonecall_number"
    contact_column = "contact_number"    
    write_filename = "reformatted_vendors_name_contact"

    whole_script_timer = Timer()
    try:
        # Read from csv file
        filename = csv_filename_checker(read_filename)    
        df = pd.read_csv(filename, dtype=str)                

        # Extract and seperate whatsapp_number column and phonecall_number
        df_cleaned_wa_column = df[[name_column, whatsapp_column]].rename(columns={whatsapp_column: contact_column}).dropna()
        df_cleaned_phone_column = df[[name_column, phone_column]].rename(columns={phone_column: contact_column}).dropna()        

        # Append the new rows to the original DataFrame
        df_reformatted = pd.concat([df_cleaned_wa_column, df_cleaned_phone_column], ignore_index=True)

        # Remove duplicated rows (make rows unique) & sort by column "name"
        df_reformatted_cleaned = df_reformatted.drop_duplicates(subset=df_reformatted.columns, keep='first').sort_values(by=[name_column])

        # Write the reformatted data into a csv file
        df_reformatted_cleaned.to_csv(csv_filename_checker(write_filename), index=False)

    except BaseException as be:
        logging.error(f"Error occurred in main exception: {be}", exc_info=True)
        print(f"Error occurred in main exception: {be}")
    finally:
        whole_script_timer.stop()
        logging.info(f"Whole script execution time: {whole_script_timer.get_execution_time():.2f} seconds") # Log info into a file
        print(f"Whole script execution time: {whole_script_timer.get_execution_time():.2f} seconds")


if __name__ == "__main__":
    main()
# END: Main Function