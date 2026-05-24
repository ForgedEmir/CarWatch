# Contributing to CarWatch

Thanks for your interest.

## Quick Start

```bash
git clone https://github.com/ForgedEmir/CarWatch.git
cd CarWatch
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# configure Telegram bot token + target chat ID
python main.py
```

## What's Helpful

- **New sources** — additional Belgian car listing sites (AutoGids, etc.).
- **Scraper robustness** — handle site structure changes, CAPTCHAs, rate limiting.
- **Deal scoring** — better price prediction models.
- **Notifications** — more granular alert configuration.

## PR Guidelines

1. Branch from `main`. Name: `feat/description` or `fix/description`.
2. One change per PR.
3. Respect robots.txt and rate limits of target sites.
4. Do not expose personal Telegram chat IDs or bot tokens.

## Code Style

- Python: standard PEP 8.
- Async code preferred for I/O-bound scraping operations.
