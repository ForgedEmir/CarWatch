import requests
import json
import os
import logging
import random
import time as _time
import unicodedata
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def _headers() -> dict:
    return {"User-Agent": random.choice(_USER_AGENTS)}


def _get(url: str, **kwargs) -> "requests.Response | None":
    for attempt in range(3):
        try:
            r = requests.get(url, **kwargs)
            if r.status_code == 429:
                logger.warning(f"Rate limited, waiting {2**attempt}s...")
                _time.sleep(2 ** attempt)
                continue
            return r
        except requests.Timeout:
            if attempt < 2:
                _time.sleep(1)
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            break
    return None


# Belgian city → zip code prefix mapping for AutoScout24 region filtering
BELGIAN_REGIONS = {
    "liège": ["4000", "4020", "4030", "4040", "4050", "4100", "4120", "4130", "4140", "4160", "4170", "4180", "4190", "4210", "4217", "4250", "4257", "4260", "4280", "4287", "4300", "4317", "4340", "4347", "4350", "4357", "4360", "4367", "4370", "4380", "4400", "4420", "4430", "4431", "4432", "4450", "4451", "4452", "4453", "4460", "4470", "4480", "4490", "4500", "4520", "4530", "4537", "4540", "4550", "4557", "4560", "4570", "4577", "4590", "4600", "4601", "4602", "4606", "4607", "4608", "4610", "4620", "4621", "4623", "4624", "4630", "4631", "4632", "4633", "4650", "4651", "4652", "4653", "4654", "4670", "4671", "4672", "4680", "4681", "4682", "4683", "4684", "4690", "4700", "4701", "4710", "4711", "4720", "4721", "4728", "4730", "4731", "4732", "4750", "4760", "4761", "4770", "4771", "4780", "4782", "4783", "4784", "4790", "4791", "4800", "4801", "4802", "4820", "4821", "4830", "4831", "4837", "4840", "4841", "4845", "4850", "4851", "4852", "4860", "4861", "4877", "4880", "4890", "4900", "4910", "4920", "4950", "4960", "4970", "4980", "4983", "4987", "4990"],
    "bruxelles": ["1000", "1010", "1020", "1030", "1040", "1050", "1060", "1070", "1080", "1081", "1082", "1083", "1090", "1100", "1101", "1110", "1120", "1130", "1140", "1150", "1160", "1170", "1180", "1190", "1200", "1210"],
    "brussels":  ["1000", "1010", "1020", "1030", "1040", "1050", "1060", "1070", "1080", "1090", "1100", "1110", "1120", "1130", "1140", "1150", "1160", "1170", "1180", "1190", "1200", "1210"],
    "gand":      ["9000", "9030", "9031", "9032", "9040", "9041", "9042", "9050", "9051", "9052"],
    "gent":      ["9000", "9030", "9031", "9032", "9040", "9041", "9042", "9050", "9051", "9052"],
    "anvers":    ["2000", "2018", "2020", "2030", "2040", "2050", "2060", "2100", "2110", "2140", "2150", "2160", "2170", "2180"],
    "antwerpen": ["2000", "2018", "2020", "2030", "2040", "2050", "2060", "2100", "2110", "2140", "2150", "2160", "2170", "2180"],
    "namur":     ["5000", "5001", "5002", "5003", "5004", "5020", "5021", "5022", "5024", "5030", "5031", "5032"],
    "charleroi": ["6000", "6001", "6010", "6020", "6030", "6031", "6032", "6040", "6041", "6042"],
    "bruges":    ["8000", "8020", "8200", "8210", "8301", "8310", "8340"],
    "brugge":    ["8000", "8020", "8200", "8210", "8301", "8310", "8340"],
    "mons":      ["7000", "7010", "7011", "7012", "7020", "7021", "7022", "7024"],
    "leuven":    ["3000", "3001", "3010", "3012", "3018", "3020", "3053", "3054"],
    "louvain":   ["3000", "3001", "3010", "3012", "3018", "3020"],
    "hasselt":   ["3500", "3501", "3510", "3511", "3512"],
}

# Pre-normalized lookup built once at import time
_REGIONS_NORM: dict = {
    unicodedata.normalize("NFD", k.lower()).encode("ascii", "ignore").decode(): v
    for k, v in BELGIAN_REGIONS.items()
}


