import requests

with open('API_KEY.txt') as file:
    API_KEY = file.read().strip()

ENDPOINT = 'https://gnews.io/api/v4/search'

def fetch(topic='general', max_articles=10):
    params = {
        'q': topic,
        'lang': 'en',
        'max': max_articles,
        'token': API_KEY
    }
    res = requests.get(ENDPOINT, params=params)

    if res.status_code != 200:
        print("Error fetching news:", res.status_code)
        return

    articles = res.json().get('articles', [])
    print('API call done!')