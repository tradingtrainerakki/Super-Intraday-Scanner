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
        <div class="tagline">ORB + OI SPURTS + VWAP + EMA · PRO</div>
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
        "candle_up": "#44aa66", "candle_down": "#cc4455",
    }
}



# Apply dynamic theme CSS
T = THEMES[st.session_state.theme]
is_dark = st.session_state.theme in ["DARK", "MODERATE"]
is_light = st.session_state.theme == "LIGHT"

# Determine text colors based on theme
if is_dark:
    text_primary = "#e8f0f8"      # Very light blue-white
    text_secondary = "#a0b8d0"   # Light blue-gray
    text_muted = "#6a8aaa"       # Medium blue-gray
    text_dark = "#3a5a7a"         # Dark blue-gray
    bg_primary = T['bg_main']     # Main background
    bg_card = T['bg_card']        # Card background
    bg_card_alt = T['bg_card_alt'] # Alt card background
    border_color = T['border']
    accent_cyan = "#00d4ff"
    accent_green = "#00ff88"
    accent_red = "#ff4060"
    accent_orange = "#ff6b6b"
    accent_yellow = "#ffc700"
    candle_up = "#00ff88"
    candle_down = "#ff4060"
    shadow = "0 4px 20px rgba(0,0,0,0.4)"
    btn_text = "#000000"
    badge_text_light = "#000000"
    badge_text_dark = "#ffffff"
else:
    text_primary = "#1a2332"      # Very dark blue
    text_secondary = "#3a4a5a"    # Dark gray-blue
    text_muted = "#6a7a8a"       # Medium gray
    text_dark = "#9aaab8"         # Light gray
    bg_primary = T['bg_main']
    bg_card = T['bg_card']
    bg_card_alt = T['bg_card_alt']
    border_color = T['border']
    accent_cyan = "#0066cc"
    accent_green = "#00aa44"
    accent_red = "#cc2244"
    accent_orange = "#dd5533"
    accent_yellow = "#cc8800"
    candle_up = "#00aa44"
    candle_down = "#cc2244"
    shadow = "0 4px 20px rgba(0,0,0,0.1)"
    btn_text = "#ffffff"
    badge_text_light = "#000000"
    badge_text_dark = "#ffffff"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap');

/* ============================================
   ROOT & BASE STYLES - HIGHEST SPECIFICITY
   ============================================ */
html, body, .stApp, [data-testid="stAppViewContainer"], 
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {{
    background-color: {bg_primary} !important;
    color: {text_primary} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* Force all text elements */
.stApp * {{
    color: {text_primary};
}}

/* Streamlit sidebar */
section[data-testid="stSidebar"] {{ 
    background-color: {bg_card} !important; 
    border-right: 1px solid {border_color} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {text_primary} !important;
}}

/* Hide default menus */
#MainMenu, footer, header {{ visibility: hidden !important; }}

/* ============================================
   HEADER
   ============================================ */
.super-header {{
    background: linear-gradient(135deg, {bg_card}, {bg_primary});
    border-bottom: 1px solid {border_color};
    padding: 16px 24px; 
    border-radius: 0 0 16px 16px;
    margin-bottom: 16px;
}}
.super-logo {{
    font-family: 'Syne', sans-serif !important;
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(90deg, {accent_cyan}, {accent_green}, {accent_orange});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: 3px;
}}
.super-sub {{
    font-size: 9px; color: {text_muted};
    letter-spacing: 3px; text-transform: uppercase;
}}

/* ============================================
   METRIC CARDS
   ============================================ */
.metric-card-super {{
    background: linear-gradient(135deg, {bg_card}, {bg_card_alt}) !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: {shadow} !important;
    transition: all 0.3s ease;
}}
.metric-card-super:hover {{
    border-color: {accent_cyan}55 !important;
    transform: translateY(-2px);
}}

/* ============================================
   SIGNAL CARDS
   ============================================ */
.card-strong-buy {{
    background: linear-gradient(135deg, {accent_green}18, {accent_green}08) !important;
    border: 1px solid {accent_green}60 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
}}
.card-buy {{
    background: linear-gradient(135deg, {accent_green}12, {accent_green}05) !important;
    border: 1px solid {accent_green}50 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
}}
.card-strong-sell {{
    background: linear-gradient(135deg, {accent_red}18, {accent_red}08) !important;
    border: 1px solid {accent_red}60 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
}}
.card-sell {{
    background: linear-gradient(135deg, {accent_red}12, {accent_red}05) !important;
    border: 1px solid {accent_red}50 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 8px 0 !important;
}}

/* ============================================
   OI BADGES
   ============================================ */
.badge-long-build {{
    background: linear-gradient(90deg, {accent_green}, {accent_green}) !important;
    color: {badge_text_light} !important; 
    font-weight: 700 !important;
    padding: 4px 12px !important; 
    border-radius: 20px !important;
    font-size: 11px !important; 
    letter-spacing: 1px !important;
    display: inline-block;
}}
.badge-short-build {{
    background: linear-gradient(90deg, {accent_red}, {accent_red}) !important;
    color: {badge_text_dark} !important; 
    font-weight: 700 !important;
    padding: 4px 12px !important; 
    border-radius: 20px !important;
    font-size: 11px !important; 
    letter-spacing: 1px !important;
    display: inline-block;
}}
.badge-short-cover {{
    background: linear-gradient(90deg, {accent_yellow}, {accent_yellow}) !important;
    color: {badge_text_light} !important; 
    font-weight: 700 !important;
    padding: 4px 12px !important; 
    border-radius: 20px !important;
    font-size: 11px !important; 
    letter-spacing: 1px !important;
    display: inline-block;
}}
.badge-long-unwind {{
    background: linear-gradient(90deg, {accent_orange}, {accent_orange}) !important;
    color: {badge_text_dark} !important; 
    font-weight: 700 !important;
    padding: 4px 12px !important; 
    border-radius: 20px !important;
    font-size: 11px !important; 
    letter-spacing: 1px !important;
    display: inline-block;
}}

/* ============================================
   ACCURACY BADGES
   ============================================ */
.acc-badge {{
    display: inline-block; 
    padding: 6px 16px;
    border-radius: 20px; 
    font-weight: 700;
    font-size: 14px; 
    letter-spacing: 1px;
}}
.acc-90 {{ 
    background: linear-gradient(90deg, {accent_green}, {accent_green}) !important; 
    color: {badge_text_light} !important; 
}}
.acc-80 {{ 
    background: linear-gradient(90deg, {accent_yellow}, {accent_yellow}) !important; 
    color: {badge_text_light} !important; 
}}
.acc-70 {{ 
    background: linear-gradient(90deg, {accent_orange}, {accent_red}) !important; 
    color: #ffffff !important; 
}}

/* ============================================
   BUTTONS
   ============================================ */
.stButton > button {{
    background: linear-gradient(90deg, {accent_cyan}25, {accent_green}25) !important;
    color: {accent_cyan} !important; 
    font-weight: 700 !important;
    font-size: 12px !important; 
    border-radius: 8px !important;
    padding: 10px 24px !important; 
    border: 1px solid {accent_cyan}50 !important;
    letter-spacing: 1px !important; 
    font-family: 'JetBrains Mono', monospace !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: linear-gradient(90deg, {accent_cyan}, {accent_green}) !important;
    color: {btn_text} !important; 
    border-color: transparent !important;
}}

/* ============================================
   TABS
   ============================================ */
.stTabs [data-baseweb="tab-list"] {{
    background: {bg_card} !important;
    border-bottom: 1px solid {border_color} !important;
    gap: 4px !important; 
    padding: 0 8px !important;
    border-radius: 8px 8px 0 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important; 
    color: {text_muted} !important;
    border-radius: 6px 6px 0 0 !important; 
    padding: 10px 20px !important;
    font-size: 11px !important; 
    font-weight: 600 !important;
    letter-spacing: 1px !important; 
    border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {accent_cyan}20, {accent_green}20) !important;
    color: {accent_cyan} !important; 
    border-bottom: 2px solid {accent_cyan} !important;
}}

/* ============================================
   INPUTS
   ============================================ */
.stTextInput > div > div > input, 
.stNumberInput > div > div > input,
.stSelectbox > div > div, 
.stSlider > div {{
    background-color: {bg_card} !important; 
    border: 1px solid {border_color} !important;
    border-radius: 8px !important; 
    color: {text_primary} !important;
    font-family: 'JetBrains Mono', monospace !important; 
    font-size: 12px !important;
}}

/* ============================================
   SECTION HEADERS
   ============================================ */
.section-h {{
    font-family: 'Syne', sans-serif !important; 
    font-size: 1rem;
    font-weight: 700; 
    color: {accent_cyan}; 
    letter-spacing: 2px;
    text-transform: uppercase; 
    border-left: 3px solid {accent_cyan};
    padding-left: 10px; 
    margin: 16px 0 12px;
}}

/* ============================================
   FILTER BOXES - CRITICAL FIX
   ============================================ */
.filter-box-super {{
    background: {bg_card} !important; 
    border: 1px solid {border_color} !important;
    border-radius: 8px !important; 
    padding: 12px !important; 
    margin: 4px 0 !important;
    font-size: 12px !important;
    color: {text_primary} !important;
    line-height: 1.5 !important;
}}
.filter-box-super b,
.filter-box-super strong {{
    color: {accent_cyan} !important;
    font-weight: 700 !important;
}}
.filter-box-super small {{
    color: {text_muted} !important;
    font-size: 10px !important;
}}
.filter-pass {{ 
    border-left: 3px solid {accent_green} !important; 
    background: linear-gradient(90deg, {accent_green}15, {bg_card}) !important;
}}
.filter-fail {{ 
    border-left: 3px solid {accent_red} !important; 
    background: linear-gradient(90deg, {accent_red}15, {bg_card}) !important;
}}

/* ============================================
   OI CARDS - CRITICAL FIX
   ============================================ */
.oi-card-super {{
    background: linear-gradient(135deg, {bg_card_alt}, {bg_card}) !important;
    border: 1px solid {border_color} !important; 
    border-radius: 10px !important;
    padding: 12px !important; 
    margin: 8px 0 !important;
    color: {text_primary} !important;
}}
.oi-metric-val {{ 
    font-size: 20px !important; 
    font-weight: 700 !important; 
    color: {accent_cyan} !important;
}}
.oi-metric-lbl {{ 
    font-size: 10px !important; 
    color: {text_muted} !important; 
    text-transform: uppercase; 
    letter-spacing: 1px;
}}

/* ============================================
   LOGIN BOX
   ============================================ */
.login-box {{
    max-width: 420px; 
    margin: 100px auto;
    background: linear-gradient(135deg, {bg_card}, {bg_card_alt}) !important;
    border: 1px solid {border_color} !important; 
    border-radius: 20px;
    padding: 50px; 
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,{'0.5' if is_dark else '0.15'});
}}

