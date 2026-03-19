"""
Background task worker for CarWatch.
Runs the full scraping pipeline in a daemon thread so FastAPI stays responsive.
"""
import asyncio
import threading
import logging
from datetime import datetime

from database import SessionLocal
from models import Listing
from data_pipeline import normalize_fuel, normalize_transmission, clean_mileage

logger = logging.getLogger(__name__)

_task_state = {
    "status": "idle",   # idle | running | done | error
    "last_run": None,
    "results_count": 0,
    "error": None,
}


def get_task_state() -> dict:
    return dict(_task_state)


def _save_to_db(items: list):
    db = SessionLocal()
    saved = 0
    try:
        for item in items:
            if db.query(Listing).filter(Listing.id == item["id"]).first():
                continue

            year_val = None
            try:
                year_val = int(item.get("year", 0)) or None
            except Exception:
                pass

            listing = Listing(
                id           = item["id"],
                source       = item.get("source", ""),
                title        = item.get("title", ""),
                price        = float(item.get("price", 0)),
                year         = year_val,
                km           = clean_mileage(item.get("km", "0")),
                city         = item.get("city", ""),
                fuel_type    = normalize_fuel(item.get("fuel_type", "")),
                transmission = normalize_transmission(item.get("transmission", "")),
                url          = item.get("url", ""),
                image_url    = item.get("image", ""),
                date_scraped = datetime.utcnow(),
                deal_score   = item.get("deal_score"),
                has_carpass  = item.get("has_carpass"),
            )
            db.add(listing)
            saved += 1

        db.commit()
        logger.info(f"Saved {saved} new listings to DB")
    except Exception as e:
        db.rollback()
        logger.error(f"DB save error: {e}")
    finally:
        db.close()


def _run_scrape_sync(params: dict):
    global _task_state
    _task_state["status"] = "running"
    _task_state["error"]  = None

    try:
        import scraper
        from media_service import batch_process_images
        from ai_analyzer import compute_deal_scores

        logger.info("Worker: starting parallel scrape...")
        all_results = scraper.run_scrape(params, return_all=True)
        logger.info(f"Worker: {len(all_results)} raw listings")

        # Download & optimise images (async inside sync thread)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_results = loop.run_until_complete(batch_process_images(all_results))
        loop.close()

        # Compute deal scores (pure math, fast)
        all_results = compute_deal_scores(all_results)

        _save_to_db(all_results)

        _task_state["status"]        = "done"
        _task_state["last_run"]      = datetime.utcnow().isoformat()
        _task_state["results_count"] = len(all_results)

    except Exception as e:
        logger.error(f"Worker error: {e}")
        _task_state["status"] = "error"
        _task_state["error"]  = str(e)


def start_background_scrape(params: dict) -> bool:
    if _task_state["status"] == "running":
        logger.warning("Scrape already running, skipping")
        return False
    thread = threading.Thread(target=_run_scrape_sync, args=(params,), daemon=True)
    thread.start()
    return True
