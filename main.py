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
        sys.stdout.write("\rTime left: {:02d}:{:02d}:{:02d} Press Enter to resume Now... ".format(int(hours), int(mins), int(secs)))
        sys.stdout.flush()

        # Check if a key was pressed
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter key is detected
                print("\nUser pressed Enter!")
                return True  # Input received

        time.sleep(0.1)  # Reduce CPU usage


def select_account():
    """Select an account for login"""
    accounts = [f for f in os.listdir("accounts") if os.path.isdir(os.path.join("accounts", f))]
    if not accounts:
        print("No accounts found in the 'accounts' directory.")
        exit(1)
    print("\n" + "=" * 50)
    print("Available accounts:")
    print("=" * 50)
    for i, account in enumerate(accounts):
        print(f"{i + 1}. {account}")
    print("-" * 50)

    while True:
        choice = input("Select an account (1-{}): ".format(len(accounts)))
        if choice.isdigit() and 1 <= int(choice) <= len(accounts):
            selected_account = accounts[int(choice) - 1]
            print(f"Selected account: {selected_account}")
            return selected_account
        else:
            print("Invalid choice.")


def select_config():
    """Select a configuration from the configs directory"""
    if not os.path.exists("configs"):
        os.makedirs("configs")
        print("Created 'configs' directory. Please add config folders with config.json files.")
        exit(1)
        
    configs = [f for f in os.listdir("configs") if os.path.isdir(os.path.join("configs", f))]
    if not configs:
        print("No configuration folders found in the 'configs' directory.")
        exit(1)
        
    print("\n" + "=" * 50)
    print("Available configurations:")
    print("=" * 50)
    for i, config in enumerate(configs):
        print(f"{i + 1}. {config}")
    print("-" * 50)

    while True:
        choice = input("Select a configuration (1-{}): ".format(len(configs)))
        if choice.isdigit() and 1 <= int(choice) <= len(configs):
            selected_config = configs[int(choice) - 1]
            # Verify that config.json exists in the selected folder
            config_path = os.path.join("configs", selected_config, "config.json")
            if not os.path.exists(config_path):
                print(f"Error: config.json not found in {selected_config} folder")
                continue
                
            print(f"Selected config: {selected_config}")
            return selected_config
        else:
            print("Invalid choice.")


def load_config(config_name):
    """Load and validate a configuration file"""
    config_path = os.path.join("configs", config_name, "config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            # Validate required fields
            required_fields = [
                "project_link", 
                "initial_prompt", 
                "generation_prompts", 
                "text_to_be_replaced_by_video_number"
            ]
            for field in required_fields:
                if field not in config:
                    raise KeyError(f"Missing required field: {field}")
            return config
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in config file: {config_path}")
        return None
    except KeyError as e:
        print(f"Invalid config file: {e}")
        return None


def claude_automation():
    print("\n" + "=" * 80)
    print(" Claude AI Automation ".center(80, "="))
    print("=" * 80 + "\n")

    # Select account and config separately
    account = select_account()
    config_name = select_config()
    
    # Load and validate the configuration
    config = load_config(config_name)
    if not config:
        print("Failed to load valid configuration. Exiting.")
        return

    # Get video number range
    while True:
        try:
            video_numbers = input("Enter the video numbers (range eg 1-15): ").split("-")
            if len(video_numbers) != 2:
                raise ValueError("Invalid input")
            print(f"Selected video numbers: {video_numbers[0]} to {video_numbers[1]}\ni.e. {[i for i in range(int(video_numbers[0]), int(video_numbers[1]) + 1)]}")
            break
        except Exception as e:
            print(f"Error: {e}. Please enter the video numbers in the format 'start-end'.")
    
    # Initialize the browser
    driver = Driver(uc=True, headless=False)
    driver.maximize_window()

    # Handle login
    handle_login(driver, account)
    print("Login successful!")
    
    # Main automation loop
    continue_generation = True
    try:
        while continue_generation:
            try:
                for video_number in range(int(video_numbers[0]), int(video_numbers[1]) + 1):
                    print(f"Processing video number: {video_number}")
                    driver.get(config["project_link"])

                    text_to_be_replaced = config["text_to_be_replaced_by_video_number"]
                    initial_prompt = config["initial_prompt"]

                    if text_to_be_replaced in initial_prompt:
                        initial_prompt = initial_prompt.replace(text_to_be_replaced, str(video_number))
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
                    
                    download_artifacts(driver, str(video_number), account)
            except Exception as e:
                print(f"An error occurred: {e}")

            choice = input(f"Do you want to continue with different video numbers? (y/n): ")
            if 'y' in choice.lower():
                continue_generation = True
                while True:
                    try:
                        video_numbers = input("Enter the video numbers (range eg 1-15): ").split("-")
                        if len(video_numbers) != 2:
                            raise ValueError("Invalid input")
                        print(f"Selected video numbers: {video_numbers[0]} to {video_numbers[1]}\ni.e. {[i for i in range(int(video_numbers[0]), int(video_numbers[1]) + 1)]}")
                        break
                    except Exception as e:
                        print(f"Error: {e}. Please enter the video numbers in the format 'start-end'.")
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