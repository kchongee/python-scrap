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
default_link = "https://www.recommend.my/services/all-services"
malaysia_contact_number_regex = r'(\+?6?01\d{8,9})'
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
def extract_elements_by_css_selector(css_selector:list, parent_element, catch_message:str=""):
    parent_element = parent_element if parent_element else driver
    elements = []
    try:
        # if isinstance(css_selector, str):
        #     # print("elements_css_selector: "+css_selector)
        #     elements = parent_element.find_elements(by=By.CSS_SELECTOR, value=css_selector)
        # else:
        #     # print("elements_css_selector: "+json.dumps(css_selector, indent=2))
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

# Select the data that fulfill regex pattern in html elements fulfill the css_selector
def extract_data_fulfill_regex_in_element(css_selector, regex):
    script_tag = driver.execute_script(
        f'return [...document.querySelector("{css_selector}")].find(script => /{regex}/.test(script.textContent));'
    )
    if script_tag:
        data = re.findall(regex, script_tag.get_attribute('outerHTML'))[0] # Extract the first data that fulfill the regex pattern
    else:
        print(f"{regex} not found in any script tags")
        return False
    return data

# def repeat_navigate_and_scrape(web_scrapper, links, web_scrapper_action, element_css_selector):
#     scrapped_data = []
#     for link in links:
#         web_scrapper.navigate_to_page(link)
#         scrapped_data.extend(getattr(web_scrapper, web_scrapper_action)(element_css_selector))
#     return scrapped_data   
# -----------------------------------END: Global use functions-------------------------------------


# Used in Step1-Step4
# Read the first column ('Link' column) of csv file, then loop throughout the links and do some scrapping data action, 
# then finally store the scrapped data into another csv file
def get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(read_file_name, custom_scrap_data_action, write_file_name="output", output_file_columns=["Link"]):
    print(f"-"*25)
    # Read links for scrap from csv file
    links = []
    if not read_file_name:
        links.append(default_link);
    else:
        link_list_data = read_data_from_csv_file(read_file_name, "list")
        if not link_list_data:
            print("invalid csv file name: "+read_file_name)
            exit()
        links.extend(link_list_data["Link"])
    print(f"Finish reading csv file and get the links from: {read_file_name}")
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
    print(f"Finish scrap all the data")
    # END: Scrap data action
    
    # Insert links/data scrapped from webite into csv file
    print(f"scrapped_data_list: {scrapped_data_list}")
    write_data_to_csv_file(scrapped_data_list, output_file_columns, write_file_name)
    # meta_stop_at_data = {"file_name":[read_file_name], "stopped_index":[stopped_index], "stopped_url":[current_url]}
    # print(f"meta_stop_at_data: {meta_stop_at_data}")
    # write_data_to_csv_file(meta_stop_at_data, ["file_name","stopped_index","stopped_url"], "meta_stop_at_data_file")
    print(f"Finish write the data into csv file: {write_file_name}")
    # END: Insert links/data scrapped from webite into csv file
    print(f"-"*25)
# END: Used in Step1-Step4


# Step1 - scrap professionals categories links
# def scrap_links_step1():
    # return scrap_links(css_selector="div.flickity-cell a", parent_element_css_selector="div.left-side-content")

# Step2 - scrap professionals links
# def scrap_links_step2():
#     return scrap_links(css_selector=["a.card-overlay-link","div.col a.text-info"], parent_element_css_selector="div#jsSideContent")

# Used in Step1 & Step2
def scrap_links(css_selector, parent_element_css_selector):
    scrapped_link_list = []
    parent_element = extract_element_by_css_selector(parent_element_css_selector,"") if parent_element_css_selector else driver
    links = extract_elements_attributes_by_css_selector(css_selector, "href", parent_element)    
    scrapped_link_list.extend(links)
    return scrapped_link_list


# Step3 - scrap vendors profile links (Loop through all the pages of the vendors list)
def scrap_links_step3():
    scrapped_link_list = []    
    while True:
        try:
            # Step a (STOP HERE)
            global current_url
            current_url = driver.current_url
            print(f"current_url: {current_url}")
            scrapped_link_list.extend(scrap_vendor_links_contain_contacts_action())

            # Step b
            # Navigate to next page (if have more than one page of vendors)
            pagination_parent_element = extract_element_by_css_selector("ul.pagination","")
            current_active_page = extract_element_text_by_css_selector("li.active", pagination_parent_element)
            next_page_btn_element = extract_element_by_css_selector("li.pagination-next a",pagination_parent_element)
            if not next_page_btn_element or not current_active_page or (next_page_btn_element.text == current_active_page):
                print("break")
                break
            driver.get(next_page_btn_element.get_attribute("href"))
            # END: Navigate to next page (if have more than one page of vendors)
        except Exception as e:
            print(f"Extend scrapped data list exception: {e}")
            print(f"stopped at link: {current_url}")
            break
        except KeyboardInterrupt:
            print(f"Keyboard Interrupt")
            print(f"stopped at link: {current_url}")
            break

    return scrapped_link_list

