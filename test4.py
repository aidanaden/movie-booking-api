
import re
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from api.models import Movie

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ' '.join([split if '’' not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    pattern2 = re.compile("[\(\[].*?[\)\]]")
    first = pattern2.sub('', splitTitlesCleaned)
    second = pattern.sub('', first)
    return second

CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
WINDOW_SIZE = "1920,1080"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument('--no-sandbox')

driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
driver.get("https://www.shaw.sg/movie")

movieFields = driver.find_elements(By.XPATH, "//div[contains(@class, 'info')]")
for movieField in movieFields:
    movieInfo = movieField.find_element(By.TAG_NAME, 'a')
    movieName = movieInfo.text
    movieUrl = f"https://www.shaw.sg/{movieInfo.get_attribute('href')}"
    print(f'movie name: {movieName}\ncleaned movie name: {cleanTitle(movieName)}\nmovie url: {movieUrl}\n')
