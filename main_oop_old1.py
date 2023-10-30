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
        print("Unmatch columns length")
        exit()
    return {key: value for key, value in zip(headers, list_item_list)}

def reformat_data_records_to_list(headers, record_list):
    cols = {}
    for header in headers:
        cols[header] = []
    for record in record_list:
        if len(headers) != len(record):
            print("Headers length doesn't match with records key")
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


class WebScraper:
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

    def extract_any_regexs_from_script_tag(self, regexs) -> str:
        for regex in regexs:
            data = self.extract_regex_from_script_tag(regex)
            if data:
                break
        return data
        
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

    def remove_duplicates_from_csv(self, filename, header):
        filename = csv_filename_checker(filename)
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(filename)        
        # Remove duplicate rows based on all columns
        df_no_duplicates = df.drop_duplicates(subset=header, keep='first')
        # Save the cleaned DataFrame to a new CSV file
        df_no_duplicates.to_csv(filename, index=False)
        
    
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
        save_point_data_from_file = csv_file_manager.read(save_point_filename, save_point_header, "records")
        self.save_point_data = save_point_data_from_file[0] if save_point_data_from_file else save_point_data_default
        # print(f"save_point_data: {self.save_point_data}")
        if save_point_data_from_file:
            self.is_save_point_exist = True
            os.remove(save_point_filename)
        # print(f"init is_save_point_exist: {self.is_save_point_exist}")
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
web_scraper = WebScraper(default_link)
csv_file_manager = CSVFileManager()
save_point_manager = SavePointManager()
# END: Configurations


# Scraping function
def repeat_navigate_scrape_data_and_click_next_page_btn(web_scraper, links, web_scraper_actions, web_scraper_params, pagination_next_btn_css_selector=None, remove_urls_param_flag=False, write_csv_file_name="links.csv", write_file_data_header=["link"], desc="step"):
    default_scraped_data = [[] for _ in web_scraper_actions]
    scraped_data = copy.deepcopy(default_scraped_data)

    if save_point_manager.get_desc() != desc:
        csv_file_manager.write_header(write_file_data_header, write_csv_file_name)

    for link_index, link in enumerate(links[save_point_manager.get_link_index():], start=save_point_manager.get_link_index()):
        is_data_scrap = True # To indicate whether the scraping action scraped some data
        url = save_point_manager.get_url() if save_point_manager.get_url() else link
        save_point_manager.clear()
        try:
            while True:
                web_scraper.navigate_to_page(url) # Navigate to the url

                try:
                    # Scrap data actions (can have multiple scrap actions, because might want to scrap different things)
                    for index, web_scraper_action in enumerate(web_scraper_actions):
                        param = web_scraper_params[index]
                        data = remove_urls_parameters(web_scraper_action(param)) if remove_urls_param_flag else web_scraper_action(param)
                        if not data:
                            is_data_scrap = False
                            scraped_data = copy.deepcopy(default_scraped_data) # Reset scraped_data to default empty
                            break
                        list_extend_or_append_data(scraped_data[index], data) # extend if the scraped data is in a list, else append it
                    # END: Scrap data actions
                except BaseException as inner_be:
                    # Handling Error Raised while scraping data
                    logging.error(f"Error occurred inner exception: {inner_be}")
                    logging.error(f"Stop at link_index: {link_index}, url: {url}, Error: {inner_be}", exc_info=True) # Log error into a file
                    save_point_record = reformat_data_list_to_records(save_point_header, [[link_index], [url], [desc]])
                    save_point_manager.write(save_point_record) # Save point
                    # END: Handling Error Raised while scraping data

                next_btn_element = web_scraper.extract_element(pagination_next_btn_css_selector) if pagination_next_btn_css_selector else None

                # Write the scraped data into a csv file (if the data list more than 50 items inside)
                flatten_scraped_data = [element for innerList in scraped_data for element in innerList]
                if(is_data_scrap and len(flatten_scraped_data) > 50 or not next_btn_element):
                    write_csv_file_name = write_csv_file_name # The csv file name that we write the data into
                    write_file_data_header = write_file_data_header # Header(s) column of csv file we write
                    scraped_records = reformat_data_list_to_records(write_file_data_header, scraped_data) # reformat the headers and scraped_data into this format: {'Header1':["data1","data2"],'Header2':["data3","data4"]}
                    csv_file_manager.append(scraped_records, write_csv_file_name)
                    
                    scraped_data = copy.deepcopy(default_scraped_data) # Reset scraped_data to default empty
                # END: Write the scraped data into a csv file 

                # Click pagination "next page" btn (if "next page" btn not exist, break the loop, continue to scrap data on next link)
                if not next_btn_element:
                    break
                web_scraper.safe_click(pagination_next_btn_css_selector)
                url = web_scraper.get_current_link()
                # END: Click pagination "next page" btn
        except BaseException as outer_be:
            logging.error(f"Error occurred outside exception: {outer_be}")
            logging.error(f"Stop at link_index: {link_index}, url: {url}, Error: {outer_be}", exc_info=True) # Log error into a file
            save_point_record = reformat_data_list_to_records(save_point_header, [index, url, desc])
            save_point_manager.write(save_point_record) # Save point
            exit()

