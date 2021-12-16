
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
movieUrls = [movieField.find_element(By.TAG_NAME, 'a').get_attribute('href') for movieField in movieFields]
movieNames = [movieField.find_element(By.TAG_NAME, 'a').text for movieField in movieFields]

for i, movieUrl, movieName in zip(movieUrls, movieNames):
    print(f'movie name: {movieName}\ncleaned movie name: {cleanTitle(movieName)}\nmovie url: {movieUrl}\n')

    driver.get(movieUrl)
    cinemaDatesFields = []
    
    try:
        cinemaDatesFields = driver.find_element(By.CLASS_NAME, 'owl-stage').find_elements(By.XPATH, './div')
    except:
        print('no movie timings available, skipping...')
        continue

    rightClickBtnField = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[8]/div/div/div/div[2]/div/div[1]/div/div[2]/div[2]/div')

    for j in range(len(cinemaDatesFields)):
        if j >= 3:
            print('clicking on right click button...')
            rightClickBtnField.click()
            time.sleep(3)

        cinemaDateField = driver.find_element(By.CLASS_NAME, 'owl-stage').find_element(By.XPATH, f'./div[{j+1}]')
        cinemaDate = cinemaDateField.find_elements(By.TAG_NAME, 'span')[-1].text
        print(f'cinema date selected: {cinemaDate}')
        # click on date and wait for timings to load
        cinemaDateField.click()
        time.sleep(3)

        cinemaFields = driver.find_element(By.XPATH, "//div[contains(@id, 'moviesDiv')]").find_elements(By.XPATH, './div')
        for k, cinemaField in enumerate(cinemaFields):
            if k == 0:
                continue
            else:
                cinemaName = cinemaField.find_element(By.XPATH, './div[1]').text
                print(f'=== {cinemaName} ===')
                cinemaTimings = []

                cinemaTimingFields = cinemaField.find_element(By.XPATH, './div[2]').find_elements(By.XPATH, './div')
                for cinemaTimingField in cinemaTimingFields:
                    cinemaTiming = cinemaTimingField.text
                    cinemaTimingUrl = cinemaTimingField.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    timingData = {
                        'timing': f'{cinemaDate} {cinemaTiming}',
                        'url': cinemaTimingUrl
                    }
                    print(timingData)
                    cinemaTimings.append(timingData)
