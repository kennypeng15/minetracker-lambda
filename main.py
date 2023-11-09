from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
from os.path import join, dirname

# todo: import my code over
def handler(event=None, context=None):
    
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    print("environment variable test: " + os.environ['MINESWEEPER_USERNAME'])
    
    """
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService("/opt/chromedriver")

    options.binary_location = '/opt/chrome/chrome'
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")

    chrome = webdriver.Chrome(options=options, service=service)
    chrome.get("https://example.com/")

    return chrome.find_element(by=By.XPATH, value="//html").text
    """
