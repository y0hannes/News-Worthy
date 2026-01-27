# 📰 News-Worthy Bot

A powerful, asynchronous Telegram bot that delivers personalized news updates directly to your chat. Built with Python, modern async libraries, and Docker.

> **Status**: 🟢 Active Development  
> **Version**: 1.0.0

## ✨ Features

- **🔍 Topic Subscription**: Subscribe to specific news categories (Tech, Business, Science, etc.)
- **⏱️ Scheduled Delivery**: Set your preferred time for daily news digests
- **⚡ Real-time Updates**: Fetch the latest headlines on command
- **📱 Responsive UI**: Interactive buttons for easy navigation
- **🐳 Dockerized**: Easy deployment with Docker and Docker Compose
- **🚀 Async Performance**: Built on `aiohttp` and `python-telegram-bot` for high concurrency

## 🛠️ Tech Stack

- **Language**: Python 3.13
- **Framework**: [python-telegram-bot](https://python-telegram-bot.org/)
- **Database**: SQLite (Async via `aiosqlite`)
- **Scheduling**: APScheduler
- **External API**: GNews API
- **Containerization**: Docker

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A GNews API Key (from [gnews.io](https://gnews.io/))

### 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/y0hannes/News-Worthy.git
   cd News-Worthy
   ```

2. **Configure Environment**
   Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```env
   TELEGRAM_TOKEN=your_telegram_token_here
   NEWS_API_TOKEN=your_gnews_api_key_here
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d --build
   ```

### 📦 Local Development

If you prefer running without Docker:

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Bot**
   ```bash
   python app/main.py
   ```

## 📖 Usage

Start a chat with your bot and use these commands:

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and register your user |
| `/subscribe` | Choose topics to follow |
| `/mysubscriptions` | View and manage your active subscriptions |
| `/news` | Get latest headlines for a specific topic instantly |
| `/mynews` | Get a personalized digest of all your topics |
| `/set_delivery_time` | Set daily delivery time (e.g., `/set_delivery_time 08:30`) |
| `/get_delivery_time` | Check your current schedule settings |
| `/help` | Show all available commands |

## 🏗️ Architecture

The project follows a modular asynchronous architecture:
- **`main.py`**: Handles Telegram updates and command routing
- **`news_fetcher.py`**: Manages business logic, database operations, and API interactions
- **Database**: Stores users, subscriptions, and caches news articles to minimize API usage

## 🤝 Contributing

Contributions are welcome! Please check out our [Contributing Guidelines](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built with ❤️ by [Yohannes]*