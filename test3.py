import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from api.models import Movie

CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
WINDOW_SIZE = "1920,1080"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument('--no-sandbox')

def getNameFromUrl(url):
    splits = [bit if '(' not in bit else '' for bit in url.split('/')[-2].split('-')]
    name = ' '.join(splits[:-1])
    return name

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ' '.join([split if '’' not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    return pattern.sub('', splitTitlesCleaned)

driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
driver.get("https://www.cathaycineplexes.com.sg/movies")

moviesContainerClass = 'boxes'
movieContainerField = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CLASS_NAME, moviesContainerClass)))

movieUrlFields = movieContainerField.find_elements(By.TAG_NAME, 'a')
movieUrls = set([movieField.get_attribute('href') for movieField in movieUrlFields])

tmdbUrl = 'https://api.themoviedb.org/3/search/movie'
tmdbApiKey = '863e63572b437caf26335f1d1143e10c'
movieInfos=[]

for o, movieUrl in enumerate(movieUrls):
    movieName = getNameFromUrl(movieUrl)
    cleanedMovieName = cleanTitle(movieName)
    print(f'\n=== {movieName} === movie number {o+1} of {len(movieUrls)}')
    print(f'{cleanedMovieName}')

    params = {
        'api_key': tmdbApiKey,
        'language': 'en-US',
        'primary_release_year': '2021',
        'query': cleanedMovieName
    }
    movieInfo = requests.get(tmdbUrl, params=params).json()
    if len(movieInfo['results']) > 0:

        movieJSON = {
            'info': movieInfo['results'][0],
            'movie': movieInfo['results'][0]['title'],
            'cinemas': []
        }

        driver.execute_script("window.open()")
        # Switch to the newly opened tab
        driver.switch_to.window(driver.window_handles[1])
        driver.get(movieUrl)
        driver.implicitly_wait(2)

        cinemaSectionFields = driver.find_element(By.XPATH, "//div[contains(@id, 'showtimes')]").find_elements(By.XPATH, "./div[contains(@id, 'ContentPlaceHolder1_wucST')]")
        cinemaTimingsTotal = []

        print(f'found {len(cinemaSectionFields)} cinemas!')

        for i, (cinemaSectionField) in enumerate(cinemaSectionFields):
            cinemaName = cinemaSectionField.find_element(By.XPATH, "./ul").find_element(By.XPATH, "./li[1]").text
            print(f'=== {cinemaName} ===')
            if cinemaSectionField.get_attribute('id') != 'ContentPlaceHolder1_wucSTPMS_tabs':
                cinemaTimingList = []
                cinemaTimings = cinemaSectionField.find_elements(By.CLASS_NAME, 'movie-timings')
                driver.implicitly_wait(1)
                for cinemaTiming in cinemaTimings:
                    print(f'timing {cinemaTiming.text} found')
                    timingDatas = cinemaTiming.find_elements(By.TAG_NAME, 'a')
                    for timingData in timingDatas:
                        timingTitleText = timingData.get_attribute('title')
                        timingBookingUrl = timingData.get_attribute(
                            'data-href-stop')
                        if len(timingTitleText) > 0:
                            timingData = {
                                'timing': timingTitleText, 'url': timingBookingUrl}
                            print(timingData)
                            cinemaTimingList.append(timingData)
                    
                if len(cinemaTimingList) > 0:
                    # cinemaTimingsTotal.append(cinemaTimingList)
                    movieJSON['cinemas'].append({
                        'cinema': f'Cathay {cinemaName}',
                        'dates': cinemaTimingList
                    })
            else:
                print('cinema is a platinum VIP suite, skip')
                continue
        
        print(movieJSON['cinemas'])
        movieInfos.append(movieJSON)

# print(movieInfos)