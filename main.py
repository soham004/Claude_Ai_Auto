from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sys
import msvcrt
from modules.automation_parts import *
import json


def sleep_until_time(time_str):
    """
    Sleep until the specified time. If the time has already passed today,
    assume it's for tomorrow.
    
    Args:
        time_str: String in format "1:30 AM" or similar
    """
    import datetime
    import time
    
    # Parse the time string
    try:
        target_time = datetime.datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        print(f"Error: Could not parse time string '{time_str}'. Expected format like '1:30 AM'")
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
        sys.stdout.write("\rTime left: {:02d}:{:02d}:{:02d} Press Enter to resume Now... ".format(int(hours), int(mins), int(secs)) )
        sys.stdout.flush()

        # Check if a key was pressed
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter key is detected
                print("\nUser pressed Enter!")
                return True  # Input received

        time.sleep(0.1)  # Reduce CPU usage


def select_account():
    accounts = [f for f in os.listdir("accounts") if os.path.isdir(os.path.join("accounts", f))]
    if not accounts:
        print("No accounts found in the 'accounts' directory.")
        return None
    print("Available accounts:")
    for i, account in enumerate(accounts):
        print(f"{i + 1}. {account}")
    choice = input("Select an account (1-{}): ".format(len(accounts)))
    if choice.isdigit() and 1 <= int(choice) <= len(accounts):
        return accounts[int(choice) - 1]


def claude_automation():
    continue_generation = True

    account = select_account()

    driver = Driver(uc=True, headless=False)
    driver.maximize_window()

    handle_login(driver, account)

    random_scroll(driver)
    try:
        while continue_generation:
            config_path = os.path.join("accounts", account, "config.json")
            if not os.path.exists(config_path):
                print(f"Config file not found for account {account}.")
                continue_generation = False
                break
            
            with open(config_path, "r") as f:
                config = json.load(f)
                try:
                    config["project_link"]
                    config["initial_prompt"]
                    config["generation_prompts"]
                    config["text_to_be_replaced_by_video_number"]
                    config["video_numbers"]
                except KeyError as e:
                    print(f"Missing key in config file for account {account}: {e}")
                    continue_generation = False
                    break
            
            try:
                video_numbers = config["video_numbers"]
                if len(video_numbers) == 0:
                    raise ValueError("No video numbers provided in the config file.")
                continue_generation = False
            except Exception as e:
                video_numbers = []
                video_number_initial = input("Enter the video number: ")
                video_numbers.append(video_number_initial)        
            
            try:
                for video_number in video_numbers:
                    driver.get(config["project_link"])

                    text_to_be_replaced = config["text_to_be_replaced_by_video_number"]
                    initial_prompt = config["initial_prompt"]

                    if text_to_be_replaced in initial_prompt:
                        initial_prompt = initial_prompt.replace(text_to_be_replaced, video_number)
                    else:
                        print(f"Warning: '{text_to_be_replaced}' not found in the initial prompt.")
                        input("Press Enter to continue...")
                    
                    
                    
                    print(f"Entering Initial Prompt: {initial_prompt}")
                    enter_prompt(driver, initial_prompt)
                    if check_limit_reached(driver):
                        limit_reached_seq(driver)

                    wait_for_response(driver)

                    generation_prompts = config["generation_prompts"]
                    for i, prompt in enumerate(generation_prompts):
                        print(f"Entering Prompt {i+1}: {prompt}")
                        
                        if check_limit_reached(driver):
                            limit_reached_seq(driver)

                        enter_prompt(driver, prompt)

                        if check_limit_reached(driver):
                            limit_reached_seq(driver)

                        wait_for_response(driver)
                        
                    
                    download_artifacts(driver, video_number, account)
            except Exception as e:
                print(f"An error occurred: {e}")

            choice = input(f"Do you want to continue with an updated config?\n(Please update the config file of the {account} account before pressing enter)\nChoice(y/n): ")
            if 'y' in choice.lower():
                continue_generation = True
            else:
                continue_generation = False
                print("Exiting the program.")
    finally:
        save_cookies(driver, account)
        driver.quit()

def limit_reached_seq(driver):
    print("Limit reached! waiting for 5 hours 10 mins...")
    reactivation_time = get_reactivation_time(driver)
    sleep_until_time(reactivation_time)
    driver.get(driver.current_url)
    ActionChains(driver).send_keys(Keys.RETURN).perform()

if __name__ == "__main__":
    claude_automation()