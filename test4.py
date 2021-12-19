import re, requests, datetime, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
# from api.models import Movie

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ' '.join([split if '’' not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    pattern2 = re.compile("[\(\[].*?[\)\]]")
    first = pattern2.sub('', splitTitlesCleaned)
    second = pattern.sub('', first)
    return second

def getMovieFromId(movieId, tmdbUrl, apiKey):
    movieParams = {
        'api_key': apiKey,
        'append_to_response': 'videos'
    }
    return requests.get(f'{tmdbUrl}/{movieId}', params=movieParams).json()

# convert time from 2:00 PM to 02:00 PM
def convertShawTiming(timing):
    splitTiming = timing.split()
    secondSplit = splitTiming[0].split(':')
    if len(secondSplit[0]) == 1:
        secondSplit[0] = f'0{secondSplit[0]}'
    splitTiming[0] = ':'.join(secondSplit)
    return ' '.join(splitTiming)

def convertShawDate(date):
    capitalDate = date.title()
    dateTimeObj = datetime.datetime.strptime(capitalDate, '%d %b %Y')
    return dateTimeObj.strftime('%d/%m/%Y')

CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
WINDOW_SIZE = "1920,1080"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument('--no-sandbox')

driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)

# SCRAPE SHAW
def scrapeShaw(driver, movies, tmdbUrl, tmdbSearchUrl, params):
    driver.get("https://www.shaw.sg/movie")

    movieFields = driver.find_elements(By.XPATH, "//div[contains(@class, 'info')]")
    movieUrls = [movieField.find_element(By.TAG_NAME, 'a').get_attribute('href') for movieField in movieFields]
    movieNames = [movieField.find_element(By.TAG_NAME, 'a').text for movieField in movieFields]

    print(f'found shaw movies: {movieNames}')

    for i, (movieUrl, movieName) in enumerate(zip(movieUrls, movieNames)):
        cleanedMovieName = cleanTitle(movieName)
        print(f'movie name: {movieName}\ncleaned movie name: {cleanedMovieName}\nmovie url: {movieUrl}\n')

        params['query'] = cleanedMovieName
        searchResultInfo = requests.get(tmdbSearchUrl, params=params).json()

        if len(searchResultInfo['results']) > 0:
            movieId = searchResultInfo['results'][0]['id']
            movieInfo = getMovieFromId(movieId, tmdbUrl, params['api_key'])

            movieData = {
                'movie': movieName,
                'info': movieInfo,
                'cinemas': []
            }

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
                
                time.sleep(1)
                cinemaDateField = driver.find_element(By.CLASS_NAME, 'owl-stage').find_element(By.XPATH, f'./div[{j+1}]')
                cinemaDateFields = cinemaDateField.find_elements(By.TAG_NAME, 'span')

                if (len(cinemaDateFields) <= 0):
                    continue
                
                print(f'length of cinema dates: {len(cinemaDateFields)}')
                cinemaDate = cinemaDateFields[-1].text
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

                        cinemaData = {
                            'cinema': cinemaName,
                            'timings': []
                        }

                        cinemaTimingFields = cinemaField.find_element(By.XPATH, './div[2]').find_elements(By.XPATH, './div')
                        for cinemaTimingField in cinemaTimingFields:
                            cinemaTiming = cinemaTimingField.text.replace('+', '').replace('*', '')
                            cinemaTimingUrl = cinemaTimingField.find_element(By.TAG_NAME, 'a').get_attribute('href')
                            timingData = {
                                'timing': f'{convertShawDate(cinemaDate)} {convertShawTiming(cinemaTiming)}',
                                'url': cinemaTimingUrl
                            }
                            print(timingData)
                            cinemaData['timings'].append(timingData)
                    
                        if len(movieData['cinemas']) > k-1:
                            movieData['cinemas'][k-1]['timings'] += cinemaData['timings']
                        else:
                            movieData['cinemas'].append(cinemaData)

            movieExists = False
            for movie in movies:
                if movie['info']['id'] == movieData['info']['id']:
                    movieExists = True
                    movie['cinemas'] += movieData['cinemas']
            if movieExists == False:
                movies.append(movieData)

    return movies

def scrapeReviewsForMovie(movieName, driver):
    print(f'finding reviews for movie: {movieName}')
    # create query param of movie name (replace spaces with %20)
    queryMovieName = '%20'.join(movieName.split(' '))
    searchQueryUrl = f"https://www.rottentomatoes.com/search?search={queryMovieName}"
    print(f'query movie name: {queryMovieName}')
    print(f'search query url: {searchQueryUrl}')
    # driver.execute_script("window.open()")
    # Switch to the newly opened tab
    # driver.switch_to.window(driver.window_handles[1])
    driver.get(searchQueryUrl)
    time.sleep(1)

    movieUrl = ''
    try:
        searchResultMovieField = driver.find_element(
            By.TAG_NAME, 'search-page-result'
        ).find_element(
            By.TAG_NAME, 'ul'
        ).find_element(
            By.XPATH, "//search-page-result[contains(@type, 'movie')]"
        ).find_element(
            By.TAG_NAME, 'ul'
        ).find_element(
            By.TAG_NAME, 'search-page-media-row'
        ).find_elements(
            By.TAG_NAME, 'a'
        )[-1]

        movieUrl = searchResultMovieField.get_attribute('href')
        searchResultMovieName = searchResultMovieField.text
        
        if movieName not in searchResultMovieName:
            print(f'movie search result {searchResultMovieName} does not contain movie name {movieName}, skipping...')
            return ({}, [])

        print(f'found movie url: {movieUrl}')
    except:
        print('could not find reviews for movie')
        return ({}, [])

    if movieUrl == '':
        print('could not find reviews for movie')
        return ({}, [])
    else:

        tomatoData = {}
        try:
            driver.get(movieUrl)
            time.sleep(2)

            scoreboardElement = driver.find_element(By.ID, 'topSection').find_element(By.XPATH, './div[1]').find_element(By.TAG_NAME, 'score-board')
            tomatoScore = scoreboardElement.get_attribute('tomatometerscore')
            audienceScore = scoreboardElement.get_attribute('audiencescore')
            rating = scoreboardElement.get_attribute('rating')

            print(f'tomatometer: {tomatoScore}, audience: {audienceScore}, rating: {rating}')

            tomatoCount = scoreboardElement.find_elements(By.TAG_NAME, 'a')[0].text.split()[0]
            audienceCount = scoreboardElement.find_elements(By.TAG_NAME, 'a')[1].text.split()[0]

            criticData = {
                'score': tomatoScore,
                'count': tomatoCount
            }
            audienceData = {
                'score': audienceScore,
                'count': audienceCount
            }
            tomatoData['rating'] = rating
            tomatoData['tomatoScore'] = criticData
            tomatoData['audienceScore'] = audienceData

        except:
            print('movie does not contain any tomato/audience ratings, skipping...')

        movieReviewsUrl = f'{movieUrl}/reviews'

        try:
            driver.get(movieReviewsUrl)
            time.sleep(2)
        except WebDriverException:
            error = """
            Message: unknown error: session deleted because of page crash
            from unknown error: cannot determine loading status
            from tab crashed
            """
            print(error)
            return ({}, [])

        print(f'review site title: {driver.title}')
        reviewDatas = []
        reviewsTableFields = []
        try:
            reviewsTableFields = driver.find_element(
                By.CLASS_NAME, 'review_table').find_elements(By.XPATH, './div')
        except:
            return ({}, [])

        for reviewField in reviewsTableFields:
            reviewData = {
                'movie': movieName
            }

            try:
                criticFields = reviewField.find_element(By.XPATH, './div[1]')
                criticImgUrl = criticFields.find_element(
                    By.TAG_NAME, 'img').get_attribute('src')
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

                reviewFields = reviewField.find_element(By.XPATH, './div[2]').find_element(
                    By.CLASS_NAME, 'review_area').find_elements(By.XPATH, './div')
                reviewDate = reviewFields[0].text
                reviewText = reviewFields[1].find_element(By.XPATH, './div[1]').text
                reviewUrl = reviewFields[1].find_element(
                    By.XPATH, './div[2]').find_element(By.TAG_NAME, 'a').get_attribute('href')
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

            except:
                print('review has missing data, skipping...')
                continue

        return (tomatoData, reviewDatas)

tmdbUrl = 'https://api.themoviedb.org/3/movie'
tmdbSearchUrl = 'https://api.themoviedb.org/3/search/movie'
tmdbApiKey = '863e63572b437caf26335f1d1143e10c'

params = {
    'api_key': tmdbApiKey,
    'language': 'en-US',
    'primary_release_year': '2021',
    'append_to_response': 'videos',
}

movies = []

# movies = scrapeGV(driver, movies, tmdbUrl, tmdbSearchUrl, params)
# movies = scrapeCathay(driver, movies, tmdbUrl, tmdbSearchUrl, params)
movies = scrapeShaw(driver, movies, tmdbUrl, tmdbSearchUrl, params)

print('creating movie object data...')
for movie in movies:
    tomatoData, reviews = scrapeReviewsForMovie(movie['movie'], driver)
    print(f'reviews for {movie["movie"]}: {reviews}')
    movie['reviews'] = reviews
    movie['info']['tomatoData'] = tomatoData