import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

driver.get(f"https://www.recommend.my/businesses/wasi-developers")

# To get the vendor profile contact (STEP 4)

# Set the maximum time to wait for the scripts to be fetched (in seconds)
max_wait_time = 10

try:
    # Wait for all scripts to be fetched using WebDriverWait and ExpectedConditions
    scripts_fetched = WebDriverWait(driver, max_wait_time).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, 'script'))
    )
    print(f'All scripts fetched successfully. Total scripts found: {len(scripts_fetched)}')
except TimeoutException:
    print('Timed out waiting for scripts to be fetched.')
else: 
    malaysia_phone_number_regex = r'(\+?6?01\d{8,9})'

    script_tag = driver.execute_script(
        f'return [...document.getElementsByTagName("script")].find(script => /{malaysia_phone_number_regex}/.test(script.textContent));'
    )    

    if script_tag:
        # Extract the phone number from the script tag using the regex pattern
        phone_numbers = re.findall(malaysia_phone_number_regex, script_tag.get_attribute('outerHTML'))
        print("Malaysia phone numbers found in the script tag:")
        for phone_number in phone_numbers:
            print(f"phone_number: {phone_number}")
    else:
        print("No Malaysia phone number found in the script tags.")

# Close the browser
driver.quit()

print('-------------------------------------------------divider line------------------------------------------------')


driver.quit()