/* ============================================
   STATUS BADGES
   ============================================ */
.status-open {{
    background: {accent_green}20 !important;
    border: 1px solid {accent_green}50 !important;
    color: {accent_green} !important;
    border-radius: 6px; 
    padding: 6px 14px;
    font-size: 11px; 
    font-weight: 700; 
    letter-spacing: 1px;
    display: inline-block;
}}
.status-closed {{
    background: {accent_red}20 !important;
    border: 1px solid {accent_red}50 !important;
    color: {accent_red} !important;
    border-radius: 6px; 
    padding: 6px 14px;
    font-size: 11px; 
    font-weight: 700; 
    letter-spacing: 1px;
    display: inline-block;
}}

/* ============================================
   SECTOR CARDS
   ============================================ */
.sector-card {{
    background: linear-gradient(135deg, {bg_card}, {bg_card_alt}) !important;
    border: 1px solid {border_color} !important; 
    border-radius: 10px;
    padding: 12px; 
    text-align: center;
}}
.sector-name {{ 
    font-size: 11px; 
    color: {text_muted}; 
    letter-spacing: 1px; 
    margin-bottom: 4px;
}}
.sector-up {{ 
    color: {accent_green}; 
    font-size: 18px; 
    font-weight: 700; 
    margin: 4px 0;
}}
.sector-down {{ 
    color: {accent_red}; 
    font-size: 18px; 
    font-weight: 700; 
    margin: 4px 0;
}}
.sector-neutral {{ 
    color: {accent_yellow}; 
    font-size: 18px; 
    font-weight: 700; 
    margin: 4px 0;
}}
.sector-trend {{ 
    font-size: 9px; 
    color: {text_dark}; 
    margin-top: 4px;
}}

/* ============================================
   SKIP BOX
   ============================================ */
.skip-box {{
    background: {accent_yellow}15 !important;
    border: 1px solid {accent_yellow}40 !important;
    border-radius: 8px; 
    padding: 10px 16px;
    color: {accent_yellow} !important; 
    font-size: 11px;
    font-weight: 600;
}}

/* ============================================
   STREAMLIT SPECIFIC FIXES
   ============================================ */
/* Expander */
.streamlit-expanderHeader {{
    color: {text_primary} !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}}
.streamlit-expanderContent {{
    background: {bg_primary} !important;
    color: {text_primary} !important;
}}

/* Dataframe */
[data-testid="stDataFrame"] {{
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
}}
[data-testid="stDataFrame"] td {{
    color: {text_primary} !important;
    background: {bg_card} !important;
    border-bottom: 1px solid {border_color} !important;
}}
[data-testid="stDataFrame"] th {{
    color: {text_muted} !important;
    background: {bg_card_alt} !important;
    border-bottom: 2px solid {border_color} !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}}

