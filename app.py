import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Swing Trading Scanner - Both Side ORB",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f9fafb;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e5e7eb;
    }
    .signal-long {
        background: #d1fae5;
        color: #065f46;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .signal-short {
        background: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .signal-neutral {
        background: #fef3c7;
        color: #92400e;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .checklist-item {
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        transition: all 0.2s;
    }
    .checklist-item:hover {
        background: #f3f4f6;
    }
    .progress-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 8px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px;
    }
    .long-box {
        border-left: 4px solid #10b981;
        background: #f0fdf4;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
    }
    .short-box {
        border-left: 4px solid #ef4444;
        background: #fef2f2;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============ TECHNICAL INDICATORS ============
def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_adx(data, period=14):
    high = data['High']
    low = data['Low']
    close = data['Close']

    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    return adx, plus_di, minus_di

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(data, period=14):
    high = data['High']
    low = data['Low']
    close = data['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_vwap(data):
    """Calculate VWAP"""
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
    return vwap

# ============ ORB DETECTION ============
def detect_orb(data, orb_minutes=15, valid_till_minutes=60):
    """
    Detect BOTH SIDE ORB:
    - Bullish: Price breaks above ORB High
    - Bearish: Price breaks below ORB Low

    Returns: dict with orb_high, orb_low, breakout_info
    """
    if len(data) < orb_minutes + 2:
        return None

    # ORB range candles
    orb_data = data.iloc[:orb_minutes]
    orb_high = orb_data['High'].max()
    orb_low = orb_data['Low'].min()
    orb_range = orb_high - orb_low
    orb_range_pct = (orb_range / orb_low) * 100

    # Post-ORB data (valid till specified minutes)
    valid_candles = min(valid_till_minutes, len(data) - orb_minutes)
    post_orb = data.iloc[orb_minutes:orb_minutes + valid_candles]

    result = {
        'orb_high': orb_high,
        'orb_low': orb_low,
        'orb_range': orb_range,
        'orb_range_pct': round(orb_range_pct, 2),
        'orb_minutes': orb_minutes,
        'valid_till_minutes': valid_till_minutes,
        'bullish_breakout': False,
        'bearish_breakdown': False,
        'breakout_price': None,
        'breakdown_price': None,
        'breakout_candle': None,
        'breakdown_candle': None,
        'breakout_volume_ratio': 0,
        'breakdown_volume_ratio': 0,
    }

    # Check for bullish breakout
    for i, (idx, row) in enumerate(post_orb.iterrows()):
        if row['Close'] > orb_high:
            result['bullish_breakout'] = True
            result['breakout_price'] = row['Close']
            result['breakout_candle'] = i
            # Volume ratio at breakout
            orb_avg_vol = orb_data['Volume'].mean()
            result['breakout_volume_ratio'] = round(row['Volume'] / orb_avg_vol, 2) if orb_avg_vol > 0 else 0
            break

    # Check for bearish breakdown
    for i, (idx, row) in enumerate(post_orb.iterrows()):
        if row['Close'] < orb_low:
            result['bearish_breakdown'] = True
            result['breakdown_price'] = row['Close']
            result['breakdown_candle'] = i
            # Volume ratio at breakdown
            orb_avg_vol = orb_data['Volume'].mean()
            result['breakdown_volume_ratio'] = round(row['Volume'] / orb_avg_vol, 2) if orb_avg_vol > 0 else 0
            break

    return result

# ============ SCANNER LOGIC ============
def analyze_stock(ticker, strategy="trend_pullback", orb_settings=None, filters=None):
    try:
        stock = yf.Ticker(ticker)

        # For intraday ORB, fetch 1d data with 5m interval
        if strategy == "intraday_orb":
            data = stock.history(period="1d", interval="5m")
        else:
            data = stock.history(period="6mo", interval="1d")

        if len(data) < 10:
            return None, "Insufficient data"

        # Calculate indicators
        data['EMA20'] = calculate_ema(data, 20)
        data['EMA50'] = calculate_ema(data, 50)
        data['EMA200'] = calculate_ema(data, 200)
        data['RSI'] = calculate_rsi(data, 14)
        data['ADX'] = calculate_adx(data, 14)[0]
        data['MACD'], data['MACD_Signal'], data['MACD_Hist'] = calculate_macd(data)
        data['ATR'] = calculate_atr(data, 14)
        data['Vol_Avg20'] = data['Volume'].rolling(20).mean()
        data['ATR_Pct'] = (data['ATR'] / data['Close']) * 100
        data['VWAP'] = calculate_vwap(data)

        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest

        result = {
            'ticker': ticker,
            'price': round(latest['Close'], 2),
            'open': round(data['Open'].iloc[0], 2) if len(data) > 0 else round(latest['Close'], 2),
            'high': round(latest['High'], 2),
            'low': round(latest['Low'], 2),
            'change_pct': round((latest['Close'] - data['Open'].iloc[0]) / data['Open'].iloc[0] * 100, 2) if len(data) > 0 else 0,
            'ema20': round(latest['EMA20'], 2),
            'ema50': round(latest['EMA50'], 2),
            'ema200': round(latest['EMA200'], 2),
            'rsi': round(latest['RSI'], 1),
            'adx': round(latest['ADX'], 1),
            'vwap': round(latest['VWAP'], 2),
            'volume': int(latest['Volume']),
            'vol_avg20': int(latest['Vol_Avg20']),
            'atr_pct': round(latest['ATR_Pct'], 2),
            'macd': round(latest['MACD'], 3),
            'macd_signal': round(latest['MACD_Signal'], 3),
            'data': data,
            'orb_info': None,
            'checks': [],
            'score': 0,
            'max_score': 0,
            'signal': 'NEUTRAL',
            'direction': None,  # 'LONG' or 'SHORT'
            'sl': None,
            'target1': None,
            'target2': None,
            'entry': None,
            'rr_ratio': None
        }

        # ========== INTRADAY ORB STRATEGY ==========
        if strategy == "intraday_orb":
            orb_min = orb_settings.get('orb_minutes', 6) if orb_settings else 6
            valid_till = orb_settings.get('valid_till', 15) if orb_settings else 15
            gap_spike_filter = filters.get('gap_spike_filter', True) if filters else True
            spike_threshold = filters.get('spike_threshold', 3.0) if filters else 3.0
            vwap_filter = filters.get('vwap_filter', False) if filters else False
            ema_filter = filters.get('ema_filter', False) if filters else False
            vol_filter = filters.get('vol_filter', 1.2) if filters else 1.2

            orb = detect_orb(data, orb_min, valid_till)
            if orb is None:
                return None, "ORB detection failed"

            result['orb_info'] = orb

            # Gap + Spike filter
            if gap_spike_filter and orb['orb_range_pct'] > spike_threshold:
                result['signal'] = 'FILTERED'
                result['checks'].append((f"ORB Range {orb['orb_range_pct']}% > {spike_threshold}% (Spike Filter)", False, f"Range: {orb['orb_low']:.0f} - {orb['orb_high']:.0f}"))
                return result, None

            # Check BOTH directions
            long_checks = []
            short_checks = []
            long_score = 0
            short_score = 0

            # ===== LONG SIDE CHECKS =====
            if orb['bullish_breakout']:
                # 1. Breakout above ORB High
                long_checks.append(("Close above ORB High", True, f"ORB High: {orb['orb_high']:.0f}, Close: {result['price']:.0f}"))
                long_score += 1

                # 2. Volume confirmation
                vol_ok = orb['breakout_volume_ratio'] >= vol_filter
                long_checks.append((f"Volume > {vol_filter}x ORB avg", vol_ok, f"Vol ratio: {orb['breakout_volume_ratio']:.1f}x"))
                if vol_ok: long_score += 1

                # 3. VWAP filter (if enabled)
                if vwap_filter:
                    above_vwap = result['price'] > result['vwap']
                    long_checks.append(("Price above VWAP", above_vwap, f"VWAP: {result['vwap']:.0f}"))
                    if above_vwap: long_score += 1
                else:
                    long_checks.append(("VWAP filter OFF", True, "Skipped"))
                    long_score += 1

                # 4. EMA filter (if enabled)
                if ema_filter:
                    above_ema = result['price'] > result['ema20']
                    long_checks.append(("Price above 20 EMA", above_ema, f"20 EMA: {result['ema20']:.0f}"))
                    if above_ema: long_score += 1
                else:
                    long_checks.append(("EMA filter OFF", True, "Skipped"))
                    long_score += 1

                # 5. Candle strength
                bullish_candle = latest['Close'] > latest['Open']
                long_checks.append(("Bullish candle", bullish_candle, f"Body: {abs(latest['Close']-latest['Open']):.0f}"))
                if bullish_candle: long_score += 1

                # 6. RSI not overbought
                rsi_ok = result['rsi'] < 75
                long_checks.append(("RSI not overbought (<75)", rsi_ok, f"RSI: {result['rsi']}"))
                if rsi_ok: long_score += 1

                # 7. ADX trend strength
                adx_ok = result['adx'] > 20 if not np.isnan(result['adx']) else True
                long_checks.append(("ADX > 20 (trend strength)", adx_ok, f"ADX: {result['adx']}"))
                if adx_ok: long_score += 1

            # ===== SHORT SIDE CHECKS =====
            if orb['bearish_breakdown']:
                # 1. Breakdown below ORB Low
                short_checks.append(("Close below ORB Low", True, f"ORB Low: {orb['orb_low']:.0f}, Close: {result['price']:.0f}"))
                short_score += 1

                # 2. Volume confirmation
                vol_ok = orb['breakdown_volume_ratio'] >= vol_filter
                short_checks.append((f"Volume > {vol_filter}x ORB avg", vol_ok, f"Vol ratio: {orb['breakdown_volume_ratio']:.1f}x"))
                if vol_ok: short_score += 1

                # 3. VWAP filter (if enabled)
                if vwap_filter:
                    below_vwap = result['price'] < result['vwap']
                    short_checks.append(("Price below VWAP", below_vwap, f"VWAP: {result['vwap']:.0f}"))
                    if below_vwap: short_score += 1
                else:
                    short_checks.append(("VWAP filter OFF", True, "Skipped"))
                    short_score += 1

                # 4. EMA filter (if enabled)
                if ema_filter:
                    below_ema = result['price'] < result['ema20']
                    short_checks.append(("Price below 20 EMA", below_ema, f"20 EMA: {result['ema20']:.0f}"))
                    if below_ema: short_score += 1
                else:
                    short_checks.append(("EMA filter OFF", True, "Skipped"))
                    short_score += 1

                # 5. Candle strength
                bearish_candle = latest['Close'] < latest['Open']
                short_checks.append(("Bearish candle", bearish_candle, f"Body: {abs(latest['Close']-latest['Open']):.0f}"))
                if bearish_candle: short_score += 1

                # 6. RSI not oversold
                rsi_ok = result['rsi'] > 25
                short_checks.append(("RSI not oversold (>25)", rsi_ok, f"RSI: {result['rsi']}"))
                if rsi_ok: short_score += 1

                # 7. ADX trend strength
                adx_ok = result['adx'] > 20 if not np.isnan(result['adx']) else True
                short_checks.append(("ADX > 20 (trend strength)", adx_ok, f"ADX: {result['adx']}"))
                if adx_ok: short_score += 1

            # ===== DECIDE WHICH SIDE IS STRONGER =====
            if orb['bullish_breakout'] and orb['bearish_breakdown']:
                # Both happened - pick the one with higher score, or the more recent one
                if long_score > short_score:
                    result['direction'] = 'LONG'
                    result['checks'] = long_checks
                    result['score'] = long_score
                    result['max_score'] = len(long_checks)
                    result['entry'] = orb['breakout_price']
                elif short_score > long_score:
                    result['direction'] = 'SHORT'
                    result['checks'] = short_checks
                    result['score'] = short_score
                    result['max_score'] = len(short_checks)
                    result['entry'] = orb['breakdown_price']
                else:
                    # Equal scores - check which happened first (more recent = stronger)
                    if orb['breakout_candle'] is not None and orb['breakdown_candle'] is not None:
                        if orb['breakout_candle'] > orb['breakdown_candle']:
                            result['direction'] = 'LONG'
                            result['checks'] = long_checks
                            result['score'] = long_score
                            result['max_score'] = len(long_checks)
                            result['entry'] = orb['breakout_price']
                        else:
                            result['direction'] = 'SHORT'
                            result['checks'] = short_checks
                            result['score'] = short_score
                            result['max_score'] = len(short_checks)
                            result['entry'] = orb['breakdown_price']
                    else:
                        result['direction'] = 'LONG'
                        result['checks'] = long_checks
                        result['score'] = long_score
                        result['max_score'] = len(long_checks)
                        result['entry'] = orb['breakout_price']

            elif orb['bullish_breakout']:
                result['direction'] = 'LONG'
                result['checks'] = long_checks
                result['score'] = long_score
                result['max_score'] = len(long_checks)
                result['entry'] = orb['breakout_price']

            elif orb['bearish_breakdown']:
                result['direction'] = 'SHORT'
                result['checks'] = short_checks
                result['score'] = short_score
                result['max_score'] = len(short_checks)
                result['entry'] = orb['breakdown_price']

            else:
                # No breakout either side
                result['signal'] = 'NO ORB'
                result['checks'].append(("No ORB breakout", False, f"ORB: {orb['orb_low']:.0f} - {orb['orb_high']:.0f}"))
                return result, None

            # Signal classification
            if result['score'] >= 5:
                result['signal'] = 'BUY' if result['direction'] == 'LONG' else 'SELL'
            elif result['score'] >= 3:
                result['signal'] = 'NEUTRAL'
            else:
                result['signal'] = 'WEAK'

            # Calculate SL and Targets
            orb_range = orb['orb_high'] - orb['orb_low']

            if result['direction'] == 'LONG':
                result['sl'] = round(max(orb['orb_low'], latest['Low'] * 0.995), 2)
                result['target1'] = round(result['entry'] + orb_range * 1.0, 2)
                result['target2'] = round(result['entry'] + orb_range * 1.5, 2)
            else:  # SHORT
                result['sl'] = round(min(orb['orb_high'], latest['High'] * 1.005), 2)
                result['target1'] = round(result['entry'] - orb_range * 1.0, 2)
                result['target2'] = round(result['entry'] - orb_range * 1.5, 2)

            # R:R calculation
            if result['direction'] == 'LONG':
                risk = result['entry'] - result['sl']
                reward = result['target1'] - result['entry']
            else:
                risk = result['sl'] - result['entry']
                reward = result['entry'] - result['target1']

            result['rr_ratio'] = round(reward / risk, 2) if risk > 0 else 0

            return result, None

        # ========== SWING STRATEGIES (existing) ==========
        checks = []
        score = 0

        if strategy == "trend_pullback":
            above_200 = latest['Close'] > latest['EMA200']
            checks.append(("Price above 200 EMA", above_200, f"₹{result['price']} vs EMA200 ₹{result['ema200']}"))
            if above_200: score += 1

            near_20 = abs(latest['Close'] - latest['EMA20']) / latest['EMA20'] * 100 < 3
            near_50 = abs(latest['Close'] - latest['EMA50']) / latest['EMA50'] * 100 < 4
            near_ema = near_20 or near_50
            checks.append(("Near 20/50 EMA", near_ema, f"20EMA: ₹{result['ema20']}, 50EMA: ₹{result['ema50']}"))
            if near_ema: score += 1

            rsi_ok = 40 < latest['RSI'] < 60
            checks.append(("RSI between 40-60", rsi_ok, f"RSI: {result['rsi']}"))
            if rsi_ok: score += 1

            vol_ok = latest['Volume'] > latest['Vol_Avg20'] * 1.2
            checks.append(("Volume > 1.2x avg", vol_ok, f"Vol: {result['volume']:,} vs Avg: {result['vol_avg20']:,}"))
            if vol_ok: score += 1

            adx_ok = latest['ADX'] > 25
            checks.append(("ADX > 25", adx_ok, f"ADX: {result['adx']}"))
            if adx_ok: score += 1

            atr_ok = latest['ATR_Pct'] < 5
            checks.append(("ATR < 5%", atr_ok, f"ATR: {result['atr_pct']}%"))
            if atr_ok: score += 1

            bullish = latest['Close'] > latest['Open']
            checks.append(("Bullish candle", bullish, f"Open: ₹{round(latest['Open'],2)}, Close: ₹{result['price']}"))
            if bullish: score += 1

            result['direction'] = 'LONG'
            result['sl'] = round(min(latest['Low'], latest['EMA50'] * 0.98), 2)
            result['target1'] = round(latest['Close'] + (latest['Close'] - result['sl']) * 2, 2)
            result['target2'] = round(latest['Close'] + (latest['Close'] - result['sl']) * 3, 2)
            result['entry'] = result['price']

        elif strategy == "breakout":
            resistance = data['High'].rolling(20).max().iloc[-2]

            above_200 = latest['Close'] > latest['EMA200']
            checks.append(("Price above 200 EMA", above_200, f"₹{result['price']} vs EMA200 ₹{result['ema200']}"))
            if above_200: score += 1

            breakout = latest['Close'] > resistance and prev['Close'] <= resistance
            checks.append(("Breakout above resistance", breakout, f"Resistance: ₹{round(resistance,2)}"))
            if breakout: score += 1

            vol_spike = latest['Volume'] > latest['Vol_Avg20'] * 2
            checks.append(("Volume > 2x average", vol_spike, f"Vol: {result['volume']:,}"))
            if vol_spike: score += 1

            rsi_ok = 50 < latest['RSI'] < 70
            checks.append(("RSI between 50-70", rsi_ok, f"RSI: {result['rsi']}"))
            if rsi_ok: score += 1

            adx_ok = latest['ADX'] > 25
            checks.append(("ADX > 25", adx_ok, f"ADX: {result['adx']}"))
            if adx_ok: score += 1

            next_res = data['High'].rolling(60).max().iloc[-1]
            room = (next_res - latest['Close']) / latest['Close'] * 100 > 5
            checks.append(("Room to next resistance", room, f"Next res ~₹{round(next_res,2)}"))
            if room: score += 1

            body_size = abs(latest['Close'] - latest['Open']) / latest['Open'] * 100
            strong_candle = body_size > 1
            checks.append(("Strong breakout candle", strong_candle, f"Body: {round(body_size,2)}%"))
            if strong_candle: score += 1

            result['direction'] = 'LONG'
            result['sl'] = round(max(latest['Low'] * 0.98, data['Low'].tail(5).min()), 2)
            result['target1'] = round(latest['Close'] * 1.05, 2)
            result['target2'] = round(latest['Close'] * 1.08, 2)
            result['entry'] = result['price']

        elif strategy == "momentum":
            rsi_cross = latest['RSI'] > 60 and prev['RSI'] <= 60
            checks.append(("RSI crossing 60", rsi_cross, f"RSI: {result['rsi']} (prev: {round(prev['RSI'],1)})"))
            if rsi_cross: score += 1

            macd_ok = latest['MACD'] > latest['MACD_Signal']
            checks.append(("MACD above signal", macd_ok, f"MACD: {result['macd']}, Signal: {result['macd_signal']}"))
            if macd_ok: score += 1

            above_20 = latest['Close'] > latest['EMA20']
            checks.append(("Price above 20 EMA", above_20, f"20EMA: ₹{result['ema20']}"))
            if above_20: score += 1

            vol_ok = latest['Volume'] > latest['Vol_Avg20'] * 1.5
            checks.append(("Volume > 1.5x avg", vol_ok, f"Vol: {result['volume']:,}"))
            if vol_ok: score += 1

            bullish = latest['Close'] > latest['Open']
            checks.append(("Bullish candle", bullish, ""))
            if bullish: score += 1

            adx_ok = latest['ADX'] > 20
            checks.append(("ADX > 20", adx_ok, f"ADX: {result['adx']}"))
            if adx_ok: score += 1

            macd_hist_rising = latest['MACD_Hist'] > prev['MACD_Hist']
            checks.append(("MACD histogram rising", macd_hist_rising, f"Hist: {round(latest['MACD_Hist'],3)}"))
            if macd_hist_rising: score += 1

            result['direction'] = 'LONG'
            result['sl'] = round(latest['EMA20'] * 0.97, 2)
            result['target1'] = round(latest['Close'] * 1.04, 2)
            result['target2'] = round(latest['Close'] * 1.07, 2)
            result['entry'] = result['price']

        result['checks'] = checks
        result['score'] = score
        result['max_score'] = len(checks)
        result['signal'] = 'BUY' if score >= 5 else 'NEUTRAL' if score >= 3 else 'AVOID'

        # R:R for swing
        risk = abs(result['entry'] - result['sl'])
        reward = abs(result['target1'] - result['entry'])
        result['rr_ratio'] = round(reward / risk, 2) if risk > 0 else 0

        return result, None

    except Exception as e:
        return None, str(e)

# ============ CHART FUNCTION ============
def create_chart(data, ticker, ema20=True, ema50=True, ema200=True, show_orb=None):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'{ticker} Price', 'Volume', 'RSI')
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price',
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    ), row=1, col=1)

    # EMAs
    if ema20 and 'EMA20' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], name='EMA20', line=dict(color='#3b82f6', width=1)), row=1, col=1)
    if ema50 and 'EMA50' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA50', line=dict(color='#f59e0b', width=1)), row=1, col=1)
    if ema200 and 'EMA200' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], name='EMA200', line=dict(color='#ef4444', width=1.5)), row=1, col=1)

    # VWAP
    if 'VWAP' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], name='VWAP', line=dict(color='#8b5cf6', width=1.5, dash='dot')), row=1, col=1)

    # ORB Lines
    if show_orb:
        fig.add_hline(y=show_orb['orb_high'], line_dash="dash", line_color="#10b981", line_width=2, 
                      annotation_text=f"ORB High: {show_orb['orb_high']:.0f}", annotation_position="right", row=1, col=1)
        fig.add_hline(y=show_orb['orb_low'], line_dash="dash", line_color="#ef4444", line_width=2,
                      annotation_text=f"ORB Low: {show_orb['orb_low']:.0f}", annotation_position="right", row=1, col=1)

        # ORB zone shading
        fig.add_hrect(y0=show_orb['orb_low'], y1=show_orb['orb_high'], 
                      fillcolor="gray", opacity=0.1, line_width=0, row=1, col=1)

    # Volume
    colors = ['#10b981' if data['Close'].iloc[i] >= data['Open'].iloc[i] else '#ef4444' for i in range(len(data))]
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color=colors, opacity=0.7), row=2, col=1)
    if 'Vol_Avg20' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['Vol_Avg20'], name='Vol Avg20', line=dict(color='#6b7280', width=1, dash='dash')), row=2, col=1)

    # RSI
    if 'RSI' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#8b5cf6', width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#9ca3af", line_width=1, row=3, col=1)

    fig.update_layout(
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        margin=dict(l=50, r=50, t=60, b=30)
    )

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

    return fig

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("<div class='main-header'>⚙️ Settings</div>", unsafe_allow_html=True)

    strategy = st.selectbox(
        "Select Strategy",
        ["intraday_orb", "trend_pullback", "breakout", "momentum"],
        format_func=lambda x: {
            "intraday_orb": "⚡ Intraday ORB (Both Side)",
            "trend_pullback": "📉 Trend Pullback (Swing)",
            "breakout": "🚀 Breakout (Swing)",
            "momentum": "🔥 Momentum (Swing)"
        }[x]
    )

    st.markdown("---")

    # ORB Settings (only for intraday)
    if strategy == "intraday_orb":
        st.markdown("**📊 ORB Settings**")
        orb_minutes = st.slider("ORB Range (candles)", 1, 12, 6, 
                                help="Kitne 5-min candles ka range lena hai. 6 = 30 min (9:15-9:45)")
        valid_till = st.slider("Valid Till (candles after ORB)", 5, 60, 15,
                               help="ORB ke baad kitne candles tak breakout valid hai")

        st.markdown("---")
        st.markdown("**🔧 Filters**")
        gap_spike_filter = st.checkbox("Gap + Spike Filter", value=True,
                                       help="Opening range zyada bada ho toh skip kare")
        spike_threshold = st.slider("Spike Threshold (%)", 1.0, 10.0, 3.0, 0.5,
                                    help="ORB range kitna % zyada ho toh reject kare")
        vwap_filter = st.checkbox("VWAP Filter", value=False,
                                  help="Price VWAP ke same side hona chahiye")
        ema_filter = st.checkbox("EMA Filter", value=False,
                                 help="Price 20 EMA ke same side hona chahiye")
        vol_filter = st.slider("Min Volume Ratio", 0.5, 3.0, 1.2, 0.1,
                               help="Breakout candle ka volume kitna x zyada hona chahiye ORB average se")

        orb_settings = {
            'orb_minutes': orb_minutes,
            'valid_till': valid_till
        }
        filters = {
            'gap_spike_filter': gap_spike_filter,
            'spike_threshold': spike_threshold,
            'vwap_filter': vwap_filter,
            'ema_filter': ema_filter,
            'vol_filter': vol_filter
        }
    else:
        orb_settings = None
        filters = None

    st.markdown("---")
    st.markdown("**📋 Watchlists**")

    watchlist_option = st.selectbox(
        "Choose Watchlist",
        ["Custom", "Nifty 50", "Nifty Next 50", "Midcap 100", "Bank Nifty", "IT Sector", "Intraday Favourites"]
    )

    default_tickers = {
        "Custom": "RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS",
        "Nifty 50": "RELIANCE.NS, TCS.NS, HDFCBANK.NS, ICICIBANK.NS, INFY.NS, HINDUNILVR.NS, SBIN.NS, BHARTIARTL.NS, ITC.NS, KOTAKBANK.NS, LT.NS, AXISBANK.NS, ASIANPAINT.NS, MARUTI.NS, TITAN.NS, BAJFINANCE.NS, WIPRO.NS, ULTRACEMCO.NS, SUNPHARMA.NS, NESTLEIND.NS",
        "Nifty Next 50": "ADANIENT.NS, ADANIPORTS.NS, APOLLOHOSP.NS, BAJAJFINSV.NS, BPCL.NS, BRITANNIA.NS, CIPLA.NS, COALINDIA.NS, DIVISLAB.NS, DRREDDY.NS, EICHERMOT.NS, GRASIM.NS, HCLTECH.NS, HDFCLIFE.NS, HEROMOTOCO.NS, HINDALCO.NS, INDUSINDBK.NS, JSWSTEEL.NS, M&M.NS, NTPC.NS",
        "Midcap 100": "ABB.NS, ALKEM.NS, AMBUJACEM.NS, AUROPHARMA.NS, BANDHANBNK.NS, BERGEPAINT.NS, BOSCHLTD.NS, CANBK.NS, CHOLAFIN.NS, COLPAL.NS, CONCOR.NS, CUMMINSIND.NS, DABUR.NS, DLF.NS, GAIL.NS, GODREJCP.NS, HAL.NS, HAVELLS.NS, HDFCAMC.NS, IDFCFIRSTB.NS",
        "Bank Nifty": "HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, KOTAKBANK.NS, AXISBANK.NS, INDUSINDBK.NS, BANKBARODA.NS, PNB.NS, CANBK.NS, IDFCFIRSTB.NS, FEDERALBNK.NS, UNIONBANK.NS",
        "IT Sector": "TCS.NS, INFY.NS, WIPRO.NS, HCLTECH.NS, TECHM.NS, MPHASIS.NS, COFORGE.NS, PERSISTENT.NS, LTTS.NS, MINDTREE.NS",
        "Intraday Favourites": "RELIANCE.NS, HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, TATAMOTORS.NS, INFY.NS, TCS.NS, BAJFINANCE.NS, ADANIENT.NS, BHARATFORG.NS, LTI.NS, M&M.NS"
    }

    tickers_input = st.text_area(
        "Stock Tickers (comma separated)",
        value=default_tickers[watchlist_option],
        height=100,
        help="Add .NS suffix for NSE stocks"
    )

    st.markdown("---")
    st.markdown("**💡 Tips:**")
    st.markdown("- Use `.NS` for NSE stocks")
    st.markdown("- Intraday ORB: 9:15-9:30 AM best time")
    st.markdown("- Both LONG and SHORT signals detected")
    st.markdown("- Gap/Spike filter ON rakho beginners ke liye")

