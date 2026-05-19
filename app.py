import os
from datetime import datetime
from io import BytesIO
import base64
import html
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import qrcode
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOCAL_LOGO = BASE_DIR / "yvora_logo.JPG"
STATE_FILE = BASE_DIR / ".last_followers_count"
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

PROFILE_URL = os.getenv("PROFILE_URL", "https://www.instagram.com/yvora.restaurante/")
BRAND_NAME = os.getenv("BRAND_NAME", "YVORA")
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "Bem-vindo à comunidade YVORA de experiências gastronômicas")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v25.0")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN", "").strip()
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "17841445877381461").strip()
MEDIA_CACHE_SECONDS = int(os.getenv("MEDIA_CACHE_SECONDS", "60"))
PARTNERS_CACHE_SECONDS = int(os.getenv("PARTNERS_CACHE_SECONDS", "60"))
MOCK_FOLLOWERS_START = int(os.getenv("MOCK_FOLLOWERS_START", "19330"))
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "10"))
WINE_EXPLORER_URL = os.getenv("WINE_EXPLORER_URL", "https://yvora-wine.streamlit.app/")
MENU_SENSORIAL_URL = os.getenv("MENU_SENSORIAL_URL", "https://yvora-menu-sensorial.streamlit.app/")
PARTNERS_SHEET_ID = os.getenv("PARTNERS_SHEET_ID", "1s1dGQZGG1A5M-6yD5fyggy4otmS8zQFl_GRBOiU32CI")
PARTNERS_SHEET_NAME = os.getenv("PARTNERS_SHEET_NAME", "Sheet1")

BRAZIL_FLAG_SVG = """
<svg class='br-flag' viewBox='0 0 120 84' xmlns='http://www.w3.org/2000/svg' aria-label='Bandeira do Brasil'>
  <rect width='120' height='84' rx='10' fill='#009739'/>
  <path d='M60 10 L110 42 L60 74 L10 42 Z' fill='#FFDF00'/>
  <circle cx='60' cy='42' r='18' fill='#002776'/>
  <path d='M43 38 C53 34 67 34 77 39' stroke='white' stroke-width='4' fill='none'/>
</svg>
""".strip()


def now_sp() -> datetime:
    return datetime.now(SAO_PAULO_TZ)


def read_previous_count() -> int | None:
    try:
        if STATE_FILE.exists():
            return int(STATE_FILE.read_text().strip())
    except Exception:
        return None
    return None


def write_previous_count(value: int) -> None:
    try:
        STATE_FILE.write_text(str(int(value)))
    except Exception:
        pass


def file_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


def drive_image_url(url: str) -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    patterns = [r"/file/d/([a-zA-Z0-9_-]+)", r"id=([a-zA-Z0-9_-]+)", r"/d/([a-zA-Z0-9_-]+)"]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w1600"
    return text


def image_data_uri_from_url(url: str) -> str:
    final_url = drive_image_url(url)
    if not final_url:
        return ""
    try:
        response = requests.get(final_url, timeout=12)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
        if "image" not in content_type:
            content_type = "image/jpeg"
        encoded = base64.b64encode(response.content).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return final_url


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


def get_status() -> dict:
    try:
        data = graph_get(f"/{IG_BUSINESS_ID}", {"fields": "username,followers_count,media_count"})
        return {"followers_count": int(data.get("followers_count", 0)), "media_count": int(data.get("media_count", 0)), "username": data.get("username", "yvora.restaurante"), "source": "Meta API", "error": ""}
    except Exception as exc:
        return {"followers_count": MOCK_FOLLOWERS_START, "media_count": 34, "username": "yvora.restaurante", "source": "Fallback", "error": str(exc)}


@st.cache_data(ttl=MEDIA_CACHE_SECONDS, show_spinner=False)
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


