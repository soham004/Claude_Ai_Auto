import traceback
from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sys
import msvcrt
from modules.automation_parts import *
import json





def select_account():
    """Select an account for login"""
    accounts = [f for f in os.listdir("accounts") if os.path.isdir(os.path.join("accounts", f))]
    if not accounts:
        print("No accounts found in the 'accounts' directory.")
        sys.exit(1)
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
        sys.exit(1)
        
    configs = [f for f in os.listdir("configs") if os.path.isdir(os.path.join("configs", f))]
    if not configs:
        print("No configuration folders found in the 'configs' directory.")
        sys.exit(1)
        
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

    while True:
        try:
            video_numbers = input("Enter the video numbers (range eg 1-15): ").split("-")
            if len(video_numbers) != 2:
                raise ValueError("Invalid input")
            print(f"Selected video numbers: {video_numbers[0]} to {video_numbers[1]}\ni.e. {[i for i in range(int(video_numbers[0]), int(video_numbers[1]) + 1)]}")
            break
        except Exception as e:
            print(f"Error: {e}. Please enter the video numbers in the format 'start-end'.")
            logging.info(traceback.format_exc())
    
    # Initialize the browser
    driver = Driver(uc=True, headless=False,)
    driver.maximize_window()

    # Handle login
    handle_login(driver, account)
    print("Login successful!")
    
    # Main automation loop
    continue_generation = True
    try:
        while continue_generation:
            try:
                for video_number in video_numbers:
                    
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
                    

                    wait_for_response(driver)

                    generation_prompts = config["generation_prompts"]
                    for i, prompt in enumerate(generation_prompts):
                        print(f"Entering Prompt {i+1}: {prompt}")
                        
                        enter_prompt(driver, prompt)

                        wait_for_response(driver)
                    
                    output_dir = account+"-"+config_name
                    download_artifacts(driver, str(video_number), output_dir)
            except Exception as e:
                print(f"An error occurred: {e}")
                logging.info(traceback.format_exc())

            choice = input(f"Do you want to continue with different video numbers? (y/n): ")
            if 'y' in choice.lower():
                continue_generation = True
                while True:
                    try:
                        video_numbers = input("Enter the video numbers (comma seperated eg 24,27,22): ").split(",")
                        if len(video_numbers) == 0:
                            raise ValueError("Invalid input")
                        print(f"No of videos to process: {len(video_numbers)}")
                        print(f"Selected video numbers: {video_numbers}\ni.e. {[i for i in video_numbers]}")
                        for num in video_numbers:
                            if not num.strip().isdigit():
                                raise ValueError(f"Invalid video number: {num}")
                        video_numbers = [int(num.strip()) for num in video_numbers]
                        break
                    except Exception as e:
                        print(f"Error: {e}. Please enter the video numbers in the correct format.")
                        logging.info(traceback.format_exc())
            else:
                continue_generation = False
                print("Exiting the program.")
    finally:
        save_cookies(driver, account)
        driver.quit()



if __name__ == "__main__":
    claude_automation()