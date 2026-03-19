"""
Deal Scorer for CarWatch.
Pure mathematical scoring based on price / year / km — no AI API needed.
"""
import logging

logger = logging.getLogger(__name__)


def compute_deal_scores(listings: list) -> list:
    """
    Compute a Deal Score (0-100) for each listing based on how competitive
    it is compared to the current batch.

    Formula:  Score = Σ (Wi × normalised_dimension)
    Weights:  Price 50% (lower = better)  |  KM 30% (lower = better)  |  Year 20% (newer = better)
    """
    if not listings:
        return listings

    prices = [l["price"] for l in listings if l.get("price") and l["price"] > 0]
    kms, years = [], []
    for l in listings:
        try:
            k = int(str(l.get("km", "0")).replace(" ", "").replace(".", ""))
            if k > 0:
                kms.append(k)
        except Exception:
            pass
        try:
            y = int(l.get("year", 0))
            if y > 1990:
                years.append(y)
        except Exception:
            pass

    if not prices or len(prices) < 2:
        for l in listings:
            l["deal_score"] = 50
        return listings

    p_min, p_max = min(prices), max(prices)
    k_min, k_max = (min(kms), max(kms)) if len(kms) >= 2 else (0, 300_000)
    y_min, y_max = (min(years), max(years)) if len(years) >= 2 else (2000, 2025)

    for l in listings:
        try:
            price = float(l.get("price", 0))
            try:
                km = int(str(l.get("km", "0")).replace(" ", "").replace(".", ""))
            except Exception:
                km = int((k_min + k_max) / 2)
            try:
                year = int(l.get("year", 0))
                if year < 1990:
                    year = int((y_min + y_max) / 2)
            except Exception:
                year = int((y_min + y_max) / 2)

            s_price = (p_max - price) / (p_max - p_min) if p_max != p_min else 0.5
            s_km    = (k_max - km)    / (k_max - k_min) if k_max != k_min else 0.5
            s_year  = (year  - y_min) / (y_max  - y_min) if y_max != y_min else 0.5

            raw = 0.50 * s_price + 0.30 * s_km + 0.20 * s_year
            l["deal_score"] = round(raw * 100, 1)
        except Exception:
            l["deal_score"] = 50

    return listings
