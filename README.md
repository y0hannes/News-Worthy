# 📰 News-Worthy: Your Personalized News Bot

**News-Worthy** is a powerful Telegram bot designed to keep you informed with fresh news tailored to your interests. It fetches headlines from global sources and delivers them straight to your chat, either on-demand or through a highly customizable daily schedule.

---

## ✨ Key Features

- **Topic-Based Subscriptions**: Choose from a variety of topics like Technology, Business, Science, Health, and more.
- **Daily Scheduled Delivery**: Get your morning (or evening!) news at the exact time you want.
- **Smart Caching**: Efficient news retrieval with a 1-hour cache to save API usage and ensure speed.
- **Interactive UI**: Navigate through topics and manage subscriptions using intuitive inline keyboards.
- **Docker Ready**: Easy deployment using Docker and Docker Compose.

---

## 🛠️ Technology Stack

- **Language**: Python 3.13
- **Bot Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **News API**: [GNews API](https://gnews.io/)
- **Database**: SQLite (via `aiosqlite`)
- **Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/)
- **Asynchronous IO**: `asyncio`, `aiohttp`

---

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.10+ (if running locally)
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (recommended)
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A GNews API Token (from [gnews.io](https://gnews.io/))

### ⚙️ Environment Configuration

Create a `.env` file in the root directory and add your credentials:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
NEWS_API_TOKEN=your_gnews_api_token_here
```

### 🐳 Run with Docker (Recommended)

The easiest way to get the bot running is using Docker Compose:

```bash
docker-compose up -d --build
```

### 🐍 Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Bot**:
   ```bash
   python app/main.py
   ```

---

## 🤖 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Initial registration and welcome message. |
| `/help` | List all available commands. |
| `/news` | View latest headlines for a specific topic. |
| `/subscribe` | Subscribe to a news topic for daily delivery. |
| `/mynews` | Get a customized feed based on your subscriptions. |
| `/mysubscriptions` | View and manage your current subscriptions. |
| `/set_delivery_time` | Set your daily delivery time (Format: `HH:MM`). |
| `/get_delivery_time` | Check your current scheduled delivery time. |

---

## 📁 Project Structure

```text
News-Worthy/
├── app/
│   ├── main.py          # Bot entry point and command handlers
│   ├── news_fetcher.py   # API integration, database logic, and scheduler
│   └── news.db          # SQLite database (generated at runtime)
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-container setup
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (ignored by git)
```

---

## 📝 License

This project is open-source and available under the MIT License.