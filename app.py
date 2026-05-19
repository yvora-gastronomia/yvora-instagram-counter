import os
import time
from datetime import datetime
from io import BytesIO

import qrcode
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROFILE_URL = os.getenv("PROFILE_URL", "https://www.instagram.com/yvora.restaurante/")
BRAND_NAME = os.getenv("BRAND_NAME", "YVORA")
BRAND_SUBTITLE = os.getenv("BRAND_SUBTITLE", "Carnes, queijos e vinhos em uma jornada sensorial")
FOLLOW_CTA = os.getenv("FOLLOW_CTA", "Explore o universo YVORA")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN", "").strip()
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "17841445877381461").strip()
MILESTONE_TARGET = int(os.getenv("MILESTONE_TARGET", "20000"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "15"))
MOCK_FOLLOWERS_START = int(os.getenv("MOCK_FOLLOWERS_START", "19330"))
FEATURED_DISH = os.getenv("FEATURED_DISH", "Tutano assado, queijo Tulha e steak tartare")
FEATURED_PAIRING = os.getenv("FEATURED_PAIRING", "Uma experiência de gordura nobre, sal, textura e vinho")
WINE_EXPLORER_URL = os.getenv("WINE_EXPLORER_URL", "https://yvora-wine.streamlit.app/")
MENU_SENSORIAL_URL = os.getenv("MENU_SENSORIAL_URL", "https://yvora-menu-sensorial.streamlit.app/")


def graph_get(path: str, params: dict | None = None, timeout: int = 10) -> dict:
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


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def get_status() -> dict:
    try:
        data = graph_get(f"/{IG_BUSINESS_ID}", {"fields": "username,followers_count,media_count"})
        return {
            "followers_count": int(data.get("followers_count", 0)),
            "media_count": int(data.get("media_count", 0)),
            "username": data.get("username", "yvora.restaurante"),
            "source": "meta",
            "error": "",
        }
    except Exception as exc:
        return {
            "followers_count": MOCK_FOLLOWERS_START,
            "media_count": 34,
            "username": "yvora.restaurante",
            "source": "mock",
            "error": str(exc),
        }


@st.cache_data(ttl=60, show_spinner=False)
def get_media() -> list[dict]:
    try:
        fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,thumbnail_url"
        data = graph_get(f"/{IG_BUSINESS_ID}/media", {"fields": fields, "limit": "12"}, timeout=12)
        items = []
        for item in data.get("data", []) or []:
            media_type = item.get("media_type") or ""
            thumb = item.get("thumbnail_url") if media_type == "VIDEO" else item.get("media_url")
            items.append({
                "caption": (item.get("caption") or "").strip()[:220],
                "media_type": media_type,
                "thumb_url": thumb or item.get("media_url") or "",
                "permalink": item.get("permalink") or "",
                "like_count": int(item.get("like_count") or 0),
                "comments_count": int(item.get("comments_count") or 0),
            })
        return items
    except Exception:
        return []


def qr_data_uri(url: str) -> str:
    img = qrcode.make(url)
    bio = BytesIO()
    img.save(bio, format="PNG")
    import base64
    return "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("utf-8")


