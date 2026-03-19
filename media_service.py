import asyncio
import aiohttp
import logging
from pathlib import Path
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("static/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


async def download_and_optimize_image(url: str, listing_id: str) -> str:
    """
    Downloads an image asynchronously, resizes to max 800 px wide, saves as WebP.
    Returns the relative URL for the frontend, or '' on failure.
    """
    if not url:
        return ""

    filename    = f"{listing_id}.webp"
    filepath    = MEDIA_DIR / filename
    relative    = f"/static/media/{filename}"

    if filepath.exists():
        return relative

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning(f"Image {listing_id}: HTTP {resp.status}")
                    return ""
                content = await resp.read()

        img = Image.open(BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > 800:
            ratio  = 800 / img.width
            img    = img.resize((800, int(img.height * ratio)), Image.Resampling.LANCZOS)
        img.save(filepath, "webp", quality=80)
        return relative

    except Exception as e:
        logger.warning(f"Image download failed [{listing_id}]: {e}")
        return ""


async def batch_process_images(items: list) -> list:
    """
    Downloads images for all items concurrently.
    Updates item["image"] with the local WebP path on success.
    """
    tasks = []
    indices = []

    for i, item in enumerate(items):
        img = item.get("image", "")
        if img and not img.startswith("/static/media"):
            tasks.append(download_and_optimize_image(img, item["id"]))
            indices.append(i)

    if not tasks:
        return items

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in zip(indices, results):
        if isinstance(result, str) and result:
            items[idx]["image"] = result   # replace with local path
        # on failure, keep the original remote URL

    return items
