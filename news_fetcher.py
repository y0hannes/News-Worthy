from telegram.ext import ContextTypes
from telegram import Update
import requests
import sqlite3

def init_db():
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT NOT NULL,
            published_at TEXT NOT NULL,
            topic TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

with open('API_KEY.txt') as file:
    API_KEY = file.read().strip()

ENDPOINT = 'https://gnews.io/api/v4/search'

def fetch_and_store_news(topic='general', max_articles=10):
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
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    for article in articles:
        title = article.get('title')
        url = article.get('url')
        published_at = article.get('publishedAt')
        content = article.get('content')

        cursor.execute('''
            INSERT INTO news (title, content, url, published_at, topic)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, url, published_at, topic))

    conn.commit()
    conn.close()
    print('API call done!')

def get_cached_news(topic='general', limit=5):
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, url FROM news
        WHERE topic = ?
        ORDER BY published_at DESC
        LIMIT ?
    ''', (topic, limit))
    results = cursor.fetchall()
    conn.close()

    return [f"• {title}\n{url}" for title, url in results]

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = ' '.join(context.args) if context.args else 'general'
    headlines = get_cached_news(topic)
    if not headlines:
        await update.message.reply_text(f"No cached news for '{topic}' yet.")
    else:
        await update.message.reply_text("\n\n".join(headlines))
