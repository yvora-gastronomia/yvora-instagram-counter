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
BRAND_SUBTITLE = os.getenv("BRAND_SUBTITLE", "Contador Instagram")
FOLLOW_CTA = os.getenv("FOLLOW_CTA", "Siga nosso Instagram")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN", "").strip()
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "17841445877381461").strip()
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "30"))
MOCK_FOLLOWERS_START = int(os.getenv("MOCK_FOLLOWERS_START", "19330"))
WINE_EXPLORER_URL = os.getenv("WINE_EXPLORER_URL", "https://yvora-wine.streamlit.app/")
MENU_SENSORIAL_URL = os.getenv("MENU_SENSORIAL_URL", "https://yvora-menu-sensorial.streamlit.app/")


def file_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


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
        return {"followers_count": int(data.get("followers_count", 0)), "media_count": int(data.get("media_count", 0)), "username": data.get("username", "yvora.restaurante"), "source": "Meta API", "error": ""}
    except Exception as exc:
        return {"followers_count": MOCK_FOLLOWERS_START, "media_count": 34, "username": "yvora.restaurante", "source": "Fallback", "error": str(exc)}


@st.cache_data(ttl=90, show_spinner=False)
def get_media() -> dict:
    result = {"items": [], "error": ""}
    try:
        fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,thumbnail_url"
        data = graph_get(f"/{IG_BUSINESS_ID}/media", {"fields": fields, "limit": "18"}, timeout=15)
        for item in data.get("data", []) or []:
            media_type = item.get("media_type") or ""
            image = item.get("thumbnail_url") if media_type == "VIDEO" else item.get("media_url")
            if not image:
                continue
            likes = int(item.get("like_count") or 0)
            comments = int(item.get("comments_count") or 0)
            result["items"].append({"caption": (item.get("caption") or "").strip()[:130], "media_type": media_type, "image": image, "permalink": item.get("permalink") or PROFILE_URL, "like_count": likes, "comments_count": comments, "score": likes + comments * 3})
    except Exception as exc:
        result["error"] = str(exc)
    return result


def esc(value: str) -> str:
    return html.escape(str(value or ""))


def qr_data_uri(url: str) -> str:
    img = qrcode.make(url)
    bio = BytesIO()
    img.save(bio, format="PNG")
    return "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("utf-8")


def post_card(item: dict, label: str) -> str:
    media_type = "Reel" if item.get("media_type") == "VIDEO" else "Post"
    return f"""
<a class="post" href="{esc(item.get('permalink') or PROFILE_URL)}" target="_blank">
  <img src="{esc(item.get('image'))}" alt="Post YVORA">
  <div class="post-body">
    <div class="post-label">{esc(label)} · {media_type}</div>
    <div class="post-stats">♥ {int(item.get('like_count') or 0)} · 💬 {int(item.get('comments_count') or 0)}</div>
    <div class="post-caption">{esc(item.get('caption') or 'Conteúdo YVORA')}</div>
  </div>
</a>
"""


def render():
    st.set_page_config(page_title="YVORA Instagram Counter", page_icon="🍷", layout="wide", initial_sidebar_state="collapsed")
    status = get_status()
    media_result = get_media()
    media = media_result.get("items", [])
    latest = media[:4]
    top_posts = sorted(media, key=lambda x: x.get("score", 0), reverse=True)[:4]
    followers = f"{status['followers_count']:,}".replace(",", ".")
    logo_uri = file_data_uri(LOCAL_LOGO)
    instagram_qr = qr_data_uri(PROFILE_URL)
    menu_qr = qr_data_uri(MENU_SENSORIAL_URL)
    wine_qr = qr_data_uri(WINE_EXPLORER_URL)
    error_msg = media_result.get("error") or status.get("error") or ""
    latest_html = "".join(post_card(item, "Último post") for item in latest) or f'<div class="empty">Sem posts carregados.<br><small>{esc(error_msg)}</small></div>'
    top_html = "".join(post_card(item, "Maior interação") for item in top_posts) or f'<div class="empty">Sem dados de interação carregados.<br><small>{esc(error_msg)}</small></div>'
    logo_html = f'<img src="{logo_uri}" class="logo-img" alt="YVORA">' if logo_uri else '<div class="logo-text">YVORA</div>'

    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: #f7f0e7; color: #211915; font-family: 'Montserrat', sans-serif;}
