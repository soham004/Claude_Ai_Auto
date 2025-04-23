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

def claude_automation():
    continue_generation = True

    driver = Driver(uc=True, headless=False)
    driver.maximize_window()
    # Handle login using the modularized function
    handle_login(driver)

    # Random human-like behavior
    random_scroll(driver)

    while continue_generation:
        with open("config.json", "r") as f:
            config = json.load(f)
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
            # driver.get("https://claude.ai/chat/bda7d3ac-e54f-472b-9d70-2e194d58c52d")
            # random_sleep(1, 2)
            # download_artifacts(driver, video_number)
            for video_number in video_numbers:
                driver.get(config["project_link"])

                
                initial_prompt = config["initial_prompt"].replace("<video_number>", video_number)
                
                enter_prompt(driver, initial_prompt)
                wait_for_response(driver)

                generation_prompts = config["generation_prompts"]
                for prompt in generation_prompts:
                    # Click on the input field and enter the prompt
                    enter_prompt(driver, prompt)
                    # Wait for the response to be generated
                    wait_for_response(driver)
                    if check_limit_reached(driver):
                        print("Limit reached! waiting for 5 hours 10 mins...")
                        wait_for_input((5 * 60 * 60)+10*60)  # Wait for 5 hours 10 minutes
                
                download_artifacts(driver, video_number)
        except Exception as e:
            print(f"An error occurred: {e}")
        # finally:
    save_cookies(driver)
    driver.quit()

if __name__ == "__main__":
    claude_automation()