def _normalize(s: str) -> str:
    """Lowercase + strip accents for fuzzy matching."""
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()


def _region_matches_zip(region: str, zip_code: str) -> bool:
    """Check if a zip code belongs to a Belgian region."""
    if not region or not zip_code:
        return False
    key = _normalize(region.strip())
    prefixes = _REGIONS_NORM.get(key)
    if prefixes:
        return any(zip_code.startswith(p) for p in prefixes)
    return key in _normalize(zip_code)


def _is_excluded(text: str, exclude: str) -> bool:
    """Return True if any comma-separated keyword from exclude appears in text."""
    if not exclude:
        return False
    text_low = text.lower()
    return any(kw.strip().lower() in text_low for kw in exclude.split(",") if kw.strip())


def _get_postcode(region: str) -> str:
    """Return the main postcode for a Belgian city name (used for radius search)."""
    if not region:
        return ""
    key = _normalize(region.strip())
    prefixes = _REGIONS_NORM.get(key)
    return prefixes[0] if prefixes else ""


# ── Seen-IDs dedup (PostgreSQL) ───────────────────────────────────────────────

def load_seen() -> set:
    from database import SessionLocal
    from models import SeenId
    db = SessionLocal()
    try:
        rows = db.query(SeenId.listing_id).all()
        return {r.listing_id for r in rows}
    except Exception:
        return set()
    finally:
        db.close()


def save_seen(new_ids: list):
    if not new_ids:
        return
    from database import SessionLocal
    from models import SeenId
    db = SessionLocal()
    try:
        existing = {r.listing_id for r in db.query(SeenId.listing_id).all()}
        for lid in new_ids:
            if lid not in existing:
                db.add(SeenId(listing_id=lid))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"save_seen error: {e}")
    finally:
        db.close()


# ── Generic Adevinta scraper (2ememain + 2dehands share the same API) ─────────

def _scrape_adevinta(params: dict, domain: str, source_name: str, id_prefix: str) -> list:
    """Reusable scraper for Adevinta-powered sites (2ememain.be, 2dehands.be)."""
    results = []

    # Build region radius params once — server-side is far more accurate than city-name matching
    postcode = _get_postcode(params.get("region", ""))
    radius_params = f"&postcode={postcode}&distanceMeters={int(params.get('radius_km', 25)) * 1000}" if postcode else ""

    for page in range(3):
        offset = page * 30
        base = f"https://www.{domain}/lrp/api/search?l1CategoryId=91"
        if params.get("price_max"):
            base += f"&priceTo={int(params['price_max']) * 100}"
        if params.get("price_min") and float(params.get("price_min", 0) or 0) > 0:
            base += f"&priceFrom={int(params['price_min']) * 100}"
        if params.get("make"):
            base += f"&query={params['make']}"
        base += radius_params
        base += f"&limit=30&offset={offset}&sortBy=DATE&sortOrder=DECREASING"

        try:
            logger.info(f"[{source_name}] GET {base}")
            r = _get(base, headers=_headers(), timeout=15)
            if r is None:
                break
            data = r.json()
            listings = data.get("listings", [])
            logger.info(f"[{source_name}] page {page}: {len(listings)} listings from API")
            if not listings:
                break

            for item in listings:
                attrs     = {a["key"]: a["value"] for a in item.get("attributes", [])}
                make_val  = attrs.get("brand", "").lower()
                model_val = attrs.get("model", "").lower()

                if params.get("make"):
                    target = params["make"].lower()
                    if target not in make_val and target not in model_val and target not in item.get("title", "").lower():
                        continue

                # Region is already filtered server-side via postcode+radius; no client-side city filter needed

                item_text = json.dumps(item).lower()
                if _is_excluded(item_text, params.get("exclude", "")):
                    continue

                if params.get("fuel"):
                    f = params["fuel"].lower()
                    if f == "essence" and not any(k in item_text for k in ["essence", "benzine", "benzin"]):
                        continue
                    elif f == "diesel" and "diesel" not in item_text:
                        continue
                    elif f == "hybride" and not any(k in item_text for k in ["hybrid", "hybride"]):
                        continue
                    elif f == "electrique" and not any(k in item_text for k in ["electri", "elektr", "elec"]):
                        continue

                if params.get("transmission"):
                    t = params["transmission"].lower()
                    if t == "manuelle" and not any(k in item_text for k in ["manuel", "manuele"]):
                        continue
                    elif t == "automatique" and not any(k in item_text for k in ["automat", "automaat"]):
                        continue

                year_str = attrs.get("constructionYear", "?")
                km_str   = attrs.get("mileage", "?")

                if params.get("year_min") and params["year_min"] != "":
                    try:
                        if int(year_str) < int(params["year_min"]):
                            continue
                    except Exception:
                        pass

                if params.get("km_max") and params["km_max"] != "":
                    try:
                        k = int("".join(filter(str.isdigit, str(km_str))))
                        if k > int(params["km_max"]):
                            continue
                    except Exception:
                        pass

                price_cents = item.get("priceInfo", {}).get("priceCents", 0)
                price = price_cents / 100 if price_cents else 0
                if price <= 0:
                    continue
                if params.get("price_min") and params["price_min"] != "" and float(params["price_min"] or 0) > 0:
                    try:
                        if price < float(params["price_min"]):
                            continue
                    except Exception:
                        pass
                if params.get("price_max") and params["price_max"] != "":
                    try:
                        if price > float(params["price_max"]):
                            continue
                    except Exception:
                        pass

                image_url = ""
                if item.get("pictures"):
                    pic = item["pictures"][0]
                    image_url = pic.get("largeUrl") or pic.get("mediumUrl") or pic.get("url", "")
                elif item.get("imageUrls"):
                    image_url = item["imageUrls"][0]
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url

                results.append({
                    "id":     f"{id_prefix}_{item['itemId']}",
                    "source": source_name,
                    "title":  item.get("title", ""),
                    "price":  price,
                    "year":   year_str,
                    "km":     km_str,
                    "city":   item.get("location", {}).get("cityName", ""),
                    "url":    f"https://www.{domain}" + item.get("vipUrl", f"/v/autos/{item['itemId']}"),
                    "image":  image_url,
                    "date":   item.get("date", ""),
                })
        except Exception as e:
            logger.error(f"[{source_name}] page {page} error: {e}")
            break
    return results


