import enum
import re, requests, datetime, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from api.models import Movie

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ' '.join([split if '’' not in split and "'" not in split else '' for split in splitTitles]).strip()
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    pattern2 = re.compile("[\(\[].*?[\)\]]")
    first = pattern2.sub('', splitTitlesCleaned)
    second = pattern.sub('', first)
    removeDisney = ' '.join([name if 'disney' not in name else '' for name in second.split()]).strip()
    return removeDisney


def getCinemaTimingUrl(cinemaUrl, cinemaTiming):
    format = '%I:%M %p'
    datetimeStr = datetime.datetime.strptime(cinemaTiming, format)
    cinemaUrlSplit = cinemaUrl.split('/')
    cinemaUrlSplit[-3] = datetimeStr.strftime('%H%M')
    cinemaTimingUrl = '/'.join(cinemaUrlSplit)
    return cinemaTimingUrl

def getNameFromUrl(url):
    splits = [bit if '(' not in bit else '' for bit in url.split('/')[-2].split('-')]
    name = ' '.join(splits[:-1])
    return name

def getMovieFromId(movieId, tmdbUrl, apiKey):
    movieParams = {
        'api_key': apiKey,
        'append_to_response': 'videos'
    }
    return requests.get(f'{tmdbUrl}/{movieId}', params=movieParams).json()

def convertShawDate(date):
    capitalDate = date.title()
    dateTimeObj = datetime.datetime.strptime(capitalDate, '%d %b %Y')
    return dateTimeObj.strftime('%d/%m/%Y')

def convertGVTiming(timing):
    timeDateTimeObj = datetime.datetime.strptime(timing, '%I:%m %p')
    return timeDateTimeObj.strftime('%I:%m %p')

# convert time from 2:00 PM to 02:00 PM
def convertShawTiming(timing):
    splitTiming = timing.split()
    secondSplit = splitTiming[0].split(':')
    if len(secondSplit[0]) == 1:
        secondSplit[0] = f'0{secondSplit[0]}'
    splitTiming[0] = ':'.join(secondSplit)
    return ' '.join(splitTiming)

# convert time from 12/12/2021 5:15:00 PM to 12/12/2021 5:15 PM
def convertCathayTiming(timing):
    ogSplit = timing.split()
    ogSplit[1] = ':'.join(ogSplit[1].split(':')[:-1])
    convertedTime = convertShawTiming(' '.join(ogSplit[1:]))
    return ' '.join([ogSplit[0], convertedTime])

