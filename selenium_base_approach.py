from seleniumbase import Driver
from modules.automation_parts import (
    handle_login, 
    random_sleep, 
    random_scroll, 
    slow_type
)
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
        
        
        driver.get("https://claude.ai/projects")
        # Wait for user to close
        input("Press Enter to close the browser...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    claude_automation()