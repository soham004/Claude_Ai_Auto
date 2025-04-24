from seleniumbase import Driver
import time
import random

def test():
    continue_generation = True

    driver = Driver(uc=False, headless=False)
    driver.maximize_window()

    # driver.get("about:blank")  # Start with blank page
    time.sleep(random.uniform(0.5, 1.5))

    driver.get("https://claude.ai")
    input("Press enter")

test()