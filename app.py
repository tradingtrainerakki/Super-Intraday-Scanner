import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import json
import time
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# NSEPYTHON - OI DATA KE LIYE
# ============================================================
try:
    from nsepython import nsefetch
    NSEPYTHON_AVAILABLE = True
except ImportError:
    NSEPYTHON_AVAILABLE = False

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

def get_ist_date():
    return datetime.now(IST).date()

st.set_page_config(
    page_title="SUPER SCANNER PRO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# FORCE SIDEBAR ALWAYS VISIBLE
# ============================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    transform: none !important; margin-left: 0 !important;
    visibility: visible !important; display: block !important;
    width: 320px !important; min-width: 320px !important;
}
</style>
<script>
window.addEventListener('load', function() {
    var sb = document.querySelector('section[data-testid="stSidebar"]');
    if (sb) { sb.style.transform='none'; sb.style.marginLeft='0'; sb.style.visibility='visible'; sb.style.display='block'; }
});
</script>
""", unsafe_allow_html=True)



# ============================================================
# AUTHENTICATION
# ============================================================
USERS = {
    "akki":  "Ca@1809",
    "admin": "admin123",
    "user1": "pass123",
    "user2": "pass456",
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if "theme" not in st.session_state:
    st.session_state.theme = "DARK"

if not st.session_state.authenticated:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap');
    html, body { background: #080c12 !important; font-family: 'JetBrains Mono', monospace !important; }
    .login-box {
        max-width: 420px; margin: 100px auto;
        background: linear-gradient(135deg, #0d1a26, #111820);
        border: 1px solid #1e2d3d; border-radius: 20px;
        padding: 50px; text-align: center;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .logo-super {
        font-family: 'Syne', sans-serif !important;
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #00ff88, #ff6b6b);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: 4px;
    }
    .tagline { color: #3a5a7a; font-size: 11px; letter-spacing: 4px; margin: 8px 0 30px; }
    </style>
    <div class="login-box">
        <div class="logo-super">🚀 SUPER SCANNER</div>
        <div class="tagline">30-MIN ORB + OI SPURTS + VWAP + EMA · PRO</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background:#0d1219;border:1px solid #1e2d3d;border-radius:12px;padding:28px;">', unsafe_allow_html=True)
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
        if st.button("🚀 LAUNCH SCANNER", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# GLOBAL STYLES
# ============================================================

# ============================================================
# THEME SYSTEM
# ============================================================
THEMES = {
    "DARK": {
        "bg_main": "#080c12", "bg_card": "#0d1a26", "bg_card_alt": "#111820",
        "text_main": "#c8d8e8", "text_dim": "#6a8aaa", "text_dark": "#3a5a7a",
        "border": "#1e2d3d", "border_hover": "#00d4ff55",
        "accent_cyan": "#00d4ff", "accent_green": "#00ff88", "accent_red": "#ff4060",
        "accent_orange": "#ff6b6b", "accent_yellow": "#ffc700",
        "candle_up": "#00ff88", "candle_down": "#ff4060",
    },
    "LIGHT": {
        "bg_main": "#f0f4f8", "bg_card": "#ffffff", "bg_card_alt": "#f8fafc",
        "text_main": "#1a2332", "text_dim": "#5a6a7a", "text_dark": "#8a9aaa",
        "border": "#d0d8e0", "border_hover": "#0066cc55",
        "accent_cyan": "#0066cc", "accent_green": "#00aa44", "accent_red": "#cc2244",
        "accent_orange": "#dd5533", "accent_yellow": "#cc8800",
        "candle_up": "#00aa44", "candle_down": "#cc2244",
    },
    "MODERATE": {
        "bg_main": "#121820", "bg_card": "#1a2436", "bg_card_alt": "#162030",
        "text_main": "#d0dce8", "text_dim": "#7a8aaa", "text_dark": "#4a5a6a",
        "border": "#2a3a50", "border_hover": "#4488cc55",
        "accent_cyan": "#4488cc", "accent_green": "#44aa66", "accent_red": "#cc4455",
        "accent_orange": "#cc6644", "accent_yellow": "#cc9944",
        "candle_up": "#44aa66", "candle_down": "#cc445