# ============ MAIN CONTENT ============
st.markdown("<div class='main-header'>📈 Swing Trading Scanner</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Both Side ORB Detection — Long & Short signals with auto SL & Targets</div>", unsafe_allow_html=True)

# Strategy description
desc = {
    "intraday_orb": {
        "title": "⚡ Intraday ORB Strategy (Both Side)",
        "desc": "Opening Range Breakout — detects BOTH bullish breakout (above ORB high) AND bearish breakdown (below ORB low). Filters: Gap/Spike, VWAP, EMA, Volume.",
        "color": "#8b5cf6"
    },
    "trend_pullback": {
        "title": "📉 Trend Pullback Strategy",
        "desc": "Stocks in uptrend that have pulled back to 20/50 EMA. Best for swing trades.",
        "color": "#3b82f6"
    },
    "breakout": {
        "title": "🚀 Breakout Strategy", 
        "desc": "Stocks breaking above resistance with volume confirmation. High conviction swing trades.",
        "color": "#10b981"
    },
    "momentum": {
        "title": "🔥 Momentum Strategy",
        "desc": "RSI crossing 60 with MACD confirmation. Early entry into momentum moves.",
        "color": "#f59e0b"
    }
}

st.markdown(f"""
<div style="border-left: 4px solid {desc[strategy]['color']}; padding-left: 16px; margin-bottom: 24px;">
    <h3 style="margin: 0; color: {desc[strategy]['color']};">{desc[strategy]['title']}</h3>
    <p style="margin: 4px 0 0 0; color: #6b7280;">{desc[strategy]['desc']}</p>
</div>
""", unsafe_allow_html=True)