# Used in Step3
def scrap_vendor_links_contain_contacts_action(): # enhancement
    # (STOP HERE)
    # if empty:
    #     no need check
    # else:
    #     check
    css_selector_whatsapp_btn = "div.profile-card-action div.business-contact a.profile-card-wa"
    css_selector_phone_btn = "div.profile-card-action div.business-contact a.profile-card-phone"
    xpath_btn_parent_element = "../../.." # To get the grand-parent element of the button element (../.. refers to parent element) 

    css_selector_vendor_title_link = "div.profile-card-sbd div.profile-card-bd div.profile-card-top-left div.profile-card-top-left-tr a.profile-card-title"
    link_attribute = "href"

    wa_btn_elements = extract_elements_by_css_selector(css_selector_whatsapp_btn, "")
    phone_btn_elements = extract_elements_by_css_selector(css_selector_phone_btn, "")
    btn_elements = wa_btn_elements if wa_btn_elements else phone_btn_elements
    scrapped_link_list = []
    for btn_element in btn_elements:
        profile_card_parent_element = btn_element.find_element(By.XPATH, xpath_btn_parent_element) #  CSS Selector: div.profile-card-bottom
        vendor_link = extract_elements_attributes_by_css_selector(css_selector_vendor_title_link, link_attribute, profile_card_parent_element)
        scrapped_link_list.extend(vendor_link)
    return scrapped_link_list
# END: Step3

# Step4 - scrap verndor name & contact data (wait the browser fetch all the script tag first, then scrap those script tag contains Malaysia contact number)
def scrap_data_step4():
    css_selector_script_tag = "script"
    malaysia_contact_number_regex = r'(\+?6?01\d{8,9})'
    parent_css_selector_for_vendor_name = "div.provider div.provider__meta div.provider__title"
    css_selector_for_vendor_name = "h4.provider__name"

    contact_number = extract_data_fulfill_regex_in_element(css_selector_script_tag, malaysia_contact_number_regex)
    if not contact_number:
        print("Not found any malaysia contact number")
        exit

    provider_parent_element = extract_element_by_css_selector(parent_css_selector_for_vendor_name, "")
    vendor_name = extract_element_text_by_css_selector(css_selector_for_vendor_name, parent_element=provider_parent_element)
    
    # (STOP HERE - change the data return based on the output file based)
    return_data = {"Name":vendor_name, "Contact":contact_number}
    print(f"return data: {return_data}")
    return return_data
# END: Step4

def main():
    # Step1
    read_csv_file_name = "" # Read all the links in a csv file from previous step to scrap the desired data from it, if its empty then only go to default_link(specified at global variables)
    target_elements_css_selector = ["div.flickity-cell a"] # Scrap for target element
    target_parent_element_css_selector = "div.left-side-content" # To ensure the target element under this element
    def scrap_data(): return scrap_links(target_elements_css_selector, target_parent_element_css_selector) # To scrap all the links ("href" attribute) from the target element
    # scrap_data = scrap_links(target_elements_css_selector, target_parent_element_css_selector)
    write_csv_file_name = "professional_categories_links" # Write the data into csv file
    
    get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
        read_csv_file_name,
        scrap_data,
        write_csv_file_name
    )
    
    # Step2
    read_csv_file_name = "professional_categories_links" # Read all the links in this csv file from previous step to scrap the desired data from it, if its empty then only go to default_link(specified at global variables)
    target_elements_css_selector = ["a.card-overlay-link","div.col a.text-info"] # Scrap for target elements
    target_parent_element_css_selector = "div#jsSideContent" # To ensure the target element under this element
    def scrap_data(): return scrap_links(target_elements_css_selector, target_parent_element_css_selector) # To scrap all the links ("href" attribute) from the target element
    write_csv_file_name = "professionals_links" # Write the data into this csv file
    get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
        read_csv_file_name,
        scrap_data,
        write_csv_file_name
    )

    # Step3
    read_csv_file_name = "professionals_links" # Read all the links in a csv file from previous step to scrap the desired data from it, if its empty then only go to default_link(specified at global variables)
    target_elements_css_selector = ["a.card-overlay-link","div.col a.text-info"] # Scrap for target elements
    target_parent_element_css_selector = "div#jsSideContent" # To ensure the target element under this element
    def scrap_data(): return scrap_links(target_elements_css_selector, target_parent_element_css_selector) # To scrap all the links ("href" attribute) from the target element
    write_csv_file_name = "profile_vendors_links" # Write the data into csv file
    get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
        read_csv_file_name,
        scrap_data,
        write_csv_file_name
    )

    # Step4
    # read_csv_file_name = "professional_categories_links" # Read all the links in a csv file from previous step to scrap the desired data from it, if its empty then only go to default_link(specified at global variables)
    # target_elements_css_selector = ["a.card-overlay-link","div.col a.text-info"] # Scrap for target elements
    # target_parent_element_css_selector = "div#jsSideContent" # To ensure the target element under this element
    # def scrap_data(): return scrap_links(target_elements_css_selector, target_parent_element_css_selector) # To scrap all the links ("href" attribute) from the target element
    # write_csv_file_name = "professionals_links" # Write the data into csv file
    # write_csv_columns = ["Link"] # Specified the header of csv file column
    # get_link_from_file_thn_custom_scrap_data_action_thn_store_to_file(
    #     "profile_vendors_links",
    #     scrap_data_step4,
    #     "vendors_name_contact",
    #     ["Name", "Contact"]
    # )

if __name__ == "__main__":
    main()