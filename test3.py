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
    splitTitlesCleaned = ' '.join([split if '’' not in split and "'" not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    pattern2 = re.compile("[\(\[].*?[\)\]]")
    first = pattern2.sub('', splitTitlesCleaned)
    second = pattern.sub('', first)
    return second

def scrapeReviewsForMovie(movieName, driver):
    # create query param of movie name (replace spaces with %20)
    queryMovieName = '%20'.join(movieName.split(' '))
    searchQueryUrl = f"https://www.rottentomatoes.com/search?search={queryMovieName}"
    driver.get(searchQueryUrl)
    driver.implicitly_wait(1)
    
    movieUrl = driver.find_element(
            By.TAG_NAME, 'search-page-result'
        ).find_element(
            By.TAG_NAME, 'ul'
        ).find_element(
            By.XPATH, "//search-page-result[contains(@type, 'movie')]"
        ).find_element(
            By.TAG_NAME, 'a'
        ).get_attribute('href')
    
    movieReviewsUrl = f'{movieUrl}/reviews'
    driver.get(movieReviewsUrl)
    time.sleep(2)

    reviewDatas = []
    reviewsTableFields = []
    try:
        reviewsTableFields = driver.find_element(By.CLASS_NAME, 'review_table').find_elements(By.XPATH, './div')
        print(f'number of reviews: {len(reviewsTableFields)}')
    except:
        return

    for reviewField in reviewsTableFields:
        reviewData = {
            'movie': movieName
        }
        
        criticFields = reviewField.find_element(By.XPATH, './div[1]')
        criticImgUrl = criticFields.find_element(By.TAG_NAME, 'img').get_attribute('src')
        criticDetails = criticFields.find_elements(By.TAG_NAME, 'a')
        # print(f'critic details: {[detail.text for detail in criticDetails]}')
        criticName = criticDetails[0].text
        criticUrl = criticDetails[0].get_attribute('href')
        criticCompany = criticDetails[1].text
        criticCompanyUrl = criticDetails[1].get_attribute('href')
        reviewData['critic'] = {
            'name': criticName,
            'url': criticUrl,
            'img': criticImgUrl,
            'company': criticCompany,
            'companyUrl': criticCompanyUrl
        }

        reviewFields = reviewField.find_element(By.XPATH, './div[2]').find_element(By.CLASS_NAME, 'review_area').find_elements(By.XPATH, './div')
        reviewDate = reviewFields[0].text
        reviewText = reviewFields[1].find_element(By.XPATH, './div[1]').text
        reviewUrl = reviewFields[1].find_element(By.XPATH, './div[2]').find_element(By.TAG_NAME, 'a').get_attribute('href')
        reviewRating = reviewFields[1].find_element(By.XPATH, './div[2]').text.strip().split(' ')[-1]

        if '/' in reviewRating:
            reviewData['review'] = {
                'date': reviewDate,
                'text': reviewText,
                'rating': reviewRating,
                'url': reviewUrl
            }
            reviewDatas.append(reviewData)
        else:
            print('review rating does not exist, skipping...')
            continue
    
    return reviewDatas


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

        cinemaSectionFields = []
        try:
            cinemaSectionFields = driver.find_element(By.XPATH, "//div[contains(@id, 'showtimes')]").find_elements(By.XPATH, "./div[contains(@id, 'ContentPlaceHolder1_wucST')]")
        except:
            print('no cinema timings for this movie, skipping...')
            pass
        cinemaTimingsTotal = []

        if (len(cinemaSectionFields) > 0):
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
            
            # print(movieJSON['cinemas'])
            movieInfos.append(movieJSON)

for movie in movieInfos:
    print(f"movie name: {movie['movie']}")
    movie['reviews'] = scrapeReviewsForMovie(movie['movie'], driver)

for movie in movieInfos:
    print(movie)
    print('')

driver.quit()
# print(movieInfos)