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
# Validate theme - fix for KeyError on Streamlit Cloud
if 'theme' not in st.session_state or st.session_state.theme not in THEMES:
    st.session_state.theme = "DARK"

T = THEMES[st.session_state.theme]
is_dark = st.session_state.theme in ["DARK", "MODERATE"]
is_light = st.session_state.theme == "LIGHT"

# Determine text colors based on theme
if is_dark:
    text_primary = "#f0f6fc"      # Very light blue-white (brighter for clarity)
    text_secondary = "#b8d0e8"   # Light blue-gray (brightened)
    text_muted = "#9fc4e8"       # Medium blue-gray (brightened from #6a8aaa)
    text_dark = "#7fa8cf"         # Dark blue-gray (brightened from #3a5a7a)
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
    text_primary = "#0a1420"      # Very dark blue (darker for more contrast)
    text_secondary = "#1e2e3e"    # Dark gray-blue (darkened)
    text_muted = "#3a5468"       # Medium gray (darkened from #6a7a8a)
    text_dark = "#6a8298"         # Light gray (darkened from #9aaab8)
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

html, body, .stApp, [data-testid="stAppViewContainer"], 
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {{
    background-color: {bg_primary} !important;
    color: {text_primary} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

.stApp * {{
    color: {text_primary};
}}

section[data-testid="stSidebar"] {{ 
    background-color: {bg_card} !important; 
    border-right: 1px solid {border_color} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {text_primary} !important;
}}

#MainMenu, footer, header {{ visibility: hidden !important; }}

[data-testid="collapsedControl"] {{
    visibility: visible !important;
    display: block !important;
    position: fixed !important;
    top: 10px !important;
    left: 10px !important;
    z-index: 999999 !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: #00d4ff !important;
}}

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

.skip-box {{
    background: {accent_yellow}15 !important;
    border: 1px solid {accent_yellow}40 !important;
    border-radius: 8px; 
    padding: 10px 16px;
    color: {accent_yellow} !important; 
    font-size: 11px;
    font-weight: 600;
}}

.streamlit-expanderHeader {{
    color: {text_primary} !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}}
.streamlit-expanderContent {{
    background: {bg_primary} !important;
    color: {text_primary} !important;
}}

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

.stRadio > div {{
    color: {text_primary} !important;
}}
.stRadio label {{
    color: {text_primary} !important;
}}

.stCheckbox > label {{
    color: {text_primary} !important;
    font-size: 12px !important;
}}

.stSlider > div > div {{
    color: {text_primary} !important;
}}

.stSelectSlider > div {{
    color: {text_primary} !important;
}}

.stNumberInput > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

.stTextInput > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

.stSelectbox > label {{
    color: {text_muted} !important;
    font-size: 11px !important;
}}

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



st.markdown("""
<style>
.streamlit-expanderHeader:hover {
    background: #1a2436 !important;
    color: #00d4ff !important;
}
.streamlit-expanderContent:hover {
    background: #080c12 !important;
}
[data-testid="stDataFrame"] tr:hover {
    background: #0d1a26 !important;
}
.metric-card-super:hover {
    border-color: #00d4ff55 !important;
}
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

st.markdown("""
<style>
.streamlit-expander {
    background-color: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 10px !important;
}
.streamlit-expanderHeader {
    background-color: #0d1a26 !important;
    color: #e8f0f8 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
.streamlit-expanderHeader:hover {
    background-color: #1a2436 !important;
    color: #00d4ff !important;
}
.streamlit-expanderContent {
    background-color: #080c12 !important;
    color: #e8f0f8 !important;
}
.stSuccess {
    background-color: #00ff8815 !important;
    border: 1px solid #00ff8840 !important;
    color: #00ff88 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
.stSuccess > div {
    color: #00ff88 !important;
}
.stInfo {
    background-color: #00d4ff15 !important;
    border: 1px solid #00d4ff40 !important;
    color: #00d4ff !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
.stInfo > div {
    color: #00d4ff !important;
}
.stWarning {
    background-color: #ffc70015 !important;
    border: 1px solid #ffc70040 !important;
    color: #ffc700 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
.stWarning > div {
    color: #ffc700 !important;
}
.stError {
    background-color: #ff406015 !important;
    border: 1px solid #ff406040 !important;
    color: #ff4060 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
.stError > div {
    color: #ff4060 !important;
}
.stCaption {
    color: #6a8aaa !important;
    font-size: 11px !important;
}
.stCaption > div {
    color: #9fc4e8 !important;
}
.stTextInput > div > div > input::placeholder {
    color: #7fa8cf !important;
    opacity: 1 !important;
}
.stNumberInput > div > div > input::placeholder {
    color: #7fa8cf !important;
    opacity: 1 !important;
}
.stSelectbox > div > div > div {
    color: #e8f0f8 !important;
}
.stSlider > div > div > div {
    color: #e8f0f8 !important;
}
.stCheckbox > label > span {
    color: #e8f0f8 !important;
}
.stRadio > div > label > div {
    color: #e8f0f8 !important;
}
.stRadio > div > label > div:hover {
    color: #00d4ff !important;
}
.stMarkdown {
    color: #e8f0f8 !important;
}
.stMarkdown p {
    color: #e8f0f8 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #00d4ff !important;
}
[data-testid="stMetricValue"] {
    color: #e8f0f8 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #6a8aaa !important;
    font-size: 11px !important;
}
[data-testid="stMetricDelta"] {
    color: #00ff88 !important;
    font-size: 12px !important;
}
[data-testid="stDataFrame"] {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 10px !important;
}
[data-testid="stDataFrame"] th {
    background: #111820 !important;
    color: #6a8aaa !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid #1e2d3d !important;
    padding: 10px 12px !important;
}
[data-testid="stDataFrame"] td {
    background: #0d1a26 !important;
    color: #e8f0f8 !important;
    border-bottom: 1px solid #1e2d3d !important;
    padding: 10px 12px !important;
    font-size: 12px !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: #1a2436 !important;
    color: #e8f0f8 !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00d4ff, #00ff88) !important;
    border-radius: 4px !important;
}
.stSpinner > div {
    border-color: #00d4ff !important;
}
.toast {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.tooltip {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.dialog {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.stButton > button:active {
    background: linear-gradient(90deg, #00d4ff, #00ff88) !important;
    color: #000 !important;
}
.stButton > button:focus {
    box-shadow: 0 0 0 2px #00d4ff50 !important;
}
.stSelectSlider > div > div {
    color: #e8f0f8 !important;
}
.stFileUploader > div {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.stColorPicker > div {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
}
.stDateInput > div > div > input {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.stTimeInput > div > div > input {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.stTextArea > div > div > textarea {
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    color: #e8f0f8 !important;
}
.stCodeBlock {
    background: #111820 !important;
    border: 1px solid #1e2d3d !important;
    color: #00ff88 !important;
}
hr {
    border-color: #1e2d3d !important;
    border-width: 1px !important;
}
a {
    color: #00d4ff !important;
    text-decoration: none !important;
}
a:hover {
    color: #00ff88 !important;
    text-decoration: underline !important;
}
li {
    color: #e8f0f8 !important;
}
strong, b {
    color: #00d4ff !important;
    font-weight: 700 !important;
}
em, i {
    color: #a0b8d0 !important;
}
blockquote {
    border-left: 3px solid #00d4ff !important;
    background: #0d1a26 !important;
    color: #e8f0f8 !important;
    padding: 12px 16px !important;
    border-radius: 0 8px 8px 0 !important;
}
table {
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
}
th {
    background: #111820 !important;
    color: #6a8aaa !important;
    border-bottom: 2px solid #1e2d3d !important;
}
td {
    background: #0d1a26 !important;
    color: #e8f0f8 !important;
    border-bottom: 1px solid #1e2d3d !important;
}
figcaption {
    color: #6a8aaa !important;
    font-size: 11px !important;
}
audio, video {
    background: #0d1a26 !important;
    border-radius: 8px !important;
}
iframe {
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
}
.json-display {
    background: #111820 !important;
    border: 1px solid #1e2d3d !important;
    color: #00ff88 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
.status-indicator {
    color: #e8f0f8 !important;
}
.status-indicator-success {
    color: #00ff88 !important;
}
.status-indicator-error {
    color: #ff4060 !important;
}
.status-indicator-warning {
    color: #ffc700 !important;
}
.status-indicator-info {
    color: #00d4ff !important;
}
.stTooltipIcon {
    color: #6a8aaa !important;
}
.stTooltipIcon:hover {
    color: #00d4ff !important;
}
.empty-state {
    color: #6a8aaa !important;
    background: #0d1a26 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 12px !important;
    padding: 40px !important;
    text-align: center !important;
}
.loading-state {
    color: #00d4ff !important;
}
.skeleton {
    background: linear-gradient(90deg, #0d1a26, #1a2436, #0d1a26) !important;
    background-size: 200% 100% !important;
}
* {
    transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease !important;
}
*:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px #00d4ff40 !important;
}
::selection {
    background: #00d4ff33 !important;
    color: #e8f0f8 !important;
}
* {
    scrollbar-width: thin !important;
    scrollbar-color: #1e2d3d #0d1a26 !important;
}
@media print {
    body {
        background: #080c12 !important;
        color: #e8f0f8 !important;
    }
}
*:active {
    background-color: transparent !important;
    color: inherit !important;
}
*:focus-visible {
    outline: 2px solid #00d4ff60 !important;
    outline-offset: 2px !important;
    background-color: transparent !important;
}
*:target {
    background-color: transparent !important;
}
.streamlit-expander:active,
.streamlit-expander:focus,
.streamlit-expander:focus-within {
    background-color: #0d1a26 !important;
    border-color: #00d4ff55 !important;
}
.streamlit-expanderHeader:active,
.streamlit-expanderHeader:focus,
.streamlit-expanderHeader:focus-visible {
    background-color: #1a2436 !important;
    color: #00d4ff !important;
    outline: none !important;
}
.stButton > button:active,
.stButton > button:focus,
.stButton > button:focus-visible {
    background: linear-gradient(90deg, #00d4ff, #00ff88) !important;
    color: #000 !important;
    box-shadow: 0 0 0 3px #00d4ff40 !important;
    outline: none !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div:focus,
.stDateInput > div > div > input:focus,
.stTimeInput > div > div > input:focus {
    background-color: #0d1a26 !important;
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 3px #00d4ff30 !important;
    color: #e8f0f8 !important;
    outline: none !important;
}
.stCheckbox input:checked + div {
    background-color: #00ff88 !important;
    border-color: #00ff88 !important;
}
.stCheckbox input:checked + div > div {
    background-color: #000 !important;
}
.stRadio input:checked + div {
    background-color: #00d4ff !important;
    border-color: #00d4ff !important;
}
.stRadio input:checked + div > div {
    background-color: #000 !important;
}
.stSelectbox > div > div[aria-expanded="true"] {
    background-color: #0d1a26 !important;
    border-color: #00d4ff !important;
}
.stSlider > div > div > div > div[role="slider"]:active,
.stSlider > div > div > div > div[role="slider"]:focus {
    background-color: #00d4ff !important;
    box-shadow: 0 0 0 4px #00d4ff40 !important;
}
[data-testid="stDataFrame"] tr[aria-selected="true"] td {
    background-color: #1a2436 !important;
    color: #00d4ff !important;
}
.stTabs [aria-selected="true"]:active,
.stTabs [aria-selected="true"]:focus {
    background: linear-gradient(135deg, #00d4ff20, #00ff8820) !important;
    border-bottom: 2px solid #00d4ff !important;
    color: #00d4ff !important;
    outline: none !important;
}
[data-testid]:active,
[data-testid]:focus {
    background-color: transparent !important;
}
section[data-testid="stSidebar"] *:active,
section[data-testid="stSidebar"] *:focus {
    background-color: transparent !important;
    color: inherit !important;
}
.streamlit-expanderHeader > div:last-child:active,
.streamlit-expanderHeader > div:last-child:focus {
    background-color: transparent !important;
    color: #00d4ff !important;
}
[class*="st-"]:active,
[class*="st-"]:focus,
[class*="st-"]:focus-within,
[class*="st-"]:focus-visible {
    background-color: transparent !important;
}
::before,
::after {
    background-color: transparent !important;
    color: inherit !important;
}
* {
    -webkit-tap-highlight-color: transparent !important;
    -webkit-focus-ring-color: transparent !important;
}
.streamlit-expanderHeader svg {
    color: #6a8aaa !important;
    fill: #6a8aaa !important;
}
.streamlit-expanderHeader:hover svg,
.streamlit-expanderHeader:active svg,
.streamlit-expanderHeader:focus svg {
    color: #00d4ff !important;
    fill: #00d4ff !important;
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

    breakout_valid_cutoff = st.slider("Breakout Valid Till (min after ORB range closes)", 5, 60, 15, 5,
                            help="ORB range (jitne minute upar select kiya) band hone ke baad, breakout ko itne "
                                 "minute ke andar aana chahiye tabhi wo VALID mana jayega. Isse zyada der ho jaye "
                                 "to wo stock 'ORB Expired' keh kar skip ho jayega — chahe aap kisi bhi time scan karo, "
                                 "result hamesha fixed rahega.\n\n"
                                 "Example: Opening Range=5min, Cutoff=15min -> Range 9:15-9:20 banega, "
                                 "breakout sirf 9:20-9:35 ke beech aana chahiye, warna expired.")
    st.session_state.breakout_valid_cutoff = breakout_valid_cutoff

    _range_close_preview = now_ist().replace(hour=9, minute=15, second=0, microsecond=0) + timedelta(minutes=orb_minutes)
    _valid_till_preview = _range_close_preview + timedelta(minutes=breakout_valid_cutoff)
    st.markdown(f"<div style='font-size:10px;color:#00d4ff;text-align:center;'>Range closes {_range_close_preview.strftime('%H:%M')} → Breakout valid till {_valid_till_preview.strftime('%H:%M')} AM</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-h'>Filters</div>", unsafe_allow_html=True)
    gap_spike_filter = st.checkbox("⚡ Gap + Spike Filter", value=True,
                                   help="2% gap + 1.5% first 5-min move → SKIP")
    use_vwap = st.checkbox("📊 VWAP Filter", value=True)
    use_ema = st.checkbox("📈 EMA Filter", value=True)
    use_volume = st.checkbox("🔊 Volume Filter", value=True)

    st.markdown("<div style='font-size:11px;color:#6a8aaa;margin:8px 0 4px;'>🔊 Min Volume Ratio</div>", unsafe_allow_html=True)
    min_vol_ratio = st.slider("", 1.0, 5.0, 2.0, 0.5,
                              help="Volume vs previous day avg (1.0x = same, 2.0x = double)",
                              label_visibility="collapsed")
    st.session_state.min_vol_ratio = min_vol_ratio
    st.markdown(f"<div style='font-size:10px;color:#00d4ff;text-align:center;'>≥ {min_vol_ratio}x previous day</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-h'>OI Analysis</div>", unsafe_allow_html=True)
    use_oi = st.checkbox("🎯 OI Buildup Analysis", value=True,
                         help="Long Buildup / Short Buildup / Short Cover / Long Unwind")

    st.markdown("<div style='font-size:11px;color:#6a8aaa;margin:8px 0 4px;'>🎯 Min OI Change %</div>", unsafe_allow_html=True)
    min_oi_change = st.slider("", 0, 50, 10, 5, 
                              help="Minimum OI change % for signal strength",
                              label_visibility="collapsed")
    st.session_state.min_oi_change = min_oi_change
    st.markdown(f"<div style='font-size:10px;color:#00d4ff;text-align:center;'>≥ {min_oi_change}% for STRONG signal</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:11px;color:#6a8aaa;margin:8px 0 4px;'>💧 Min Absolute OI (Liquidity)</div>", unsafe_allow_html=True)
    min_absolute_oi = st.slider("", 100, 5000, 500, 100,
                              help="Isse kam absolute OI (contracts) wale stocks 'LOW LIQUIDITY ⚠️' tag "
                                   "ke saath dikhenge — chahe unka OI% badha hua kyun na dikhe, kyunki "
                                   "chhoti base OI par bada % noise ho sakta hai.",
                              label_visibility="collapsed")
    st.session_state.min_absolute_oi = min_absolute_oi
    st.markdown(f"<div style='font-size:10px;color:#00d4ff;text-align:center;'>≥ {min_absolute_oi:,} contracts</div>", unsafe_allow_html=True)

    st.markdown("---")
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

    if 'dhan_token' not in st.session_state:
        st.session_state.dhan_token = ''
    if 'dhan_renew_token' not in st.session_state:
        st.session_state.dhan_renew_token = ''
    if 'dhan_token_expiry' not in st.session_state:
        st.session_state.dhan_token_expiry = None

    if st.session_state.dhan_token:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #00ff8820, #00ff8808);
                    border: 1px solid #00ff8860;
                    border-radius: 8px; padding: 10px 14px;
                    margin-bottom: 12px; text-align: center;">
            <div style="color: #00ff88; font-size: 12px; font-weight: 700; letter-spacing: 1px;">
                🟢 DHAN API ACTIVE
            </div>
            <div style="color: #6a8aaa; font-size: 10px; margin-top: 4px;">
                Real-time data enabled
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #ffc70020, #ffc70008);
                    border: 1px solid #ffc70060;
                    border-radius: 8px; padding: 10px 14px;
                    margin-bottom: 12px; text-align: center;">
            <div style="color: #ffc700; font-size: 12px; font-weight: 700; letter-spacing: 1px;">
                🔴 YAHOO FINANCE
            </div>
            <div style="color: #6a8aaa; font-size: 10px; margin-top: 4px;">
                15-20 min delay
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("⚡ Dhan API (Optional)", expanded=False):
        st.markdown("""
        <div style="font-size:11px;color:#6a8aaa;margin-bottom:8px;line-height:1.5;">
            Paste your <b>Dhan Access Token</b> for real-time data.<br>
            <span style="color:#3a5a7a;">Get token from: Dhan Profile → Generate Access Token</span>
        </div>
        """, unsafe_allow_html=True)

        if 'dhan_token_loaded' not in st.session_state:
            st.markdown("""
            <script>
            (function() {
                var saved = localStorage.getItem('dhan_token');
                if (saved) {
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: saved}, '*');
                }
            })();
            </script>
            """, unsafe_allow_html=True)
            st.session_state.dhan_token_loaded = True

        dhan_token = st.text_input("Access Token", 
                                    value=st.session_state.dhan_token,
                                    type="password",
                                    placeholder="Paste your Dhan Access Token (eyJ...)",
                                    label_visibility="collapsed",
                                    key="dhan_token_input")
        st.session_state.dhan_token = dhan_token

        if dhan_token:
            st.markdown(f"""
            <script>
            localStorage.setItem('dhan_token', '{dhan_token}');
            </script>
            """, unsafe_allow_html=True)

        if dhan_token:
            st.success("✅ Dhan Token Active — Real-time data enabled!")
        else:
            st.info("ℹ️ Using Yahoo Finance (15-20 min delay)")

        st.markdown("""
        <div style="font-size:10px;color:#3a5a7a;margin-top:8px;line-height:1.5;border-top:1px solid #1e2d3d;padding-top:8px;">
            <b>How to get token:</b><br>
            1. Go to <a href="https://web.dhan.co" target="_blank" style="color:#00d4ff;">web.dhan.co</a> → Profile<br>
            2. Click "Generate Access Token / API Key"<br>
            3. Enter app name (e.g. "Super Scanner")<br>
            4. Click "Generate Access Token"<br>
            5. Copy the token (starts with eyJ...)<br>
            6. Paste above 👆<br><br>
            <b>Note:</b> Token valid for 24 hours. Regenerate daily.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    refresh = st.button("🚀 SCAN NOW", type="primary", use_container_width=True)

    if st.button("🗑️ Clear Cache", use_container_width=True):
        for key in ['scan_results', 'oi_list', 'sector_perf']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # ── DHAN DEBUG PANEL — asli error yahan dikhega ──
    if st.session_state.get('dhan_token'):
        with st.expander("🐛 Dhan Debug Info", expanded=False):
            sm_status = st.session_state.get('scrip_master_debug', 'Not loaded yet — scan karo pehle')
            st.markdown(f"**Scrip Master:** {sm_status}")
            dhan_errs = st.session_state.get('dhan_debug', {})
            if dhan_errs:
                st.markdown("**Per-stock Dhan fetch errors:**")
                for tkr, msg in dhan_errs.items():
                    st.markdown(f"- **{tkr}**: {msg}")
            else:
                st.caption("Koi error nahi (ya abhi tak scan nahi hua)")

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
# DHAN CONFIG  (FIX: hardcoded fake/placeholder IDs hata kar
# scrip-master se dynamic, sahi security_id lookup use kiya —
# jaisa F&O Pro Scanner (app.py) mein already kaam kar raha hai)
# ============================================================
DHAN_BASE_URL = "https://api.dhan.co/v2"

def get_dhan_headers(access_token):
    return {'Content-Type': 'application/json', 'access-token': access_token}

@st.cache_data(ttl=6*3600, show_spinner=False)
def load_dhan_scrip_master():
    """
    Dhan ka poora NSE equity scrip master CSV ek baar download karke
    symbol -> security_id ka dynamic, LIVE mapping banata hai (6 ghante
    cache hota hai).

    FIX: Pehle DHAN_SECURITY_IDS ek hardcoded dict tha jismein IDs asal
    mein Dhan se nahi aayi thi — kisi ne 123, 124, 125... karke sirf
    sequential placeholder numbers bhar diye the. Isse kai stocks
    (SIEMENS/CUMMINSIND, DMART/NAUKRI, AUBANK/APOLLOHOSP, etc.) ki IDs
    clash kar rahi thi, jisse Dhan API galat/fail response deta tha aur
    code silently Yahoo par fallback ho jaata tha — token daalne ke
    baad bhi. Ab yahan se HAMESHA sahi, official security_id milegi.

    DEBUG: Ab exception silently swallow nahi hoti — asli error
    st.session_state['scrip_master_debug'] mein store hoti hai taaki
    UI mein dikhaya ja sake (pehle bare 'except: return {}' tha jisse
    kabhi pata hi nahi chalta tha ki fail kyun hua).
    """
    try:
        url = "https://images.dhan.co/api-data/api-scrip-master.csv"
        df = pd.read_csv(url, low_memory=False)

        exch_col = 'SEM_EXM_EXCH_ID' if 'SEM_EXM_EXCH_ID' in df.columns else 'EXCH_ID'
        seg_col  = 'SEM_SEGMENT'     if 'SEM_SEGMENT'     in df.columns else 'SEGMENT'
        sym_col  = 'SEM_TRADING_SYMBOL' if 'SEM_TRADING_SYMBOL' in df.columns else 'SYMBOL_NAME'
        id_col   = 'SEM_SMST_SECURITY_ID' if 'SEM_SMST_SECURITY_ID' in df.columns else 'SECURITY_ID'

        eq = df[(df[exch_col].astype(str).str.upper() == 'NSE') &
                (df[seg_col].astype(str).str.upper() == 'E')]

        mapping = dict(zip(
            eq[sym_col].astype(str).str.upper().str.strip(),
            eq[id_col].astype(str).str.strip()
        ))
        st.session_state['scrip_master_debug'] = f"OK — {len(mapping)} symbols loaded. Columns used: {sym_col}/{id_col}"
        return mapping
    except Exception as e:
        st.session_state['scrip_master_debug'] = f"FAILED: {type(e).__name__}: {e}"
        return {}


def get_security_id(ticker):
    """Symbol -> Dhan security_id, live scrip master se (index symbols
    ke liye chhota manual override rakha hai kyunki wo scrip master
    mein equity segment ke saath nahi aate)."""
    INDEX_OVERRIDES = {
        "NIFTY": "13", "BANKNIFTY": "25", "FINNIFTY": "27", "MIDCPNIFTY": "442",
    }
    if ticker in INDEX_OVERRIDES:
        return INDEX_OVERRIDES[ticker]
    mapping = load_dhan_scrip_master()
    return mapping.get(ticker.upper())

# ============================================================
# DATA FETCHING FUNCTIONS
# ============================================================

def fetch_dhan_intraday(ticker, access_token, interval="5"):
    """Fetch 5m intraday data from Dhan API.

    DEBUG: Har fail-point par asli reason st.session_state['dhan_debug']
    mein us ticker ke against store hota hai — pehle bare 'except: return
    None' tha jisme pata hi nahi chalta tha ki security_id missing hai,
    ya API ne 401/403/429 diya, ya response format hi alag tha."""
    debug = st.session_state.setdefault('dhan_debug', {})
    try:
        security_id = get_security_id(ticker)
        if not security_id:
            debug[ticker] = "No security_id found for this symbol in scrip master"
            return None
        if not access_token:
            debug[ticker] = "No access_token provided"
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
            debug[ticker] = f"HTTP {resp.status_code} (security_id={security_id}): {resp.text[:200]}"
            return None
        data = resp.json()
        if not data or 'open' not in data:
            debug[ticker] = f"Bad response shape (security_id={security_id}): {str(data)[:200]}"
            return None
        df = pd.DataFrame({
            'Open': data['open'], 'High': data['high'], 'Low': data['low'],
            'Close': data['close'], 'Volume': data['volume'],
        })
        idx = pd.to_datetime(data['timestamp'], unit='s').tz_localize('UTC').tz_convert('Asia/Kolkata')
        df.index = idx
        if len(df) < 20:
            debug[ticker] = f"Only {len(df)} candles returned (need >=20), security_id={security_id}"
            return None
        debug.pop(ticker, None)
        return df
    except Exception as e:
        debug[ticker] = f"Exception: {type(e).__name__}: {str(e)[:200]}"
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
# NEWS & CORPORATE ACTION CHECK
# ============================================================

def get_corporate_actions(ticker):
    """Check for today's corporate actions, results, block deals, bulk deals"""
    try:
        if NSEPYTHON_AVAILABLE:
            try:
                ca_url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={ticker}"
                ca_data = nsefetch(ca_url)
                if ca_data and len(ca_data) > 0:
                    today_str = datetime.now(IST).strftime('%d-%b-%Y')
                    for item in ca_data[:5]:
                        desc = item.get('desc', '').lower()
                        if any(kw in desc for kw in ['result', 'earnings', 'dividend', 'bonus', 'split', 'rights', 'board meeting', 'agm']):
                            return {
                                'has_news': True,
                                'type': 'CORPORATE ACTION',
                                'description': item.get('desc', 'Corporate announcement'),
                                'date': item.get('an_dt', today_str)
                            }
            except:
                pass

            try:
                deals_url = "https://www.nseindia.com/api/snapshot-capital-market-info"
                deals_data = nsefetch(deals_url)
                if deals_data:
                    block_deals = deals_data.get('blockDeals', [])
                    for deal in block_deals:
                        if deal.get('symbol', '') == ticker:
                            return {
                                'has_news': True,
                                'type': 'BLOCK DEAL',
                                'description': f"Block deal: {deal.get('quantity', 'N/A')} shares @ ₹{deal.get('price', 'N/A')}",
                                'date': datetime.now(IST).strftime('%d-%b-%Y')
                            }

                    bulk_deals = deals_data.get('bulkDeals', [])
                    for deal in bulk_deals:
                        if deal.get('symbol', '') == ticker:
                            return {
                                'has_news': True,
                                'type': 'BULK DEAL',
                                'description': f"Bulk deal: {deal.get('quantity', 'N/A')} shares @ ₹{deal.get('price', 'N/A')}",
                                'date': datetime.now(IST).strftime('%d-%b-%Y')
                            }
            except:
                pass

        today = datetime.now(IST)
        month = today.month

        return {'has_news': False, 'type': None, 'description': None, 'date': None}

    except Exception as e:
        return {'has_news': False, 'type': None, 'description': None, 'date': None}

# ============================================================
# NSE OI SPURTS - FIXED WITH NSEPYTHON
# ============================================================

def get_oi_spurts_nsepython():
    """Fetch OI Spurts from NSE using nsepython library"""
    if not NSEPYTHON_AVAILABLE:
        return None, "nsepython not installed"

    try:
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

                        pchg = item.get('avgInOI',
                               item.get('pchangeinOpenInterest', 
                               item.get('pChange', 
                               item.get('pchangeinOi', 0)))) or 0

                        prev_oi = item.get('prevOI', 
                                  item.get('previousOI', 0)) or 0

                        latest_oi = item.get('latestOI', 
                                    item.get('openInterest', 0)) or 0

                        chg_oi = float(latest_oi) - float(prev_oi)

                        oi_data_quality = 'exact'
                        if float(pchg) == 0 and float(prev_oi) > 0 and float(latest_oi) > 0:
                            pchg = round(((float(latest_oi) - float(prev_oi)) / float(prev_oi)) * 100, 2)
                        elif float(prev_oi) <= 0:
                            oi_data_quality = 'estimated'

                        items.append({
                            'symbol': sym,
                            'oi_chg_pct': round(float(pchg), 2),
                            'prev_oi': int(prev_oi),
                            'latest_oi': int(latest_oi),
                            'chg_oi': int(chg_oi),
                            'oi_data_quality': oi_data_quality,
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
    """Fallback: Direct NSE requests — lightweight single-hit session"""
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/", "Connection": "keep-alive",
        }
        session.headers.update(headers)
        try:
            session.get("https://www.nseindia.com", timeout=10)
        except:
            pass

        endpoints = [
            "https://www.nseindia.com/api/live-analysis-oi-spurts-underlyings",
            "https://www.nseindia.com/api/live-analysis-oi-spurts",
        ]

        for endpoint in endpoints:
            response = session.get(endpoint, timeout=15)
            if response.status_code == 200:
                data = response.json()
                items = []
                raw = data if isinstance(data, list) else data.get('data', [])

                for item in raw[:50]:
                    sym = item.get('symbol', '')
                    if not sym:
                        continue
                    pchg = item.get('avgInOI', item.get('pchangeinOpenInterest', item.get('pChange', 0))) or 0
                    prev_oi = item.get('prevOI', 0) or 0
                    latest_oi = item.get('latestOI', 0) or 0
                    prev_oi_f, latest_oi_f = float(prev_oi), float(latest_oi)

                    chg_oi = latest_oi_f - prev_oi_f

                    if prev_oi_f > 0:
                        oi_chg_pct = round((latest_oi_f - prev_oi_f) / prev_oi_f * 100, 2)
                        data_quality = 'exact'
                    else:
                        oi_chg_pct = round(float(pchg), 2)
                        data_quality = 'estimated'

                    items.append({
                        'symbol': sym,
                        'oi_chg_pct': oi_chg_pct,
                        'prev_oi': int(prev_oi),
                        'latest_oi': int(latest_oi),
                        'chg_oi': int(chg_oi),
                        'oi_data_quality': data_quality,
                    })

                if items:
                    items.sort(key=lambda x: x['oi_chg_pct'], reverse=True)
                    return items[:30], "direct"

    except Exception as e:
        return None, f"direct error: {e}"

    return None, "direct failed"

def get_oi_spurts():
    """Unified OI Spurts fetcher"""
    result, source = get_oi_spurts_direct()
    if result:
        return result, source

    result, source = get_oi_spurts_nsepython()
    if result:
        return result, source

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
    try:
        df, source = get_data(ticker, access_token)
        if df is None or len(df) < 20:
            return None, "No data"

        today = pd.Timestamp.now().date()
        today_data = df[df.index.date == today]
        prev_data = df[df.index.date < today]

        if len(today_data) < 2:
            all_dates = sorted(pd.Series(df.index.date).unique())
            if len(all_dates) < 2:
                return None, "No previous data"
            today_data = df[df.index.date == all_dates[-1]]
            prev_data = df[df.index.date == all_dates[-2]]

        if len(prev_data) == 0 or len(today_data) == 0:
            return None, "Data error"

        market_open_dt = today_data.index[0].replace(hour=9, minute=15, second=0, microsecond=0)
        range_close_dt = market_open_dt + timedelta(minutes=orb_mins)
        breakout_cutoff_min = st.session_state.get("breakout_valid_cutoff", 15)
        valid_till_dt = range_close_dt + timedelta(minutes=breakout_cutoff_min)

        opening_range = today_data[today_data.index < range_close_dt]
        if opening_range.empty:
            return None, "ORB range still forming"

        breakout_window_data = today_data[(today_data.index >= range_close_dt) & (today_data.index <= valid_till_dt)]

        if breakout_window_data.empty:
            if today_data.index[-1] <= range_close_dt:
                return None, "ORB range still forming"
            return None, f"Breakout window expired ({breakout_cutoff_min} min cutoff crossed)"

        orb_high = opening_range['High'].max()
        orb_low = opening_range['Low'].min()

        current_candle = breakout_window_data.iloc[-1]
        current_price = float(current_candle['Close'])

        base_signal = None
        entry_price = None
        stop_loss = None
        orb_break_time = None
        orb_retraced = False

        if current_price > orb_high:
            base_signal = "BUY"
            entry_price = orb_high
            stop_loss = orb_low
        elif current_price < orb_low:
            base_signal = "SELL"
            entry_price = orb_low
            stop_loss = orb_high
        else:
            breakout_time = None
            breakdown_time = None
            last_breakout_price = None
            last_breakdown_price = None

            for idx, row in breakout_window_data.iterrows():
                c = float(row['Close'])
                if c > orb_high:
                    breakout_time = idx
                    last_breakout_price = c
                if c < orb_low:
                    breakdown_time = idx
                    last_breakdown_price = c

            if breakout_time is not None and breakdown_time is not None:
                if breakout_time > breakdown_time:
                    base_signal = "BUY"
                    entry_price = orb_high
                    stop_loss = orb_low
                    orb_break_time = breakout_time
                    orb_retraced = True
                else:
                    base_signal = "SELL"
                    entry_price = orb_low
                    stop_loss = orb_high
                    orb_break_time = breakdown_time
                    orb_retraced = True
            elif breakout_time is not None:
                base_signal = "BUY"
                entry_price = orb_high
                stop_loss = orb_low
                orb_break_time = breakout_time
                orb_retraced = True
            elif breakdown_time is not None:
                base_signal = "SELL"
                entry_price = orb_low
                stop_loss = orb_high
                orb_break_time = breakdown_time
                orb_retraced = True
            else:
                return None, "No ORB breakout"

        today_data = today_data[today_data.index <= valid_till_dt]

        prev_close = float(prev_data['Close'].iloc[-1])
        today_open = float(today_data['Open'].iloc[0])

        gap_pct = round(((today_open - prev_close) / prev_close) * 100, 2)
        if gap_filter and abs(gap_pct) >= 2.0:
            return None, f"Gap filter: {gap_pct}%"

        first_candle_close = float(today_data['Close'].iloc[0])
        first_candle_move = abs(first_candle_close - prev_close) / prev_close * 100
        if gap_filter and first_candle_move >= 2.0:
            return None, f"Spike filter: {first_candle_move:.1f}%"

        vwap = calculate_vwap(today_data)
        vwap_pass = False
        if vwap_filter and vwap:
            vwap_pass = (base_signal == "BUY" and current_price > vwap) or (base_signal == "SELL" and current_price < vwap)

        df_for_ema = df[df.index <= valid_till_dt]
        ema20 = float(ema(df_for_ema['Close'], 20).iloc[-1])
        ema_pass = False
        if ema_filter:
            ema_pass = (base_signal == "BUY" and current_price > ema20) or (base_signal == "SELL" and current_price < ema20)

        vol_ratio = None
        vol_pass = False
        if volume_filter:
            prev_avg_vol = float(prev_data['Volume'].mean())
            num_candles = len(today_data)
            if num_candles >= 2 and prev_avg_vol > 0:
                curr_vol = float(today_data['Volume'].sum())
                expected_vol = prev_avg_vol * num_candles
                vol_ratio = round(curr_vol / expected_vol, 1)
                vol_pass = vol_ratio > st.session_state.get("min_vol_ratio", 2.0)

        gap_pass = True

        filters_passed = 1
        total_filters = 1
        retrace_note = " [RETRACED]" if orb_retraced else ""
        filter_details = [("ORB Breakout", True, f"Price broke {base_signal} @ {orb_break_time.strftime('%H:%M') if orb_break_time else 'N/A'}{retrace_note}")]

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

        oi_pct = oi_info.get('oi_chg_pct', 0)

        if volume_filter and vol_ratio is not None:
            min_vol = st.session_state.get("min_vol_ratio", 2.0)
            if vol_ratio < min_vol:
                return None, f"Volume filter: {vol_ratio}x < {min_vol}x"

        if use_oi:
            min_oi = st.session_state.get("min_oi_change", 10)
            if abs(oi_pct) < min_oi:
                return None, f"OI filter: {abs(oi_pct)}% < {min_oi}%"

        oi_up = oi_pct > 0
        price_up = current_price > today_open

        if oi_up and price_up:
            oi_buildup = "🐂 LONG BUILDUP"
            oi_signal = "STRONG LONG" if oi_pct > st.session_state.get("min_oi_change", 10) else "LONG"
        elif oi_up and not price_up:
            oi_buildup = "🐻 SHORT BUILDUP"
            oi_signal = "STRONG SHORT" if oi_pct > st.session_state.get("min_oi_change", 10) else "SHORT"
        elif not oi_up and price_up:
            oi_buildup = "📤 SHORT COVERING"
            oi_signal = "SHORT SQUEEZE"
        else:
            oi_buildup = "📉 LONG UNWINDING"
            oi_signal = "WEAKNESS"

        oi_alignment = 0
        if base_signal == "BUY" and oi_signal in ["STRONG LONG", "LONG", "SHORT SQUEEZE"]:
            oi_alignment = 1
        elif base_signal == "SELL" and oi_signal in ["STRONG SHORT", "SHORT", "WEAKNESS"]:
            oi_alignment = 1
        elif base_signal == "BUY" and oi_signal in ["STRONG SHORT", "SHORT", "WEAKNESS"]:
            oi_alignment = -1
        elif base_signal == "SELL" and oi_signal in ["STRONG LONG", "LONG", "SHORT SQUEEZE"]:
            oi_alignment = -1

        news_info = get_corporate_actions(ticker)
        has_news = news_info.get('has_news', False)
        news_type = news_info.get('type', '')
        news_desc = news_info.get('description', '')

        if has_news:
            if accuracy >= 80 and oi_alignment >= 0:
                final_signal = f"🚨 NEWS TODAY — {base_signal} (CAUTION)"
            elif accuracy >= 60 and oi_alignment >= 0:
                final_signal = f"⚠️ NEWS TODAY — WEAK {base_signal}"
            else:
                final_signal = "🟡 WAIT — NEWS TODAY"
        else:
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
            "NEWS_ALERT": "🚨 " + news_type if has_news else "✅ No News",
            "NEWS_DESC": news_desc if has_news else "No corporate action today",
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
            "ORB_RETRACED": orb_retraced,
            "ORB_BREAK_TIME": str(orb_break_time.strftime("%H:%M")) if orb_break_time else "N/A",
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

        st.markdown("<div class='section-h'>📋 Filter Analysis</div>", unsafe_allow_html=True)
        filter_details = result.get('filter_details', [])
        for name, passed, detail in filter_details:
            if passed:
                st.markdown(f'<div class="filter-box-super filter-pass" style="color: #e8f0f8; background: linear-gradient(90deg, #00ff8815, #0d1a26); border: 1px solid #1e2d3d; border-left: 3px solid #00ff88; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;">✅ <b style="color: #00d4ff;">{name}</b> — <span style="color: #a0b8d0;">{detail}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="filter-box-super filter-fail" style="color: #e8f0f8; background: linear-gradient(90deg, #ff406015, #0d1a26); border: 1px solid #1e2d3d; border-left: 3px solid #ff4060; border-radius: 8px; padding: 12px; margin: 4px 0; font-size: 12px; line-height: 1.5;">❌ <b style="color: #ff4060;">{name}</b> — <span style="color: #a0b8d0;">{detail}</span></div>', unsafe_allow_html=True)

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

    if refresh or 'scan_results' not in st.session_state:
        if refresh:
            with st.spinner("🔍 Fetching NSE OI Spurts data..."):
                oi_list, oi_source = get_oi_spurts()
                st.session_state['oi_list'] = oi_list
                st.session_state['oi_source'] = oi_source

            if not oi_list:
                st.error("❌ Failed to fetch OI data from NSE. Try again or check connection.")
                st.info("💡 Tip: If nsepython is installed, it should handle NSE session automatically.")
            else:
                st.success(f"✅ OI Spurts loaded via {oi_source}! Top: {oi_list[0]['symbol']} (+{oi_list[0]['oi_chg_pct']:.2f}%)")

                _min_abs_oi = st.session_state.get('min_absolute_oi', 500)
                low_liq_count = sum(1 for x in oi_list[:20]
                                     if x.get('latest_oi', 0) < _min_abs_oi or x.get('prev_oi', 0) < _min_abs_oi)
                if low_liq_count:
                    st.warning(f"⚠️ {low_liq_count}/{len(oi_list[:20])} stocks LOW LIQUIDITY hain "
                               f"(absolute OI < {_min_abs_oi:,} contracts) — inka OI% bada dikh sakta hai, "
                               f"par size chhota liya jaye.")

                oi_preview = pd.DataFrame([{
                    'RANK': i+1,
                    'SYMBOL': x['symbol'],
                    'OI CHANGE %': (f"{'🟢' if x['oi_chg_pct'] >= 0 else '🔴'} {x['oi_chg_pct']:+.2f}%")
                                   + (" ~est" if x.get('oi_data_quality') == 'estimated' else ""),
                    'PREV OI': f"{x['prev_oi']:,}",
                    'LATEST OI': f"{x['latest_oi']:,}",
                    'CHG OI': f"{x['chg_oi']:+,}",
                    'LIQUIDITY': "⚠️ LOW" if (x.get('latest_oi', 0) < _min_abs_oi or x.get('prev_oi', 0) < _min_abs_oi) else "✅ OK",
                } for i, x in enumerate(oi_list[:20])])

                with st.expander("📊 NSE OI Spurts Raw Data", expanded=True):
                    st.dataframe(oi_preview, use_container_width=True, hide_index=True)
                    st.caption("**~est** = prev-day OI 0/missing tha, isliye NSE ka pchg fallback use hua "
                               "(real calculated % nahi). **⚠️ LOW** = absolute OI threshold se kam, illiquid contract.")

                if "QUICK" in scan_mode:
                    stock_list = [item['symbol'] for item in oi_list[:20]]
                    st.info(f"🏃 Quick Scan: Top {len(stock_list)} OI Spurt stocks")
                else:
                    universe = st.session_state.get('selected_universe', 'Nifty 50')

                    if universe == "F&O Pro Top 20":
                        stock_list = [item['symbol'] for item in oi_list[:20]]
                    elif universe == "Custom":
                        stock_list = st.session_state.get('custom_stock_list', ["RELIANCE", "TCS", "HDFCBANK"])
                    else:
                        stock_list = STOCK_UNIVERSES.get(universe, [])

                    st.info(f"🔍 Full Scan: {universe} — {len(stock_list)} stocks")

                results = []
                skipped = []
                progress = st.progress(0)
                status = st.empty()

                access_token = st.session_state.get('dhan_token', '')

                for i, ticker in enumerate(stock_list):
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

                st.session_state['scan_results'] = results
                st.session_state['skipped'] = skipped

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

                st.markdown("<div class='section-h'>📈 Scan Results</div>", unsafe_allow_html=True)
                f1, f2 = st.columns([1, 3])
                with f1:
                    signal_filter = st.selectbox("Filter", 
                        ["All Signals", "🚀 Strong Buy", "✅ Buy", "🔴 Strong Sell", "🔻 Sell", "⚠️ Weak", "🟡 Wait"],
                        label_visibility="collapsed")

                df_results = pd.DataFrame(results)

                if not df_results.empty:
                    desired_order = [
                        'STOCK', 'SIGNAL', 'NEWS_ALERT', 'NEWS_DESC', 'LTP', 'CHG %',
                        'OI SPURT %', 'VOL RATIO', 'OI BUILDUP', 'OI SIGNAL',
                        'FILTERS', 'OI ALIGN', 'ACCURACY', 'DATA_SOURCE'
                    ]
                    remaining = [c for c in df_results.columns if c not in desired_order]
                    df_results = df_results[desired_order + remaining]

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

                csv = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"super_scan_{now_ist().strftime('%d%m%Y_%H%M')}.csv",
                    mime='text/csv',
                )

                st.markdown("---")
                st.markdown("<div class='section-h'>🔍 Detailed Analysis</div>", unsafe_allow_html=True)

                priority = {"🚀 STRONG BUY": 0, "✅ BUY": 1, "🔴 STRONG SELL": 2, "🔻 SELL": 3, "⚠️ WEAK BUY": 4, "⚠️ WEAK SELL": 5, "🟡 WAIT": 6}
                sorted_results = sorted(results, key=lambda x: priority.get(x['SIGNAL'], 99))

                for result in sorted_results[:10]:
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