# ── 2ememain ─────────────────────────────────────────────────────────────────

def build_2ememain_url(params: dict, offset: int = 0) -> str:
    base = "https://www.2ememain.be/lrp/api/search?l1CategoryId=91"
    if params.get("price_max"):
        base += f"&priceTo={int(params['price_max']) * 100}"
    if params.get("price_min") and float(params.get("price_min", 0) or 0) > 0:
        base += f"&priceFrom={int(params['price_min']) * 100}"
    if params.get("make"):
        base += f"&query={params['make']}"
    postcode = _get_postcode(params.get("region", ""))
    if postcode:
        base += f"&postcode={postcode}&distanceMeters={int(params.get('radius_km', 25)) * 1000}"
    base += f"&limit=30&offset={offset}&sortBy=DATE&sortOrder=DECREASING"
    return base


def scrape_2dehands(params: dict) -> list:
    """2dehands.be — Dutch-language Flemish sister site, same Adevinta API."""
    return _scrape_adevinta(params, "2dehands.be", "2dehands", "2dh")


def scrape_2ememain(params: dict) -> list:
    results = []
    for page in range(3):
        url = build_2ememain_url(params, offset=page * 30)
        try:
            logger.info(f"[2ememain] GET {url}")
            r = _get(url, headers=_headers(), timeout=15)
            if r is None:
                break
            data = r.json()
            listings = data.get("listings", [])
            logger.info(f"[2ememain] page {page}: {len(listings)} listings from API")
            if not listings:
                break

            for item in listings:
                attrs = {a["key"]: a["value"] for a in item.get("attributes", [])}
                make  = attrs.get("brand", "").lower()
                model = attrs.get("model", "").lower()

                if params.get("make"):
                    target = params["make"].lower()
                    if target not in make and target not in model and target not in item.get("title", "").lower():
                        continue

                # Region is already filtered server-side via postcode+radius in build_2ememain_url()

                item_text = json.dumps(item).lower()
                if _is_excluded(item_text, params.get("exclude", "")):
                    continue

                if params.get("fuel"):
                    f = params["fuel"].lower()
                    if f == "essence" and not any(k in item_text for k in ["essence", "benzine", "benzin"]):
                        continue
                    elif f == "diesel" and "diesel" not in item_text:
                        continue
                    elif f == "hybride" and not any(k in item_text for k in ["hybrid", "hybride"]):
                        continue
                    elif f == "electrique" and not any(k in item_text for k in ["electri", "elektr", "élec"]):
                        continue

                if params.get("transmission"):
                    t = params["transmission"].lower()
                    if t == "manuelle" and not any(k in item_text for k in ["manuel", "manuele"]):
                        continue
                    elif t == "automatique" and not any(k in item_text for k in ["automat", "automaat"]):
                        continue

                year_str = attrs.get("constructionYear", "?")
                km_str   = attrs.get("mileage", "?")

                if params.get("year_min") and params["year_min"] != "":
                    try:
                        if int(year_str) < int(params["year_min"]):
                            continue
                    except Exception:
                        pass

                if params.get("km_max") and params["km_max"] != "":
                    try:
                        k = int("".join(filter(str.isdigit, str(km_str))))
                        if k > int(params["km_max"]):
                            continue
                    except Exception:
                        pass

                price_cents = item.get("priceInfo", {}).get("priceCents", 0)
                price = price_cents / 100 if price_cents else 0

                # Skip listings with no price (price on request)
                if price <= 0:
                    continue

                if params.get("price_min") and params["price_min"] != "" and float(params["price_min"]) > 0:
                    try:
                        if price < float(params["price_min"]):
                            continue
                    except Exception:
                        pass
                if params.get("price_max") and params["price_max"] != "":
                    try:
                        if price > float(params["price_max"]):
                            continue
                    except Exception:
                        pass

                image_url = ""
                if item.get("pictures"):
                    pic = item["pictures"][0]
                    image_url = pic.get("largeUrl") or pic.get("mediumUrl") or pic.get("url", "")
                elif item.get("imageUrls"):
                    image_url = item["imageUrls"][0]
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url

                results.append({
                    "id":     f"2em_{item['itemId']}",
                    "source": "2ememain",
                    "title":  item.get("title", ""),
                    "price":  price,
                    "year":   year_str,
                    "km":     km_str,
                    "city":   item.get("location", {}).get("cityName", ""),
                    "url":    "https://www.2ememain.be" + item.get("vipUrl", f"/v/autos/{item['itemId']}"),
                    "image":  image_url,
                    "date":   item.get("date", ""),
                })
        except Exception as e:
            logger.error(f"[2ememain] page {page} error: {e}")
            break
    return results