.block-container {padding: 24px 34px 22px 34px; max-width: 100%;}
.shell {max-width: 1480px; margin: 0 auto;}
.header {display:flex; justify-content:space-between; align-items:center; gap:24px; margin-bottom:22px;}
.brand {display:flex; align-items:center; gap:18px;}
.logo-box {width:86px; height:86px; border-radius:22px; background:#fff; border:1px solid #ddd0c0; display:flex; align-items:center; justify-content:center; overflow:hidden;}
.logo-img {width:100%; height:100%; object-fit:contain; padding:7px;}
.logo-text {font-size:22px; font-weight:800; letter-spacing:2px;}
.title {font-size:42px; font-weight:800; letter-spacing:2px; color:#211915; line-height:1;}
.subtitle {font-size:15px; color:#6f6257; margin-top:8px;}
.pill {background:#fff; border:1px solid #ddd0c0; border-radius:999px; padding:12px 18px; color:#6f6257; font-size:14px; white-space:nowrap;}
.grid {display:grid; grid-template-columns: 410px 1fr; gap:22px; align-items:start;}
.card {background:#fffaf4; border:1px solid #ddd0c0; border-radius:24px; padding:24px; box-shadow:0 12px 30px rgba(57,43,35,.08);}
.counter-label {font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#a7672d; font-weight:800;}
.counter {font-size:76px; line-height:1; font-weight:800; color:#211915; margin:14px 0 8px;}
.handle {font-size:17px; color:#6f6257; font-weight:600;}
.cta {font-size:19px; font-weight:700; margin-top:18px; color:#211915;}
.main-qr {margin-top:22px; padding:18px; background:#fff; border:1px solid #eadfd1; border-radius:22px; text-align:center;}
.main-qr img {width:250px; max-width:100%; display:block; margin:0 auto;}
.main-qr-title {font-size:24px; font-weight:800; color:#211915; margin-top:12px;}
.main-qr-subtitle {font-size:14px; color:#6f6257; margin-top:6px;}
.metrics {display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:20px;}
.metric {background:#f7f0e7; border-radius:16px; padding:14px; border:1px solid #eadfd1;}
.metric b {display:block; font-size:22px; color:#211915;}
.metric span {font-size:12px; color:#6f6257; text-transform:uppercase; letter-spacing:1px;}
.small-qrs {display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; margin-top:20px;}
.qr {background:#fff; border:1px solid #eadfd1; border-radius:14px; padding:8px; text-align:center;}
.qr img {width:100%; max-width:82px; display:block; margin:0 auto;}
.qr span {font-size:10px; color:#6f6257; font-weight:700;}
.section-title {font-size:22px; font-weight:800; color:#211915; margin:0 0 14px;}
.posts {display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px;}
.post {display:block; background:#fff; border:1px solid #eadfd1; border-radius:18px; overflow:hidden; text-decoration:none; color:#211915; min-height:310px;}
.post img {width:100%; height:170px; object-fit:cover; display:block; background:#eadfd1;}
.post-body {padding:12px;}
.post-label {font-size:11px; color:#a7672d; font-weight:800; text-transform:uppercase; letter-spacing:1.3px;}
.post-stats {font-size:13px; color:#6f6257; font-weight:700; margin-top:6px;}
.post-caption {font-size:12px; color:#6f6257; line-height:1.35; margin-top:7px;}
.empty {padding:22px; border:1px dashed #cdbdaa; border-radius:16px; color:#6f6257; font-size:14px;}
.empty small {display:block; margin-top:8px; color:#a7672d; word-break:break-word;}
.stack {display:flex; flex-direction:column; gap:18px;}
.footer-note {margin-top:18px; color:#8e8074; font-size:12px;}
@media (max-width:1100px) {.grid {grid-template-columns:1fr;} .posts {grid-template-columns:repeat(2, 1fr);} .counter {font-size:58px;}}
</style>
"""
    header_html = f"""
<div class="shell">
  <div class="header">
    <div class="brand"><div class="logo-box">{logo_html}</div><div><div class="title">{esc(BRAND_NAME)}</div><div class="subtitle">{esc(BRAND_SUBTITLE)} · @{esc(status.get('username'))}</div></div></div>
    <div class="pill">{esc(status.get('source'))} · atualizado em {datetime.now().strftime('%d/%m %H:%M')}</div>
  </div>
  <div class="grid">
"""
    left_html = f"""
<div class="card">
  <div class="counter-label">Seguidores no Instagram</div>
  <div class="counter">{followers}</div>
  <div class="handle">@{esc(status.get('username'))}</div>
  <div class="main-qr"><img src="{instagram_qr}"><div class="main-qr-title">Siga nosso Instagram</div><div class="main-qr-subtitle">Aponte a câmera e acompanhe o YVORA</div></div>
  <div class="cta">{esc(FOLLOW_CTA)}</div>
  <div class="metrics"><div class="metric"><b>{int(status.get('media_count', 0))}</b><span>publicações</span></div><div class="metric"><b>{len(media)}</b><span>posts lidos</span></div></div>
  <div class="small-qrs"><div class="qr"><img src="{menu_qr}"><span>Menu Sensorial</span></div><div class="qr"><img src="{wine_qr}"><span>Wine Explorer</span></div></div>
  <div class="footer-note">Rua dos Pinheiros · São Paulo</div>
</div>
"""
    right_html = f"""
<div class="stack">
  <div class="card"><div class="section-title">Últimos posts</div><div class="posts">{latest_html}</div></div>
  <div class="card"><div class="section-title">Posts com maior interação</div><div class="posts">{top_html}</div></div>
</div>
"""
    close_html = "</div></div>"

    st.markdown(css + header_html + left_html + right_html + close_html, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
