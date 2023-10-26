import re
import os
import sys
import time
import json
import logging
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs

# Global variables
default_link = "https://www.recommend.my/services/all-services"
logging.basicConfig(filename='recommend_info.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
save_point_filename = "save_point"
save_point_header = ["link_index", "url", "desc"]
# END: Global variables

# # Custom exception class with constructor arguments
# class CustomException(Exception):
#     def __init__(self, message, custom_variable):
#         super().__init__(message)
#         self.custom_variable = custom_variable

# Global function
def reformat_data_list_to_records(headers, list_item_list):
    if len(headers) != len(list_item_list):
        print("Unmatch columns length")
        exit
    return {key: value for key, value in zip(headers, list_item_list)}

def reformat_data_records_to_list(headers, record_list):
    cols = {}
    for header in headers:
        cols[header] = []
    for record in record_list:
        if len(headers) != len(record):
            print("Headers length doesn't match with records key")
            exit
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

# # Higher-Order Function (HOC) to create a decorator
# def handle_exceptions(func): 
#     def wrapper(*args, **kwargs):
#         try:
#             result = func(*args, **kwargs)
#         except CustomException as e:
#             # You can handle the exception here (log it, raise a custom exception, etc.)
#             result = None  # Or any other default value you want to return on exception
#             logging.error(f"An error occurred when performing {func.__name__}: {e}")

#             sys.exit("Script terminated due to an error.")
#         return result
#     return wrapper

# END: Global function
class WebScrapper:
    def __init__(self, url) -> None:
        self.url = url
        self.driver = webdriver.Chrome()


    def navigate_to_page(self, url) -> None:
        self.url = url if url else self.url
        print(f"URL: {url}")
        self.driver.get(self.url)


    def get_current_link(self) -> str:
        return self.driver.current_url
    

    def extract_element(self, css_selector) -> WebElement:
        try:
            element = self.driver.find_element(by=By.CSS_SELECTOR, value=css_selector)
        except Exception as e:    
            print(f"Failed to extract element [{css_selector}]: {e}")
            return None
        else:
            return element
        

    def extract_elements(self, css_selectors) -> list:
        elements = []
        for css_selector in css_selectors:
            elements.append(self.extract_element(css_selector))
        return elements    
    

    def extract_element_attr(self, css_selector, attr) -> str:
        return self.extract_element(css_selector).get_attribute(attr)
    

    def extract_elements_attrs(self, css_selectors, attr) -> list:
        attrs = []
        for css_selector in css_selectors:
            elements = self.driver.find_elements(by=By.CSS_SELECTOR, value=css_selector)
            for element in elements:
                attrs.append(element.get_attribute(attr))
        return attrs
    

    def extract_element_link(self, css_selector) -> str:
        return self.extract_element_attr(css_selector, "href")
    

    def extract_elements_links(self, css_selectors) -> list:
        return self.extract_elements_attrs(css_selectors, "href")    
    

    def extract_element_text(self, css_selector) -> str:
        return self.extract_element(css_selector).text
    

    def extract_elements_texts(self, css_selectors) -> list:
        texts = []
        for css_selector in css_selectors:
            elements = self.driver.find_elements(by=By.CSS_SELECTOR, value=css_selector)
            for element in elements:
                texts.append(element.text)
        return texts
    

    def extract_regex(self, css_selector, regex) -> str:
        script_tag = self.driver.execute_script(
            f'return [...document.querySelectorAll("{css_selector}")].find(element => /{regex}/.test(element.textContent));'
        )
        if script_tag:
            data = re.findall(regex, script_tag.get_attribute('outerHTML'))[0] # Extract the first matched data that fulfill the regex pattern
        else:
            print(f"{regex} not found in any script tags")
            return False
        return data
    

    def extract_regex_from_script_tag(self, regex) -> str:
        return self.extract_regex("script", regex) # strictly from "script" tag only
        

    def safe_click(self, css_selector) -> None:
        element = self.extract_element(css_selector)
        try:
            element.click()
        except Exception as e:
            print(f"Error clicking element: {e}")


    def click_next_page_btn(self, btn_css_selector) -> None:
        self.navigate_to_page(self.url)
        self.safe_click(btn_css_selector)
        self.url = self.get_current_link()


    def fill_form_field(self, field_element_css_selector, value) -> None:
        field_element = self.driver.find_element(by=By.CSS_SELECTOR, value=field_element_css_selector)
        field_element.clear()
        field_element.send_keys(value)


    def fill_form_fields(self, field_element_css_selectors=[], values=[]) -> None:
        for index, field_element_css_selector in enumerate(field_element_css_selectors):
            self.fill_form_field(field_element_css_selector, values[index])        


    def scroll_to(self, id) -> None:
        self.navigate_to_page(f"{self.driver.current_url}#{id}")


    def scroll_to(self, x_position, y_position) -> None:
        self.driver.execute_script(f"window.scrollTo({x_position}, {y_position});")


    def wait_for_element(self, driver, by, value, timeout=10) -> None:
        driver = driver if driver else self.driver
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


    def handle_alert(self, action='accept') -> None:
        alert = self.driver.switch_to.alert
        if action.lower() == 'accept':
            alert.accept()
        elif action.lower() == 'dismiss':
            alert.dismiss()
        else:
            raise ValueError('Invalid action specified')        

    def switch_to_new_window(self) -> None:
        window_handles = self.driver.window_handles
        self.driver.switch_to.window(window_handles[-1])


    def close_browser(self) -> None:
        self.driver.quit()    

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
            print(f"Write data into {filename} failed: {e}")

    def write_header(self, header, filename):
        df = pd.DataFrame(columns=header)
        filename = csv_filename_checker(filename)
        try:
            # Export the DataFrame to a CSV file
            df.to_csv(filename, index=False)  # Set index=False to exclude row numbers in the CSV
        except Exception as e:    
            print(f"Write data into {filename} failed: {e}")


    def append(self, data, filename):
        df = pd.DataFrame(data)
        filename = csv_filename_checker(filename)
        try:
            # Append the DataFrame to a CSV file
            df.to_csv(filename, mode="a", index=False, header=False)  # Set index=False to exclude row numbers and header=False to exclude extra column names in the CSV
        except Exception as e:    
            print(f"Append data into {filename} failed: {e}")    
    
    def is_file_exist(self, filename):
        return pd.io.common.file_exists(csv_filename_checker(filename))

    def remove_duplicates_from_csv(self, read_filename, write_filename, header):
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(read_filename)        
        # Remove duplicate rows based on all columns
        df_no_duplicates = df.drop_duplicates(subset=header, keep='first')
        # Save the cleaned DataFrame to a new CSV file
        df_no_duplicates.to_csv(write_filename, index=False)
        
    
class SavePointManager:
    def __init__(self)-> None:
        self.is_save_point_exist = False
        self.save_point_data = self.read(save_point_filename)

    def write(self, save_point_record)-> None:
        print(f"save_point_record: {save_point_record}")
        print(f"save_point_header: {save_point_header}")
        print(f"save_point_filename: {save_point_filename}")
        csv_file_manager.write(save_point_record, save_point_header, save_point_filename)
    
    def read(self, save_point_filename=save_point_filename)-> None:
        save_point_filename = csv_filename_checker(save_point_filename)
        save_point_data_default = reformat_data_list_to_records(save_point_header,[0,None,None])
        save_point_data_from_file = csv_file_manager.read(save_point_filename, save_point_header, "records")[0]
        self.save_point_data = save_point_data_from_file if save_point_data_from_file else save_point_data_default
        print(f"save_point_data: {self.save_point_data}")
        if save_point_data_from_file:
            self.is_save_point_exist = True
            os.remove(save_point_filename)
        print(f"init is_save_point_exist: {self.is_save_point_exist}")
        return self.save_point_data

    def check_save_point_exist(self):
        return self.is_save_point_exist
    
    def get_link_index(self):
        return self.save_point_data["link_index"]
    
    def get_url(self):
        return self.save_point_data["url"]
    
    def get_desc(self):
        return self.save_point_data["desc"]
    
    def clear(self):
        save_point_data_default = reformat_data_list_to_records(save_point_header,[0,None,None])
        self.save_point_data = save_point_data_default
    
# Configurations
web_scrapper = WebScrapper(default_link)
csv_file_manager = CSVFileManager()
save_point_manager = SavePointManager()
# END: Configurations

# Scraping function
def repeat_navigate_scrape_data_and_click_next_page_btn(web_scrapper, links, web_scrapper_actions, web_scrapper_params, pagination_next_btn_css_selector=None, remove_urls_param_flag=False, write_csv_file_name="links.csv", write_file_data_header=["Link"], desc="step"):
    scrapped_data = [[] for _ in web_scrapper_actions]

    if save_point_manager.get_desc() != desc:
        csv_file_manager.write_header(write_file_data_header, write_csv_file_name)

    # i = 0
    for link_index, link in enumerate(links[save_point_manager.get_link_index():], start=save_point_manager.get_link_index()):
        is_data_scrap = True # To indicate whether the scrapping action scrapped some data
        url = save_point_manager.get_url() if save_point_manager.get_url() else link
        save_point_manager.clear()
        try:
            while True:
                # i+=1
                # if i==4: return scrapped_data

                # Navigate to the url
                web_scrapper.navigate_to_page(url) 
                # END: Navigate to the url

                try:
                    # Scrap the data (can have multiple scrap actions, because might want to scrap different things)
                    for index, web_scrapper_action in enumerate(web_scrapper_actions):
                        param = web_scrapper_params[index]
                        data = remove_urls_parameters(web_scrapper_action(param)) if remove_urls_param_flag else web_scrapper_action(param)
                        if not data:
                            is_data_scrap = False
                            # Clear data list
                            for list in scrapped_data:
                                list.clear()
                            # END: Clear data list
                            break
                        list_extend_or_append_data(scrapped_data[index], data) # extend if the scrapped data is in a list, else append it
                    # END: Scrap the data
                except BaseException as inner_be:
                    # Handling Error Raised while scrapping data
                    logging.error(f"Error occurred inner exception: {inner_be}")
                    logging.error(f"Stop at link_index: {link_index}, url: {url}, Error: {inner_be}") # Log error into a file
                    save_point_record = reformat_data_list_to_records(save_point_header, [[link_index], [url], [desc]])
                    save_point_manager.write(save_point_record) # Save point
                    # END: Handling Error Raised while scrapping data

                next_btn_element = web_scrapper.extract_element(pagination_next_btn_css_selector) if pagination_next_btn_css_selector else None

                # print(f"scrapped data length: {len(scrapped_data)}")
                print(f"scrapped data: {scrapped_data}")
                flat_list = [element for innerList in scrapped_data for element in innerList]
                # print(f"flat list length: {len(flat_list)}")
                print(f"flat list: {flat_list}")

                # Write the scrapped data into a csv file (if the data list more than 50 items inside)
                if(len(flat_list) > 50 or not next_btn_element and is_data_scrap):
                    write_csv_file_name = write_csv_file_name # The csv file name that we write the data into
                    write_file_data_header = write_file_data_header # Header(s) column of csv file we write
                    scrapped_records = reformat_data_list_to_records(write_file_data_header, scrapped_data) # reformat the headers and scrapped_data into this format: {'Header1':["data1","data2"],'Header2':["data3","data4"]}
                    csv_file_manager.append(scrapped_records, write_csv_file_name)
                        
                    # print(f"scrapped_data before clear: {scrapped_data}")
                    # Reset scrapped_data to empty
                    for list in scrapped_data:
                        list.clear()
                    # END: Reset scrapped_data to empty
                    # print(f"scrapped_data after clear: {scrapped_data}")

                # END: Write the scrapped data into a csv file 

                # Click "next page" btn (if "next page" btn not exist, break the loop)
                if not next_btn_element:
                    break
                web_scrapper.safe_click(pagination_next_btn_css_selector)
                url = web_scrapper.get_current_link()
                # END: Click "next page" btn
        except BaseException as outer_be:
            logging.error(f"Error occurred outside exception: {outer_be}")
            logging.error(f"Stop at link_index: {link_index}, url: {url}, Error: {outer_be}") # Log error into a file
            save_point_record = reformat_data_list_to_records(save_point_header, [index, url, desc])
            save_point_manager.write(save_point_record) # Save point
            exit()

    # return scrapped_data

def website_scrap_action(read_csv_file_name, web_scrapper_action_names, web_scrapper_action_params, write_csv_file_name, write_file_data_header, pagination_next_btn_css_selector=None, remove_urls_param_flag=False, desc="Step 1", link=""):
    if save_point_manager.check_save_point_exist() and save_point_manager.get_desc() != desc:
        return 

    # Section 1: Read data from csv file
    read_csv_file_name = read_csv_file_name 
    read_csv_file_col = ["Link"]
    csv_file_data = csv_file_manager.read(read_csv_file_name, read_csv_file_col) # Read and get the data from the csv file and desired column
    link = link if link else default_link
    links = csv_file_data["Link"] if csv_file_data else [link] # only default_link if the csv file not exist, else get the 'Link' column from the csv file
    # END: Section 1: Read data from csv file

    # Section 2: Scrap data based on the links retrieved from [Section 1]
    web_scrapper_action_names = web_scrapper_action_names # should in a list, it is the web_scrapper action names that have to execute
    web_scrapper_action_params = web_scrapper_action_params # should in a list, it is the parameters for the web_scrapper action names above (The items inside corresponds to the items in list [web_scrapper_action_names], note: it might be a nested list sometimes)

    web_scrapper_actions = [getattr(web_scrapper, action_name) for action_name in web_scrapper_action_names]
    # scrapped_data = []
    # scrapped_data.extend(
    repeat_navigate_scrape_data_and_click_next_page_btn(
        web_scrapper, 
        links,
        web_scrapper_actions,
        web_scrapper_action_params,
        pagination_next_btn_css_selector=pagination_next_btn_css_selector,
        remove_urls_param_flag=remove_urls_param_flag,
        write_csv_file_name=write_csv_file_name,
        write_file_data_header=write_file_data_header,
        desc=desc
    )
    # )
    # END: Section 2: Scrap data based on the links retrieved from [Section 1]
    
    # Section 3: Write the scrapped data into a csv file
    # write_csv_file_name = write_csv_file_name # The csv file name that we write the data into
    # write_file_data_header = write_file_data_header # Header(s) column of csv file we write
    # scrapped_records = reformat_data_list_to_records(write_file_data_header, scrapped_data) # reformat the headers and scrapped_data into this format: {'Header1':["data1","data2"],'Header2':["data3","data4"]}
    # csv_file_manager.write(scrapped_records, write_file_data_header, write_csv_file_name)
    # END: Section 3: Write the scrapped data into a csv file

    # Remove duplicated rows in CSV file
    csv_file_manager.remove_duplicates_from_csv(read_csv_file_name, write_csv_file_name, write_file_data_header)
    # END: Remove duplicated rows in CSV file

# END: Scraping function

def main():
    recommend_web_scrape_steps_params = [
        # Sample
        # {
        #     "desc": "Step 0",
        #     "read_csv_file_name": "",
        #     "web_scrapper_action_names": ["extract_elements_links"], # (should in a list)
        #     "web_scrapper_action_params": [["div.left-side-content div.flickity-cell a"]],  # (should in a list)
        #     "write_csv_file_name": "professional_categories_links",
        #     "write_file_data_header": ["Link"], # (should in a list)
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": False
        # },
        # {
        #     "desc": "Step 1",
        #     "read_csv_file_name": "",
        #     "web_scrapper_action_names": ["extract_elements_links"],
        #     "web_scrapper_action_params": [["div.left-side-content div.flickity-cell a"]],
        #     "write_csv_file_name": "professional_categories_links",
        #     "write_file_data_header": ["Link"],
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": False
        # },
        # {
        #     "desc": "Step 2",
        #     "read_csv_file_name": "professional_categories_links",
        #     "web_scrapper_action_names": ["extract_elements_links"],
        #     "web_scrapper_action_params": [["div#jsSideContent a.card-overlay-link","div#jsSideContent div.col a.text-info"]],
        #     "write_csv_file_name": "professionals_links",
        #     "write_file_data_header": ["Link"],
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": True,
        # },
        # {
        #     "desc": "Step 3",
        #     "read_csv_file_name": "professionals_links",
        #     "web_scrapper_action_names": ["extract_elements_links"],
        #     "web_scrapper_action_params": [["div.profile-card-action div.business-contact a.profile-card-phone"]],
        #     "write_csv_file_name": "profile_vendors_links",
        #     "write_file_data_header": ["Link"],
        #     "pagination_next_btn_css_selector": "ul.pagination li.pagination-next a",
        #     "remove_urls_param_flag": True,
        # },
        {
            "desc": "Step 4",
            "read_csv_file_name": "profile_vendors_links",
            "web_scrapper_action_names": ["extract_elements_texts", "extract_regex_from_script_tag"],
            "web_scrapper_action_params": [["div.provider div.provider__meta div.provider__title h4.provider__name"], r'(\+?6?01\d{8,9})'],
            "write_csv_file_name": "vendors_name_contact",
            "write_file_data_header": ["Name", "Contact"],
            "pagination_next_btn_css_selector": None,
            "remove_urls_param_flag": False,
        }
        # {
        #     "desc": "Step 4",
        #     "read_csv_file_name": "",
        #     "web_scrapper_action_names": ["extract_elements_texts", "extract_regex_from_script_tag"],
        #     "web_scrapper_action_params": [["div.provider div.provider__meta div.provider__title h4.provider__name"], r'(\+?6?01\d{8,9})'],
        #     "write_csv_file_name": "vendors_name_contact",
        #     "write_file_data_header": ["Name", "Contact"],
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": False,
        #     "link": "https://www.recommend.my/businesses/ma-global-design"
        # }
    ]

    start_time = time.time()

    try:
        for step_params in recommend_web_scrape_steps_params:
            website_scrap_action(**step_params)
    except BaseException as be:
        logging.error(f"Error occurred in main exception:{be}")
        print(f"Error occurred in main exception:{be}")
    else:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Whole script run time taken: {elapsed_time:.2f} seconds") # Log info into a file
        print(f"Whole script run time taken: {elapsed_time:.2f} seconds")
    
    web_scrapper.close_browser()

if __name__ == "__main__":
    main()