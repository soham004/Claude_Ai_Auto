import pickle
import os
import time
import random
from seleniumbase import Driver

def load_cookies():
    """Load cookies from file"""
    if os.path.exists("claude_cookies.pkl"):
        with open("claude_cookies.pkl", "rb") as f:
            return pickle.load(f)
    return None

def save_cookies(driver:Driver):
    """Save cookies to file"""
    all_cookies = driver.get_cookies()
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in all_cookies 
                if ".claude.ai" in cookie.get("domain", "")}
    with open("claude_cookies.pkl", "wb") as f:
        pickle.dump(cookie_dict, f)
    print("Cookies saved successfully")

def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time between min and max seconds"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def handle_login(driver:Driver):
    """Handle the login process for Claude.ai"""
    # Navigate to Claude.ai
    driver.get("about:blank")  # Start with blank page
    random_sleep(0.5, 1.5)
    
   
    cookies = load_cookies()  # Try to load cookies if they exist
    if cookies:
        driver.get("https://claude.ai")
        random_sleep(1, 2)
        
        # Add cookies
        for name, value in cookies.items():
            driver.add_cookie({"name": name, "value": value, "domain": ".claude.ai"})
        
        # Navigate to chats page
        random_sleep(0.5, 1)
        driver.get("https://claude.ai/projects")
        random_sleep(2, 3)
        
        # Check if we need to log in again
        if "Log in" in driver.page_source:
            print("Cookies expired or invalid, please log in manually")
            driver.get("https://claude.ai")
            input("Press Enter after you've logged in...")
            save_cookies(driver)
    else:
        # First time login
        driver.get("https://claude.ai")
        
        # Check for Cloudflare challenge
        try:
            if driver.find_element("css selector", "iframe[src*='cloudflare']"):
                print("⚠️ Cloudflare challenge detected! Please solve it manually.")
                input("Press Enter after solving the Cloudflare challenge...")
        except:
            pass
        
        input("Please log in manually and press Enter when done...")
        save_cookies(driver)
    
    return driver

def random_scroll(driver:Driver):
    """Perform random scrolling to appear more human-like"""
    for _ in range(random.randint(1, 3)):
        scroll_amount = random.randint(100, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        random_sleep(0.3, 0.7)

def slow_type(driver:Driver, element, text):
    """Type text with random delays between keystrokes"""
    element.click()
    
    for char in text:
        driver.execute_script(
            'arguments[0].value = arguments[0].value + arguments[1];',
            element, char
        )
        random_sleep(0.05, 0.2)