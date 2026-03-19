import re

def normalize_fuel(raw_fuel: str) -> str:
    """Standardize fuel types to common French terms."""
    if not raw_fuel:
        return "Autre"
        
    s = raw_fuel.lower()
    if any(k in s for k in ["essence", "benzine", "benzin"]):
        return "Essence"
    if "diesel" in s:
        return "Diesel"
    if any(k in s for k in ["hybride", "hybrid"]):
        return "Hybride"
    if any(k in s for k in ["electri", "elektr", "élec"]):
        return "Électrique"
    if any(k in s for k in ["lpg", "cng", "gaz"]):
        return "LPG/CNG"
        
    return "Autre"

def normalize_transmission(raw_trans: str) -> str:
    """Standardize transmission types."""
    if not raw_trans:
        return "Inconnue"
        
    s = raw_trans.lower()
    if any(k in s for k in ["manuel", "manuele", "manuell"]):
        return "Manuelle"
    if any(k in s for k in ["automat", "automaat"]):
        return "Automatique"
        
    return "Inconnue"

def clean_price(price_str: str) -> float:
    """Remove currency symbols and spaces from price strings."""
    if not price_str:
        return 0.0
    # Remove everything except digits and commas/dots
    cleaned = re.sub(r'[^\d,\.]', '', str(price_str))
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except:
        return 0.0

def clean_mileage(km_str: str) -> int:
    if not km_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', str(km_str))
    try:
        return int(cleaned)
    except:
        return 0
