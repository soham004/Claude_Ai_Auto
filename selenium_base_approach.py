from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sys
import msvcrt
from modules.automation_parts import *
import json

 
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
    print(f"{len(accounts) + 1}. Add a new account")
    choice = input("Select an account (1-{}): ".format(len(accounts)+1))
    if choice.isdigit() and 1 <= int(choice) <= len(accounts):
        return accounts[int(choice) - 1]
    elif choice == str(len(accounts) + 1):
        new_account = input("Enter the name for the new account: ")
        new_account = clean_file_name(new_account)
        os.makedirs(os.path.join("accounts", new_account), exist_ok=True)
        return new_account


def claude_automation():
    continue_generation = True

    account = select_account()

    driver = Driver(uc=True, headless=False)
    driver.maximize_window()
    # Handle login using the modularized function
    handle_login(driver, account)

    # Random human-like behavior
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
                    initial_prompt = config["initial_prompt"].replace(config["text_to_be_replaced_by_video_number"], video_number)
                    
                    enter_prompt(driver, initial_prompt)
                    wait_for_response(driver)

                    generation_prompts = config["generation_prompts"]
                    for i, prompt in enumerate(generation_prompts):
                        print(f"Entering Prompt {i+1}: {prompt}")
                        if check_limit_reached(driver):
                            print("Limit reached! waiting for 5 hours 10 mins...")
                            wait_for_input((5 * 60 * 60)+10*60)  # wait for 5 hours 10 minutes
                        
                        enter_prompt(driver, prompt)
                        wait_for_response(driver)
                        
                    
                    download_artifacts(driver, video_number, account)
            except Exception as e:
                print(f"An error occurred: {e}")
    finally:
        save_cookies(driver, account)
        driver.quit()

if __name__ == "__main__":
    claude_automation()