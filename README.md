# CarWatch 🚗

Real-time Belgian used car alert system. Scrapes **2ememain.be**, **2dehands.be** and **AutoScout24.be** in parallel, scores deals mathematically, and pushes **Telegram notifications** the moment a matching listing goes online.

## Features

- **Multi-source scraping** — 2ememain, 2dehands & AutoScout24 scraped in parallel
- **Deal scoring** — each car gets a 0–100 score based on price, mileage and year
- **Telegram alerts** — instant notification when a new matching car appears
- **Radius search** — search within X km of any Belgian city
- **Filters** — make, budget, mileage, year, fuel type, gearbox, region
- **Web dashboard** — clean React UI to browse and sort results
- **Deployable on Railway** in minutes

## Stack

- **Backend** — FastAPI + SQLAlchemy (SQLite / PostgreSQL)
- **Frontend** — React 18 (CDN, no build step) + Tailwind CSS
- **Bot** — python-telegram-bot with job queue scheduler
- **Scraping** — requests + BeautifulSoup4 + Adevinta JSON API

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/ForgedEmir/CarWatch.git
cd CarWatch
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS / Linux
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_TOKEN=your_token_from_botfather
ALLOWED_USER_ID=your_telegram_user_id
DATABASE_URL=sqlite:///./data/carwatch.db
DATA_DIR=./data
```

**Get your Telegram credentials:**
- `TELEGRAM_TOKEN` → talk to [@BotFather](https://t.me/BotFather), send `/newbot`
- `ALLOWED_USER_ID` → talk to [@userinfobot](https://t.me/userinfobot)

### 4. Run locally

In two separate terminals:

```bash
# Terminal 1 — web interface
uvicorn app:app --reload

# Terminal 2 — Telegram bot + scheduler
python bot.py
```

Open [http://localhost:8000](http://localhost:8000)

## Deploy on Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Add a **PostgreSQL** plugin — Railway sets `DATABASE_URL` automatically
4. Add environment variables: `TELEGRAM_TOKEN`, `ALLOWED_USER_ID`
5. Railway reads the `Procfile` and starts both the web server and the bot

## Telegram Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot and activate alerts |
| `/status` | Show current search configuration |
| `/marque BMW` | Set car make |
| `/prix 2000 8000` | Set price range (€) |
| `/km 150000` | Set max mileage |
| `/annee 2015` | Set minimum year |
| `/region Liège` | Set search region |
| `/carburant diesel` | Set fuel type |
| `/boite automatique` | Set gearbox type |
| `/intervalle 1` | Check every N hours (default: 2) |
| `/search` | Trigger an immediate search |

## Project Structure

```
app.py           → FastAPI server + web UI
bot.py           → Telegram bot + alert scheduler
scraper.py       → Parallel scraper (2ememain, 2dehands, AutoScout24)
ai_analyzer.py   → Mathematical deal scoring
worker.py        → Background thread + database save
database.py      → SQLAlchemy setup
models.py        → Listing model
media_service.py → Async image download + WebP optimization
data_pipeline.py → Data normalization helpers
static/          → React frontend (index.html, app.js, styles.css)
Procfile         → Railway process config
requirements.txt → Python dependencies
```

## License

MIT
