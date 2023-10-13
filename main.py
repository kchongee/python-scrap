import re
import time
import json
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs

# Global variables
current_url = ""
# END: Global variables

# Configuration 
# Selenium
options = Options()
custom_user_agent = "Mozilla/5.0 (Linux; Android 11; 100011886A Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.69 Safari/537.36"
options.add_argument(f'user-agent={custom_user_agent}')
driver = webdriver.Chrome(options=options)
# END: Configuration 

# --------------------------------------Global use functions--------------------------------------
# Read data from a csv file
# [format] can refer to 'orient' parameter from pandas .to_dict() method: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_dict.html
def read_data_from_csv_file(file_name:str, format:str='records'):  
    format = "records" if format=="dict" else format
    file_name = file_name if ".csv" in file_name else file_name+".csv"
    if format in ["dict", "list", "series", "split", "tight", "records", "index"]:
        try:
            df = pd.read_csv(file_name)
        except Exception as e:
            print(f"Read csv file exception: {e}")
            return False
        else:
            data = df.to_dict(format)
        return data
    else:
        return False
    
# Write data into a csv file
def write_data_to_csv_file(data, header:[], file_name:str):
    df = pd.DataFrame(data)
    file_name = file_name if ".csv" in file_name else file_name+".csv"
    try:
        # Export the DataFrame to a CSV file
        df.to_csv(file_name, header=header, index=False)  # Set index=False to exclude row numbers in the CSV
    except Exception as e:    
        print(f"Append data into {file_name} failed: {e}")

# Append data into a csv file
def append_data_to_csv_file(data, file_name:str):    
    df = pd.DataFrame(data)
    file_name = file_name if ".csv" in file_name else file_name+".csv"
    try:
        # Append the DataFrame to a CSV file
        df.to_csv(file_name, mode="a", index=False, header=False)  # Set index=False to exclude row numbers in the CSV
    except Exception as e:    
        print(f"Append data into {file_name} failed: {e}")
    
# Select ALL the elements match with css_selector
def extract_elements_by_css_selector(css_selector, parent_element, catch_message:str=""):
    parent_element = parent_element if parent_element else driver
    elements = []
    try:
        if isinstance(css_selector, str):
            # print("elements_css_selector: "+css_selector)
            elements = parent_element.find_elements(by=By.CSS_SELECTOR, value=css_selector)
        else:
            # print("elements_css_selector: "+json.dumps(css_selector, indent=2))
            for cs in css_selector:
                elements.extend(parent_element.find_elements(by=By.CSS_SELECTOR, value=cs))
    except NoSuchElementException:            
        catch_message = catch_message if catch_message else f"Element [{css_selector}] in {parent_element}! NOT found"
        print(catch_message)
        return False
    else:
        return elements

# Select ONLY ONE element that match with css_selector
def extract_element_by_css_selector(css_selector, parent_element, catch_message:str=""):
    parent_element = parent_element if parent_element else driver    
    try:
        # print("element_css_selector: "+css_selector)
        element = parent_element.find_element(by=By.CSS_SELECTOR, value=css_selector)
    except NoSuchElementException:
        catch_message = catch_message if catch_message else f"Element [{css_selector}] in {parent_element}? NOT found"
        print(catch_message)
        return False
    else:
        return element
    
# Select ALL element's attributes that match with css_selector
def extract_elements_attributes_by_css_selector(css_selector, attribute, parent_element, catch_message:str=""):
    attribute = attribute if attribute else "href"
    elements = extract_elements_by_css_selector(css_selector, parent_element, catch_message)
    element_attributes = [element.get_attribute(attribute) for element in elements]
    # print("element_attributes: "+json.dumps(element_attributes,indent=2))
    return element_attributes

# Select element's text that match with css_selector
def extract_element_text_by_css_selector(css_selector, parent_element, catch_message:str=""):
    element = extract_element_by_css_selector(css_selector, parent_element, catch_message)
    return element.text
# -----------------------------------END:Global use functions-------------------------------------


# Used in Step1-Step4
# Read the first column ('Link' column) of csv file, then loop throughout the links and do some scrapping data action, 
# then finally store the scrapped data into another csv file
def get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(input_file_name, custom_scrap_data_action, output_file_name="output", output_file_columns=["Link"]):
    # Read links for scrap from csv file
    links = []    
    if not input_file_name:
        links.append("https://www.recommend.my/services/all-services");
    else:
        link_list_data = read_data_from_csv_file(input_file_name, "list")
        if not link_list_data:
            print("invalid csv file name: "+input_file_name)
            exit()
        links.extend(link_list_data["Link"])
    # END:Read links for scrap from csv file

    # Scrap data action
    meta_stop_at_data_file = read_data_from_csv_file("meta_stop_at_data_file")
    # stopped_index = meta_stop_at_data_file[0]["stopped_index"] if meta_stop_at_data_file else 0
    stopped_index = 0
    scrapped_data_list = []    
    for index, link in enumerate(links[stopped_index:]):
        try:
            driver.get(link)
            data = custom_scrap_data_action()
            if(isinstance(data, list)):
                scrapped_data_list.extend(data)
            elif(isinstance(data, dict)):
                scrapped_data_list.append(data)
            else:
                print(f"Invalid scrapped_data type, it should be a dict or list")
        except Exception as e:
            print(f"Extend scrapped data list exception: {e}")
            stopped_index += index
            break
        except KeyboardInterrupt:
            print(f"Keyboard Interrupt")
            stopped_index += index
            break
    # END: Scrap data action
    
    # Insert links/data scrapped from webite into csv file
    print(f"scrapped_data_list: {scrapped_data_list}")
    write_data_to_csv_file(scrapped_data_list, output_file_columns, output_file_name)
    meta_stop_at_data = {"file_name":[input_file_name], "stopped_index":[stopped_index], "stopped_url":[current_url]}
    print(f"meta_stop_at_data: {meta_stop_at_data}")
    write_data_to_csv_file(meta_stop_at_data, ["file_name","stopped_index","stopped_url"], "meta_stop_at_data_file")
    # END: Insert links/data scrapped from webite into csv file
