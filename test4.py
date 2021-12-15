
def getNameFromUrls(urls):
    names = []
    for url in urls:
        name = ' '.join(url.split('/')[-2].split('-')[:-1])
        names.append(name)
    return names

test = 'https://www.cathaycineplexes.com.sg/movies/my-hero-academia-the-movie-3-pg13/'
tests = ' '.join(test.split('/')[-2].split('-')[:-1])
print(tests)