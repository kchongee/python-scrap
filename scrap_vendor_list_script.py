from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

driver = webdriver.Chrome()

driver.get(f"https://www.recommend.my/professionals/air-conditioning")
 
# To get all the vendor profile links (STEP 3)
for parent_element in driver.find_elements(by=By.CSS_SELECTOR, value="div.list-card-lists div.card.list-card div.card-body div.profile-card-bottom"):
    is_wa_btn_exist = False
    is_phone_btn_exist = False

    try:
        # Attempt to find the child element within the parent element
        wa_btn_element = parent_element.find_element(by=By.CSS_SELECTOR, value='div.profile-card-action div.business-contact a.profile-card-wa')
        print("Whatsapp btn element found within the parent element.")
    except NoSuchElementException:
        print("Whatsapp btn element NOT found within the parent element.")
    else:
        is_wa_btn_exist = True
        wa_link = wa_btn_element.get_attribute('href')
        print("wa_link: "+wa_link)

    if not is_wa_btn_exist:
        try:
            # Attempt to find the child element within the parent element
            phone_btn_element = parent_element.find_element(by=By.CSS_SELECTOR, value='div.profile-card-action div.business-contact a.profile-card-phone')
            print("Phone element found within the parent element.")
        except NoSuchElementException:
            print("Phone btn element NOT found within the parent element.")
        else:
            is_phone_btn_exist = True

    if is_wa_btn_exist or is_phone_btn_exist:
        try:
            vendor_name_element = parent_element.find_element(by=By.CSS_SELECTOR, value='div.profile-card-sbd div.profile-card-bd div.profile-card-top-left div.profile-card-top-left-tr a.profile-card-title')
        except NoSuchElementException:
            print("Vendor name element NOT found within the parent element.")
        else:
            vendor_name = vendor_name_element.text
            vendor_link = vendor_name_element.get_attribute('href')
            print("vendor name: "+vendor_name)
            print("vendor link: "+vendor_link)

    print('-------------------------------------------------divider line------------------------------------------------')

def try_extract_by_css_selector(css_selector, parent_element, catch_message):
    parent_element = parent_element if parent_element else driver
    try:
        element = parent_element.find_element(by=By.CSS_SELECTOR, value=css_selector)
    except NoSuchElementException:            
        catch_message = catch_message if catch_message else f"Element [{css_selector}] in {parent_element} NOT found"
        print(catch_message)
        return False
    else:
        return element

driver.quit()