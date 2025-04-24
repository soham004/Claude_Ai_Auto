import pickle
import os
import time
import random
from seleniumbase import Driver
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def clean_file_name(file_name:str)->str:
    """Clean the file name by removing special characters"""
    return "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def click_element(driver:webdriver.Chrome,element):
    """Click on the element"""
    ActionChains(driver).move_to_element(element).click().perform()


def js_click_element(driver:webdriver.Chrome, element):
    """Click on the element using JavaScript"""
    driver.execute_script("arguments[0].click();", element)


def load_cookies(account:str)->dict:
    """Load cookies from file"""
    cookie_file_path = os.path.join("accounts", account, "claude_cookies.pkl")
    if os.path.exists(cookie_file_path):
        with open(cookie_file_path, "rb") as f:
            return pickle.load(f)
    return None


def save_cookies(driver, account):
    """Save cookies to file"""
    all_cookies = driver.get_cookies()
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in all_cookies 
                if ".claude.ai" in cookie.get("domain", "")}
    cookie_file_path = os.path.join("accounts", account, "claude_cookies.pkl")
    with open(cookie_file_path, "wb") as f:
        pickle.dump(cookie_dict, f)
    print("Cookies saved successfully")


def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time between min and max seconds"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def check_limit_reached(driver:webdriver.Chrome)->bool:
    try:
        main_side = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[1]')
    except Exception as e:
        try:
            main_side = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/main/div[1]')
        except Exception as e:
            print("Error finding element for limit check:", e)
            return False
    main_side_html = main_side.get_attribute('innerHTML')
    if "limit reached" in main_side_html:
        return True
    return False

def handle_login(driver:webdriver.Chrome, account:str):
    """Handle the login process for Claude.ai"""
    # Navigate to Claude.ai
    driver.get("about:blank")  # Start with blank page
    random_sleep(0.5, 1.5)
    
   
    cookies = load_cookies(account)  # Try to load cookies if they exist
    if cookies:
        print("Cookies found, attempting to log in...")
        driver.get("https://claude.ai")
        random_sleep(1, 2)
    
        # Add cookies
        print("Adding cookies...")
        for name, value in cookies.items():
            driver.add_cookie({"name": name, "value": value, "domain": ".claude.ai"})
        
        # Navigate to chats page
        random_sleep(0.5, 1)
        driver.get("https://claude.ai/projects")
        random_sleep(4, 5)
        
        # Check if we need to log in again
        current_url = driver.current_url
        # print(f"Current URL: {current_url}")
        
        if "login" in current_url:
            print("Cookies expired or invalid, please log in manually")
            driver.get("https://claude.ai")
            input("Press Enter after you've logged in...")
            save_cookies(driver, account)
    else:
        print("No cookies found, please log in manually")
        # First time login
        driver.get("https://claude.ai")
        
        # Check for Cloudflare challenge
        try:
            if driver.find_element("iframe[src*='cloudflare']","css selector"):
                print("⚠️ Cloudflare challenge detected! Please solve it manually.")
                input("Press Enter after solving the Cloudflare challenge...")
        except:
            pass
        
        input("Please log in manually and press Enter when done...")
        save_cookies(driver, account)


def random_scroll(driver):
    """Perform random scrolling to appear more human-like"""
    for _ in range(random.randint(1, 3)):
        scroll_amount = random.randint(100, 300)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        random_sleep(0.3, 0.7)


def download_artifacts(driver:webdriver.Chrome, video_number:str, account:str):
    artifact_buttons = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "artifact-block-cell ")]/parent::button[@aria-label="Preview contents"]'))
    )
    for i, artifact_button in enumerate(artifact_buttons):
        try:
            chapter_name = artifact_button.find_element(By.XPATH, './/child::div[contains(@class, "leading-tight")]').text
            print(f"Downloading artifact for chapter: {chapter_name}")
        except Exception as e:
            print(f"Error finding chapter name")
            chapter_name = f"Chapter {i+1}"
            print(f"Using chapter name:", chapter_name)
        js_click_element(driver, artifact_button)
        random_sleep(0.5, 1.5)
        # Wait for the download button to appear
        try:
            chapter_title = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="markdown-artifact"]//h1'))
            ).text
        except TimeoutException:
            print("Chapter title not found! Using chapter name instead.")
            chapter_title = chapter_name
            continue
        artifact_section_paragraphs = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@id="markdown-artifact"]//p'))
        )
        complete_text = ""
        for paragraph in artifact_section_paragraphs:
            complete_text += paragraph.text + "\n"

        
        output_dir = os.path.join("outputFiles", account, f"Video_{video_number}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(os.path.join(output_dir, f"{clean_file_name(chapter_title)}.txt"), "w", encoding="utf-8") as f:
            f.write(complete_text)
        print(f"Artifact for chapter '{chapter_title}' downloaded successfully.")


def enter_prompt(driver:webdriver.Chrome, prompt:str):
    try:
        # Wait for the input field to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Write your prompt to Claude"]'))
        ).click()
    except TimeoutException:
        print("Input field not found!")
        return
    actions = ActionChains(driver)
    for char in prompt:
        actions.send_keys(char)
        actions.perform()
        random_sleep(0.02, 0.05)
    actions.send_keys(Keys.RETURN).perform()

def wait_for_response(driver:webdriver.Chrome):
    while True:
        try:
            print("Waiting for response to start...")
            response = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Stop response"]'))
            )
            print("Response started.")
            break
        except:
            pass
        random_sleep(0.5, 1.5)

    while True:
        try:
            response = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Stop response"]'))
            )
        except TimeoutException:
            print("Response finished.")
            break
            
        random_sleep(0.5, 1.5)
    