# Scan button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    scan_clicked = st.button("🔍 RUN SCANNER", type="primary", use_container_width=True)

if scan_clicked:
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if not tickers:
        st.error("Please enter at least one stock ticker!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []
        errors = []

        for i, ticker in enumerate(tickers):
            progress = (i + 1) / len(tickers)
            progress_bar.progress(progress)
            status_text.text(f"Scanning {ticker}... ({i+1}/{len(tickers)})")

            result, error = analyze_stock(ticker, strategy, orb_settings, filters)
            if result:
                results.append(result)
            else:
                errors.append(f"{ticker}: {error}")

        progress_bar.empty()
        status_text.empty()

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        # Summary metrics
        long_count = sum(1 for r in results if r.get('direction') == 'LONG' and r['score'] >= 5)
        short_count = sum(1 for r in results if r.get('direction') == 'SHORT' and r['score'] >= 5)
        neutral_count = sum(1 for r in results if r['signal'] == 'NEUTRAL')
        no_orb_count = sum(1 for r in results if r['signal'] == 'NO ORB')
        filtered_count = sum(1 for r in results if r['signal'] == 'FILTERED')

        st.markdown("---")
        st.markdown("### 📊 Scan Results Summary")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total", len(tickers))
        with m2:
            st.metric("🟢 LONG", long_count)
        with m3:
            st.metric("🔴 SHORT", short_count)
        with m4:
            st.metric("⚪ NEUTRAL", neutral_count)
        with m5:
            if strategy == "intraday_orb":
                st.metric("❌ No ORB", no_orb_count)

        if strategy == "intraday_orb" and filtered_count > 0:
            st.info(f"⚠️ {filtered_count} stocks filtered out due to Gap/Spike filter. Adjust filter threshold to see them.")

        # Results
        st.markdown("### 🎯 Ranked Results")

        for result in results:
            # Skip filtered/no-orb in main view (show in expander)
            if result['signal'] in ['NO ORB', 'FILTERED']:
                continue

            is_long = result.get('direction') == 'LONG'
            signal_class = "signal-long" if is_long else "signal-short" if result.get('direction') == 'SHORT' else "signal-neutral"
            signal_emoji = "🟢" if is_long else "🔴" if result.get('direction') == 'SHORT' else "⚪"
            signal_text = result['signal']
            box_class = "long-box" if is_long else "short-box" if result.get('direction') == 'SHORT' else ""

            orb_text = ""
            if result.get('orb_info'):
                orb = result['orb_info']
                orb_text = f" | ORB: {orb['orb_low']:.0f}-{orb['orb_high']:.0f} ({orb['orb_range_pct']}%)"

            with st.expander(f"{signal_emoji} {result['ticker']} — ₹{result['price']} | {signal_text} {signal_text} | Score: {result['score']}/{result['max_score']}{orb_text}", expanded=(result['score'] >= 5)):

                cols = st.columns([2, 3])

                with cols[0]:
                    direction_color = "#10b981" if is_long else "#ef4444"
                    direction_text = "LONG" if is_long else "SHORT" if result.get('direction') == 'SHORT' else "NEUTRAL"

                    st.markdown(f"""
                    <div style="background: #f9fafb; border-radius: 12px; padding: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-size: 1.5rem; font-weight: 700;">{result['ticker']}</span>
                            <span class="{signal_class}">{signal_text}</span>
                        </div>
                        <div style="font-size: 2rem; font-weight: 700; color: {direction_color};">₹{result['price']}</div>
                        <div style="margin-top: 8px; font-size: 0.9rem; color: #6b7280;">
                            Direction: <strong style="color: {direction_color};">{direction_text}</strong> | 
                            Score: <strong>{result['score']}/{result['max_score']}</strong>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {result['score']/result['max_score']*100}%; background: {direction_color}"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if result.get('orb_info'):
                        orb = result['orb_info']
                        st.markdown("**ORB Details:**")
                        st.markdown(f"- ORB High: ₹{orb['orb_high']:.0f}")
                        st.markdown(f"- ORB Low: ₹{orb['orb_low']:.0f}")
                        st.markdown(f"- ORB Range: {orb['orb_range_pct']:.1f}%")
                        if orb['bullish_breakout']:
                            st.markdown(f"- Breakout @ ₹{orb['breakout_price']:.0f} (Vol: {orb['breakout_volume_ratio']:.1f}x)")
                        if orb['bearish_breakdown']:
                            st.markdown(f"- Breakdown @ ₹{orb['breakdown_price']:.0f} (Vol: {orb['breakdown_volume_ratio']:.1f}x)")

                    st.markdown("**Trade Plan:**")
                    st.markdown(f"- Entry: ₹{result['entry']:.2f}")
                    st.markdown(f"- Stop Loss: ₹{result['sl']:.2f}")
                    st.markdown(f"- Target 1: ₹{result['target1']:.2f}")
                    st.markdown(f"- Target 2: ₹{result['target2']:.2f}")

                    if result.get('rr_ratio'):
                        rr_color = "#10b981" if result['rr_ratio'] >= 2 else "#f59e0b" if result['rr_ratio'] >= 1 else "#ef4444"
                        st.markdown(f"- **Risk:Reward = <span style='color: {rr_color};'>1:{result['rr_ratio']}</span>**", unsafe_allow_html=True)

                with cols[1]:
                    st.markdown("**Checklist:**")
                    for check_name, passed, detail in result['checks']:
                        icon = "✅" if passed else "❌"
                        color = "#10b981" if passed else "#ef4444"
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f3f4f6;">
                            <span style="color: {color}; font-size: 1.1rem;">{icon}</span>
                            <div>
                                <div style="font-weight: 500;">{check_name}</div>
                                <div style="font-size: 0.8rem; color: #9ca3af;">{detail}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Chart with ORB lines
                fig = create_chart(result['data'], result['ticker'], show_orb=result.get('orb_info'))
                st.plotly_chart(fig, use_container_width=True)

        # Show skipped stocks
        skipped = [r for r in results if r['signal'] in ['NO ORB', 'FILTERED']]
        if skipped:
            with st.expander(f"⚠️ Skipped Stocks ({len(skipped)})"):
                for r in skipped:
                    reason = "Gap/Spike filter" if r['signal'] == 'FILTERED' else "No ORB breakout"
                    st.text(f"{r['ticker']}: {reason}")

        if errors:
            with st.expander("⚠️ Errors (tickers not found)"):
                for err in errors:
                    st.text(err)

        # Export results
        if results:
            df_export = pd.DataFrame([
                {
                    'Ticker': r['ticker'],
                    'Price': r['price'],
                    'Signal': r['signal'],
                    'Direction': r.get('direction', 'N/A'),
                    'Score': f"{r['score']}/{r['max_score']}",
                    'Entry': r.get('entry', 'N/A'),
                    'Stop Loss': r.get('sl', 'N/A'),
                    'Target 1': r.get('target1', 'N/A'),
                    'Target 2': r.get('target2', 'N/A'),
                    'R:R': r.get('rr_ratio', 'N/A')
                }
                for r in results if r['signal'] not in ['NO ORB']
            ])

            csv = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name=f"orb_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

else:
    # Show instructions
    st.markdown("---")

    if strategy == "intraday_orb":
        st.markdown("### 🚀 How to Use Intraday ORB Scanner")

        steps = [
            ("1️⃣ Set ORB Range", "6 candles = 30 min (9:15-9:45). Adjust based on volatility."),
            ("2️⃣ Configure Filters", "Gap/Spike filter ON rakho for safety. VWAP/EMA optional."),
            ("3️⃣ Pick Watchlist", "Intraday Favourites ya apni list. .NS lagana mat bhoolna."),
            ("4️⃣ Run at 9:30-9:45 AM", "Best time — ORB range ban chuka hota hai."),
            ("5️⃣ Review Signals", "🟢 LONG = Buy above ORB High | 🔴 SHORT = Sell below ORB Low"),
            ("6️⃣ Verify on Chart", "ORB lines, volume spike, aur candle strength confirm karo."),
            ("7️⃣ Execute with SL", "Auto-calculated SL aur Targets ke saath trade karo.")
        ]

        for title, desc in steps:
            st.markdown(f"""
            <div style="background: #f9fafb; border-radius: 10px; padding: 14px 18px; margin: 8px 0; border-left: 3px solid #8b5cf6;">
                <div style="font-weight: 600; color: #1f2937;">{title}</div>
                <div style="color: #6b7280; font-size: 0.9rem; margin-top: 2px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📋 ORB Rules")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="long-box">
                <h4 style="margin: 0; color: #065f46;">🟢 LONG Setup</h4>
                <ul style="margin: 8px 0; padding-left: 18px; color: #374151;">
                    <li>Price closes above ORB High</li>
                    <li>Volume > 1.2x ORB average</li>
                    <li>Bullish candle preferred</li>
                    <li>RSI not overbought (&lt;75)</li>
                    <li>SL: ORB Low ya recent low</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="short-box">
                <h4 style="margin: 0; color: #991b1b;">🔴 SHORT Setup</h4>
                <ul style="margin: 8px 0; padding-left: 18px; color: #374151;">
                    <li>Price closes below ORB Low</li>
                    <li>Volume > 1.2x ORB average</li>
                    <li>Bearish candle preferred</li>
                    <li>RSI not oversold (&gt;25)</li>
                    <li>SL: ORB High ya recent high</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("### 🚀 How to Use Swing Scanner")

        steps = [
            ("1️⃣ Select Strategy", "Trend Pullback, Breakout, ya Momentum — apne style ke hisaab se."),
            ("2️⃣ Pick Watchlist", "Nifty 50, Bank Nifty, ya custom stocks."),
            ("3️⃣ Run Scanner", "Click RUN — EMA, RSI, ADX, Volume sab analyze hoga."),
            ("4️⃣ Review Results", "Score 5+ wale stocks best hain."),
            ("5️⃣ Chart Verify", "Candlestick pattern aur volume confirm karo."),
            ("6️⃣ Execute Trade", "Auto SL aur Targets ke saath entry karo.")
        ]

        for title, desc in steps:
            st.markdown(f"""
            <div style="background: #f9fafb; border-radius: 10px; padding: 14px 18px; margin: 8px 0; border-left: 3px solid #3b82f6;">
                <div style="font-weight: 600; color: #1f2937;">{title}</div>
                <div style="color: #6b7280; font-size: 0.9rem; margin-top: 2px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>Swing Trading Scanner v2.0 | Both Side ORB | Built with Streamlit + yfinance</div>", unsafe_allow_html=True)
