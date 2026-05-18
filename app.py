import os
import time
from datetime import datetime
from pathlib import Path
from io import BytesIO

import qrcode
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, send_file

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

load_dotenv()

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

PROFILE_URL = os.getenv("PROFILE_URL", "https://www.instagram.com/yvora.restaurante/")
BRAND_NAME = os.getenv("BRAND_NAME", "YVORA")
BRAND_SUBTITLE = os.getenv("BRAND_SUBTITLE", "Carnes, queijos e vinhos em uma jornada sensorial")
FOLLOW_CTA = os.getenv("FOLLOW_CTA", "Explore o universo YVORA")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")

USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN", "").strip()
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "17841445877381461").strip()

MILESTONE_TARGET = int(os.getenv("MILESTONE_TARGET", "20000"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "15"))
MEDIA_CACHE_SECONDS = int(os.getenv("MEDIA_CACHE_SECONDS", "60"))
MOCK_FOLLOWERS_START = int(os.getenv("MOCK_FOLLOWERS_START", "19330"))

FEATURED_DISH = os.getenv("FEATURED_DISH", "Tutano assado, queijo Tulha e steak tartare")
FEATURED_PAIRING = os.getenv("FEATURED_PAIRING", "Uma experiência de gordura nobre, sal, textura e vinho")
WINE_EXPLORER_URL = os.getenv("WINE_EXPLORER_URL", "https://yvora-wine.streamlit.app/")
MENU_SENSORIAL_URL = os.getenv("MENU_SENSORIAL_URL", "https://yvora-menu-sensorial.streamlit.app/")

_cache = {"ts": 0.0, "followers_count": 0, "source": "mock", "source_error": ""}
_media_cache = {"ts": 0.0, "data": None, "source": "mock", "source_error": ""}


def now_str() -> str:
    return datetime.now().strftime("%d/%m %H:%M:%S")


def _graph_get(path: str, params: dict | None = None, timeout: int = 10) -> dict:
    if not USER_ACCESS_TOKEN:
        raise RuntimeError("USER_ACCESS_TOKEN vazio no ambiente")
    if not path.startswith("/"):
        path = "/" + path
    url = f"https://graph.facebook.com/{GRAPH_VERSION}{path}"
    query = dict(params or {})
    query["access_token"] = USER_ACCESS_TOKEN
    response = requests.get(url, params=query, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_followers_from_meta() -> int:
    if not IG_BUSINESS_ID:
        raise RuntimeError("IG_BUSINESS_ID vazio no ambiente")
    data = _graph_get(f"/{IG_BUSINESS_ID}", params={"fields": "followers_count"}, timeout=10)
    return int(data.get("followers_count", 0))


def get_followers_count_cached():
    now = time.time()
    if now - _cache["ts"] < CACHE_SECONDS:
        return _cache["followers_count"], _cache["source"], _cache["ts"], _cache.get("source_error", "")
    try:
        count = fetch_followers_from_meta()
        source = "meta"
        source_error = ""
    except Exception as exc:
        count = MOCK_FOLLOWERS_START
        source = "mock"
        source_error = str(exc)
    _cache.update({"ts": now, "followers_count": count, "source": source, "source_error": source_error})
    return count, source, _cache["ts"], _cache.get("source_error", "")


def fetch_media_from_meta(limit: int = 25) -> dict:
    if not IG_BUSINESS_ID:
        raise RuntimeError("IG_BUSINESS_ID vazio no ambiente")
    fields = ",".join([
        "id",
        "caption",
        "media_type",
        "media_url",
        "permalink",
        "timestamp",
        "like_count",
        "comments_count",
        "thumbnail_url",
    ])
    data = _graph_get(f"/{IG_BUSINESS_ID}/media", params={"fields": fields, "limit": str(limit)}, timeout=12)
    normalized = []
    for item in data.get("data", []) or []:
        media_type = item.get("media_type") or ""
        thumb = item.get("thumbnail_url") if media_type == "VIDEO" else item.get("media_url")
        caption = (item.get("caption") or "").strip()
        normalized.append({
            "id": item.get("id"),
            "caption": caption[:220],
            "media_type": media_type,
            "thumb_url": thumb or item.get("media_url") or "",
            "permalink": item.get("permalink") or "",
            "timestamp": item.get("timestamp") or "",
            "like_count": int(item.get("like_count") or 0),
            "comments_count": int(item.get("comments_count") or 0),
        })
    last_post = normalized[0] if normalized else None
    reels = [x for x in normalized if "/reel/" in x.get("permalink", "").lower() or x.get("media_type") == "VIDEO"]
    featured_reel = max(reels, key=lambda x: x["like_count"]) if reels else None
    return {
        "last_post": last_post,
        "featured_reel": featured_reel,
        "likes_last10": sum(x["like_count"] for x in normalized[:10]),
        "items": normalized[:12],
    }


def get_media_cached():
    now = time.time()
    if now - _media_cache["ts"] < MEDIA_CACHE_SECONDS and _media_cache["data"]:
        return _media_cache["data"], _media_cache["source"], _media_cache["ts"], ""
    try:
        data = fetch_media_from_meta()
        source = "meta"
        source_error = ""
    except Exception as exc:
        data = {"last_post": None, "featured_reel": None, "likes_last10": 0, "items": []}
        source = "mock"
        source_error = str(exc)
    _media_cache.update({"ts": now, "data": data, "source": source, "source_error": source_error})
    return data, source, now, source_error


def template_payload(vertical: bool = False):
    return {
        "milestone_target": MILESTONE_TARGET,
        "brand_name": BRAND_NAME,
        "brand_subtitle": BRAND_SUBTITLE,
        "follow_cta": FOLLOW_CTA,
        "profile_url": PROFILE_URL,
        "featured_dish": FEATURED_DISH,
        "featured_pairing": FEATURED_PAIRING,
        "wine_explorer_url": WINE_EXPLORER_URL,
        "menu_sensorial_url": MENU_SENSORIAL_URL,
        "vertical": vertical,
    }


@app.route("/")
def index():
    return render_template("index.html", **template_payload(vertical=False))


@app.route("/vertical")
def vertical():
    return render_template("index.html", **template_payload(vertical=True))


@app.route("/healthz")
def healthz():
    return jsonify(status="ok", app=BRAND_NAME)


@app.route("/api/status")
def api_status():
    count, source, _, source_error = get_followers_count_cached()
    return jsonify(
        followers_count=count,
        last_updated=now_str(),
        profile_url=PROFILE_URL,
        milestone_target=MILESTONE_TARGET,
        source=source,
        source_error=source_error,
        graph_version=GRAPH_VERSION,
        brand_name=BRAND_NAME,
        featured_dish=FEATURED_DISH,
        featured_pairing=FEATURED_PAIRING,
    )


@app.route("/api/media")
def api_media():
    data, source, _, source_error = get_media_cached()
    return jsonify(media=data, last_updated=now_str(), source=source, source_error=source_error)


@app.route("/qr.png")
def qr_png():
    img = qrcode.make(PROFILE_URL)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return send_file(bio, mimetype="image/png")


@app.route("/qr-menu.png")
def qr_menu_png():
    img = qrcode.make(MENU_SENSORIAL_URL)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return send_file(bio, mimetype="image/png")


@app.route("/qr-wine.png")
def qr_wine_png():
    img = qrcode.make(WINE_EXPLORER_URL)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return send_file(bio, mimetype="image/png")


def main():
    port = int(os.getenv("PORT", "8501"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