# END: Used in Step1-Step4


# Step1
def scrap_links_step1():
    return scrap_links(css_selector="div.flickity-cell a", parent_element_css_selector="div.left-side-content")

# Step2
def scrap_links_step2():
    return scrap_links(css_selector=["a.card-overlay-link","div.col a.text-info"], parent_element_css_selector="div#jsSideContent")

# Used in Step1 & Step2
def scrap_links(css_selector, parent_element_css_selector):
    scrapped_link_list = []
    parent_element = extract_element_by_css_selector(parent_element_css_selector,"") if parent_element_css_selector else driver
    links = extract_elements_attributes_by_css_selector(css_selector, "href", parent_element)    
    scrapped_link_list.extend(links)
    return scrapped_link_list

# Step3 (Loop through all the pages of the vendors list)
def scrap_links_step3(): # def scrap_links_thru_all_vendor_list_pages():
    scrapped_link_list = []    
    while True:
        try:
            global current_url
            current_url = driver.current_url
            print(f"current_url: {current_url}")
            scrapped_link_list.extend(scrap_vendor_links_contain_contacts_action())

            # Navigate to next page (if have more than one page of vendors)
            pagination_parent_element = extract_element_by_css_selector("ul.pagination","")
            current_active_page = extract_element_text_by_css_selector("li.active", pagination_parent_element)
            next_page_btn_element = extract_element_by_css_selector("li.pagination-next a",pagination_parent_element)
            if not next_page_btn_element or not current_active_page or (next_page_btn_element.text == current_active_page):
                print("break")
                break
            driver.get(next_page_btn_element.get_attribute("href"))            
        except Exception as e:
            print(f"Extend scrapped data list exception: {e}")
            print(f"stopped at link: {current_url}")
            break
        except KeyboardInterrupt:
            print(f"Keyboard Interrupt")
            print(f"stopped at link: {current_url}")
            break

    # print(f"scrapped_link_list [scrap_links_step3]: {scrapped_link_list}")
    return scrapped_link_list

# Used in Step3
def scrap_vendor_links_contain_contacts_action(): # enhancement
    wa_btn_elements = extract_elements_by_css_selector("div.profile-card-action div.business-contact a.profile-card-wa", "")
    phone_btn_elements = extract_elements_by_css_selector("div.profile-card-action div.business-contact a.profile-card-phone", "")
    scrapped_link_list = []
    if len(wa_btn_elements) == len(phone_btn_elements):
        for wa_btn_element in wa_btn_elements:
            # parent_element = wa_btn_element.find_element_by_css_selector(':parent')
            profile_card_parent_element = wa_btn_element.find_element(By.XPATH, '../../..') #  CSS Selector: div.profile-card-bottom
            # print("profile_card_parent_element: "+str(profile_card_parent_element.get_attribute("class")))
            vendor_link = extract_elements_attributes_by_css_selector("div.profile-card-sbd div.profile-card-bd div.profile-card-top-left div.profile-card-top-left-tr a.profile-card-title", "href", profile_card_parent_element)
            scrapped_link_list.extend(vendor_link)
    # print(f"scrapped_link_list [scrap_vendor_links_contain_contacts_action_2]: {scrapped_link_list}")
    return scrapped_link_list
# END: Step3

# Step4 (wait the browser fetch all the script tag first, then scrap those script tag contains Malaysia contact number)
def scrap_data_step4(): # def scrap_vendor_name_and_contact_action():
    max_wait_time = 10 # Set the maximum time to wait for the scripts to be fetched (in seconds)

    try:
        # Wait for all scripts to be fetched using WebDriverWait and ExpectedConditions
        scripts_fetched = WebDriverWait(driver, max_wait_time).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'script'))
        )
    except TimeoutException:
        print('Timed out waiting for scripts to be fetched.')
        return {}
    else: 
        malaysia_contact_number_regex = r'(\+?6?01\d{8,9})'

        script_tag = driver.execute_script(
            f'return [...document.getElementsByTagName("script")].find(script => /{malaysia_contact_number_regex}/.test(script.textContent));'
        )

        if script_tag:
            # Extract the phone number from the script tag using the regex pattern
            contact_numbers = re.findall(malaysia_contact_number_regex, script_tag.get_attribute('outerHTML'))
        else:
            print("No Malaysia phone number found in the script tags.")

    provider_parent_element = extract_element_by_css_selector("div.provider div.provider__meta div.provider__title", "")
    vendor_name = extract_element_text_by_css_selector("h4.provider__name",parent_element=provider_parent_element)
    
    return {"Name":vendor_name, "Contact":contact_numbers[0]}
# END: Step4

def main():
    # Step1    
    # get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
    #     "",
    #     scrap_links_step1,
    #     "professional_categories_links"
    # )

    # Step2
    # get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
    #     "professional_categories_links",
    #     scrap_links_step2,
    #     "professionals_links"
    # )

    # # Step3
    get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
        "professionals_links",
        scrap_links_step3,
        "profile_vendors_links"
    )    

    # # Step4
    # get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
    #     "profile_vendors_links",
    #     scrap_data_step4,
    #     "vendors_name_contact",
    #     ["Name", "Contact"]
    # )

if __name__ == "__main__":
    main()