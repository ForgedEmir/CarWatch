import asyncio
import json
import os
import logging
import html
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from scraper import run_scrape
from ai_analyzer import compute_deal_scores
import pathlib

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DATA_DIR      = pathlib.Path(os.environ.get("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE   = DATA_DIR / "config.json"
TOKEN         = os.environ.get("TELEGRAM_TOKEN", "")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))


# ── Config helpers ────────────────────────────────────────────────────────────

def load_config() -> dict:
    default = {
        "make":           "",
        "price_min":      0,
        "price_max":      50000,
        "year_min":       0,
        "km_max":         300000,
        "region":         "",
        "radius_km":      25,
        "exclude":        "",
        "fuel":           "",
        "transmission":   "",
        "interval_hours": 2,
        "active":         True,
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
            default.update(saved)
    return default


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def _fmt(val, fallback="Tous"):
    return str(val) if val else fallback


def config_summary(cfg: dict) -> str:
    km_max   = cfg.get("km_max", 0)
    km_str   = f"{int(km_max):,} km" if km_max and str(km_max).strip() else "Illimité"
    lines = [
        "⚙️ *Configuration actuelle*",
        f"🚗 Marque : `{_fmt(cfg.get('make'))}`",
        f"💰 Prix : `{cfg.get('price_min', 0)}€ → {cfg.get('price_max', '∞')}€`",
        f"📅 Année min : `{_fmt(cfg.get('year_min'))}`",
        f"🛣️ KM max : `{km_str}`",
        f"📍 Région : `{_fmt(cfg.get('region'), 'Belgique entière')}`",
        f"⛽ Carburant : `{_fmt(cfg.get('fuel'))}`",
        f"⚙️ Boîte : `{_fmt(cfg.get('transmission'))}`",
        f"⏱️ Intervalle : toutes les `{cfg.get('interval_hours', 2)}h`",
        f"🟢 Actif : `{'Oui' if cfg.get('active') else 'Non'}`",
    ]
    return "\n".join(lines)


# ── Auth decorator ────────────────────────────────────────────────────────────

def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not ALLOWED_USER_ID:
            await update.message.reply_text(
                f"👋 Ton ID Telegram : `{user_id}`\n\nAjoute-le dans `.env` comme `ALLOWED_USER_ID`.",
                parse_mode="Markdown",
            )
            return
        if user_id != ALLOWED_USER_ID:
            await update.message.reply_text("❌ Accès refusé.")
            return
        return await func(update, context)
    return wrapper


# ── Command handlers ──────────────────────────────────────────────────────────

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    keyboard = [
        [InlineKeyboardButton("⚙️ Configurer", callback_data="menu_config")],
        [InlineKeyboardButton("🔍 Lancer une recherche", callback_data="search_now")],
        [InlineKeyboardButton("⏸️ Pause / Reprendre",   callback_data="toggle_active")],
    ]
    await update.message.reply_text(
        f"👋 *CarWatch actif !*\n\n{config_summary(cfg)}\n\nQue veux-tu faire ?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@restricted
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(config_summary(load_config()), parse_mode="Markdown")


@restricted
async def set_make(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /marque BMW  |  /marque tout")
        return
    cfg = load_config()
    value = " ".join(context.args)
    cfg["make"] = "" if value.lower() == "tout" else value
    save_config(cfg)
    await update.message.reply_text(f"✅ Marque : `{cfg['make'] or 'Toutes'}`", parse_mode="Markdown")


@restricted
async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /prix 2000 8000")
        return
    cfg = load_config()
    try:
        cfg["price_min"] = int(context.args[0])
        cfg["price_max"] = int(context.args[1])
        save_config(cfg)
        await update.message.reply_text(
            f"✅ Prix : `{cfg['price_min']}€ → {cfg['price_max']}€`", parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Format invalide. Usage: /prix 2000 8000")


@restricted
async def set_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /km 150000")
        return
    cfg = load_config()
    try:
        cfg["km_max"] = int(context.args[0])
        save_config(cfg)
        await update.message.reply_text(f"✅ KM max : `{cfg['km_max']:,} km`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Nombre invalide")


@restricted
async def set_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /annee 2015")
        return
    cfg = load_config()
    try:
        cfg["year_min"] = int(context.args[0])
        save_config(cfg)
        await update.message.reply_text(f"✅ Année min : `{cfg['year_min']}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Année invalide")


@restricted
async def set_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /region Liège  |  /region tout")
        return
    cfg = load_config()
    value = " ".join(context.args)
    cfg["region"] = "" if value.lower() == "tout" else value
    save_config(cfg)
    await update.message.reply_text(
        f"✅ Région : `{cfg['region'] or 'Belgique entière'}`", parse_mode="Markdown"
    )


@restricted
async def set_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /carburant essence  |  diesel  |  hybride  |  electrique  |  tout"
        )
        return
    cfg  = load_config()
    val  = context.args[0].lower()
    cfg["fuel"] = "" if val == "tout" else val
    save_config(cfg)
    await update.message.reply_text(f"✅ Carburant : `{cfg['fuel'] or 'Tous'}`", parse_mode="Markdown")


@restricted
async def set_transmission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /boite manuelle  |  automatique  |  tout")
        return
    cfg = load_config()
    val = context.args[0].lower()
    cfg["transmission"] = "" if val == "tout" else val
    save_config(cfg)
    await update.message.reply_text(
        f"✅ Boîte : `{cfg['transmission'] or 'Toutes'}`", parse_mode="Markdown"
    )


@restricted
async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /intervalle 2 (en heures)")
        return
    cfg = load_config()
    try:
        cfg["interval_hours"] = max(1, int(context.args[0]))
        save_config(cfg)
        if hasattr(context.application, "job_queue") and context.application.job_queue:
            update_job(context.application, update.effective_chat.id, cfg["interval_hours"])
        await update.message.reply_text(
            f"✅ Intervalle : toutes les `{cfg['interval_hours']}h`", parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Nombre invalide")


@restricted
async def search_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    await update.message.reply_text("🔍 Recherche en cours…")
    results = run_scrape(cfg, return_all=True)
    results = compute_deal_scores(results)
    await send_results(context.bot, update.effective_chat.id, results)


# ── Send results ──────────────────────────────────────────────────────────────

async def send_results(bot, chat_id: int, results: list):
    if not results:
        await bot.send_message(chat_id, "✅ Aucune nouvelle annonce trouvée.")
        return

    # Sort best deals first
    results = sorted(results, key=lambda x: x.get("deal_score") or 0, reverse=True)

    await bot.send_message(
        chat_id,
        f"🚗 <b>{len(results)} annonce(s) trouvée(s) !</b>",
        parse_mode="HTML",
    )

    import requests as req
    from io import BytesIO

    for r in results[:25]:
        score     = r.get("deal_score") or 0
        score_int = int(round(score))

        if score_int >= 75:
            score_label = f"🔥 Top Deal ({score_int}/100)"
        elif score_int >= 55:
            score_label = f"⭐ Bonne Affaire ({score_int}/100)"
        elif score_int >= 35:
            score_label = f"✅ Correct ({score_int}/100)"
        else:
            score_label = f"• Standard ({score_int}/100)"

        km_raw = r.get("km", "?")
        try:
            km_display = f"{int(str(km_raw).replace(' ', '').replace('.', '')):,} km"
        except Exception:
            km_display = str(km_raw)

        title = html.escape(r.get("title", ""))
        msg = (
            f"<b>{title}</b>\n"
            f"💰 {r.get('price', 0):.0f} € | 📅 {r.get('year', '?')} | 🛣️ {km_display}\n"
            f"📍 {r.get('city', '?')} — {r.get('source', '')}\n"
            f"{score_label}\n"
            f"🔗 {r.get('url', '')}"
        )

        image_url = r.get("image", "")
        sent = False
        if image_url and image_url.startswith("http"):
            try:
                img_data = req.get(
                    image_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                ).content
                photo = BytesIO(img_data)
                photo.name = "car.jpg"
                await bot.send_photo(chat_id, photo=photo, caption=msg, parse_mode="HTML")
                sent = True
            except Exception as e:
                logger.warning(f"Image send failed: {e}")

        if not sent:
            await bot.send_message(chat_id, msg, parse_mode="HTML", disable_web_page_preview=True)

        await asyncio.sleep(0.4)


# ── Callback buttons ──────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user_id = query.from_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await query.answer("❌ Accès refusé")
        return

    await query.answer()
    data = query.data

    if data == "search_now":
        cfg = load_config()
        await query.message.reply_text("🔍 Recherche en cours…")
        results = run_scrape(cfg, return_all=True)
        results = compute_deal_scores(results)
        await send_results(context.bot, query.message.chat_id, results)

    elif data == "toggle_active":
        cfg          = load_config()
        cfg["active"] = not cfg["active"]
        save_config(cfg)
        state = "🟢 Activé" if cfg["active"] else "🔴 Mis en pause"
        await query.message.reply_text(f"Surveillance {state}")

    elif data == "menu_config":
        msg = (
            "⚙️ *Commandes de configuration :*\n\n"
            "/marque BMW — Filtrer par marque\n"
            "/prix 2000 8000 — Budget min/max\n"
            "/km 150000 — Kilométrage max\n"
            "/annee 2015 — Année minimum\n"
            "/region Liège — Région belge\n"
            "/carburant essence — Type de carburant\n"
            "/boite automatique — Boîte de vitesse\n"
            "/intervalle 2 — Fréquence (heures)\n"
            "/status — Voir la config actuelle"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")


# ── Scheduler ─────────────────────────────────────────────────────────────────

async def scheduled_search_job(context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    if not cfg.get("active"):
        return
    chat_id = context.job.chat_id
    results = run_scrape(cfg)
    if results:
        results = compute_deal_scores(results)
        await send_results(context.bot, chat_id, results)


def update_job(app: Application, chat_id: int, interval_hours: int):
    for job in app.job_queue.get_jobs_by_name("search_job"):
        job.schedule_removal()
    app.job_queue.run_repeating(
        scheduled_search_job,
        interval=interval_hours * 3600,
        first=10,
        chat_id=chat_id,
        name="search_job",
    )
    logger.info(f"Scheduler updated: every {interval_hours}h")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        logger.error("❌ TELEGRAM_TOKEN non défini dans .env")
        return

    app = Application.builder().token(TOKEN).build()

    for cmd, handler in [
        ("start",      start),
        ("status",     status),
        ("marque",     set_make),
        ("prix",       set_price),
        ("km",         set_km),
        ("annee",      set_year),
        ("region",     set_region),
        ("carburant",  set_fuel),
        ("boite",      set_transmission),
        ("intervalle", set_interval),
        ("search",     search_now_cmd),
    ]:
        app.add_handler(CommandHandler(cmd, handler))

    app.add_handler(CallbackQueryHandler(button_handler))

    cfg = load_config()
    logger.info(f"✅ CarWatch démarré. Intervalle: {cfg['interval_hours']}h")

    async def post_init(app: Application):
        if ALLOWED_USER_ID:
            update_job(app, ALLOWED_USER_ID, cfg["interval_hours"])
            logger.info(f"✅ Scheduler actif : toutes les {cfg['interval_hours']}h")

    app.post_init = post_init
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
