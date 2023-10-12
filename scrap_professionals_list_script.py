import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

driver = webdriver.Chrome()

driver.get(f"https://www.recommend.my/services/all-services")

# To get all the professionals category links (STEP 1)
prof_category_parent_element = driver.find_element(by=By.CSS_SELECTOR, value="div.left-side-content")
try:
    prof_category_link_elements = prof_category_parent_element.find_elements(by=By.CSS_SELECTOR, value="div.flickity-cell a")
    prof_category_links = []
    for prof_category_link_element in prof_category_link_elements:
        prof_category_links.append(prof_category_link_element.get_attribute('href'))

    for index, prof_category_link in enumerate(prof_category_links):
        print(f"prof_category_link_{index}: {prof_category_link}")
        driver.get(f"{prof_category_link}")
        time.sleep(2)
        print("slept 2 seconds")
        
except NoSuchElementException:
    print("No professional/services link found with card overlay")

# To get all the professionals links (STEP 2)
# prof_parent_element = driver.find_element(by=By.CSS_SELECTOR, value="div#jsSideContent")
# try:
#     for prof_link_element in prof_parent_element.find_elements(by=By.CSS_SELECTOR, value="a.card-overlay-link"):            
#         prof_link = prof_link_element.get_attribute('href')
#         print("prof_link: "+prof_link)
#         print('-------------------------------------------------divider 1 line------------------------------------------------')
# except NoSuchElementException:
#     print("No professional/services link found with card overlay")

# try:
#     for prof_link_wo_card_overlay_element in prof_parent_element.find_elements(by=By.CSS_SELECTOR, value="div.col a.text-info"):
#         prof_link = prof_link_wo_card_overlay_element.get_attribute('href')
#         print("prof_link: "+prof_link)
#         print('-------------------------------------------------divider 2 line------------------------------------------------')
# except NoSuchElementException:
#     print("No professional/services link found withOUT card overlay")

driver.quit()