def website_scrap_action(read_csv_file_name, web_scraper_action_names, web_scraper_action_params, write_csv_file_name, write_file_data_header, pagination_next_btn_css_selector=None, remove_urls_param_flag=False, desc="Step 1", link=""):
    if save_point_manager.check_save_point_exist() and save_point_manager.get_desc() != desc:
        return 

    # Section 1: Read data from csv file
    read_csv_file_name = read_csv_file_name 
    read_csv_file_col = ["link"]
    csv_file_data = csv_file_manager.read(read_csv_file_name, read_csv_file_col) # Read and get the data from the csv file and desired column
    link = link if link else default_link
    links = csv_file_data["link"] if csv_file_data else [link] # only default_link if the csv file not exist, else get the 'link' column from the csv file
    # END: Section 1: Read data from csv file

    # Section 2: Scrap data based on the links retrieved from and then save into csv file [Section 1]
    web_scraper_action_names = web_scraper_action_names # should in a list, it is the web_scraper action names that have to execute
    web_scraper_action_params = web_scraper_action_params # should in a list, it is the parameters for the web_scraper action names above (The items inside corresponds to the items in list [web_scraper_action_names], note: it might be a nested list sometimes)

    web_scraper_actions = [getattr(web_scraper, action_name) for action_name in web_scraper_action_names]
    
    repeat_navigate_scrape_data_and_click_next_page_btn(
        web_scraper, 
        links,
        web_scraper_actions,
        web_scraper_action_params,
        pagination_next_btn_css_selector=pagination_next_btn_css_selector,
        remove_urls_param_flag=remove_urls_param_flag,
        write_csv_file_name=write_csv_file_name,
        write_file_data_header=write_file_data_header,
        desc=desc
    )
    # END: Section 2: Scrap data based on the links retrieved from and then save into csv file [Section 1]    

    # Section 3: Remove duplicated rows in CSV file
    csv_file_manager.remove_duplicates_from_csv(write_csv_file_name, write_file_data_header)
    # END: Section 3: Remove duplicated rows in CSV file
# END: Scraping function

def main():
    recommend_web_scrape_steps_params = [
        # Sample
        # {
        #     "desc": "Step 0", ## description for the step (for logging purpose)
        #     "read_csv_file_name": "", ## the csv file where we read to get all the links to scrap through
        #     "web_scraper_action_names": ["extract_elements_links"], ## should in a list
        #     "web_scraper_action_params": [["div.left-side-content div.flickity-cell a"]],  ## should in a list, no. item inside should correspond to the no. item of variable [web_scraper_action_names] above
        #     "write_csv_file_name": "professional_categories_links", ## The csv file where we read to get all the links to scrap through
        #     "write_file_data_header": ["link"], ## should in a list
        #     "pagination_next_btn_css_selector": None, ## indicate whats the pagination next page button css, if None means need not to click the button
        #     "remove_urls_param_flag": False ## indicate whether is there a need to remove the url's param from the scraped data
        # },
        # {
        #     "desc": "Step 1",
        #     "read_csv_file_name": "",
        #     "web_scraper_action_names": ["extract_elements_links"],
        #     "web_scraper_action_params": [["div.left-side-content div.flickity-cell a"]],
        #     "write_csv_file_name": "professional_categories_links",
        #     "write_file_data_header": ["link"],
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": False
        # },
        # {
        #     "desc": "Step 2",
        #     "read_csv_file_name": "professional_categories_links",
        #     "web_scraper_action_names": ["extract_elements_links"],
        #     "web_scraper_action_params": [["div#jsSideContent a.card-overlay-link","div#jsSideContent div.col a.text-info"]],
        #     "write_csv_file_name": "professionals_links",
        #     "write_file_data_header": ["link"],
        #     "pagination_next_btn_css_selector": None,
        #     "remove_urls_param_flag": True,
        # },
        # {
        #     "desc": "Step 3",
        #     "read_csv_file_name": "professionals_links",
        #     "web_scraper_action_names": ["extract_elements_links"],
        #     "web_scraper_action_params": [["div.profile-card-action div.business-contact a.profile-card-phone"]],
        #     "write_csv_file_name": "profile_vendors_links",
        #     "write_file_data_header": ["link"],
        #     "pagination_next_btn_css_selector": "ul.pagination li.pagination-next a",
        #     "remove_urls_param_flag": True,
        # },
        {
            "desc": "Step 4",
            "read_csv_file_name": "profile_vendors_links",
            "web_scraper_action_names": ["extract_elements_texts", "extract_any_regexs_from_script_tag",],
            "web_scraper_action_params": [["div.provider div.provider__meta div.provider__title h4.provider__name"], [r'(011\d{8}|01[0-46-9]\d{7})', r'60[2-9]\d{8}']], # assume both whatsapp-phone and call-phone having same phone number
            "write_csv_file_name": "vendors_name_contact",
            "write_file_data_header": ["name", "contact"],
            "pagination_next_btn_css_selector": None,
            "remove_urls_param_flag": False,
        }
    ]    

    whole_start_time = time.time()

    for step_params in recommend_web_scrape_steps_params:
        each_start_time = time.time()
        try:
            website_scrap_action(**step_params)
        except BaseException as be:
            logging.error(f"Error occurred in main exception: {be}", exc_info=True)
            print(f"Error occurred in main exception: {be}")
        finally:
            each_end_time = time.time()
            each_elapsed_time = each_end_time - each_start_time
            logging.info(f"<{step_params['desc']}> execution time: {each_elapsed_time:.2f} seconds") # Log info into a file
            print(f"<{step_params['desc']}> execution time: {each_elapsed_time:.2f} seconds")
    
    web_scraper.close_browser()

    whole_end_time = time.time()
    whole_elapsed_time = whole_end_time - whole_start_time
    logging.info(f"Whole script execution time: {whole_elapsed_time:.2f} seconds") # Log info into a file
    print(f"Whole script execution time: {whole_elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()