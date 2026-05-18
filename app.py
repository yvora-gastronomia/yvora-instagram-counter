import os
from datetime import datetime
from io import BytesIO
import base64
import html
from pathlib import Path

import qrcode
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOCAL_LOGO = BASE_DIR / "yvora_logo.JPG"

PROFILE_URL = os.getenv("PROFILE_URL", "https://www.instagram.com/yvora.restaurante/")
BRAND_NAME = os.getenv("BRAND_NAME", "YVORA")
BRAND_SUBTITLE = os.getenv("BRAND_SUBTITLE", "Carnes, queijos e vinhos em uma jornada sensorial")
FOLLOW_CTA = os.getenv("FOLLOW_CTA", "Experimente, combine, descubra.")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN", "").strip()
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "17841445877381461").strip()
MILESTONE_TARGET = int(os.getenv("MILESTONE_TARGET", "20000"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "30"))
MOCK_FOLLOWERS_START = int(os.getenv("MOCK_FOLLOWERS_START", "19330"))
FEATURED_DISH = os.getenv("FEATURED_DISH", "Tutano assado, queijo Tulha e steak tartare")
FEATURED_PAIRING = os.getenv("FEATURED_PAIRING", "Uma experiência de gordura nobre, sal, textura e vinho")
WINE_EXPLORER_URL = os.getenv("WINE_EXPLORER_URL", "https://yvora-wine.streamlit.app/")
MENU_SENSORIAL_URL = os.getenv("MENU_SENSORIAL_URL", "https://yvora-menu-sensorial.streamlit.app/")
LOGO_URL = os.getenv("LOGO_URL", "")


def file_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


def logo_src() -> str:
    if LOGO_URL:
        return LOGO_URL
    return file_data_uri(LOCAL_LOGO)


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


@st.cache_data(ttl=90, show_spinner=False)
def get_media() -> list[dict]:
    try:
        fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,thumbnail_url"
        data = graph_get(f"/{IG_BUSINESS_ID}/media", {"fields": fields, "limit": "18"}, timeout=15)
        items = []
        for item in data.get("data", []) or []:
            media_type = item.get("media_type") or ""
            thumb = item.get("thumbnail_url") if media_type == "VIDEO" else item.get("media_url")
            caption = (item.get("caption") or "").strip()
            if not thumb:
                continue
            items.append({
                "id": item.get("id", ""),
                "caption": caption[:180],
                "media_type": media_type,
                "thumb_url": thumb or item.get("media_url") or "",
                "permalink": item.get("permalink") or "",
                "timestamp": item.get("timestamp") or "",
                "like_count": int(item.get("like_count") or 0),
                "comments_count": int(item.get("comments_count") or 0),
                "score": int(item.get("like_count") or 0) + int(item.get("comments_count") or 0) * 3,
            })
        return items
    except Exception:
        return []


def esc(value: str) -> str:
    return html.escape(str(value or ""))


def qr_data_uri(url: str) -> str:
    img = qrcode.make(url)
    bio = BytesIO()
    img.save(bio, format="PNG")
    return "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("utf-8")


def media_card(item: dict, title: str) -> str:
    image = esc(item.get("thumb_url"))
    caption = esc(item.get("caption") or "Conteúdo YVORA")
    permalink = esc(item.get("permalink") or PROFILE_URL)
    likes = int(item.get("like_count") or 0)
    comments = int(item.get("comments_count") or 0)
    tag = "Reel" if item.get("media_type") == "VIDEO" else "Post"
    return f"""
      <a class="post-card" href="{permalink}" target="_blank">
        <div class="post-title">{esc(title)}</div>
        <img src="{image}" alt="{caption}">
        <div class="post-meta"><span>{tag}</span><span>♥ {likes} · 💬 {comments}</span></div>
        <div class="post-caption">{caption}</div>
      </a>
    """


