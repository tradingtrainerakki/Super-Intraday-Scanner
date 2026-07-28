import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import requests
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Super Scanner Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# THEME SWITCHER (CSS)
# ============================================================
def apply_theme(theme):
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: #fafafa; }
        .stSidebar { background-color: #161b22; }
        div[data-testid="stMetricValue"] { color: #00ff88 !important; }
        div[data-testid="stMetricDelta"] { color: #ff6b6b !important; }
        .stDataFrame { background-color: #161b22; }
        .stButton>button { background-color: #238636; color: white; border-radius: 8px; }
        .stButton>button:hover { background-color: #2ea043; }
        h1, h2, h3 { color: #58a6ff; }
        .stAlert { background-color: #21262d; border-left: 4px solid #58a6ff; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background-color: #ffffff; color: #1f2937; }
        .stSidebar { background-color: #f3f4f6; }
        div[data-testid="stMetricValue"] { color: #059669 !important; }
        div[data-testid="stMetricDelta"] { color: #dc2626 !important; }
        .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; }
        .stButton>button:hover { background-color: #1d4ed8; }
        h1, h2, h3 { color: #1e40af; }
        </style>
        """, unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = pd.DataFrame()
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚙️ Scanner Settings")

    # Theme Switcher
    st.session_state.theme = st.radio("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state.theme == "Dark" else 1)
    apply_theme(st.session_state.theme)

    st.divider()

    # Market Selection
    market = st.selectbox("📍 Market", ["NSE (India)", "US Stocks", "Crypto"])

    # Timeframe
    timeframe = st.selectbox("⏱️ Timeframe", ["1m", "5m", "15m", "30m", "1h", "1d"], index=2)

    # ORB Settings
    st.subheader("📐 ORB Settings")
    orb_minutes = st.slider("ORB Minutes (Opening Range)", 5, 60, 15)
    orb_breakout_pct = st.slider("Breakout %", 0.1, 5.0, 1.0, 0.1)

    # Volume & OI Filters
    st.subheader("📊 Volume & OI Filters")
    min_volume = st.slider("Min Volume (x Avg)", 1.0, 10.0, 2.0, 0.5)
    min_oi_change = st.slider("Min OI Change %", 0, 50, 10)

    # EMA/VWAP Filters
    st.subheader("📈 EMA / VWAP Filters")
    use_vwap = st.checkbox("Above VWAP", value=True)
    use_ema20 = st.checkbox("Above EMA 20", value=True)
    use_ema50 = st.checkbox("Above EMA 50", value=False)

    # Strict Mode
    st.subheader("🔒 Strict Filters")
    strict_mode = st.checkbox("Strict Mode (All conditions)", value=False)

    st.divider()

    # Scan Button
    scan_btn = st.button("🚀 RUN SCAN", use_container_width=True, type="primary")

    st.divider()

    # Watchlist Editor
    st.subheader("📋 Watchlist")
    watchlist_input = st.text_area("Stocks (comma separated)", ", ".join(st.session_state.watchlist), height=100)
    if st.button("💾 Save Watchlist"):
        st.session_state.watchlist = [s.strip().upper() for s in watchlist_input.split(",") if s.strip()]
        st.success("Watchlist saved!")

# ============================================================
# MAIN CONTENT
# ============================================================
st.title("📊 Super Scanner Pro")
st.caption("Real-time Stock Scanner with ORB, OI, VWAP & EMA Filters")

# News Warning Banner
st.warning("⚠️ **Market News Alert**: Always check latest news before taking any position. Scanner signals are for analysis only, not financial advice.")

# Helper Functions
@st.cache_data(ttl=300)
def fetch_data(ticker, period="5d", interval="15m"):
    """Fetch OHLCV data from yfinance"""
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if data.empty:
            return None
        # Flatten multi-index columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        return None

def calculate_vwap(data):
    """Calculate VWAP"""
    df = data.copy()
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['Vol_TP'] = df['TP'] * df['Volume']
    df['Cum_Vol_TP'] = df['Vol_TP'].cumsum()
    df['Cum_Vol'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cum_Vol_TP'] / df['Cum_Vol']
    return df

def calculate_ema(data, period):
    """Calculate EMA"""
    return data['Close'].ewm(span=period, adjust=False).mean()

def orb_scanner(data, orb_minutes=15, breakout_pct=1.0):
    """Opening Range Breakout Scanner"""
    if data is None or len(data) < orb_minutes + 5:
        return None, None, None

    # Get opening range (first N candles)
    opening_range = data.iloc[:orb_minutes]
    orb_high = opening_range['High'].max()
    orb_low = opening_range['Low'].min()

    # Current price (last close)
    current = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current

    # Breakout detection
    breakout_up = current > orb_high * (1 + breakout_pct/100)
    breakout_down = current < orb_low * (1 - breakout_pct/100)

    return orb_high, orb_low, {
        'current': current,
        'prev_close': prev_close,
        'breakout_up': breakout_up,
        'breakout_down': breakout_down,
        'orb_range': orb_high - orb_low
    }

def volume_analysis(data):
    """Volume analysis"""
    if data is None or len(data) < 20:
        return None
    avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
    current_volume = data['Volume'].iloc[-1]
    vol_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    return {
        'avg_volume': avg_volume,
        'current_volume': current_volume,
        'vol_ratio': vol_ratio
    }

def oi_analysis(ticker):
    """Simulated OI analysis (placeholder - real OI needs broker API)"""
    # In real app, this would fetch from NSE/Broker API
    # Returning simulated data for demo
    np.random.seed(hash(ticker) % 10000)
    oi_change = np.random.uniform(-30, 40)
    return {
        'oi_change_pct': oi_change,
        'oi_trend': 'Rising' if oi_change > 10 else 'Falling' if oi_change < -10 else 'Stable'
    }

def scan_stock(ticker, orb_min, orb_pct, min_vol, min_oi, use_vwap, use_ema20, use_ema50, strict):
    """Run full scan on a single stock"""
    # Map timeframe to yfinance params
    tf_map = {"1m": ("5d", "1m"), "5m": ("5d", "5m"), "15m": ("5d", "15m"), 
              "30m": ("1mo", "30m"), "1h": ("1mo", "1h"), "1d": ("6mo", "1d")}
    period, interval = tf_map.get(timeframe, ("5d", "15m"))

    data = fetch_data(ticker, period=period, interval=interval)
    if data is None or len(data) < 20:
        return None

    # Calculate indicators
    data = calculate_vwap(data)
    data['EMA20'] = calculate_ema(data, 20)
    data['EMA50'] = calculate_ema(data, 50)

    # ORB Scan
    orb_high, orb_low, orb_info = orb_scanner(data, orb_min, orb_pct)
    if orb_info is None:
        return None

    # Volume
    vol_info = volume_analysis(data)
    if vol_info is None:
        return None

    # OI
    oi_info = oi_analysis(ticker)

    current = orb_info['current']
    vwap = data['VWAP'].iloc[-1]
    ema20 = data['EMA20'].iloc[-1]
    ema50 = data['EMA50'].iloc[-1]

    # Check conditions
    conditions = {
        'volume_ok': vol_info['vol_ratio'] >= min_vol,
        'oi_ok': abs(oi_info['oi_change_pct']) >= min_oi,
        'vwap_ok': current > vwap if use_vwap else True,
        'ema20_ok': current > ema20 if use_ema20 else True,
        'ema50_ok': current > ema50 if use_ema50 else True,
        'breakout_up': orb_info['breakout_up'],
        'breakout_down': orb_info['breakout_down']
    }

    if strict:
        # Strict: all enabled conditions must pass + breakout
        signal = all([
            conditions['volume_ok'],
            conditions['oi_ok'] if min_oi > 0 else True,
            conditions['vwap_ok'],
            conditions['ema20_ok'],
            conditions['ema50_ok'],
            (conditions['breakout_up'] or conditions['breakout_down'])
        ])
    else:
        # Normal: at least breakout + volume
        signal = conditions['volume_ok'] and (conditions['breakout_up'] or conditions['breakout_down'])

    if not signal:
        return None

    return {
        'Ticker': ticker,
        'Price': round(current, 2),
        'Change %': round((current - orb_info['prev_close']) / orb_info['prev_close'] * 100, 2),
        'Signal': 'BUY' if conditions['breakout_up'] else 'SELL' if conditions['breakout_down'] else 'HOLD',
        'ORB High': round(orb_high, 2),
        'ORB Low': round(orb_low, 2),
        'VWAP': round(vwap, 2),
        'EMA20': round(ema20, 2),
        'EMA50': round(ema50, 2),
        'Vol Ratio': round(vol_info['vol_ratio'], 2),
        'OI Change %': round(oi_info['oi_change_pct'], 2),
        'OI Trend': oi_info['oi_trend'],
        'Volume': int(vol_info['current_volume']),
        'Above VWAP': 'Yes' if conditions['vwap_ok'] else 'No',
        'Above EMA20': 'Yes' if conditions['ema20_ok'] else 'No',
        'Above EMA50': 'Yes' if conditions['ema50_ok'] else 'No'
    }

# ============================================================
# SCAN EXECUTION
# ============================================================
if scan_btn:
    with st.spinner("🔍 Scanning stocks... Please wait"):
        watchlist = st.session_state.watchlist
        results = []
        progress_bar = st.progress(0)

        for i, ticker in enumerate(watchlist):
            result = scan_stock(
                ticker, orb_minutes, orb_breakout_pct, 
                min_volume, min_oi_change,
                use_vwap, use_ema20, use_ema50, strict_mode
            )
            if result:
                results.append(result)
            progress_bar.progress((i + 1) / len(watchlist))
            time.sleep(0.1)  # Rate limit

        progress_bar.empty()

        if results:
            df = pd.DataFrame(results)
            st.session_state.scan_results = df
            st.success(f"✅ Found {len(results)} signals!")
        else:
            st.session_state.scan_results = pd.DataFrame()
            st.info("ℹ️ No signals found with current filters. Try relaxing filters.")

# ============================================================
# DISPLAY RESULTS
# ============================================================
if not st.session_state.scan_results.empty:
    df = st.session_state.scan_results

    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    buy_count = len(df[df['Signal'] == 'BUY'])
    sell_count = len(df[df['Signal'] == 'SELL'])

    with col1:
        st.metric("Total Signals", len(df))
    with col2:
        st.metric("Buy Signals", buy_count, delta=f"+{buy_count}")
    with col3:
        st.metric("Sell Signals", sell_count, delta=f"-{sell_count}", delta_color="inverse")
    with col4:
        avg_change = df['Change %'].mean()
        st.metric("Avg Change %", f"{avg_change:.2f}%")

    st.divider()

    # Color-coded table
    def color_signal(val):
        if val == 'BUY':
            return 'background-color: #064e3b; color: #34d399; font-weight: bold'
        elif val == 'SELL':
            return 'background-color: #450a0a; color: #f87171; font-weight: bold'
        return ''

    def color_change(val):
        if val > 0:
            return 'color: #34d399'
        elif val < 0:
            return 'color: #f87171'
        return ''

    styled_df = df.style.applymap(color_signal, subset=['Signal'])                         .applymap(color_change, subset=['Change %'])                         .format({'Price': '{:.2f}', 'ORB High': '{:.2f}', 'ORB Low': '{:.2f}', 
                                  'VWAP': '{:.2f}', 'EMA20': '{:.2f}', 'EMA50': '{:.2f}'})

    st.subheader("📋 Scan Results")
    st.dataframe(styled_df, use_container_width=True, height=400)

    # Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "scanner_results.csv", "text/csv", use_container_width=True)

    # Individual Stock Detail
    st.divider()
    st.subheader("🔍 Stock Detail")
    selected = st.selectbox("Select stock for detail view", df['Ticker'].tolist())

    if selected:
        row = df[df['Ticker'] == selected].iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Price", f"₹{row['Price']}")
        c2.metric("Signal", row['Signal'])
        c3.metric("VWAP", f"₹{row['VWAP']}")
        c4.metric("Vol Ratio", f"{row['Vol Ratio']}x")
        c5.metric("OI Change", f"{row['OI Change %']}%")

        # Mini chart
        tf_map = {"1m": ("5d", "1m"), "5m": ("5d", "5m"), "15m": ("5d", "15m"), 
                  "30m": ("1mo", "30m"), "1h": ("1mo", "1h"), "1d": ("6mo", "1d")}
        period, interval = tf_map.get(timeframe, ("5d", "15m"))
        chart_data = fetch_data(selected, period=period, interval=interval)
        if chart_data is not None:
            chart_data = calculate_vwap(chart_data)
            chart_data['EMA20'] = calculate_ema(chart_data, 20)
            st.line_chart(chart_data[['Close', 'VWAP', 'EMA20']].rename(columns={
                'Close': 'Price', 'VWAP': 'VWAP', 'EMA20': 'EMA 20'
            }))

else:
    # Empty state
    st.info("👆 Click **RUN SCAN** in the sidebar to start scanning!")

    # Demo data preview
    with st.expander("📝 How to use this scanner"):
        st.markdown("""
        ### Steps:
        1. **Set your watchlist** in the sidebar (default: NSE stocks)
        2. **Choose timeframe** — 15m recommended for intraday
        3. **Adjust ORB settings** — Opening Range Breakout minutes & %
        4. **Set Volume & OI filters** — Minimum volume ratio & OI change
        5. **Enable EMA/VWAP filters** — Price above VWAP/EMA confirmation
        6. **Toggle Strict Mode** — All conditions must pass
        7. **Click RUN SCAN** — Results will appear here

        ### Features:
        - ✅ **ORB Scanner** — Detects opening range breakouts
        - ✅ **Volume Filter** — Only stocks with volume > Nx average
        - ✅ **OI Analysis** — Open Interest change detection
        - ✅ **VWAP/EMA** — Trend confirmation filters
        - ✅ **Theme Switcher** — Dark/Light mode
        - ✅ **Export CSV** — Download results
        """)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("⚠️ **Disclaimer**: This scanner is for educational purposes only. Not financial advice. Always do your own research before trading.")
st.caption("Made with ❤️ using Streamlit | Data: Yahoo Finance")
