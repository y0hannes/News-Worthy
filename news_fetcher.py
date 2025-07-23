import os
import requests
import sqlite3
import logging
from enum import Enum
from datetime import datetime, timedelta
from dotenv import load_dotenv

# setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

load_dotenv()
class NewsTopics(Enum):
    GENERAL = 'general'
    WORLD = 'world'
    NATION = 'nation'
    BUSINESS = 'business'
    TECHNOLOGY = 'technology'
    ENTERTAINMENT = 'entertainment'
    SPORTS = 'sports'
    SCIENCE = 'science'
    HEALTH = 'health'

CACHE_DURATION = timedelta(hours=1)

def init_db():
    with sqlite3.connect("news.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                topic TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
        ''')
        conn.commit()

NEWS_API_TOKEN = os.getenv('NEWS_API_TOKEN')

if not NEWS_API_TOKEN:
    LOGGER.error("API TOKEN not found.")

ENDPOINT = 'https://gnews.io/api/v4/search'

def fetch_and_store_news(topic: NewsTopics, max_articles=10):
    params = {
        'q': topic.value,
        'lang': 'en',
        'max': max_articles,
        'token': NEWS_API_TOKEN
    }
    try:
        res = requests.get(ENDPOINT, params=params)
        res.raise_for_status() 
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Error fetching news for topic '{topic.value}': {e}")
        return []

    articles = res.json().get('articles', [])
    if not articles:
        LOGGER.info(f"No articles found for topic '{topic.value}'.")
        return []

    headlines_to_return = []
    with sqlite3.connect("news.db") as conn:
        cursor = conn.cursor()
        fetched_at = datetime.now().isoformat()

        for article in articles:
            title = article.get('title')
            url = article.get('url')
            published_at = article.get('publishedAt')
            content = article.get('content')

            cursor.execute('''
                INSERT INTO news (title, content, url, published_at, topic, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, url, published_at, topic.value, fetched_at))
            
            headlines_to_return.append(f"• {title}\n{url}")

    LOGGER.info(f"Successfully fetched and stored {len(articles)} articles for topic '{topic.value}'.")
    return headlines_to_return

def get_cached_news(topic: NewsTopics, limit=5):
    with sqlite3.connect("news.db") as conn:
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - CACHE_DURATION
        # cursor.execute("DELETE FROM news WHERE fetched_at < ?", (cutoff_time.isoformat(),))
        
        cursor.execute('''
            SELECT title, url FROM news
            WHERE topic =? 
            ORDER BY published_at DESC
            LIMIT ?
        ''', (topic.value, limit))
        results = cursor.fetchall()

    return [f"• {title}\n{url}" for title, url in results]