# ── AutoScout24 ───────────────────────────────────────────────────────────────

def build_autoscout_url(params: dict) -> str:
    # Put make directly in the path so AutoScout24 filters server-side
    make_slug = params["make"].lower().replace(" ", "-") if params.get("make") else ""
    base = f"https://www.autoscout24.be/fr/lst/{make_slug}" if make_slug else "https://www.autoscout24.be/fr/lst"
    base += "?cy=B&atype=C&sort=age&desc=0"
    if params.get("price_min") and params["price_min"] != "" and int(params["price_min"]) > 0:
        base += f"&pricefrom={int(params['price_min'])}"
    if params.get("price_max") and params["price_max"] != "":
        base += f"&priceto={int(params['price_max'])}"
    if params.get("year_min") and params["year_min"] != "" and int(params["year_min"]) > 0:
        base += f"&fregfrom={int(params['year_min'])}"
    if params.get("km_max") and params["km_max"] != "" and int(params["km_max"]) > 0:
        base += f"&kmto={int(params['km_max'])}"
    # Transmission server-side filter
    if params.get("transmission"):
        t = params["transmission"].lower()
        if "manuelle" in t or "manuel" in t:
            base += "&gear=M"
        elif "automatique" in t or "automat" in t:
            base += "&gear=A"
    return base


