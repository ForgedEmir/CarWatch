import os
import logging
import asyncio
import time
import hashlib
import json as _json
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union, Optional

from scraper import run_scrape
from database import engine, SessionLocal, Base
from models import Listing
from worker import start_background_scrape, get_task_state
from ai_analyzer import compute_deal_scores
import bot

Base.metadata.create_all(bind=engine)

API_SECRET = os.environ.get("API_SECRET", "")

def _check_key(x_api_key: str = Header(default="")):
    if API_SECRET and x_api_key != API_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

_cache: dict = {"ts": 0.0, "key": "", "data": None}
CACHE_TTL = 300  # 5 minutes

app = FastAPI(title="CarWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    if API_SECRET:
        html = html.replace(
            "</head>",
            f'<script>window.__API_KEY="{API_SECRET}";</script></head>',
            1,
        )
    return html


class ConfigUpdate(BaseModel):
    make:         str              = ""
    price_min:    Union[int, str]  = ""
    price_max:    Union[int, str]  = ""
    year_min:     Union[int, str]  = ""
    km_max:       Union[int, str]  = ""
    region:       str              = ""
    radius_km:    Union[int, str]  = 25
    exclude:      str              = ""
    fuel:         str              = ""
    transmission: str              = ""


@app.get("/api/config")
async def get_config():
    return bot.load_config()


@app.post("/api/config")
async def update_config(config: ConfigUpdate, _: None = Depends(_check_key)):
    cfg = bot.load_config()
    cfg.update(config.model_dump())
    bot.save_config(cfg)
    return {"status": "success", "config": cfg}


@app.get("/api/search")
async def search(_: None = Depends(_check_key)):
    cfg = bot.load_config()
    cfg_key = hashlib.md5(_json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL and _cache["key"] == cfg_key:
        return _cache["data"]
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: run_scrape(cfg, return_all=True))
    results = compute_deal_scores(results)
    results.sort(key=lambda r: r.get("deal_score") or 0, reverse=True)
    response = {"status": "success", "count": len(results), "results": results}
    _cache.update({"ts": now, "key": cfg_key, "data": response})
    return response


@app.post("/api/search/background")
async def search_background():
    """Start a background scrape. Poll /api/task for status."""
    cfg     = bot.load_config()
    started = start_background_scrape(cfg)
    return {"status": "started" if started else "already_running"}


@app.get("/api/task")
async def task_status():
    return get_task_state()


@app.get("/api/listings")
async def get_listings(
    source:    Optional[str]   = None,
    min_score: Optional[float] = None,
    limit:     int             = 100,
):
    """Query stored listings from the database."""
    db = SessionLocal()
    try:
        q = db.query(Listing).order_by(Listing.deal_score.desc().nullslast())
        if source:
            q = q.filter(Listing.source == source)
        if min_score is not None:
            q = q.filter(Listing.deal_score >= min_score)
        listings = q.limit(limit).all()
        return {
            "count": len(listings),
            "results": [
                {
                    "id":           l.id,
                    "source":       l.source,
                    "title":        l.title,
                    "price":        l.price,
                    "year":         l.year,
                    "km":           l.km,
                    "city":         l.city,
                    "fuel_type":    l.fuel_type,
                    "transmission": l.transmission,
                    "url":          l.url,
                    "image":        l.image_url,
                    "deal_score":   l.deal_score,
                    "has_carpass":  l.has_carpass,
                    "date":         str(l.date_scraped)[:10] if l.date_scraped else "",
                }
                for l in listings
            ],
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
