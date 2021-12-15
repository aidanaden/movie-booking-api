import enum
import re, requests, datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.models import Movie

CHROMEDRIVER_PATH = '/home/aidan/chromedriver'
WINDOW_SIZE = "1920,1080"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
driver.get("https://www.gv.com.sg/GVMovies")

movieFieldId = 'nowMovieThumb'
movieFieldId2 = 'nowMovieThumb13'

movieFields1 = driver.find_elements(By.ID, movieFieldId)
movieFields2 = driver.find_elements(By.ID, movieFieldId2)
movieFields = movieFields1 + movieFields2

movies = []
Movie.objects.all().delete()

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ' '.join([split if '’' not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    return pattern.sub('', splitTitlesCleaned)

def getCinemaTimingUrl(cinemaUrl, cinemaTiming):
    format = '%I:%M %p'
    datetimeStr = datetime.datetime.strptime(cinemaTiming, format)
    cinemaUrlSplit = cinemaUrl.split('/')
    cinemaUrlSplit[-3] = datetimeStr.strftime('%H%M')
    cinemaTimingUrl = '/'.join(cinemaUrlSplit)
    return cinemaTimingUrl

print(f'found {len(movieFields)} movies in GV')

for k, movieField in enumerate(movieFields):
    if (k+1) >= len(movieFields):
        break
    cinemas = []

    titleText = movieField.find_element(By.TAG_NAME, 'h5').text
    cleanedTitleText = cleanTitle(titleText)
    movieDetailsUrl = movieField.find_element(By.TAG_NAME, 'a').get_attribute('href')
    print(f'\n=== {titleText} === movie number {k+1} of {len(movieFields)}')
    print(f'{cleanedTitleText}')
    # Opens a new tab
    driver.execute_script("window.open()")
    # Switch to the newly opened tab
    driver.switch_to.window(driver.window_handles[1])
    driver.get(movieDetailsUrl)

    numCinemas = len(driver.find_element(
        By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li'))

    for i in range(numCinemas):
        cinemaDates = []
        driver.implicitly_wait(1)
        movieCinemas = driver.find_element(
            By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
        movieCinema = movieCinemas[i]

        movieCinemaElement = movieCinema.find_element(By.TAG_NAME, 'a')
        cinemaName = movieCinemaElement.text
        print(f'=== {cinemaName} ===')
        driver.execute_script('arguments[0].click();', movieCinemaElement)

        try:
            cinemaTimings = driver.find_element(By.CLASS_NAME, 'time-body')
            daysElementList = WebDriverWait(cinemaTimings, 5).until(
                        EC.presence_of_element_located((By.XPATH, './ul')))
            daysElements = daysElementList.find_elements(By.XPATH, './li')

            for j in range(len(daysElements)):
                # Click on cinema button (to display cinema timings)
                # AFTER calling driver.back()
                movieCinemas = driver.find_element(
                    By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                movieCinema = movieCinemas[i]

                movieCinemaElement = movieCinema.find_element(By.TAG_NAME, 'a')
                cinemaName = movieCinemaElement.text
                driver.execute_script('arguments[0].click();', movieCinemaElement)

                # get list of available days for current cinema
                # and select latest non-visited day
                cinemaTimings = driver.find_element(By.CLASS_NAME, 'time-body')
                newDaysElementList = WebDriverWait(cinemaTimings, 5).until(
                    EC.presence_of_element_located((By.XPATH, './ul')))
                newDaysElements = newDaysElementList.find_elements(By.XPATH, './li')
                dayElement = newDaysElements[j]

                try:
                    timingBtns = dayElement.find_element(
                        By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                    cinemaTimings = [timingBtn.text for timingBtn in timingBtns]

                    cinemaDate = dayElement.find_element(By.TAG_NAME, 'p').text
                    timingBtn = timingBtns[0].find_element(By.TAG_NAME, 'button')

                    driver.execute_script("arguments[0].click();", timingBtn)
                    cinemaUrl = driver.current_url

                    for cinemaTiming in cinemaTimings:
                        cinemaTimingUrl = getCinemaTimingUrl(cinemaUrl, cinemaTiming)
                        cinemaDateData = {
                            "timing": f'{cinemaDate.split()[-1]} {cinemaTiming}',
                            "url": cinemaTimingUrl
                        }
                        print(cinemaDateData)
                        cinemaDates.append(cinemaDateData)

                    driver.back()

                finally:
                    continue
            
            cinemas.append({
                "cinema": cinemaName,
                "dates": cinemaDates
            })

        finally:
            continue

    tmdbUrl = 'https://api.themoviedb.org/3/search/movie'
    tmdbApiKey = '863e63572b437caf26335f1d1143e10c'
    params = {
        'api_key': tmdbApiKey,
        'language': 'en-US',
        'primary_release_year': '2021',
        'query': cleanedTitleText
    }
    movieInfo = requests.get(tmdbUrl, params=params).json()

    if (len(movieInfo['results']) > 0):
        data = {
            'movie': cleanedTitleText,
            'cinemas': cinemas,
            'info': movieInfo['results'][0]
        }
        movies.append(Movie.objects.create(data=data))

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

print('closing driver...')
driver.quit()