@st.cache_data(ttl=PARTNERS_CACHE_SECONDS, show_spinner=False)
def get_partners() -> list[dict]:
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{PARTNERS_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={PARTNERS_SHEET_NAME}"
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status()
        import csv
        from io import StringIO
        rows = list(csv.DictReader(StringIO(response.text)))
        partners = []
        for row in rows:
            name = (row.get("Parceiros") or row.get("parceiros") or row.get("Nome") or row.get("nome") or "").strip()
            image = (row.get("URL") or row.get("url") or row.get("Imagem") or row.get("imagem") or "").strip()
            active = str(row.get("Ativo") or row.get("ativo") or "0").strip()
            order_raw = str(row.get("Ordem") or row.get("ordem") or "999").strip()
            if active != "1" or not name or not image:
                continue
            try:
                order = int(float(order_raw.replace(",", ".")))
            except Exception:
                order = 999
            partners.append({"name": name, "image": image_data_uri_from_url(image), "order": order})
        return sorted(partners, key=lambda x: (x["order"], x["name"]))
    except Exception:
        return []


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


def partner_banner(partners: list[dict]) -> str:
    if not partners:
        return ""
    cards = "".join([f'<div class="partner-card"><img src="{esc(item["image"])}" alt="{esc(item["name"])}" title="{esc(item["name"])}"></div>' for item in partners])
    return f"""
    <div class="partner-bar">
      <div class="partner-label">Parceiros YVORA</div>
      <div class="partner-logos">{cards}</div>
    </div>
"""


def render():
    st.set_page_config(page_title="YVORA", page_icon="🍷", layout="wide", initial_sidebar_state="collapsed")
    st_autorefresh(interval=REFRESH_SECONDS * 1000, key="yvora_autorefresh")

    current_time = now_sp()
    status = get_status()
    media_result = get_media()
    partners = get_partners()
    media = media_result.get("items", [])
    latest = media[:4]
    top_posts = sorted(media, key=lambda x: x.get("score", 0), reverse=True)[:4]
    current_count = int(status.get("followers_count", 0))
    previous_count = read_previous_count()
    delta = 0 if previous_count is None else current_count - previous_count
    write_previous_count(current_count)
    followers = f"{current_count:,}".replace(",", ".")
    logo_uri = file_data_uri(LOCAL_LOGO)
    instagram_qr = qr_data_uri(PROFILE_URL)
    menu_qr = qr_data_uri(MENU_SENSORIAL_URL)
    wine_qr = qr_data_uri(WINE_EXPLORER_URL)
    error_msg = media_result.get("error") or status.get("error") or ""
    latest_html = "".join(post_card(item, "Último post") for item in latest) or f'<div class="empty">Sem posts carregados.<br><small>{esc(error_msg)}</small></div>'
    top_html = "".join(post_card(item, "Maior interação") for item in top_posts) or f'<div class="empty">Sem dados de interação carregados.<br><small>{esc(error_msg)}</small></div>'
    logo_html = f'<img src="{logo_uri}" class="logo-img" alt="YVORA">' if logo_uri else '<div class="logo-text">YVORA</div>'
    should_burst = delta > 0
    celebration_items = ["🍷", BRAZIL_FLAG_SVG, "🍽️", "🥂", BRAZIL_FLAG_SVG, "🍷", "🍽️", "🥂", BRAZIL_FLAG_SVG, "🍷", "🍽️", "🥂"]
    burst_html = "".join([f'<div class="celebration-burst w{i}">{celebration_items[i]}</div>' for i in range(len(celebration_items))]) if should_burst else ""
    welcome_icons = f"<span>🍷</span><span class='inline-br-flag'>{BRAZIL_FLAG_SVG}</span><span>🍽️</span>"
    welcome_html = f'<div class="welcome-toast"><div class="welcome-kicker">Novo seguidor</div><div class="welcome-title">{esc(WELCOME_MESSAGE)}</div><div class="welcome-icons">{welcome_icons}</div></div>' if should_burst else ""
    change_html = f'<div class="change positive">+{delta} novo seguidor</div>' if delta == 1 else (f'<div class="change positive">+{delta} novos seguidores</div>' if delta > 1 else "")
    partners_html = partner_banner(partners)

    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
#MainMenu, footer, header {{visibility: hidden;}}
.stApp {{background: #f7f0e7; color: #211915; font-family: 'Montserrat', sans-serif;}}
.block-container {{padding: 24px 34px 22px 34px; max-width: 100%;}}
.shell {{max-width: 1480px; margin: 0 auto;}}
.header {{display:flex; justify-content:space-between; align-items:center; gap:24px; margin-bottom:22px;}}
.brand {{display:flex; align-items:center; gap:18px; flex:0 0 auto;}}
.logo-box {{width:86px; height:86px; border-radius:22px; background:#fff; border:1px solid #ddd0c0; display:flex; align-items:center; justify-content:center; overflow:hidden;}}
.logo-img {{width:100%; height:100%; object-fit:contain; padding:7px;}}
.logo-text {{font-size:22px; font-weight:800; letter-spacing:2px;}}
.title {{font-size:42px; font-weight:800; letter-spacing:2px; color:#211915; line-height:1;}}
.subtitle {{font-size:15px; color:#6f6257; margin-top:8px;}}
.pill {{background:#fff; border:1px solid #ddd0c0; border-radius:999px; padding:12px 18px; color:#6f6257; font-size:14px; white-space:nowrap; flex:0 0 auto;}}
.partner-bar {{height:86px; flex:1 1 auto; min-width:380px; max-width:620px; background:#fffaf4; border:1px solid #ddd0c0; border-radius:22px; padding:10px 16px; display:grid; grid-template-columns: 120px 1fr; gap:12px; align-items:center; overflow:hidden; box-shadow:0 10px 24px rgba(57,43,35,.07);}}
.partner-label {{font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#a7672d; font-weight:800; line-height:1.25;}}
.partner-logos {{display:flex; gap:10px; align-items:center; justify-content:space-around; overflow:hidden; height:100%;}}
.partner-card {{width:104px; height:54px; background:#fff; border:1px solid #eadfd1; border-radius:14px; display:flex; align-items:center; justify-content:center; overflow:hidden; flex:0 0 auto; padding:8px;}}
.partner-card img {{width:100%; height:100%; object-fit:contain; display:block;}}
.grid {{display:grid; grid-template-columns: 410px 1fr; gap:22px; align-items:start;}}
.card {{background:#fffaf4; border:1px solid #ddd0c0; border-radius:24px; padding:24px; box-shadow:0 12px 30px rgba(57,43,35,.08); position:relative; overflow:hidden;}}
.counter-label {{font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#a7672d; font-weight:800;}}
.counter {{font-size:76px; line-height:1; font-weight:800; color:#211915; margin:14px 0 8px;}}
.handle {{font-size:17px; color:#6f6257; font-weight:600;}}
.change {{display:inline-block; margin-top:8px; padding:8px 12px; border-radius:999px; background:#f3e0c9; color:#8b4a19; font-size:13px; font-weight:800;}}
.main-qr {{margin-top:22px; padding:18px; background:#fff; border:1px solid #eadfd1; border-radius:22px; text-align:center;}}
.main-qr-heading {{font-size:25px; line-height:1.25; font-weight:800; color:#211915; margin-bottom:14px;}}
.main-qr-heading span {{color:#a7672d;}}
.main-qr img {{width:250px; max-width:100%; display:block; margin:0 auto;}}
.main-qr-title {{font-size:22px; font-weight:800; color:#211915; margin-top:12px;}}
.main-qr-subtitle {{font-size:14px; color:#6f6257; margin-top:6px;}}
.metrics {{display:grid; grid-template-columns:1fr; gap:12px; margin-top:20px;}}
.metric {{background:#f7f0e7; border-radius:16px; padding:14px; border:1px solid #eadfd1;}}
.metric b {{display:block; font-size:22px; color:#211915;}}
.metric span {{font-size:12px; color:#6f6257; text-transform:uppercase; letter-spacing:1px;}}
.small-qrs {{display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; margin-top:20px;}}
.qr {{background:#fff; border:1px solid #eadfd1; border-radius:14px; padding:8px; text-align:center;}}
.qr img {{width:100%; max-width:82px; display:block; margin:0 auto;}}
.qr span {{font-size:10px; color:#6f6257; font-weight:700;}}
.section-title {{font-size:22px; font-weight:800; color:#211915; margin:0 0 14px;}}
.posts {{display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px;}}
.post {{display:block; background:#fff; border:1px solid #eadfd1; border-radius:18px; overflow:hidden; text-decoration:none; color:#211915; min-height:310px;}}
.post img {{width:100%; height:170px; object-fit:cover; display:block; background:#eadfd1;}}
.post-body {{padding:12px;}}
.post-label {{font-size:11px; color:#a7672d; font-weight:800; text-transform:uppercase; letter-spacing:1.3px;}}
.post-stats {{font-size:13px; color:#6f6257; font-weight:700; margin-top:6px;}}
.post-caption {{font-size:12px; color:#6f6257; line-height:1.35; margin-top:7px;}}
.empty {{padding:22px; border:1px dashed #cdbdaa; border-radius:16px; color:#6f6257; font-size:14px;}}
.empty small {{display:block; margin-top:8px; color:#a7672d; word-break:break-word;}}
.stack {{display:flex; flex-direction:column; gap:18px;}}
.footer-note {{margin-top:18px; color:#8e8074; font-size:12px;}}
.welcome-toast {{position:fixed; top:34px; left:50%; transform:translateX(-50%); z-index:1000000; width:min(720px, 86vw); text-align:center; background:rgba(255,250,244,.96); border:1px solid #d7c6b2; border-radius:24px; padding:20px 26px; box-shadow:0 22px 60px rgba(57,43,35,.22); animation: welcomeToast 7.2s ease-out forwards;}}
.welcome-kicker {{font-size:12px; text-transform:uppercase; letter-spacing:2.5px; color:#a7672d; font-weight:800; margin-bottom:8px;}}
.welcome-title {{font-size:26px; line-height:1.25; color:#211915; font-weight:800;}}
.welcome-icons {{font-size:26px; margin-top:8px; display:flex; align-items:center; justify-content:center; gap:14px;}}
.inline-br-flag {{display:inline-flex; width:38px; height:27px; align-items:center; justify-content:center;}}
.br-flag {{width:100%; height:100%; display:block;}}
.celebration-burst {{position:fixed; bottom:-44px; font-size:46px; z-index:999999; animation: celebrationFloat 7.8s ease-out forwards; pointer-events:none; filter: drop-shadow(0 8px 10px rgba(0,0,0,.18)); width:52px; height:52px; display:flex; align-items:center; justify-content:center;}}
.celebration-burst .br-flag {{width:52px; height:36px; border-radius:6px;}}
.w0 {{left:6%; animation-delay:0s;}} .w1 {{left:13%; animation-delay:.16s;}} .w2 {{left:21%; animation-delay:.32s;}} .w3 {{left:30%; animation-delay:.48s;}} .w4 {{left:39%; animation-delay:.64s;}} .w5 {{left:48%; animation-delay:.80s;}} .w6 {{left:57%; animation-delay:.96s;}} .w7 {{left:66%; animation-delay:1.12s;}} .w8 {{left:75%; animation-delay:1.28s;}} .w9 {{left:83%; animation-delay:1.44s;}} .w10 {{left:91%; animation-delay:1.60s;}} .w11 {{left:96%; animation-delay:1.76s;}}
@keyframes celebrationFloat {{0% {{transform:translateY(0) scale(.58) rotate(-8deg); opacity:0;}} 12% {{opacity:1;}} 82% {{opacity:1;}} 100% {{transform:translateY(-110vh) scale(1.24) rotate(12deg); opacity:0;}}}}
@keyframes welcomeToast {{0% {{opacity:0; transform:translate(-50%, -18px) scale(.96);}} 12% {{opacity:1; transform:translate(-50%, 0) scale(1);}} 82% {{opacity:1; transform:translate(-50%, 0) scale(1);}} 100% {{opacity:0; transform:translate(-50%, -18px) scale(.98);}}}}
@media (max-width:1100px) {{.header {{flex-wrap:wrap;}} .partner-bar {{order:3; flex-basis:100%; max-width:none;}} .grid {{grid-template-columns:1fr;}} .posts {{grid-template-columns:repeat(2, 1fr);}} .counter {{font-size:58px;}} .welcome-title {{font-size:20px;}}}}
</style>
"""
    header_html = f"""
<div class="shell">
  {welcome_html}
  {burst_html}
  <div class="header">
    <div class="brand"><div class="logo-box">{logo_html}</div><div><div class="title">{esc(BRAND_NAME)}</div><div class="subtitle">@{esc(status.get('username'))}</div></div></div>
    {partners_html}
    <div class="pill">{esc(status.get('source'))} · atualizado às {current_time.strftime('%H:%M:%S')} · refresh {REFRESH_SECONDS}s</div>
  </div>
  <div class="grid">
"""
    left_html = f"""
<div class="card">
  <div class="counter-label">Seguidores no Instagram</div>
  <div class="counter">{followers}</div>
  <div class="handle">@{esc(status.get('username'))}</div>
  {change_html}
  <div class="main-qr"><div class="main-qr-heading">Siga o <span>YVORA no Instagram</span></div><img src="{instagram_qr}"><div class="main-qr-title">Aponte a câmera</div><div class="main-qr-subtitle">e acompanhe o YVORA</div></div>
  <div class="metrics"><div class="metric"><b>{int(status.get('media_count', 0))}</b><span>publicações</span></div></div>
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
    st.markdown(css + header_html + left_html + right_html + "</div></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
