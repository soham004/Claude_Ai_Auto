from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from modules.automation_parts import (
    handle_login, 
    random_sleep, 
    random_scroll, 
    slow_type,
    save_cookies
)
import json


with open("config.json", "r") as f:
    config = json.load(f)
def claude_automation():
    # Initialize the driver directly using the Driver class
    driver = Driver(uc=True, headless=False)
    
    try:
        # Configure the browser
        driver.maximize_window()
        
        # Handle login using the modularized function
        driver = handle_login(driver)
        
        # Random human-like behavior
        random_scroll(driver)
        
        
        driver.get(config["project_link"])
        driver.click('div[aria-label="Write your prompt to Claude"]')
        actions = ActionChains(driver)
        for char in 'Create a video outline for Video #5. Refer to the Characters in the Project Knowledge. Ensure the chat name is named after the Video # that I just input. Here is the format "Video #x : Title Here"':
            actions.send_keys(char)
            actions.perform()
            random_sleep(0.05, 0.08)
        # driver.send_keys('div[aria-label="Write your prompt to Claude"]', 'Create a video outline for Video #5. Refer to the Characters in the Project Knowledge. Ensure the chat name is named after the Video # that I just input. Here is the format "Video #x : Title Here"')
        actions.send_keys(Keys.RETURN).perform()

        input("Press Enter to close the browser...")
    
    finally:
        save_cookies(driver)
        print("Cookies saved successfully.")
        driver.quit()

if __name__ == "__main__":
    claude_automation()