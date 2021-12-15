import requests, re

def cleanTitle(title):
    splitTitles = title.split()
    splitTitlesCleaned = ''.join([split if '’' not in split else '' for split in splitTitles])
    pattern = re.compile("[^a-zA-Z0-9-':\s]+")
    return pattern.sub('', splitTitlesCleaned)

name = "Disney’s Encanto"
tmdbUrl = 'https://api.themoviedb.org/3/search/movie'
tmdbApiKey = '863e63572b437caf26335f1d1143e10c'
params = {
    'api_key': tmdbApiKey,
    'language': 'en-US',
    'query': cleanTitle(name)
}
movieInfo = requests.get(tmdbUrl, params=params).json()
print(cleanTitle(name))
print(movieInfo['results'][0])