# SCRAPE GV
def scrapeGV(driver, movies, tmdbUrl, tmdbSearchUrl, params):
    driver.get("https://www.gv.com.sg/GVMovies")

    movieFieldId = 'nowMovieThumb'
    movieFieldId2 = 'nowMovieThumb13'

    movieFields1 = driver.find_elements(By.ID, movieFieldId)
    movieFields2 = driver.find_elements(By.ID, movieFieldId2)
    movieFields = movieFields1 + movieFields2

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
        driver.implicitly_wait(1)

        numCinemas = len(driver.find_element(
            By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li'))
        print(f'original numCinemas: {numCinemas}')

        for i in range(numCinemas):
            cinemaDates = []
            movieCinemas = driver.find_element(
                By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
            print(f'new numCinemas: {len(movieCinemas)}')
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

                    timingBtnFields = dayElement.find_element(
                        By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                    try:
                        for k in range(len(timingBtnFields)):

                            # RE-find elements/fields due to driver.back()
                            movieCinemas = driver.find_element(
                                By.CLASS_NAME, 'cinemas-body').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                            movieCinema = movieCinemas[i]

                            movieCinemaElement = movieCinema.find_element(
                                By.TAG_NAME, 'a')
                            cinemaName = movieCinemaElement.text
                            driver.execute_script(
                                'arguments[0].click();', movieCinemaElement)

                            # get list of available days for current cinema
                            # and select latest non-visited day
                            cinemaTimings = driver.find_element(
                                By.CLASS_NAME, 'time-body')
                            newDaysElementList = WebDriverWait(cinemaTimings, 5).until(
                                EC.presence_of_element_located((By.XPATH, './ul')))
                            newDaysElements = newDaysElementList.find_elements(
                                By.XPATH, './li')
                            dayElement = newDaysElements[j]

                            timingBtnFields = dayElement.find_element(
                                By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                            cinemaDate = dayElement.find_element(
                                By.TAG_NAME, 'p').text

                            # get current timing button and URL
                            timingBtn = timingBtnFields[k].find_element(
                                By.TAG_NAME, 'button')
                            cinemaTiming = timingBtn.text
                            driver.execute_script(
                                "arguments[0].click();", timingBtn)
                            cinemaUrl = driver.current_url

                            cinemaDateData = {
                                "timing": f'{cinemaDate.split()[-1]} {convertGVTiming(cinemaTiming)}',
                                "url": cinemaUrl
                            }
                            print(cinemaDateData)
                            cinemaDates.append(cinemaDateData)

                            driver.back()
                    except:
                        print('Exception occurred while trying to loop thru timings')
                        continue

                cinemas.append({
                    "cinema": cinemaName,
                    "dates": cinemaDates
                })

            finally:
                continue
        
        params['query'] = cleanedTitleText
        searchResultInfo = requests.get(tmdbSearchUrl, params=params).json()

        if (len(searchResultInfo['results']) > 0):
            movieId = searchResultInfo['results'][0]['id']
            movieInfo = getMovieFromId(movieId, tmdbUrl, params['api_key'])

            data = {
                'movie': movieInfo['title'],
                'info': movieInfo,
                'reviews': [],
                'cinemas': cinemas,
            }
            movies.append(data)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    return movies

# SCRAPE CATHAY 
def scrapeCathay(driver, movies, tmdbUrl, tmdbSearchUrl, params):
    driver.get("https://www.cathaycineplexes.com.sg/movies")

    moviesContainerClass = 'boxes'
    movieContainerField = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, moviesContainerClass)))

    movieUrlFields = movieContainerField.find_elements(By.TAG_NAME, 'a')
    movieUrls = set([movieField.get_attribute('href') for movieField in movieUrlFields])

    print('scraping cathay...')

    for o, movieUrl in enumerate(movieUrls):
        movieName = getNameFromUrl(movieUrl)
        cleanedMovieName = cleanTitle(movieName)
        print(f'\n=== {movieName} === movie number {o+1} of {len(movieUrls)}')
        print(f'{cleanedMovieName}')

        params['query'] = cleanedMovieName
        searchResultInfo = requests.get(tmdbSearchUrl, params=params).json()

        if len(searchResultInfo['results']) > 0:
            movieId = searchResultInfo['results'][0]['id']
            movieInfo = getMovieFromId(movieId, tmdbUrl, params['api_key'])
            movieJSON = {
                'info': movieInfo,
                'movie': movieInfo['title'],
                'cinemas': [],
                'reviews': []
            }

            driver.execute_script("window.open()")
            # Switch to the newly opened tab
            driver.switch_to.window(driver.window_handles[1])
            driver.get(movieUrl)
            driver.implicitly_wait(1)

            cinemaSectionFields = []

            try:
                cinemaSectionFields = driver.find_element(By.XPATH, "//div[contains(@id, 'showtimes')]").find_elements(By.XPATH, "./div[contains(@id, 'ContentPlaceHolder1_wucST')]")
            except:
                print('movie has no timings, skipping...')
                pass
            
            if (len(cinemaSectionFields) > 0):
                for cinemaSectionField in cinemaSectionFields:
                    cinemaName = cinemaSectionField.find_element(By.XPATH, "./ul").find_element(By.XPATH, "./li[1]").text
                    print(f'=== {cinemaName} ===')
                    if cinemaSectionField.get_attribute('id') != 'ContentPlaceHolder1_wucSTPMS_tabs':
                        cinemaTimingList = []
                        cinemaTimings = cinemaSectionField.find_elements(By.CLASS_NAME, 'movie-timings')
                        for cinemaTiming in cinemaTimings:
                            print(f'timing {cinemaTiming.text} found')
                            timingDatas = cinemaTiming.find_elements(By.TAG_NAME, 'a')
                            for timingData in timingDatas:
                                timingTitleText = timingData.get_attribute('title')
                                timingBookingUrl = timingData.get_attribute(
                                    'data-href-stop')
                                if len(timingTitleText) > 0:
                                    timingData = {
                                        'timing': convertCathayTiming(timingTitleText),
                                        'url': timingBookingUrl
                                    }
                                    print(timingData)
                                    cinemaTimingList.append(timingData)
                            
                        if len(cinemaTimingList) > 0:
                            movieJSON['cinemas'].append({
                                'cinema': f'Cathay {cinemaName}',
                                'dates': cinemaTimingList
                            })
                    else:
                        print('cinema is a platinum VIP suite, skip')
                        continue
                
                movieExists = False
                for movie in movies:
                    if movie['info']['id'] == movieJSON['info']['id']:
                        movieExists = True
                        movie['cinemas'] += movieJSON['cinemas']
                
                if movieExists == False:
                    movies.append(movieJSON)
    
    return movies

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

        driver.get(movieUrl)
        time.sleep(1)

        tomatoData = {}
        scoreFields = driver.find_element(By.CLASS_NAME, 'scores-container').find_elements(By.XPATH, './div')
        tomatoScore = scoreFields[0].find_element(By.CLASS_NAME, 'percentage').text
        audienceScore = scoreFields[1].find_element(By.CLASS_NAME, 'percentage').text
        tomatoNumCritics = driver.find_element(By.XPATH, "//a[contains(@slot, 'critics-count')]").text
        audienceNumCritics = driver.find_element(By.XPATH, "//a[contains(@slot, 'audience-count')]").text
        criticData = {
            'score': tomatoScore,
            'numCritics': tomatoNumCritics
        }
        audienceData = {
            'score': audienceScore,
            'numAudience': audienceNumCritics
        }
        tomatoData['tomatoScore'] = criticData
        tomatoData['audienceScore'] = audienceData

        # try:
        #     scoreFields = driver.find_element(By.CLASS_NAME, 'scores-container').find_elements(By.XPATH, './div')
        #     tomatoScore = scoreFields[0].find_element(By.CLASS_NAME, 'percentage').text
        #     audienceScore = scoreFields[1].find_element(By.CLASS_NAME, 'percentage').text
        #     tomatoNumCritics = driver.find_element(By.XPATH, "//a[contains(@slot, 'critics-count')]").text
        #     audienceNumCritics = driver.find_element(By.XPATH, "//a[contains(@slot, 'audience-count')]").text
        #     criticData = {
        #         'score': tomatoScore,
        #         'numCritics': tomatoNumCritics
        #     }
        #     audienceData = {
        #         'score': audienceScore,
        #         'numAudience': audienceNumCritics
        #     }
        #     tomatoData['tomatoScore'] = criticData
        #     tomatoData['audienceScore'] = audienceData

        # except:
        #     print('movie does not contain any tomato/audience ratings, skipping...')

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

CHROMEDRIVER_PATH = '/home/aidan/chromedriver'
WINDOW_SIZE = "1920,1080"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')      
driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)

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
movies = scrapeCathay(driver, movies, tmdbUrl, tmdbSearchUrl, params)
movies = scrapeShaw(driver, movies, tmdbUrl, tmdbSearchUrl, params)

print('creating movie object data...')
for movie in movies:
    tomatoData, reviews = scrapeReviewsForMovie(movie['movie'], driver)
    print(f'reviews for {movie["movie"]}: {reviews}')
    movie['reviews'] = reviews
    movie['info']['tomatoData'] = tomatoData

print('updating database with new movie timing data...')
Movie.objects.all().delete()
for movie in movies:
    Movie.objects.create(data=movie)

print('closing driver...')
driver.quit()