def render():
    st.set_page_config(page_title="YVORA Social Wall", page_icon="🍷", layout="wide", initial_sidebar_state="collapsed")
    status = get_status()
    media = get_media()
    highlight = media[0] if media else {}
    image_url = highlight.get("thumb_url") or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200&auto=format&fit=crop"
    caption = highlight.get("caption") or "Explore pratos, harmonizações e experiências sensoriais do YVORA."
    followers = f"{status['followers_count']:,}".replace(",", ".")
    media_count = status.get("media_count", 0)
    source_label = "Meta API" if status.get("source") == "meta" else "Modo fallback"
    instagram_qr = qr_data_uri(PROFILE_URL)
    menu_qr = qr_data_uri(MENU_SENSORIAL_URL)
    wine_qr = qr_data_uri(WINE_EXPLORER_URL)

    st.markdown(f"""
<style>
#MainMenu, footer, header {{visibility: hidden;}}
.stApp {{background: radial-gradient(circle at top, #2b2118 0%, #0d0d0d 55%); color: #f5efe7;}}
.block-container {{padding: 3rem 4rem 2rem 4rem; max-width: 100%;}}
.yvora-grid {{display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 42px; min-height: 82vh;}}
.logo {{font-size: 76px; letter-spacing: 10px; color: #d6ab67; font-weight: 800;}}
.subtitle {{font-size: 27px; color: #f3e6d2; max-width: 760px; line-height: 1.35; margin-top: 8px;}}
.counter-box {{margin-top: 42px; padding: 40px; border: 1px solid rgba(214,171,103,.35); border-radius: 28px; background: rgba(255,255,255,.045);}}
.counter-label {{color: #d6ab67; font-size: 19px; text-transform: uppercase; letter-spacing: 3px;}}
.counter {{font-size: 124px; font-weight: 800; line-height: 1; margin-top: 18px; color: #fff;}}
.cta {{margin-top: 18px; font-size: 24px; color: #f3e6d2;}}
.dish-box {{margin-top: 34px; padding: 30px; border-left: 4px solid #d6ab67; background: rgba(255,255,255,.035);}}
.dish-title {{font-size: 34px; color: #fff; margin-bottom: 12px;}}
.dish-text {{font-size: 20px; line-height: 1.6; color: #e5d7c3;}}
.footer {{font-size: 16px; opacity: .68; margin-top: 34px;}}
.qr-group {{display: flex; gap: 18px; justify-content: center; margin-top: 12px;}}
.qr-card {{background: rgba(255,255,255,.055); border: 1px solid rgba(214,171,103,.25); padding: 16px; border-radius: 20px; text-align: center; width: 180px;}}
.qr-card img {{width: 100%; border-radius: 12px; background: white; padding: 8px;}}
.qr-card p {{margin: 12px 0 0 0; font-size: 16px; color: #f5efe7;}}
.media-highlight {{margin-top: 28px; border-radius: 24px; overflow: hidden; border: 1px solid rgba(214,171,103,.25); background: rgba(255,255,255,.045);}}
.media-highlight img {{width: 100%; height: 330px; object-fit: cover; display: block;}}
.media-caption {{padding: 18px; font-size: 16px; line-height: 1.5; color: #f3e6d2;}}
.source {{font-size: 14px; color: #b9aa95; margin-top: 8px;}}
@media (max-width: 900px) {{.yvora-grid {{grid-template-columns: 1fr;}} .counter {{font-size: 82px;}} .logo {{font-size: 54px;}} .qr-group {{flex-wrap: wrap;}}}}
</style>
<script>
setInterval(function() {{ window.location.reload(); }}, 60000);
</script>
<div class="yvora-grid">
  <div>
    <div class="logo">{BRAND_NAME}</div>
    <div class="subtitle">{BRAND_SUBTITLE}</div>
    <div class="counter-box">
      <div class="counter-label">Seguidores brindando com o YVORA</div>
      <div class="counter">{followers}</div>
      <div class="cta">{FOLLOW_CTA}</div>
      <div class="source">{source_label} • {media_count} publicações • atualizado em {datetime.now().strftime('%d/%m %H:%M')}</div>
    </div>
    <div class="dish-box">
      <div class="dish-title">{FEATURED_DISH}</div>
      <div class="dish-text">{FEATURED_PAIRING}</div>
    </div>
    <div class="footer">Rua dos Pinheiros • São Paulo • Experimente, combine, descubra.</div>
  </div>
  <div>
    <div class="qr-group">
      <div class="qr-card"><img src="{instagram_qr}"><p>Instagram</p></div>
      <div class="qr-card"><img src="{menu_qr}"><p>Menu Sensorial</p></div>
      <div class="qr-card"><img src="{wine_qr}"><p>Wine Explorer</p></div>
    </div>
    <div class="media-highlight">
      <img src="{image_url}">
      <div class="media-caption">{caption}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