/* Metrics */
[data-testid="stMetricValue"] {{
    color: {text_primary} !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricLabel"] {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}
[data-testid="stMetricDelta"] {{
    color: {accent_green} !important;
}}

/* Radio buttons */
.stRadio > div {{
    color: {text_primary} !important;
}}
.stRadio label {{
    color: {text_primary} !important;
}}

/* Checkbox */
.stCheckbox > label {{
    color: {text_primary} !important;
    font-size: 12px !important;
}}

/* Slider */
.stSlider > div > div {{
    color: {text_primary} !important;
}}

/* Select slider */
.stSelectSlider > div {{
    color: {text_primary} !important;
}}

/* Number input labels */
.stNumberInput > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

/* Text input labels */
.stTextInput > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

/* Selectbox labels */
.stSelectbox > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

/* ============================================
   SCROLLBAR
   ============================================ */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}
::-webkit-scrollbar-track {{
    background: {bg_card};
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb {{
    background: {border_color};
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {accent_cyan};
}}

</style>
""", unsafe_allow_html=True)



# ============================================================
# HOVER FIX CSS (Separate from theme to avoid f-string brace conflicts)
# ============================================================
st.markdown("""
<style>
/* Expander hover - prevent white flash */
.streamlit-expanderHeader:hover {
    background: #1a2436 !important;
    color: #00d4ff !important;
}
.streamlit-expanderContent:hover {
    background: #080c12 !important;
}

/* Dataframe hover */
[data-testid="stDataFrame"] tr:hover {
    background: #0d1a26 !important;
}

/* Card hover */
.metric-card-super:hover {
    border-color: #00d4ff55 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px; height: 8px;
}
::-webkit-scrollbar-track {
    background: #0d1a26; border-radius: 4px;
}
::-webkit-scrollbar-thumb {
    background: #1e2d3d; border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #00d4ff;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1a26, #111820); 
                padding: 16px; border-radius: 12px; border: 1px solid #1e2d3d;
                color: white; text-align: center; margin-bottom: 20px;">
        <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;
                    background:linear-gradient(90deg,#00d4ff,#00ff88);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            🚀 SUPER SCANNER
        </div>
        <div style="color:#3a5a7a;font-size:9px;letter-spacing:2px;margin-top:4px;">
            ORB + OI + VWAP + EMA
        </div>
        <div style="color:#6a8aaa;font-size:11px;margin-top:8px;">
            👤 {st.session_state.username.upper()}<br>
            ⏰ {now_ist().strftime('%d %b %Y | %H:%M')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.markdown("---")

    # THEME SELECTOR
    st.markdown("<div class='section-h'>🎨 Theme</div>", unsafe_allow_html=True)
    theme_cols = st.columns(3)
    with theme_cols[0]:
        if st.button("🌑 DARK", use_container_width=True, 
                     type="primary" if st.session_state.theme == "DARK" else "secondary"):
            st.session_state.theme = "DARK"
            st.rerun()
    with theme_cols[1]:
        if st.button("☀️ LIGHT", use_container_width=True,
                     type="primary" if st.session_state.theme == "LIGHT" else "secondary"):
            st.session_state.theme = "LIGHT"
            st.rerun()
    with theme_cols[2]:
        if st.button("🌓 MOD", use_container_width=True,
                     type="primary" if st.session_state.theme == "MODERATE" else "secondary"):
            st.session_state.theme = "MODERATE"
            st.rerun()

    st.markdown("---")
    st.markdown("<div class='section-h'>Scanner Mode</div>", unsafe_allow_html=True)

    scan_mode = st.radio("", 
        ["🏃 QUICK SCAN (Top 20 OI Spurts)", "🔍 FULL SCAN (Select Universe)"],
        label_visibility="collapsed"
    )

    # Show universe selector immediately when FULL SCAN is selected
    if "FULL" in scan_mode:
        st.markdown("<div class='section-h'>📋 Select Universe</div>", unsafe_allow_html=True)
        universe = st.selectbox("", 
            ["Nifty 50", "Nifty Next 50", "Bank Nifty", "F&O Pro Top 20", "Custom"],
            label_visibility="collapsed",
            key="universe_select")

        if universe == "Custom":
            custom_input = st.text_area("Enter symbols (comma separated)", 
                                        "RELIANCE, TCS, HDFCBANK", key="custom_stocks")
            st.session_state.custom_stock_list = [s.strip().upper() for s in custom_input.split(",") if s.strip()]
        else:
            st.session_state.selected_universe = universe

    st.markdown("---")
    st.markdown("<div class='section-h'>ORB Settings</div>", unsafe_allow_html=True)
    orb_minutes = st.slider("Opening Range (min)", 5, 30, 15, 
                            help="First kitne minutes ka range lo ORB ke liye")

    st.markdown("<div class='section-h'>Filters</div>", unsafe_allow_html=True)
    gap_spike_filter = st.checkbox("⚡ Gap + Spike Filter", value=True,
                                   help="2% gap + 1.5% first 5-min move → SKIP")
    use_vwap = st.checkbox("📊 VWAP Filter", value=True)
    use_ema = st.checkbox("📈 EMA Filter", value=True)
    use_volume = st.checkbox("🔊 Volume Filter", value=True)

    st.markdown("<div class='section-h'>OI Analysis</div>", unsafe_allow_html=True)
    use_oi = st.checkbox("🎯 OI Buildup Analysis", value=True,
                         help="Long Buildup / Short Buildup / Short Cover / Long Unwind")

    st.markdown("<div class='section-h'>Accuracy Mode</div>", unsafe_allow_html=True)
    accuracy_mode = st.select_slider("", 
        options=["Conservative (80%+)", "Balanced (70-80%)", "Aggressive (60-70%)"],
        value="Balanced (70-80%)"
    )
    min_accuracy = {"Conservative (80%+)": 80, "Balanced (70-80%)": 70, "Aggressive (60-70%)": 60}[accuracy_mode]

    st.markdown("<div class='section-h'>Risk</div>", unsafe_allow_html=True)
    risk_reward = st.slider("R:R Ratio", 1.0, 4.0, 2.5, 0.5)

    st.markdown("<div class='section-h'>Price Range</div>", unsafe_allow_html=True)
    min_price = st.number_input("Min ₹", 50, 50000, 100)
    max_price = st.number_input("Max ₹", 50, 50000, 10000)

    st.markdown("---")

    # DHAN TOKEN
    if 'dhan_token' not in st.session_state:
        st.session_state.dhan_token = ''

    with st.expander("⚡ Dhan API (Optional)", expanded=False):
        dhan_token = st.text_input("Access Token", 
                                    value=st.session_state.dhan_token,
                                    type="password",
                                    placeholder="Paste Dhan token",
                                    label_visibility="collapsed")
        st.session_state.dhan_token = dhan_token
        if dhan_token:
            st.success("✅ Active")
        else:
            st.caption("Blank = Yahoo Finance")

    st.markdown("---")
    refresh = st.button("🚀 SCAN NOW", type="primary", use_container_width=True)

    if st.button("🗑️ Clear Cache", use_container_width=True):
        for key in ['scan_results', 'oi_list', 'sector_perf']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ============================================================
# HEADER
# ============================================================

def is_market_open():
    now = now_ist()
    if now.weekday() >= 5:
        return False, "Weekend — Market Closed"
    if now.hour < 9 or (now.hour == 9 and now.minute < 15):
        return False, "Pre-market (Opens 9:15 AM)"
    if now.hour > 15 or (now.hour == 15 and now.minute > 30):
        return False, "Market Closed (3:30 PM)"
    return True, "Market Open"

# =======================================

open_status, market_msg = is_market_open()
now_str = now_ist().strftime("%d %b %Y · %H:%M:%S IST")

st.markdown(f"""
<div class="super-header">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div>
      <div class="super-logo">🚀 SUPER SCANNER</div>
      <div class="super-sub">ORB + OI SPURTS + VWAP + EMA · NSE INTRADAY LIVE</div>
    </div>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
      <div class="{'status-open' if open_status else 'status-closed'}">
        {'🟢' if open_status else '🔴'} {market_msg}
      </div>
      <div style="color:#6a8aaa;font-size:13px;font-weight:600;letter-spacing:1px;">⏰ {now_str}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# STOCK UNIVERSES
# ============================================================
STOCK_UNIVERSES = {
    "Nifty 50": [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC", "SBIN",
        "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
        "SUNPHARMA", "BAJFINANCE", "WIPRO", "ULTRACEMCO", "NESTLEIND", "POWERGRID", "NTPC",
        "TATASTEEL", "M&M", "HCLTECH", "TECHM", "INDUSINDBK", "GRASIM", "ADANIENT", "CIPLA",
        "SBILIFE", "BAJAJFINSV", "BRITANNIA", "APOLLOHOSP", "ONGC", "EICHERMOT", "TATAMOTORS",
        "DIVISLAB", "HDFCLIFE", "COALINDIA", "JSWSTEEL", "HEROMOTOCO", "BPCL", "DRREDDY",
        "ADANIPORTS", "HINDALCO", "UPL", "SHREECEM", "BAJAJ-AUTO", "TATACONSUM"
    ],
    "Nifty Next 50": [
        "BERGEPAINT", "CHOLAFIN", "DABUR", "GODREJCP", "HAVELLS", "ICICIPRULI", "INDIGO",
        "JINDALSTEL", "LICI", "LODHA", "MCDOWELL-N", "MOTHERSON", "NAUKRI", "PIDILITIND",
        "POLYCAB", "SIEMENS", "SRF", "TORNTPHARM", "TVSMOTOR", "ABB", "ACC", "AMBUJACEM",
        "AUROPHARMA", "BANDHANBNK", "BANKBARODA", "BEL", "BHEL", "CANBK", "COLPAL", "CONCOR",
        "CUMMINSIND", "DMART", "GAIL", "GODREJPROP", "HAL", "HINDPETRO", "IDBI", "IDFCFIRSTB",
        "INDUSTOWER", "IOB", "IRCTC", "JUBLFOOD", "L&TFH", "LUPIN", "MARICO", "MUTHOOTFIN",
        "NMDC", "OBEROIRLTY", "PFC"
    ],
    "Bank Nifty": [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK", "BANDHANBNK",
        "FEDERALBNK", "IDFCFIRSTB", "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "AUBANK", "RBLBANK"
    ],
    "F&O Pro Top 20": [],  # Will be populated from OI Spurts
    "Custom": []
}

SECTOR_ETFS = {
    "IT": ["^CNXIT", "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "BANK": ["^NSEBANK", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"],
    "AUTO": ["^CNXAUTO", "MARUTI", "TATAMOTORS", "M&M", "EICHERMOT", "BAJAJ-AUTO"],
    "PHARMA": ["^CNXPHARMA", "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP"],
    "FMCG": ["^CNXFMCG", "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "METAL": ["^CNXMETAL", "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA"],
    "ENERGY": ["^CNXENERGY", "RELIANCE", "ONGC", "POWERGRID", "NTPC", "BPCL"],
    "INFRA": ["^CNXINFRA", "LT", "ADANIENT", "ADANIPORTS", "ULTRACEMCO"],
}

STOCK_TO_SECTOR = {}
for sector, stocks in SECTOR_ETFS.items():
    for stock in stocks[1:]:
        STOCK_TO_SECTOR[stock] = sector

# ============================================================
# DHAN CONFIG
# ============================================================
DHAN_SECURITY_IDS = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333", "ICICIBANK": "4963",
    "INFY": "1594", "HINDUNILVR": "1394", "ITC": "1660", "SBIN": "3045",
    "BHARTIARTL": "10604", "KOTAKBANK": "1922", "LT": "11483", "AXISBANK": "5900",
    "ASIANPAINT": "236", "MARUTI": "10999", "TITAN": "3506", "SUNPHARMA": "3351",
    "BAJFINANCE": "317", "WIPRO": "3787", "ULTRACEMCO": "11532", "NESTLEIND": "17963",
    "POWERGRID": "14977", "NTPC": "11630", "TATASTEEL": "3499", "M&M": "2031",
    "HCLTECH": "1851", "TECHM": "13538", "INDUSINDBK": "5258", "GRASIM": "1232",
    "ADANIENT": "25", "CIPLA": "694", "SBILIFE": "21808", "BAJAJFINSV": "16675",
    "BRITANNIA": "1406", "APOLLOHOSP": "157", "ONGC": "2475", "EICHERMOT": "910",
    "TATAMOTORS": "3456", "DIVISLAB": "10568", "HDFCLIFE": "467", "COALINDIA": "20374",
    "JSWSTEEL": "11723", "HEROMOTOCO": "1348", "BPCL": "526", "DRREDDY": "881",
    "ADANIPORTS": "15083", "HINDALCO": "1363", "UPL": "11287", "SHREECEM": "3103",
    "BAJAJ-AUTO": "16669", "TATACONSUM": "3432", "BERGEPAINT": "1023", "CHOLAFIN": "1034",
    "DABUR": "1075", "GODREJCP": "1174", "HAVELLS": "1341", "ICICIPRULI": "4962",
    "INDIGO": "1480", "JINDALSTEL": "158", "LICI": "11537", "LODHA": "1169",
    "MCDOWELL-N": "1166", "MOTHERSON": "1167", "NAUKRI": "137", "PIDILITIND": "1404",
    "POLYCAB": "1480", "SIEMENS": "136", "SRF": "148", "TORNTPHARM": "1168",
    "TVSMOTOR": "1169", "ABB": "123", "ACC": "125", "AMBUJACEM": "127",
    "AUROPHARMA": "128", "BANDHANBNK": "129", "BANKBARODA": "130", "BEL": "131",
    "BHEL": "132", "CANBK": "133", "COLPAL": "134", "CONCOR": "135",
    "CUMMINSIND": "136", "DMART": "137", "GAIL": "138", "GODREJPROP": "139",
    "HAL": "140", "HINDPETRO": "141", "IDBI": "142", "IDFCFIRSTB": "143",
    "INDUSTOWER": "144", "IOB": "145", "IRCTC": "146", "JUBLFOOD": "147",
    "L&TFH": "148", "LUPIN": "149", "MARICO": "150", "MUTHOOTFIN": "151",
    "NMDC": "152", "OBEROIRLTY": "153", "PFC": "154", "PNB": "155",
    "UNIONBANK": "156", "AUBANK": "157", "RBLBANK": "158", "FEDERALBNK": "159",
    "NIFTY": "35001", "BANKNIFTY": "35002", "FINNIFTY": "35003", "MIDCPNIFTY": "35004",
}

DHAN_BASE_URL = "https://api.dhan.co/v2"

def get_dhan_headers(access_token):
    return {'Content-Type': 'application/json', 'access-token': access_token}

# ============================================================
# DATA FETCHING FUNCTIONS
# ============================================================

def fetch_dhan_intraday(ticker, access_token, interval="5"):
    """Fetch 5m intraday data from Dhan API"""
    try:
        security_id = DHAN_SECURITY_IDS.get(ticker)
        if not security_id or not access_token:
            return None
        from_date = (now_ist() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        to_date = now_ist().strftime('%Y-%m-%d %H:%M:%S')
        resp = requests.post(
            f"{DHAN_BASE_URL}/charts/intraday",
            json={
                "securityId": security_id, "exchangeSegment": "NSE_EQ",
                "instrument": "EQUITY", "interval": interval,
                "fromDate": from_date, "toDate": to_date
            },
            headers=get_dhan_headers(access_token), timeout=10
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or 'open' not in data:
            return None
        df = pd.DataFrame({
            'Open': data['open'], 'High': data['high'], 'Low': data['low'],
            'Close': data['close'], 'Volume': data['volume'],
        })
        idx = pd.to_datetime(data['timestamp'], unit='s').tz_localize('UTC').tz_convert('Asia/Kolkata')
        df.index = idx
        return df if len(df) >= 20 else None
    except Exception:
        return None

def fetch_yahoo_data(ticker, period="5d", interval="5m"):
    """Fetch data from Yahoo Finance"""
    try:
        df = yf.download(ticker + ".NS", period=period, interval=interval, progress=False)
        if df.empty or len(df) < 20:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        return df
    except Exception:
        return None

def get_data(ticker, access_token=""):
    """Unified data fetcher - Dhan first, then Yahoo"""
    if access_token:
        df = fetch_dhan_intraday(ticker, access_token)
        if df is not None:
            return df, "dhan"
    df = fetch_yahoo_data(ticker)
    if df is not None:
        return df, "yahoo"
    return None, None

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_vwap(df):
    try:
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        return float((p * v).cumsum().iloc[-1] / v.cumsum().iloc[-1])
    except:
        return None

def calculate_atr(df, period=14):
    try:
        df = df.copy()
        df['tr1'] = df['High'] - df['Low']
        df['tr2'] = abs(df['High'] - df['Close'].shift())
        df['tr3'] = abs(df['Low'] - df['Close'].shift())
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        atr = df['tr'].rolling(window=period).mean()
        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
    except:
        return 0

# ============================================================
# NSE OI SPURTS - FIXED WITH NSEPYTHON
# ============================================================

def get_oi_spurts_nsepython():
    """Fetch OI Spurts from NSE using nsepython library"""
    if not NSEPYTHON_AVAILABLE:
        return None, "nsepython not installed"

    try:
        # Try multiple endpoints
        endpoints = [
            "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings",
            "https://www.nseindia.com/api/live-analysis-oi-spurts",
        ]

        for endpoint in endpoints:
            try:
                data = nsefetch(endpoint)
                if data:
                    items = []
                    raw = data if isinstance(data, list) else data.get('data', [])

                    for item in raw[:50]:
                        sym = item.get('symbol', '')
                        if not sym:
                            continue

                        pchg = item.get('pchangeinOpenInterest', 
                               item.get('pChange', 
                               item.get('pchangeinOi', 0))) or 0

                        prev_oi = item.get('prevOI', 
                                  item.get('previousOI', 0)) or 0

                        latest_oi = item.get('latestOI', 
                                    item.get('openInterest', 0)) or 0

                        chg_oi = item.get('changeinOpenInterest',
                                 item.get('changeInOpenInterest', 0)) or 0

                        # Calculate OI change % if not provided
                        if float(pchg) == 0 and float(prev_oi) > 0 and float(latest_oi) > 0:
                            pchg = round(((float(latest_oi) - float(prev_oi)) / float(prev_oi)) * 100, 2)

                        items.append({
                            'symbol': sym,
                            'oi_chg_pct': round(float(pchg), 2),
                            'prev_oi': int(prev_oi),
                            'latest_oi': int(latest_oi),
                            'chg_oi': int(chg_oi),
                        })

                    if items:
                        items.sort(key=lambda x: x['oi_chg_pct'], reverse=True)
                        return items[:30], "nsepython"

            except Exception as e:
                continue

    except Exception as e:
        return None, f"nsepython error: {e}"

    return None, "all endpoints failed"

def get_oi_spurts_direct():
    """Fallback: Direct NSE requests with session management"""
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        session.get('https://www.nseindia.com', headers=headers, timeout=15)
        time.sleep(1)
        session.get('https://www.nseindia.com/market-data', headers=headers, timeout=15)
        time.sleep(1)
        session.get('https://www.nseindia.com/market-data/oi-spurts', headers=headers, timeout=15)
        time.sleep(1)

        api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/market-data/oi-spurts',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }

        endpoints = [
            "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings",
            "https://www.nseindia.com/api/live-analysis-oi-spurts",
        ]

        for endpoint in endpoints:
            response = session.get(endpoint, headers=api_headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                items = []
                raw = data if isinstance(data, list) else data.get('data', [])

                for item in raw[:50]:
                    sym = item.get('symbol', '')
                    if not sym:
                        continue
                    pchg = item.get('pchangeinOpenInterest', item.get('pChange', 0)) or 0
                    prev_oi = item.get('prevOI', 0) or 0
                    latest_oi = item.get('latestOI', 0) or 0
                    chg_oi = item.get('changeinOpenInterest', 0) or 0

                    items.append({
                        'symbol': sym,
                        'oi_chg_pct': round(float(pchg), 2),
                        'prev_oi': int(prev_oi),
                        'latest_oi': int(latest_oi),
                        'chg_oi': int(chg_oi),
                    })

                if items:
                    items.sort(key=lambda x: x['oi_chg_pct'], reverse=True)
                    return items[:30], "direct"

    except Exception as e:
        return None, f"direct error: {e}"

    return None, "direct failed"

def get_oi_spurts():
    """Unified OI Spurts fetcher - tries nsepython first, then direct"""
    # Method 1: nsepython
    result, source = get_oi_spurts_nsepython()
    if result:
        return result, source

    # Method 2: Direct requests
    result, source = get_oi_spurts_direct()
    if result:
        return result, source

    # Fallback: empty list
    return [], "failed"

# ============================================================
# SECTOR PERFORMANCE
# ============================================================

def get_sector_performance():
    sector_perf = {}
    for sector, etf_list in SECTOR_ETFS.items():
        try:
            etf = yf.Ticker(etf_list[0])
            df = etf.history(period="2d", interval="5m")
            if df.empty or len(df) < 2:
                sector_perf[sector] = {"change": 0, "trend": "NEUTRAL"}
                continue
            df.reset_index(inplace=True)
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            if 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            today = datetime.now().date()
            df_today = df[df['Date'].dt.date == today]
            if df_today.empty:
                sector_perf[sector] = {"change": 0, "trend": "NEUTRAL"}
                continue
            open_price = df_today['Open'].iloc[0]
            current = df_today['Close'].iloc[-1]
            change_pct = ((current - open_price) / open_price) * 100
            if change_pct > 1.5: trend = "STRONG_UP"
            elif change_pct > 0.5: trend = "UP"
            elif change_pct < -1.5: trend = "STRONG_DOWN"
            elif change_pct < -0.5: trend = "DOWN"
            else: trend = "NEUTRAL"
            sector_perf[sector] = {"change": round(change_pct, 2), "trend": trend, "open": open_price, "current": current}
        except:
            sector_perf[sector] = {"change": 0, "trend": "NEUTRAL"}
    return sector_perf

# ============================================================
# CORE ANALYSIS - ORB + 5 FILTERS + OI BUILDUP
# ============================================================

def analyze_stock_orb_oi(ticker, oi_info, orb_mins=15, gap_filter=True, 
                          vwap_filter=True, ema_filter=True, volume_filter=True,
                          access_token=""):
    """
    SUPER SCANNER CORE:
    1. Fetch data (Dhan/Yahoo)
    2. ORB Breakout detection
    3. Gap + Spike Filter
    4. 5 Filters: ORB, Volume, VWAP, EMA, Gap+Spike
    5. OI Buildup Classification
    6. Signal generation with accuracy
    """
    try:
        # Fetch data
        df, source = get_data(ticker, access_token)
        if df is None or len(df) < 20:
            return None, "No data"

        today = pd.Timestamp.now().date()
        today_data = df[df.index.date == today]
        prev_data = df[df.index.date < today]

        if len(today_data) < 2:
            all_dates = sorted(df.index.date.unique())
            if len(all_dates) < 2:
                return None, "No previous data"
            today_data = df[df.index.date == all_dates[-1]]
            prev_data = df[df.index.date == all_dates[-2]]

        if len(prev_data) == 0 or len(today_data) == 0:
            return None, "Data error"

        prev_close = float(prev_data['Close'].iloc[-1])
        today_open = float(today_data['Open'].iloc[0])

        # ── FILTER 1: GAP + SPIKE FILTER ──
        gap_pct = round(((today_open - prev_close) / prev_close) * 100, 2)
        if gap_filter and abs(gap_pct) >= 2.0:
            return None, f"Gap filter: {gap_pct}%"

        first_candle_close = float(today_data['Close'].iloc[0])
        first_candle_move = abs(first_candle_close - prev_close) / prev_close * 100
        if gap_filter and first_candle_move >= 2.0:
            return None, f"Spike filter: {first_candle_move:.1f}%"

        # ── ORB CALCULATION ──
        candles_needed = max(1, orb_mins // 5)
        opening_range = today_data.head(candles_needed)
        if opening_range.empty:
            return None, "ORB empty"

        orb_high = opening_range['High'].max()
        orb_low = opening_range['Low'].min()
        current_candle = today_data.iloc[-1]
        current_price = float(current_candle['Close'])

        if current_price > orb_high:
            base_signal = "BUY"
            entry_price = orb_high
            stop_loss = orb_low
        elif current_price < orb_low:
            base_signal = "SELL"
            entry_price = orb_low
            stop_loss = orb_high
        else:
            return None, "No ORB breakout"

        # ── FILTER 2: VWAP ──
        vwap = calculate_vwap(today_data)
        vwap_pass = False
        if vwap_filter and vwap:
            vwap_pass = (base_signal == "BUY" and current_price > vwap) or                        (base_signal == "SELL" and current_price < vwap)

        # ── FILTER 3: EMA ──
        ema20 = float(ema(df['Close'], 20).iloc[-1])
        ema_pass = False
        if ema_filter:
            ema_pass = (base_signal == "BUY" and current_price > ema20) or                       (base_signal == "SELL" and current_price < ema20)

        # ── FILTER 4: VOLUME ──
        vol_ratio = None
        vol_pass = False
        if volume_filter:
            prev_avg_vol = float(prev_data['Volume'].mean())
            num_candles = len(today_data)
            if num_candles >= 2 and prev_avg_vol > 0:
                curr_vol = float(today_data['Volume'].sum())
                expected_vol = prev_avg_vol * num_candles
                vol_ratio = round(curr_vol / expected_vol, 1)
                vol_pass = vol_ratio > 1.2

        # ── FILTER 5: GAP+SPIKE (already passed above) ──
        gap_pass = True

        # ── ACCURACY CALCULATION ──
        filters_passed = 1  # ORB always passed
        total_filters = 1
        filter_details = [("ORB Breakout", True, f"Price broke {base_signal}")]

        if vwap_filter:
            total_filters += 1
            filters_passed += 1 if vwap_pass else 0
            filter_details.append(("VWAP", vwap_pass, f"₹{vwap:.2f}" if vwap else "N/A"))

        if ema_filter:
            total_filters += 1
            filters_passed += 1 if ema_pass else 0
            filter_details.append(("EMA 20", ema_pass, f"₹{ema20:.2f}"))

        if volume_filter:
            total_filters += 1
            filters_passed += 1 if vol_pass else 0
            filter_details.append(("Volume", vol_pass, f"{vol_ratio}x" if vol_ratio else "N/A"))

        if gap_filter:
            total_filters += 1
            filters_passed += 1
            filter_details.append(("Gap+Spike", True, f"Gap: {gap_pct}%"))

        accuracy = round((filters_passed / total_filters) * 100, 1) if total_filters > 0 else 0

        # ── ATR & LEVELS ──
        atr = calculate_atr(today_data)
        if atr > 0:
            if base_signal == "BUY":
                atr_sl = entry_price - (1.5 * atr)
                stop_loss = max(stop_loss, atr_sl)
            else:
                atr_sl = entry_price + (1.5 * atr)
                stop_loss = min(stop_loss, atr_sl)

        risk = abs(entry_price - stop_loss)
        target = entry_price + (risk * risk_reward) if base_signal == "BUY" else entry_price - (risk * risk_reward)

        # ── OI BUILDUP CLASSIFICATION ──
        oi_pct = oi_info.get('oi_chg_pct', 0)
        oi_up = oi_pct > 0
        price_up = ((current_price - prev_close) / prev_close * 100) > 0

        if oi_up and price_up:
            oi_buildup = "🐂 LONG BUILDUP"
            oi_signal = "STRONG LONG" if oi_pct > 15 else "LONG"
        elif oi_up and not price_up:
            oi_buildup = "🐻 SHORT BUILDUP"
            oi_signal = "STRONG SHORT" if oi_pct > 15 else "SHORT"
        elif not oi_up and price_up:
            oi_buildup = "📤 SHORT COVERING"
            oi_signal = "SHORT SQUEEZE"
        else:
            oi_buildup = "📉 LONG UNWINDING"
            oi_signal = "WEAKNESS"

        # ── OI-SIGNAL ALIGNMENT ──
        oi_alignment = 0
        if base_signal == "BUY" and oi_signal in ["STRONG LONG", "LONG", "SHORT SQUEEZE"]:
            oi_alignment = 1
        elif base_signal == "SELL" and oi_signal in ["STRONG SHORT", "SHORT", "WEAKNESS"]:
            oi_alignment = 1
        elif base_signal == "BUY" and oi_signal in ["STRONG SHORT", "SHORT", "WEAKNESS"]:
            oi_alignment = -1
        elif base_signal == "SELL" and oi_signal in ["STRONG LONG", "LONG", "SHORT SQUEEZE"]:
            oi_alignment = -1

        # ── FINAL SIGNAL ──
        if accuracy >= 80 and oi_alignment >= 0:
            final_signal = f"🚀 STRONG {base_signal}"
        elif accuracy >= 60 and oi_alignment >= 0:
            final_signal = f"✅ {base_signal}"
        elif accuracy >= 60 and oi_alignment < 0:
            final_signal = f"⚠️ WEAK {base_signal}"
        else:
            final_signal = "🟡 WAIT"

        chg_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

        return {
            "STOCK": ticker,
            "SIGNAL": final_signal,
            "BASE_SIGNAL": base_signal,
            "LTP": round(current_price, 2),
            "CHG %": f"{'+' if chg_pct >= 0 else ''}{chg_pct}%",
            "ORB_HIGH": round(orb_high, 2),
            "ORB_LOW": round(orb_low, 2),
            "ENTRY": round(entry_price, 2),
            "SL": round(stop_loss, 2),
            "TARGET": round(target, 2),
            "RISK": round(risk, 2),
            "RISK %": round((risk / entry_price) * 100, 2),
            "ACCURACY": f"{accuracy}%",
            "FILTERS": f"{filters_passed}/{total_filters}",
            "VWAP": "⬆ ABOVE" if (vwap and current_price > vwap) else "⬇ BELOW" if vwap else "N/A",
            "EMA TREND": "📈 BULLISH" if current_price > ema20 else "📉 BEARISH",
            "VOL RATIO": f"{vol_ratio}x" if vol_ratio else "N/A",
            "OI SPURT %": f"{'🟢' if oi_pct >= 0 else '🔴'} {oi_pct:+.2f}%",
            "OI BUILDUP": oi_buildup,
            "OI SIGNAL": oi_signal,
            "OI ALIGN": "✅ ALIGNED" if oi_alignment > 0 else "⚠️ CONFLICT" if oi_alignment < 0 else "➖ NEUTRAL",
            "SECTOR": STOCK_TO_SECTOR.get(ticker, "—"),
            "DATA_SOURCE": source.upper(),
            "filter_details": filter_details,
            "vwap_val": round(vwap, 2) if vwap else None,
            "ema20_val": round(ema20, 2),
            "atr": round(atr, 2),
            "gap_pct": gap_pct,
            "oi_chg_pct": oi_pct,
            "oi_prev": oi_info.get('prev_oi', 0),
            "oi_latest": oi_info.get('latest_oi', 0),
            "oi_chng": oi_info.get('chg_oi', 0),
        }, None

    except Exception as e:
        return None, f"Error: {str(e)}"


# ============================================================
# CHART FUNCTIONS
# ============================================================

def get_chart_data(ticker, interval, period, access_token=""):
    """Get data for charts"""
    try:
        if access_token:
            interval_map = {"5m": "5", "15m": "15", "1h": "60"}
            dhan_int = interval_map.get(interval, "5")
            df = fetch_dhan_intraday(ticker, access_token, dhan_int)
            if df is not None:
                return df
        df = yf.download(ticker + ".NS", period=period, interval=interval, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        df['EMA9'] = ema(df['Close'], 9)
        df['EMA21'] = ema(df['Close'], 21)
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
        return df
    except:
        return None

def plot_super_chart(df, ticker, interval_label):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, row_heights=[0.75, 0.25])
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="Price",
        increasing_line_color='#00ff88', decreasing_line_color='#ff4060',
        increasing_fillcolor='#00ff8855', decreasing_fillcolor='#ff406055',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'],
        line=dict(color='#ffc700', width=1.5), name='EMA 9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'],
        line=dict(color='#ff6b6b', width=1.5), name='EMA 21'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'],
        line=dict(color='#00d4ff', width=1.5, dash='dot'), name='VWAP'), row=1, col=1)
    colors = ['#00ff88' if float(df['Close'].iloc[i]) >= float(df['Open'].iloc[i])
              else '#ff4060' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'],
        marker_color=colors, name='Volume', opacity=0.6), row=2, col=1)
    fig.update_layout(
        title=dict(text=f"<b>{ticker}</b> — {interval_label}",
                   font=dict(size=16, color='#c8d8e8')),
        template="plotly_dark", paper_bgcolor='#080c12', plot_bgcolor='#0d1219',
        xaxis_rangeslider_visible=False, height=580,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=10, r=10, t=60, b=10),
        font=dict(family='JetBrains Mono')
    )
    fig.update_xaxes(showgrid=True, gridcolor='#1e2d3d', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#1e2d3d', zeroline=False)
    return fig

# ============================================================
# COLOR FUNCTIONS
# ============================================================

def color_signal_super(val):
    v = str(val)
    if "STRONG BUY" in v: return "background:#00ff8815;color:#00ff88;font-weight:700;"
    if "BUY" in v and "WEAK" not in v: return "background:#00cc6615;color:#00cc66;font-weight:700;"
    if "STRONG SELL" in v: return "background:#ff406015;color:#ff4060;font-weight:700;"
    if "SELL" in v and "WEAK" not in v: return "background:#ff202015;color:#ff2020;font-weight:700;"
    if "WEAK" in v: return "background:#ffc70015;color:#ffc700;font-weight:700;"
    if "WAIT" in v: return "background:#6a8aaa15;color:#6a8aaa;font-weight:700;"
    return ""

def color_oi_super(val):
    v = str(val)
    if '🟢' in v: return 'color:#00ff88;font-weight:700;font-size:13px;'
    if '🔴' in v: return 'color:#ff4060;font-weight:700;font-size:13px;'
    return ''

def color_oi_buildup(val):
    v = str(val)
    if 'LONG BUILDUP' in v: return 'background:#00ff8810;color:#00ff88;font-weight:700;'
    if 'SHORT BUILDUP' in v: return 'background:#ff406010;color:#ff4060;font-weight:700;'
    if 'SHORT COVER' in v: return 'background:#ffc70010;color:#ffc700;font-weight:700;'
    if 'LONG UNWIND' in v: return 'background:#ff6b6b10;color:#ff6b6b;font-weight:700;'
    return ''

def color_accuracy(val):
    try:
        v = int(str(val).replace('%',''))
        if v >= 90: return "background:#00ff8820;color:#00ff88;font-weight:700;"
        if v >= 80: return "background:#00cc6620;color:#00cc66;font-weight:700;"
        if v >= 70: return "background:#ffc70020;color:#ffc700;font-weight:700;"
        return "background:#ff406020;color:#ff4060;font-weight:700;"
    except: return ""

def color_chg_super(val):
    try:
        v = float(str(val).replace('%','').replace('+',''))
        if v > 0: return 'color:#00ff88;font-weight:700'
        if v < 0: return 'color:#ff4060;font-weight:700'
    except: pass
    return ''

def color_ema_super(val):
    if "BULLISH" in str(val): return 'color:#00ff88;font-weight:700'
    if "BEARISH" in str(val): return 'color:#ff4060;font-weight:700'
    return ''

def color_vwap_super(val):
    if "ABOVE" in str(val): return 'color:#00ff88'
    if "BELOW" in str(val): return 'color:#ff4060'
    return ''

def color_oi_align(val):
    v = str(val)
    if 'ALIGNED' in v: return 'background:#00ff8810;color:#00ff88;font-weight:700;'
    if 'CONFLICT' in v: return 'background:#ff406010;color:#ff4060;font-weight:700;'
    return 'background:#6a8aaa10;color:#6a8aaa;font-weight:700;'

# ============================================================
# JOURNAL FUNCTIONS
# ============================================================
JOURNAL_FILE = "super_journal.json"

def load_journal():
    try:
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_journal(entries):
    with open(JOURNAL_FILE, "w") as f:
        json.dump(entries, f, indent=2)

def color_pnl(val):
    try:
        if float(val) > 0: return 'color:#00ff88;font-weight:700'
        if float(val) < 0: return 'color:#ff4060;font-weight:700'
    except: pass
    return ''

def color_status(val):
    if val == "HIT TARGET": return 'color:#00ff88;font-weight:700'
    if val == "HIT SL": return 'color:#ff4060;font-weight:700'
    if val == "OPEN": return 'color:#ffc700;font-weight:700'
    return ''

# ============================================================
# DISPLAY CARD
# ============================================================

def display_signal_card(result):
    """Display detailed signal card with all info"""
    signal = result['SIGNAL']
    base = result['BASE_SIGNAL']

    # Determine card class
    if "STRONG BUY" in signal:
        card_class = "card-strong-buy"
        signal_icon = "🚀"
        signal_color = "#00ff88"
    elif "BUY" in signal and "WEAK" not in signal:
        card_class = "card-buy"
        signal_icon = "✅"
        signal_color = "#00cc66"
    elif "STRONG SELL" in signal:
        card_class = "card-strong-sell"
        signal_icon = "🔴"
        signal_color = "#ff4060"
    elif "SELL" in signal and "WEAK" not in signal:
        card_class = "card-sell"
        signal_icon = "🔻"
        signal_color = "#ff2020"
    elif "WEAK" in signal:
        card_class = ""
        signal_icon = "⚠️"
        signal_color = "#ffc700"
    else:
        card_class = ""
        signal_icon = "🟡"
        signal_color = "#6a8aaa"

    # OI Buildup badge
    oi_buildup = result['OI BUILDUP']
    if "LONG BUILDUP" in oi_buildup:
        oi_badge = f'<span class="badge-long-build">{oi_buildup}</span>'
    elif "SHORT BUILDUP" in oi_buildup:
        oi_badge = f'<span class="badge-short-build">{oi_buildup}</span>'
    elif "SHORT COVER" in oi_buildup:
        oi_badge = f'<span class="badge-short-cover">{oi_buildup}</span>'
    elif "LONG UNWIND" in oi_buildup:
        oi_badge = f'<span class="badge-long-unwind">{oi_buildup}</span>'
    else:
        oi_badge = ''

    # Accuracy badge
    try:
        acc_val = result['ACCURACY']
        if isinstance(acc_val, (int, float)):
            acc = int(acc_val)
        else:
            acc = int(str(acc_val).replace('%','').strip())
    except (ValueError, TypeError):
        acc = 0
    if acc >= 90:
        acc_class = "acc-90"
    elif acc >= 80:
        acc_class = "acc-80"
    else:
        acc_class = "acc-70"

    with st.expander(f"{signal_icon} {result['STOCK']} | ₹{result['LTP']} | {result['ACCURACY']} | {result['OI BUILDUP']}"):
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

        # Top row: Signal + Accuracy
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.markdown(f"""
            <div style="font-size:24px;font-weight:800;color:{signal_color};letter-spacing:2px;">
                {signal}
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="acc-badge {acc_class}">{result["ACCURACY"]}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:right;color:#6a8aaa;font-size:11px;">{result["FILTERS"]} Filters</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # OI Section
        st.markdown("<div class='section-h'>📊 OI Analysis</div>", unsafe_allow_html=True)
        oi_col1, oi_col2, oi_col3, oi_col4 = st.columns(4)
        with oi_col1:
            st.markdown(f"""
            <div class="oi-card-super">
                <div class="oi-metric-val">{result['OI SPURT %']}</div>
                <div class="oi-metric-lbl">OI Change</div>
            </div>
            """, unsafe_allow_html=True)
        with oi_col2:
            st.markdown(f"""
            <div class="oi-card-super">
                <div class="oi-metric-val">{result['OI SIGNAL']}</div>
                <div class="oi-metric-lbl">OI Signal</div>
            </div>
            """, unsafe_allow_html=True)
        with oi_col3:
            st.markdown(f"""
            <div class="oi-card-super">
                <div class="oi-metric-val">{result['OI ALIGN']}</div>
                <div class="oi-metric-lbl">Alignment</div>
            </div>
            """, unsafe_allow_html=True)
        with oi_col4:
            st.markdown(f"""
            <div class="oi-card-super">
                <div class="oi-metric-val">{result['SECTOR']}</div>
                <div class="oi-metric-lbl">Sector</div>
            </div>
            """, unsafe_allow_html=True)

        # Trade Levels
        st.markdown("<div class='section-h'>💰 Trade Levels</div>", unsafe_allow_html=True)
        t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
        with t_col1:
            st.metric("Entry", f"₹{result['ENTRY']}")
        with t_col2:
            st.metric("SL", f"₹{result['SL']}", delta=f"-{result['RISK %']}%", delta_color="inverse")
        with t_col3:
            st.metric("Target", f"₹{result['TARGET']}")
        with t_col4:
            st.metric("Risk", f"₹{result['RISK']}")
        with t_col5:
            st.metric("R:R", f"1:{risk_reward}")

        # Technicals
        st.markdown("<div class='section-h'>📈 Technicals</div>", unsafe_allow_html=True)
        tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
        with tech_col1:
            st.markdown(f'<div style="color: #e8f0f8; background: #0d1a26; border: 1px solid #1e2d3d; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;"><b style="color: #00d4ff;">VWAP:</b> {result["VWAP"]}<br><small style="color: #a0b8d0;">Value: ₹{result.get("vwap_val", "N/A")}</small></div>', unsafe_allow_html=True)
        with tech_col2:
            st.markdown(f'<div style="color: #e8f0f8; background: #0d1a26; border: 1px solid #1e2d3d; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;"><b style="color: #00d4ff;">EMA:</b> {result["EMA TREND"]}<br><small style="color: #a0b8d0;">Value: ₹{result.get("ema20_val", "N/A")}</small></div>', unsafe_allow_html=True)
        with tech_col3:
            st.markdown(f'<div style="color: #e8f0f8; background: #0d1a26; border: 1px solid #1e2d3d; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;"><b style="color: #00d4ff;">Volume:</b> {result["VOL RATIO"]}<br><small style="color: #a0b8d0;">vs Previous Day</small></div>', unsafe_allow_html=True)
        with tech_col4:
            st.markdown(f'<div style="color: #e8f0f8; background: #0d1a26; border: 1px solid #1e2d3d; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;"><b style="color: #00d4ff;">ATR:</b> ₹{result.get("atr", "N/A")}<br><small style="color: #a0b8d0;">Gap: {result.get("gap_pct", 0)}%</small></div>', unsafe_allow_html=True)

        # Filter Details
        st.markdown("<div class='section-h'>📋 Filter Analysis</div>", unsafe_allow_html=True)
        filter_details = result.get('filter_details', [])
        for name, passed, detail in filter_details:
            if passed:
                st.markdown(f'<div class="filter-box-super filter-pass" style="color: #e8f0f8; background: linear-gradient(90deg, #00ff8815, #0d1a26); border: 1px solid #1e2d3d; border-left: 3px solid #00ff88; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;">✅ <b style="color: #00d4ff;">{name}</b> — <span style="color: #a0b8d0;">{detail}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="filter-box-super filter-fail" style="color: #e8f0f8; background: linear-gradient(90deg, #ff406015, #0d1a26); border: 1px solid #1e2d3d; border-left: 3px solid #ff4060; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;">❌ <b style="color: #ff4060;">{name}</b> — <span style="color: #a0b8d0;">{detail}</span></div>', unsafe_allow_html=True)

        # Add to Journal button
        if st.button(f"📝 Add {result['STOCK']} to Journal", key=f"journal_{result['STOCK']}"):
            entries = load_journal()
            entries.append({
                "date": str(now_ist().date()),
                "stock": result['STOCK'],
                "type": base,
                "entry": result['ENTRY'],
                "sl": result['SL'],
                "target": result['TARGET'],
                "qty": 1,
                "status": "OPEN",
                "pnl": 0,
                "notes": f"Super Scanner | {signal} | {result['OI BUILDUP']} | Acc: {result['ACCURACY']}"
            })
            save_journal(entries)
            st.success(f"✅ {result['STOCK']} added to Journal!")

# ============================================================
# MAIN TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(["  🚀  SUPER SCANNER  ", "  📊  CHARTS  ", "  📓  JOURNAL  "])

# ─────────────────────────────────────────
# TAB 1 — SUPER SCANNER
# ─────────────────────────────────────────
with tab1:
    if not open_status:
        st.warning(f"⚠️ {market_msg} — Showing last available data")

    # Show sector performance
    if 'sector_perf' not in st.session_state or refresh:
        with st.spinner("Loading sector data..."):
            sector_perf = get_sector_performance()
            st.session_state['sector_perf'] = sector_perf
    else:
        sector_perf = st.session_state['sector_perf']

    if sector_perf:
        st.markdown("<div class='section-h'>🏢 Sector Performance</div>", unsafe_allow_html=True)
        sec_cols = st.columns(4)
        for i, (sector, data) in enumerate(sector_perf.items()):
            with sec_cols[i % 4]:
                trend = data['trend']
                change = data['change']
                if trend in ["STRONG_UP", "UP"]:
                    color = "#00ff88"
                    icon = "📈"
                elif trend in ["STRONG_DOWN", "DOWN"]:
                    color = "#ff4060"
                    icon = "📉"
                else:
                    color = "#ffc700"
                    icon = "➖"
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d1a26,#111820);
                            border:1px solid #1e2d3d;border-radius:10px;
                            padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#6a8aaa;letter-spacing:1px;">{sector}</div>
                    <div style="font-size:18px;font-weight:700;color:{color};margin:4px 0;">
                        {icon} {change:+.2f}%
                    </div>
                    <div style="font-size:9px;color:#3a5a7a;">{trend}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # SCAN BUTTON
    if refresh or 'scan_results' not in st.session_state:
        if refresh:
            # Get OI Spurts
            with st.spinner("🔍 Fetching NSE OI Spurts data..."):
                oi_list, oi_source = get_oi_spurts()
                st.session_state['oi_list'] = oi_list
                st.session_state['oi_source'] = oi_source

            if not oi_list:
                st.error("❌ Failed to fetch OI data from NSE. Try again or check connection.")
                st.info("💡 Tip: If nsepython is installed, it should handle NSE session automatically.")
            else:
                st.success(f"✅ OI Spurts loaded via {oi_source}! Top: {oi_list[0]['symbol']} (+{oi_list[0]['oi_chg_pct']:.2f}%)")

                # Show OI preview
                oi_preview = pd.DataFrame([{
                    'RANK': i+1,
                    'SYMBOL': x['symbol'],
                    'OI CHANGE %': f"{'🟢' if x['oi_chg_pct'] >= 0 else '🔴'} {x['oi_chg_pct']:+.2f}%",
                    'PREV OI': f"{x['prev_oi']:,}",
                    'LATEST OI': f"{x['latest_oi']:,}",
                    'CHG OI': f"{x['chg_oi']:+,}",
                } for i, x in enumerate(oi_list[:20])])

                with st.expander("📊 NSE OI Spurts Raw Data", expanded=False):
                    st.dataframe(oi_preview, use_container_width=True, hide_index=True)

                # Determine stock list based on mode
                if "QUICK" in scan_mode:
                    stock_list = [item['symbol'] for item in oi_list[:20]]
                    st.info(f"🏃 Quick Scan: Top {len(stock_list)} OI Spurt stocks")
                else:
                    # Full scan - use pre-selected universe from sidebar
                    universe = st.session_state.get('selected_universe', 'Nifty 50')

                    if universe == "F&O Pro Top 20":
                        stock_list = [item['symbol'] for item in oi_list[:20]]
                    elif universe == "Custom":
                        stock_list = st.session_state.get('custom_stock_list', ["RELIANCE", "TCS", "HDFCBANK"])
                    else:
                        stock_list = STOCK_UNIVERSES.get(universe, [])

                    st.info(f"🔍 Full Scan: {universe} — {len(stock_list)} stocks")

                # Scan stocks
                results = []
                skipped = []
                progress = st.progress(0)
                status = st.empty()

                access_token = st.session_state.get('dhan_token', '')

                for i, ticker in enumerate(stock_list):
                    # Find OI info for this ticker
                    oi_info = next((item for item in oi_list if item['symbol'] == ticker), 
                                  {'symbol': ticker, 'oi_chg_pct': 0, 'prev_oi': 0, 'latest_oi': 0, 'chg_oi': 0})

                    status.markdown(
                        f'<div style="color:#6a8aaa;font-size:11px;">'
                        f'⏳ SCANNING: <span style="color:#00d4ff;font-weight:700;">{ticker}</span> '
                        f'| OI: <span style="color:#00ff88;">{oi_info["oi_chg_pct"]:+.1f}%</span> '
                        f'({i+1}/{len(stock_list)})</div>',
                        unsafe_allow_html=True
                    )

                    result, error = analyze_stock_orb_oi(
                        ticker, oi_info, 
                        orb_mins=orb_minutes,
                        gap_filter=gap_spike_filter,
                        vwap_filter=use_vwap,
                        ema_filter=use_ema,
                        volume_filter=use_volume,
                        access_token=access_token
                    )

                    if result:
                        results.append(result)
                    else:
                        skipped.append((ticker, error))

                    progress.progress((i + 1) / len(stock_list))
                    time.sleep(0.1)

                status.empty()
                progress.empty()

                # Save results
                st.session_state['scan_results'] = results
                st.session_state['skipped'] = skipped

        # Display results
        if 'scan_results' in st.session_state:
            results = st.session_state['scan_results']
            skipped = st.session_state.get('skipped', [])

            if skipped:
                skip_msg = ", ".join([f"{s[0]} ({s[1]})" for s in skipped[:10]])
                st.markdown(f"""
                <div style="background:#ffc70010;border:1px solid #ffc70030;border-radius:8px;
                            padding:10px 16px;color:#ffc700;font-size:11px;margin-bottom:12px;">
                    ⚡ <b>Skipped {len(skipped)} stocks:</b> {skip_msg}
                    {"..." if len(skipped) > 10 else ""}
                </div>
                """, unsafe_allow_html=True)

            if results:
                # Metrics
                strong_buy = len([r for r in results if "STRONG BUY" in r['SIGNAL']])
                buy = len([r for r in results if r['SIGNAL'] == "✅ BUY"])
                strong_sell = len([r for r in results if "STRONG SELL" in r['SIGNAL']])
                sell = len([r for r in results if r['SIGNAL'] == "🔻 SELL"])
                weak = len([r for r in results if "WEAK" in r['SIGNAL']])
                wait = len([r for r in results if "WAIT" in r['SIGNAL']])

                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("🚀 Strong Buy", strong_buy)
                m2.metric("✅ Buy", buy)
                m3.metric("🔴 Strong Sell", strong_sell)
                m4.metric("🔻 Sell", sell)
                m5.metric("⚠️ Weak", weak)
                m6.metric("🟡 Wait", wait)

                st.markdown("---")

                # Filter
                st.markdown("<div class='section-h'>📈 Scan Results</div>", unsafe_allow_html=True)
                f1, f2 = st.columns([1, 3])
                with f1:
                    signal_filter = st.selectbox("Filter", 
                        ["All Signals", "🚀 Strong Buy", "✅ Buy", "🔴 Strong Sell", "🔻 Sell", "⚠️ Weak", "🟡 Wait"],
                        label_visibility="collapsed")

                df_results = pd.DataFrame(results)

                if signal_filter != "All Signals":
                    filter_map = {
                        "🚀 Strong Buy": "STRONG BUY",
                        "✅ Buy": "✅ BUY",
                        "🔴 Strong Sell": "STRONG SELL",
                        "🔻 Sell": "🔻 SELL",
                        "⚠️ Weak": "WEAK",
                        "🟡 Wait": "WAIT"
                    }
                    filter_key = filter_map.get(signal_filter, "")
                    df_results = df_results[df_results['SIGNAL'].str.contains(filter_key.replace("🚀 ", "").replace("✅ ", "").replace("🔴 ", "").replace("🔻 ", ""))]

                # Styled dataframe
                styled = (
                    df_results.style
                    .map(color_signal_super, subset=['SIGNAL'])
                    .map(color_oi_super, subset=['OI SPURT %'])
                    .map(color_oi_buildup, subset=['OI BUILDUP'])
                    .map(color_accuracy, subset=['ACCURACY'])
                    .map(color_chg_super, subset=['CHG %'])
                    .map(color_ema_super, subset=['EMA TREND'])
                    .map(color_vwap_super, subset=['VWAP'])
                    .map(color_oi_align, subset=['OI ALIGN'])
                    .set_properties(**{
                        'background-color': '#0d1219',
                        'color': '#c8d8e8',
                        'border-color': '#1e2d3d',
                        'font-size': '12px',
                    })
                    .set_table_styles([
                        {'selector': 'thead th', 'props': [
                            ('background-color', '#111820'),
                            ('color', '#6a8aaa'),
                            ('font-size', '10px'),
                            ('letter-spacing', '2px'),
                            ('text-transform', 'uppercase'),
                            ('border-bottom', '2px solid #1e2d3d'),
                            ('padding', '10px 12px'),
                        ]},
                        {'selector': 'tbody tr:hover', 'props': [
                            ('background-color', '#111820 !important'),
                        ]},
                        {'selector': 'tbody td', 'props': [
                            ('padding', '10px 12px'),
                            ('border-bottom', '1px solid #1e2d3d'),
                        ]},
                    ])
                )

                st.markdown(styled.to_html(escape=False), unsafe_allow_html=True)

                # CSV Download
                csv = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"super_scan_{now_ist().strftime('%d%m%Y_%H%M')}.csv",
                    mime='text/csv',
                )

                # Detailed Cards
                st.markdown("---")
                st.markdown("<div class='section-h'>🔍 Detailed Analysis</div>", unsafe_allow_html=True)

                # Sort by signal strength
                priority = {"🚀 STRONG BUY": 0, "✅ BUY": 1, "🔴 STRONG SELL": 2, "🔻 SELL": 3, "⚠️ WEAK BUY": 4, "⚠️ WEAK SELL": 5, "🟡 WAIT": 6}
                sorted_results = sorted(results, key=lambda x: priority.get(x['SIGNAL'], 99))

                for result in sorted_results[:10]:  # Show top 10
                    display_signal_card(result)
            else:
                st.warning("⚠️ No signals found. Try adjusting filters or check market hours.")
    else:
        st.info("💡 Click '🚀 SCAN NOW' in sidebar to start scanning")


# ─────────────────────────────────────────
# TAB 2 — CHARTS
# ─────────────────────────────────────────
with tab2:
    st.markdown("<div class='section-h'>📊 Advanced Charts — EMA + VWAP + Volume</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        chart_ticker = st.text_input("Stock Symbol", value="RELIANCE", placeholder="e.g. RELIANCE, TCS, SBIN").upper()
    with c2:
        chart_tf = st.selectbox("Timeframe", ["5 Min", "15 Min", "1 Hour", "1 Day"])
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        load_chart = st.button("📈 Load Chart", use_container_width=True)

    tf_map = {"5 Min": ("5m", "5d"), "15 Min": ("15m", "5d"), "1 Hour": ("1h", "30d"), "1 Day": ("1d", "6mo")}

    if load_chart:
        interval, period = tf_map[chart_tf]
        with st.spinner(f"Loading {chart_ticker} {chart_tf} chart..."):
            access_token = st.session_state.get('dhan_token', '')
            df_chart = get_chart_data(chart_ticker, interval, period, access_token)

        if df_chart is not None and len(df_chart) > 5:
            fig = plot_super_chart(df_chart, chart_ticker, chart_tf)
            st.plotly_chart(fig, use_container_width=True)

            last = df_chart.iloc[-1]
            prev = df_chart.iloc[-2] if len(df_chart) > 1 else last
            chg_val = round(float(last['Close']) - float(prev['Close']), 2)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("💰 LTP", round(float(last['Close']), 2), delta=chg_val)
            m2.metric("〰 VWAP", round(float(last['VWAP']), 2))
            m3.metric("📊 EMA 9", round(float(last['EMA9']), 2))
            m4.metric("📊 EMA 21", round(float(last['EMA21']), 2))
            m5.metric("📊 Volume", f"{int(last['Volume']):,}")

            cp = float(last['Close'])
            vwap = float(last['VWAP'])
            e9 = float(last['EMA9'])
            e21 = float(last['EMA21'])

            if cp > vwap and e9 > e21:
                sig_color = "#00ff88"; sig_text = "🚀 BULLISH SETUP — All aligned"
            elif cp < vwap and e9 < e21:
                sig_color = "#ff4060"; sig_text = "🔴 BEARISH SETUP — All aligned"
            else:
                sig_color = "#ffc700"; sig_text = "🟡 MIXED — Wait for confirmation"

            st.markdown(f"""
            <div style="background:{sig_color}15;border:1px solid {sig_color}40;
                        border-radius:8px;padding:12px 20px;margin-top:8px;
                        color:{sig_color};font-weight:700;font-size:13px;letter-spacing:1px;">
                {sig_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ Chart data not available. Check symbol or try again.")


# ─────────────────────────────────────────
# TAB 3 — JOURNAL
# ─────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-h'>📓 Trade Journal — Track Your Performance</div>", unsafe_allow_html=True)

    with st.expander("➕ Add New Trade", expanded=False):
        j1, j2, j3 = st.columns(3)
        j_date = j1.date_input("📅 Date", datetime.now())
        j_stock = j2.text_input("📌 Stock", placeholder="RELIANCE")
        j_type = j3.selectbox("📊 Type", ["BUY", "SELL"])

        j4, j5, j6 = st.columns(3)
        j_entry = j4.number_input("💰 Entry", min_value=0.0, format="%.2f")
        j_sl = j5.number_input("🛑 SL", min_value=0.0, format="%.2f")
        j_target = j6.number_input("🎯 Target", min_value=0.0, format="%.2f")

        j7, j8 = st.columns(2)
        j_qty = j7.number_input("📦 Qty", min_value=1, value=1)
        j_status = j8.selectbox("🔖 Status", ["OPEN", "HIT TARGET", "HIT SL", "EXITED"])
        j_notes = st.text_area("📝 Notes", placeholder="Setup reason, OI data, etc.")

        if st.button("💾 Save Entry", use_container_width=True):
            if j_stock:
                entries = load_journal()
                pnl = 0
                if j_status != "OPEN":
                    if j_type == "BUY":
                        exit_p = j_target if j_status == "HIT TARGET" else j_sl if j_status == "HIT SL" else j_entry
                    else:
                        exit_p = j_sl if j_status == "HIT TARGET" else j_target if j_status == "HIT SL" else j_entry
                    pnl = round((exit_p - j_entry) * j_qty if j_type == "BUY" else (j_entry - exit_p) * j_qty, 2)

                entries.append({
                    "date": str(j_date), "stock": j_stock.upper(),
                    "type": j_type, "entry": j_entry, "sl": j_sl,
                    "target": j_target, "qty": j_qty,
                    "status": j_status, "pnl": pnl, "notes": j_notes
                })
                save_journal(entries)
                st.success(f"✅ {j_stock.upper()} saved!")
            else:
                st.error("❌ Enter stock name!")

    st.markdown("---")
    entries = load_journal()
    if entries:
        df_j = pd.DataFrame(entries)
        total_pnl = df_j['pnl'].sum()
        wins = len(df_j[df_j['pnl'] > 0])
        losses = len(df_j[df_j['pnl'] < 0])
        open_t = len(df_j[df_j['status'] == 'OPEN'])
        win_rate = round((wins / max(wins + losses, 1)) * 100, 1)

        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("💰 Total P&L", f"₹{round(total_pnl,2)}")
        p2.metric("✅ Wins", wins)
        p3.metric("❌ Losses", losses)
        p4.metric("🎯 Win Rate", f"{win_rate}%")
        p5.metric("🔓 Open", open_t)

        styled_j = (
            df_j.style
            .map(color_pnl, subset=['pnl'])
            .map(color_status, subset=['status'])
            .set_properties(**{'background-color':'#0d1219','color':'#c8d8e8','border-color':'#1e2d3d','font-size':'12px'})
            .set_table_styles([
                {'selector':'thead th','props':[('background-color','#111820'),('color','#6a8aaa'),
                 ('font-size','10px'),('letter-spacing','2px'),('text-transform','uppercase'),
                 ('border-bottom','2px solid #1e2d3d'),('padding','10px 12px')]},
                {'selector':'tbody td','props':[('padding','10px 12px'),('border-bottom','1px solid #1e2d3d')]},
            ])
        )
        st.markdown(styled_j.to_html(escape=False), unsafe_allow_html=True)

        if st.button("🗑️ Clear Journal"):
            save_journal([])
            st.success("Journal cleared!")
            st.rerun()
    else:
        st.markdown("""
        <div style="background:#0d1219;border:1px solid #1e2d3d;border-radius:10px;
                    padding:40px;text-align:center;color:#3a5a7a;">
            <div style="font-size:2rem;margin-bottom:8px;">📓</div>
            <div style="font-size:12px;letter-spacing:2px;">No entries yet. Add your first trade above!</div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#3a5a7a;font-size:10px;letter-spacing:1px;">
    <b>🚀 SUPER SCANNER PRO</b> | ORB + OI Spurts + VWAP + EMA | NSE Intraday Live<br>
    Disclaimer: Educational purposes only. Not financial advice.
</div>
""", unsafe_allow_html=True)