def render():
    st.set_page_config(page_title="YVORA Social Wall", page_icon="🍷", layout="wide", initial_sidebar_state="collapsed")
    status = get_status()
    media = get_media()
    latest = media[:3]
    top_posts = sorted(media, key=lambda x: x.get("score", 0), reverse=True)[:3]
    hero = top_posts[0] if top_posts else (latest[0] if latest else {})
    followers = f"{status['followers_count']:,}".replace(",", ".")
    media_count = status.get("media_count", 0)
    source_label = "Meta API" if status.get("source") == "meta" else "Modo fallback"
    instagram_qr = qr_data_uri(PROFILE_URL)
    menu_qr = qr_data_uri(MENU_SENSORIAL_URL)
    wine_qr = qr_data_uri(WINE_EXPLORER_URL)
    hero_img = esc(hero.get("thumb_url") or "")
    hero_caption = esc(hero.get("caption") or "Os últimos conteúdos do YVORA aparecerão aqui assim que o token permitir leitura de mídia.")
    logo = logo_src()
    logo_html = f'<img class="brand-logo-img" src="{esc(logo)}" alt="YVORA">' if logo else '<div class="brand-logo-text">YVORA</div>'
    latest_html = "".join(media_card(item, "Último post") for item in latest) or '<div class="empty-card">Configure USER_ACCESS_TOKEN para carregar os últimos posts do Instagram.</div>'
    top_html = "".join(media_card(item, "Maior interação") for item in top_posts) or '<div class="empty-card">Os posts de maior interação aparecerão aqui.</div>'

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Montserrat:wght@400;500;600;700&display=swap');
#MainMenu, footer, header {{visibility: hidden;}}
.stApp {{background: #faf6ef; color: #47372E;}}
.block-container {{padding: 2.2rem 3rem 1.5rem 3rem; max-width: 100%;}}
.yvora-shell {{min-height: 90vh; border: 1px solid #D7CFC3; border-radius: 30px; padding: 28px; background: linear-gradient(135deg, #faf6ef 0%, #efe7dd 50%, #f5efe7 100%); box-shadow: 0 24px 70px rgba(71,55,46,.12);}}
.topbar {{display: flex; justify-content: space-between; align-items: center; gap: 24px; border-bottom: 1px solid #D7CFC3; padding-bottom: 18px;}}
.brand {{display: flex; align-items: center; gap: 18px;}}
.brand-mark {{width: 92px; height: 92px; border-radius: 50%; background: #F3EADF; border: 1px solid #C8B7A3; display:flex; align-items:center; justify-content:center; overflow:hidden;}}
.brand-logo-img {{width: 100%; height: 100%; object-fit: contain; padding: 6px;}}
.brand-logo-text {{font-family: 'Cormorant Garamond', serif; color: #47372E; font-size: 24px; letter-spacing: 2px; font-weight: 700;}}
.brand-title {{font-family: 'Cormorant Garamond', serif; font-size: 62px; letter-spacing: 7px; color: #47372E; line-height: .9;}}
.brand-subtitle {{font-family: 'Montserrat', sans-serif; font-size: 17px; color: #7A685B; margin-top: 8px;}}
.status-pill {{font-family:'Montserrat', sans-serif; border:1px solid #C8B7A3; border-radius:999px; padding:12px 18px; color:#7A685B; background:rgba(255,255,255,.45);}}
.grid {{display:grid; grid-template-columns: .85fr 1.15fr; gap: 28px; margin-top: 28px;}}
.panel {{background: rgba(255,255,255,.58); border:1px solid #D7CFC3; border-radius: 26px; padding: 28px;}}
.counter-label {{font-family:'Montserrat', sans-serif; color:#B06F2F; font-size:14px; text-transform:uppercase; letter-spacing:2.8px; font-weight:700;}}
.counter {{font-family:'Cormorant Garamond', serif; font-size:118px; line-height:1; color:#47372E; margin-top:10px;}}
.handle {{font-family:'Montserrat', sans-serif; color:#7A685B; font-size:20px;}}
.cta {{font-family:'Montserrat', sans-serif; margin-top:18px; color:#47372E; font-size:22px; font-weight:600;}}
.dish-title {{font-family:'Cormorant Garamond', serif; color:#47372E; font-size:38px; margin-top:30px;}}
.dish-text {{font-family:'Montserrat', sans-serif; color:#7A685B; font-size:18px; line-height:1.55; margin-top:8px;}}
.qrs {{display:flex; gap:14px; margin-top:28px;}}
.qr {{flex:1; text-align:center; border:1px solid #D7CFC3; border-radius:18px; padding:12px; background:#faf6ef;}}
.qr img {{width:100%; max-width:120px; border-radius:10px;}}
.qr p {{font-family:'Montserrat', sans-serif; margin:8px 0 0; color:#7A685B; font-size:13px;}}
.section-title {{font-family:'Cormorant Garamond', serif; font-size:34px; color:#47372E; margin-bottom:14px;}}
.hero {{display:grid; grid-template-columns:.95fr 1.05fr; gap:18px; align-items:stretch;}}
.hero-img {{width:100%; height:310px; object-fit:cover; border-radius:22px; background:#E7DDD2;}}
.hero-img[src=""] {{display:none;}}
.hero-copy {{font-family:'Montserrat', sans-serif; color:#7A685B; font-size:18px; line-height:1.55; border-left:3px solid #B06F2F; padding-left:18px;}}
.posts-grid {{display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-top:14px;}}
.post-card {{display:block; text-decoration:none; color:#47372E; background:#faf6ef; border:1px solid #D7CFC3; border-radius:20px; overflow:hidden; min-height: 330px;}}
.post-card img {{width:100%; height:180px; object-fit:cover; display:block; background:#E7DDD2;}}
.post-title {{font-family:'Montserrat', sans-serif; color:#B06F2F; font-weight:700; font-size:12px; letter-spacing:1.8px; text-transform:uppercase; padding:14px 14px 8px;}}
.post-meta {{display:flex; justify-content:space-between; gap:8px; font-family:'Montserrat', sans-serif; color:#9C948B; font-size:12px; padding:10px 14px 0;}}
.post-caption {{font-family:'Montserrat', sans-serif; color:#7A685B; font-size:13px; line-height:1.45; padding:8px 14px 16px;}}
.empty-card {{font-family:'Montserrat', sans-serif; color:#7A685B; border:1px dashed #C8B7A3; border-radius:18px; padding:22px; background:#faf6ef;}}
.footer-note {{font-family:'Montserrat', sans-serif; color:#9C948B; margin-top:18px; font-size:13px;}}
@media (max-width: 1100px) {{.grid,.hero {{grid-template-columns:1fr;}} .posts-grid {{grid-template-columns:1fr;}} .counter {{font-size:82px;}} .brand-title {{font-size:46px;}}}}
</style>
<script>setInterval(function() {{ window.location.reload(); }}, 90000);</script>
<div class="yvora-shell">
  <div class="topbar">
    <div class="brand">
      <div class="brand-mark">{logo_html}</div>
      <div>
        <div class="brand-title">{esc(BRAND_NAME)}</div>
        <div class="brand-subtitle">{esc(BRAND_SUBTITLE)}</div>
      </div>
    </div>
    <div class="status-pill">{source_label} · atualizado em {datetime.now().strftime('%d/%m %H:%M')}</div>
  </div>
  <div class="grid">
    <div class="panel">
      <div class="counter-label">Seguidores no Instagram</div>
      <div class="counter">{followers}</div>
      <div class="handle">@{esc(status.get('username', 'yvora.restaurante'))} · {media_count} publicações</div>
      <div class="cta">{esc(FOLLOW_CTA)}</div>
      <div class="dish-title">{esc(FEATURED_DISH)}</div>
      <div class="dish-text">{esc(FEATURED_PAIRING)}</div>
      <div class="qrs">
        <div class="qr"><img src="{instagram_qr}"><p>Instagram</p></div>
        <div class="qr"><img src="{menu_qr}"><p>Menu Sensorial</p></div>
        <div class="qr"><img src="{wine_qr}"><p>Wine Explorer</p></div>
      </div>
      <div class="footer-note">Rua dos Pinheiros · São Paulo</div>
    </div>
    <div>
      <div class="panel">
        <div class="section-title">Destaque de interação</div>
        <div class="hero">
          <img class="hero-img" src="{hero_img}" alt="Post YVORA">
          <div class="hero-copy">{hero_caption}</div>
        </div>
      </div>
      <div class="panel" style="margin-top:18px;">
        <div class="section-title">Últimos posts</div>
        <div class="posts-grid">{latest_html}</div>
      </div>
      <div class="panel" style="margin-top:18px;">
        <div class="section-title">Maior interação</div>
        <div class="posts-grid">{top_html}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
