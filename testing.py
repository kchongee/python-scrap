import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

# Configuration (Selenium)
driver = webdriver.Chrome()


def read_data_from_csv_file(file_name, format='records'):  
    format = "records" if format=="dict" else format
    if format=="records" or format=="list":
        df = pd.read_csv(file_name+".csv")
        data = df.to_dict(format)
        return data
    else:
        return False

def write_data_to_csv_file(data, file_name):    
    df = pd.DataFrame(data)
    # Export the DataFrame to a CSV file
    df.to_csv(file_name+".csv", index=False)  # Set index=False to exclude row numbers in the CSV


def extract_element_by_css_selector(css_selector:str, parent_element:WebElement, catch_message:str=""):
    parent_element = parent_element if parent_element else driver
    try:
        elements = parent_element.find_elements(by=By.CSS_SELECTOR, value=css_selector)
    except NoSuchElementException:            
        catch_message = catch_message if catch_message else f"Element [{css_selector}] in {parent_element} NOT found"
        print(catch_message)
        return False
    else:
        return elements
    
def extract_element_attributes_by_css_selector(css_selector:str, attribute:str, parent_element: WebElement, catch_message: str):
    attribute = attribute if attribute else "href"
    elements = extract_element_by_css_selector(css_selector, parent_element, catch_message)
    element_attributes = [element.get_attribute(attribute) for element in elements]
    return element_attributes


driver.get("https://www.recommend.my/services/all-services");
elements = extract_element_by_css_selector("div.left-side-content",driver)
print(type(elements[0]))