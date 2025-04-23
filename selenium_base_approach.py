from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from modules.automation_parts import *
import json



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
                
                download_artifacts(driver, video_number)
        except Exception as e:
            print(f"An error occurred: {e}")
        # finally:
    save_cookies(driver)
    driver.quit()

if __name__ == "__main__":
    claude_automation()