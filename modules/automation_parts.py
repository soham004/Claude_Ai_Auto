import pickle
import os
import time
import random
import traceback
from typing import Optional
import pyperclip
import sys
import msvcrt  
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='automation.log', filemode='a')


def clean_file_name(file_name:str)->str:
    """Clean the file name by removing special characters"""
    return "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def click_element(driver:webdriver.Chrome,element):
    """Click on the element"""
    ActionChains(driver).move_to_element(element).click().perform()


def js_click_element(driver:webdriver.Chrome, element):
    """Click on the element using JavaScript"""
    driver.execute_script("arguments[0].click();", element)


def load_cookies(account:str)->Optional[dict]:
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


def random_sleep(min_seconds=1.0, max_seconds=3.0):
    """Sleep for a random amount of time between min and max seconds"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def check_limit_reached(driver:webdriver.Chrome)->bool:
    try:
        driver.find_element(By.XPATH, '//div[contains(text(), "limit reached")]')
        return True
    except Exception as e:
        return False
def get_reactivation_time(driver:webdriver.Chrome)->Optional[str]:
    try:
        reactivation_time_element = driver.find_element(By.XPATH, '//div[contains(text(), "limit reached")]/span')
        reactivation_time = reactivation_time_element.text
        print(f"Reactivation time: {reactivation_time}")
        return reactivation_time
    except Exception as e:
        print("Error getting reactivation time:", e)
        logging.error(f"Error getting reactivation time: {traceback.format_exc()}")
        return None

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
    video_name = ""
    for i, artifact_button in enumerate(artifact_buttons):
        try:
            chapter_name = artifact_button.find_element(By.XPATH, './/child::div[contains(@class, "leading-tight")]').text
            print(f"Downloading artifact for chapter: {chapter_name}")
            if "chapter " not in chapter_name.lower()[:15]:
                raise Exception("Chapter name not found")
        except Exception as e:
            try:
                chapter_title = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@id="markdown-artifact"]//h1'))
                ).text
                if "chapter " not in chapter_title.lower()[:15]:
                    raise Exception("Chapter name not found")
                chapter_name = chapter_title
            except Exception as e: 
                print(f"Error finding chapter name")
                chapter_name = f"Chapter {i+1}"
                print(f"Using chapter name:", chapter_name)

        ActionChains(driver).scroll_to_element(artifact_button).perform()
        js_click_element(driver, artifact_button)
        random_sleep(0.5, 1.5)

        complete_text = ""
        try:
            copy_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(),"Copy")]/parent::div/parent::button')))
            pyperclip.copy("")  # Clear clipboard before copying
            click_element(driver, copy_button)
            random_sleep(0.5, 1.5)
            random_sleep(0.5, 1.5)
            # Get the copied text from clipboard
            complete_text = pyperclip.paste()
            logging.info(f"Used copy button to get complete text for chapter: {chapter_name}")
        except TimeoutException:
            try:
                complete_text = ""
                artifact_section_paragraphs = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@id="markdown-artifact"]//p')))
                for paragraph in artifact_section_paragraphs:
                    complete_text += paragraph.text + "\n"
                logging.info(f"Used paragraphs to get complete text for chapter: {chapter_name}")

            except Exception as e:
                print("Error finding artifact section paragraphs:", e)
                logging.error(f"Error finding artifact section paragraphs: {traceback.format_exc()}")

        if video_name == "":
            try:
                video_name_element = driver.find_element(By.XPATH, '//button[@data-testid="chat-menu-trigger"]/div/div')
                video_name = video_name_element.text
                video_name = clean_file_name(video_name)
                video_name = video_name + f"_{video_number}"
            except Exception as e:
                print("Error finding video name element:", e)
                video_name = f"Video_{video_number}"
            
            print(f"Using {video_name} as video name")
        
        output_dir = os.path.join("outputFiles", account, video_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(os.path.join(output_dir, f"{clean_file_name(chapter_name)}.txt"), "w", encoding="utf-8") as f:
            f.write(complete_text)
        print(f"Artifact for chapter '{chapter_name}' downloaded successfully.")
    
    # After all artifacts are downloaded, rename them based on modification time
    output_dir = os.path.join("outputFiles", account, video_name)
    files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.txt')]
    
    # Sort files by modification time
    files.sort(key=os.path.getmtime)
    
    for i, file_path in enumerate(files, 1):
        new_name = os.path.join(output_dir, f"Chapter-{i}.txt")
        os.rename(file_path, new_name)
        print(f"Renamed {os.path.basename(file_path)} to Chapter-{i}.txt")


def enter_prompt(driver:webdriver.Chrome, prompt:str):
    actions = ActionChains(driver)
    try:
        # Wait for the input field to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Write your prompt to Claude"]'))
        ).click()
    except TimeoutException:
        print("Input field not found!")
        return
    for char in prompt:
        actions.send_keys(char)
        actions.perform()
        random_sleep(0.02, 0.05)
    while True:
        try:
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send message"]')))
            break
        except TimeoutException:
            if check_limit_reached(driver):
                limit_reached_seq(driver)
                break
            else:
                print("Send button not found!")

    actions.send_keys(Keys.RETURN).perform()
    random_sleep(1, 1.5)


def wait_for_input(timeout):
    """Waits for Enter key press with a timeout while displaying a countdown (Windows version)."""
    start_time = time.time()
    while True:
        remaining_time = timeout - (time.time() - start_time)
        if remaining_time <= 0:
            print("\nTime's up!.")
            return False  # Timeout reached
        mins, secs = divmod(remaining_time, 60)
        hours, mins = divmod(mins, 60)
        sys.stdout.write("\rTime left: {:02d}:{:02d}:{:02d} Press Enter to resume Now... ".format(int(hours), int(mins), int(secs)))
        sys.stdout.flush()

        # Check if a key was pressed
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter key is detected
                print("\nUser pressed Enter!")
                return True  # Input received

        time.sleep(0.1)  # Reduce CPU usage


def sleep_until_time(time_str:str):
    
    import datetime
    import time
    
    # Parse the time string
    try:
        target_time = datetime.datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        print(f"Error: Could not parse time string '{time_str}'. Expected format like '1:30 AM'")
        logging.error(traceback.format_exc())
        return
    
    # Get current time
    now = datetime.datetime.now()
    
    # Create target datetime (combines today's date with target time)
    target_datetime = datetime.datetime.combine(now.date(), target_time)
    
    # If target time has already passed today, set it for tomorrow
    if target_datetime < now:
        target_datetime += datetime.timedelta(days=1)
    
    # Calculate seconds until target time
    seconds_to_wait = (target_datetime - now).total_seconds()
    seconds_to_wait += 10*60  # Add 10 minutes buffer
    
    print(f"Waiting until {time_str} ({seconds_to_wait:.0f} seconds from now)")
    
    # Using your existing wait_for_input function which shows a countdown
    # and allows user to skip by pressing Enter
    return wait_for_input(seconds_to_wait)


def limit_reached_seq(driver:webdriver.Chrome):
    reactivation_time = get_reactivation_time(driver)
    if reactivation_time == None:
        print("Limit reached! waiting for 5 hours 10 mins...")
        wait_for_input(5*60*60 + 10*60)  # Wait for 5 hours 10 minutes
    else:
        sleep_until_time(reactivation_time)
    driver.get(driver.current_url)
    ActionChains(driver).send_keys(Keys.RETURN).perform()

def wait_for_response(driver:webdriver.Chrome):
    current_time = time.time()
    while True:
        if time.time() - current_time > 900:
            print("Waiting for response timed out after 15 minutes.")
            return
        try:
            print("Waiting for response to start...")
            response = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Stop response"]')))
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