def scrape_autoscout24(params: dict) -> list:
    all_results = []
    for page in range(1, 4):
        url = build_autoscout_url(params) + f"&page={page}"
        try:
            r = _get(url, headers=_headers(), timeout=15)
            if r is None:
                break
            soup = BeautifulSoup(r.text, "lxml")
            articles = soup.find_all("article", attrs={"data-testid": "list-item"})
            if not articles:
                break

            for a in articles:
                title_tag = a.find("h2") or a.find(attrs={"data-testid": "regular-headline"})
                title = title_tag.text.strip() if title_tag else (
                    a.get("data-make", "") + " " + a.get("data-model", "")
                )

                # Make was already filtered server-side via URL path, skip double-check
                a_text = a.text.lower()
                if _is_excluded(a_text, params.get("exclude", "")):
                    continue

                if params.get("fuel"):
                    f = params["fuel"].lower()
                    if f == "essence" and not any(k in a_text for k in ["essence", "benzine", "benzin"]):
                        continue
                    elif f == "diesel" and "diesel" not in a_text:
                        continue
                    elif f == "hybride" and not any(k in a_text for k in ["hybrid", "hybride"]):
                        continue
                    elif f == "electrique" and not any(k in a_text for k in ["electri", "elektr", "élec"]):
                        continue

                if params.get("transmission"):
                    t = params["transmission"].lower()
                    if t == "manuelle" and not any(k in a_text for k in ["manuel", "manuele", "manuell"]):
                        continue
                    elif t == "automatique" and not any(k in a_text for k in ["automat", "automaat"]):
                        continue

                price_raw = a.get("data-price", "0")
                try:
                    price = float(price_raw)
                except Exception:
                    price = 0

                if params.get("price_min") and params["price_min"] != "":
                    try:
                        if price < float(params["price_min"]):
                            continue
                    except Exception:
                        pass
                if params.get("price_max") and params["price_max"] != "":
                    try:
                        if price > float(params["price_max"]):
                            continue
                    except Exception:
                        pass

                guid = a.get("data-guid", "")
                # data-first-registration format: "07-2007" (MM-YYYY) — extract year only
                reg_raw = a.get("data-first-registration", "")
                if reg_raw and "-" in reg_raw:
                    year = reg_raw.split("-")[-1]   # "07-2007" → "2007"
                elif reg_raw and len(reg_raw) >= 4:
                    year = reg_raw[:4]
                else:
                    year = "?"
                km        = a.get("data-mileage", "?")
                zip_code  = a.get("data-listing-zip-code", "")

                # ── Region filter ────────────────────────────────────────────
                if params.get("region"):
                    if not _region_matches_zip(params["region"], zip_code):
                        continue

                link_tag    = a.find("a", href=True)
                url_listing = link_tag["href"] if link_tag else ""
                if url_listing.startswith("/"):
                    url_listing = "https://www.autoscout24.be" + url_listing
                if not url_listing or not url_listing.startswith("http"):
                    continue

                # Try data-src first (lazy-loaded images), fall back to src
                img_tag   = a.find("img")
                image_url = ""
                if img_tag:
                    image_url = (img_tag.get("data-src") or img_tag.get("src") or "")

                all_results.append({
                    "id":     f"as24_{guid}",
                    "source": "AutoScout24",
                    "title":  title,
                    "price":  price,
                    "year":   year,
                    "km":     km,
                    "city":   zip_code,
                    "url":    url_listing,
                    "image":  image_url,
                    "date":   "Récent",
                })
        except Exception as e:
            logger.error(f"[autoscout24] page {page} error: {e}")
            break
    return all_results


# ── Orchestrator (parallel) ───────────────────────────────────────────────────

def run_scrape(params: dict, return_all: bool = False) -> list:
    """Run both scrapers in parallel and return results."""
    seen_set = load_seen()

    logger.info(f"Scraping — exclude={params.get('exclude')!r}")
    logger.info("Scraping 2ememain & AutoScout24 in parallel...")
    all_results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(scrape_2ememain,    params): "2ememain",
            executor.submit(scrape_2dehands,    params): "2dehands",
            executor.submit(scrape_autoscout24, params): "AutoScout24",
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                items = future.result()
                logger.info(f"  [{source}] {len(items)} listings")
                all_results.extend(items)
            except Exception as e:
                logger.error(f"  [{source}] scraper error: {e}")

    new_results = [r for r in all_results if r["id"] not in seen_set]

    save_seen([r["id"] for r in new_results])

    logger.info(f"Total: {len(all_results)} | New: {len(new_results)}")

    return all_results if return_all else new_results


if __name__ == "__main__":
    import pprint
    results = run_scrape({"make": "BMW", "price_min": 2000, "price_max": 8000})
    pprint.pprint(results[:3])
