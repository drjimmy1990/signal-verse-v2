# fawda_scanner_ws_fixed.py
# ------------------------------------------------------------
# Real-time multi-timeframe Binance Futures scanner (USDT-M)
# using WebSockets only (no REST), candle-close processing.
# Includes corrected Nakel + Hadena logic and full indexing adjustments.
# ------------------------------------------------------------

import json
import time
import traceback
from datetime import datetime
from threading import Thread, Lock

import numpy as np
import pandas as pd
import websocket
from scipy.signal import argrelextrema
from tabulate import tabulate

# =========================
# 0) CONFIG
# =========================

# Sample list with 3 coins for demonstration
SYMBOLS =  ['btcusdt', 'ethusdt', 'bchusdt', 'xrpusdt', 'ltcusdt', 'trxusdt', 'etcusdt', 'linkusdt', 'xlmusdt', 'adausdt', 'xmrusdt', 'dashusdt', 'zecusdt', 'xtzusdt', 'bnbusdt', 'atomusdt', 'ontusdt', 'iotausdt', 'batusdt', 'vetusdt', 'neousdt', 'qtumusdt', 'iostusdt', 'thetausdt', 'algousdt', 'zilusdt', 'kncusdt', 'zrxusdt', 'compusdt', 'dogeusdt', 'sxpusdt', 'kavausdt', 'bandusdt', 'rlcusdt', 'mkrusdt', 'snxusdt', 'dotusdt', 'yfiusdt', 'crvusdt', 'trbusdt', 'runeusdt', 'sushiusdt', 'egldusdt', 'solusdt', 'icxusdt', 'storjusdt', 'uniusdt', 'avaxusdt', 'enjusdt', 'flmusdt', 'ksmusdt', 'nearusdt', 'aaveusdt', 'filusdt', 'rsrusdt', 'lrcusdt', 'belusdt', 'axsusdt', 'alphausdt', 'zenusdt', 'sklusdt', 'grtusdt', '1inchusdt', 'chzusdt', 'sandusdt', 'ankrusdt', 'rvnusdt', 'sfpusdt', 'cotiusdt', 'chrusdt', 'manausdt', 'aliceusdt', 'hbarusdt', 'oneusdt', 'dentusdt', 'celrusdt', 'hotusdt', 'mtlusdt', 'ognusdt', 'nknusdt', '1000shibusdt', 'bakeusdt', 'gtcusdt', 'btcdomusdt', 'iotxusdt', 'c98usdt', 'maskusdt', 'atausdt', 'dydxusdt', '1000xecusdt', 'galausdt', 'celousdt', 'arusdt', 'arpausdt', 'ctsiusdt', 'lptusdt', 'ensusdt', 'peopleusdt', 'roseusdt', 'duskusdt', 'flowusdt', 'imxusdt', 'api3usdt', 'gmtusdt', 'apeusdt', 'woousdt', 'jasmyusdt', 'opusdt', 'injusdt', 'stgusdt', 'spellusdt', '1000luncusdt', 'luna2usdt', 'ldousdt', 'icpusdt', 'aptusdt', 'qntusdt', 'fetusdt', 'fxsusdt', 'hookusdt', 'magicusdt', 'tusdt', 'highusdt', 'minausdt', 'astrusdt', 'phbusdt', 'gmxusdt', 'cfxusdt', 'stxusdt', 'achusdt', 'ssvusdt', 'ckbusdt', 'perpusdt', 'truusdt', 'lqtyusdt', 'usdcusdt', 'idusdt', 'arbusdt', 'joeusdt', 'tlmusdt', 'leverusdt', 'rdntusdt', 'hftusdt', 'xvsusdt', 'blurusdt', 'eduusdt', 'suiusdt', '1000pepeusdt', '1000flokiusdt', 'umausdt', 'nmrusdt', 'mavusdt', 'xvgusdt', 'wldusdt', 'pendleusdt', 'arkmusdt', 'agldusdt', 'yggusdt', 'dodoxusdt', 'bntusdt', 'oxtusdt', 'seiusdt', 'cyberusdt', 'hifiusdt', 'arkusdt', 'bicousdt', 'bigtimeusdt', 'waxpusdt', 'bsvusdt', 'rifusdt', 'polyxusdt', 'gasusdt', 'powrusdt', 'tiausdt', 'cakeusdt', 'memeusdt', 'twtusdt', 'tokenusdt', 'ordiusdt', 'steemusdt', 'ilvusdt', 'ntrnusdt', 'kasusdt', 'beamxusdt', '1000bonkusdt', 'pythusdt', 'superusdt', 'ustcusdt', 'ongusdt', 'ethwusdt', 'jtousdt', '1000satsusdt', 'auctionusdt', '1000ratsusdt', 'aceusdt', 'movrusdt', 'nfpusdt', 'aiusdt', 'xaiusdt', 'wifusdt', 'mantausdt', 'ondousdt', 'lskusdt', 'altusdt', 'jupusdt', 'zetausdt', 'roninusdt', 'dymusdt', 'omusdt', 'pixelusdt', 'strkusdt', 'glmusdt', 'portalusdt', 'tonusdt', 'axlusdt', 'myrousdt', 'metisusdt', 'aevousdt', 'vanryusdt', 'bomeusdt', 'ethfiusdt', 'enausdt', 'wusdt', 'tnsrusdt', 'sagausdt', 'taousdt', 'omniusdt', 'rezusdt', 'bbusdt', 'notusdt', 'turbousdt', 'iousdt', 'zkusdt', 'mewusdt', 'listausdt', 'zrousdt', 'renderusdt', 'bananausdt', 'rareusdt', 'gusdt', 'synusdt', 'sysusdt', 'voxelusdt', 'brettusdt', 'popcatusdt', 'sunusdt', 'dogsusdt', 'mboxusdt', 'chessusdt', 'fluxusdt', 'bswusdt', 'quickusdt', 'neiroethusdt', 'rplusdt', 'polusdt', 'uxlinkusdt', '1mbabydogeusdt', 'neirousdt', 'kdausdt', 'fidausdt', 'fiousdt', 'catiusdt', 'ghstusdt', 'hmstrusdt', 'reiusdt', 'cosusdt', 'eigenusdt', 'diausdt', '1000catusdt', 'scrusdt', 'goatusdt', 'moodengusdt', 'safeusdt', 'santosusdt', 'ponkeusdt', 'cowusdt', 'cetususdt', '1000000mogusdt', 'grassusdt', 'driftusdt', 'swellusdt', 'actusdt', 'pnutusdt', 'hippousdt', '1000xusdt', 'degenusdt', 'banusdt', 'aktusdt', 'slerfusdt', 'scrtusdt', '1000cheemsusdt', '1000whyusdt', 'theusdt', 'morphousdt', 'chillguyusdt', 'kaiausdt', 'aerousdt', 'acxusdt', 'orcausdt', 'moveusdt', 'raysolusdt', 'komausdt', 'virtualusdt', 'spxusdt', 'meusdt', 'avausdt', 'degousdt', 'velodromeusdt', 'mocausdt', 'vanausdt', 'penguusdt', 'lumiausdt', 'usualusdt', 'aixbtusdt', 'fartcoinusdt', 'kmnousdt', 'cgptusdt', 'hiveusdt', 'dexeusdt', 'phausdt', 'dfusdt', 'griffainusdt', 'ai16zusdt', 'zerebrousdt', 'biousdt', 'cookieusdt', 'alchusdt', 'swarmsusdt', 'sonicusdt', 'dusdt', 'promusdt', 'susdt', 'solvusdt', 'arcusdt', 'avaaiusdt', 'trumpusdt', 'melaniausdt', 'vthousdt', 'animeusdt', 'vineusdt', 'pippinusdt', 'vvvusdt', 'berausdt', 'tstusdt', 'layerusdt', 'heiusdt', 'b3usdt', 'ipusdt', 'gpsusdt', 'shellusdt', 'kaitousdt', 'redusdt', 'vicusdt', 'epicusdt', 'bmtusdt', 'mubarakusdt', 'formusdt', 'bidusdt', 'tutusdt', 'broccoli714usdt', 'broccolif3busdt', 'sirenusdt', 'bananas31usdt', 'brusdt', 'plumeusdt', 'nilusdt', 'partiusdt', 'jellyjellyusdt', 'maviausdt', 'paxgusdt', 'walusdt', 'btcusdt_250926', 'ethusdt_250926', 'funusdt', 'mlnusdt', 'gunusdt', 'athusdt', 'babyusdt', 'forthusdt', 'promptusdt', 'xcnusdt', 'stousdt', 'fheusdt', 'kernelusdt', 'wctusdt', 'initusdt', 'aergousdt', 'bankusdt', 'eptusdt', 'deepusdt', 'hyperusdt', 'fisusdt', 'jstusdt', 'signusdt', 'pundixusdt', 'ctkusdt', 'aiotusdt', 'dolousdt', 'haedalusdt', 'sxtusdt', 'asrusdt', 'alpineusdt', 'b2usdt', 'milkusdt', 'syrupusdt', 'obolusdt', 'doodusdt', 'ogusdt', 'zkjusdt', 'skyaiusdt', 'nxpcusdt', 'cvcusdt', 'agtusdt', 'aweusdt', 'busdt', 'soonusdt', 'humausdt', 'ausdt', 'sophusdt', 'merlusdt', 'hypeusdt', 'bdxnusdt', 'pufferusdt', 'port3usdt', '1000000bobusdt', 'lausdt', 'skateusdt', 'homeusdt', 'resolvusdt', 'taikousdt', 'sqdusdt', 'pumpbtcusdt', 'spkusdt', 'myxusdt', 'fusdt', 'newtusdt', 'dmcusdt', 'husdt', 'olusdt', 'saharausdt', 'btcusdt_251226', 'ethusdt_251226', 'icntusdt', 'bullausdt', 'idolusdt', 'musdt', 'tanssiusdt', 'pumpusdt', 'crossusdt', 'ainusdt', 'cusdt', 'velvetusdt', 'tacusdt', 'erausdt', 'tausdt', 'cvxusdt', 'slpusdt', 'zorausdt', 'tagusdt', 'zrcusdt', 'esportsusdt', 'treeusdt', 'a2zusdt', 'playusdt', 'naorisusdt', 'townsusdt', 'proveusdt', 'allusdt', 'inusdt', 'yalausdt', 'carvusdt', 'aiousdt', 'xnyusdt', 'uselessusdt', 'damusdt', 'cudisusdt', 'sapienusdt', 'xplusdt', 'wlfiusdt', 'somiusdt', 'basusdt', 'btrusdt']

# Main scanning timeframes
MAIN_TIMEFRAMES = ["15m", "1h", "4h", "1d"]

# Nakel uses lower timeframe slices inside higher candles
NAKEL_MINOR_FOR = {
    "1m": "1s",
    "5m": "1m",
    "15m": "1m",
    "1h": "1m",
    "4h": "5m",
    "1d": "15m",
}

MAX_ROWS = 1500
PRINT_TABLE_ON_SIGNAL = True

# Binance WS: max 1024 streams per connection
MAX_STREAMS_PER_SOCKET = 200


# Global lock for thread-safe printing to the console
PRINT_LOCK = Lock()


# =========================
# 1) UTILITIES
# =========================

def to_ts(ms):
    return pd.to_datetime(ms, unit="ms", utc=True)

def timeframe_to_millis(tf_str):
    val = int(tf_str[:-1])
    unit = tf_str[-1]
    if unit == 'm': return val * 60 * 1000
    if unit == 'h': return val * 60 * 60 * 1000
    if unit == 'd': return val * 24 * 60 * 60 * 1000
    return 0

# =========================
# 2) SIGNAL ENGINE (Nakel + Hadena) - FULLY CORRECTED
# =========================

def fibonacci_levels(high, low):
    diff = high - low
    return {
        "0": low, "23.6": low + 0.236 * diff, "38.2": low + 0.382 * diff,
        "50": low + 0.5 * diff, "61.8": low + 0.618 * diff, "76.4": low + 0.764 * diff,
        "100": high, "123.6": high + 0.236 * diff, "-123.6": low - 0.236 * diff,
        "152.8": high + 0.528 * diff, "-152.8": low - 0.528 * diff,
        "176.4": high + 0.764 * diff, "-176.4": low - 0.764 * diff,
    }

def update_hadena(df, hadena, bullish_hadena, bearish_hadena):
    for index, row in df.iterrows():
        if row['High'] > df.loc[hadena, '123.6']:
            hadena, bullish_hadena = index, index
        elif row['Low'] < df.loc[hadena, '-123.6']:
            hadena, bearish_hadena = index, index
    return hadena, bullish_hadena, bearish_hadena

def signal_gen(df):
    if len(df) < 2: return None, None, None
    hadena = bullish_hadena = bearish_hadena = df.index[0]
    hadena, bullish_hadena, bearish_hadena = update_hadena(df, hadena, bullish_hadena, bearish_hadena)
    signal, hadena_type = "", None
    if hadena == bearish_hadena:
        hadena_type = "Bearish"
        if df.iloc[-1]['Close'] > df.loc[bearish_hadena, '100']: signal = "Bearish"
    elif hadena == bullish_hadena:
        hadena_type = "Bullish"
        if df.iloc[-1]['Close'] < df.loc[bullish_hadena, '0']: signal = "Bullish"
    if hadena_type == signal: return hadena_type, signal, hadena
    return hadena_type, None, hadena

def Nakel(ohlcv_df, nakel_klines_df):
    if len(ohlcv_df) < 2: return ""
    
    last_candle, previous_candle = ohlcv_df.iloc[-1], ohlcv_df.iloc[-2]
    last_candle_length = float(last_candle["High"] - last_candle["Low"])
    previous_candle_length = float(previous_candle["High"] - previous_candle["Low"])
    
    if previous_candle_length == 0: return ""
    error_margin = float(1/50 * previous_candle_length)
    signal_n = ""

    # --- Standard Signal Logic ---
    if previous_candle["23.6"] - error_margin <= last_candle["Low"] <= previous_candle["23.6"] + error_margin: signal_n += "(W-B 23.6)🚀"
    if previous_candle["76.4"] - error_margin <= last_candle["High"] <= previous_candle["76.4"] + error_margin: signal_n += "(W-S 76.4)🔻"
    if previous_candle["-123.6"] - error_margin <= last_candle["Low"] <= previous_candle["-123.6"] + error_margin: signal_n += "(B 123.6)🚀"
    if previous_candle["123.6"] - error_margin <= last_candle["High"] <= previous_candle["123.6"] + error_margin: signal_n += "(S 123.6)🔻"
    if previous_candle["152.8"] - error_margin <= last_candle["High"] <= previous_candle["152.8"] + error_margin: signal_n += "(152.8--S)🔻"
    if previous_candle["-152.8"] - error_margin <= last_candle["Low"] <= previous_candle["-152.8"] + error_margin: signal_n += "(152.8--B)🚀"
    if previous_candle["176.4"] - error_margin <= last_candle["High"] <= previous_candle["176.4"] + error_margin: signal_n += "(176.4--S)🔻"
    if previous_candle["-176.4"] - error_margin <= last_candle["Low"] <= previous_candle["-176.4"] + error_margin: signal_n += "(176.4--B)🚀"
    if last_candle_length <= (previous_candle_length / 2) and previous_candle["-123.6"] <= last_candle["Low"] < previous_candle["Low"]: signal_n += "(T-B)"
    if last_candle_length <= (previous_candle_length / 2) and previous_candle["123.6"] >= last_candle["High"] > previous_candle["High"]: signal_n += "(T-S)"
    if last_candle_length > (previous_candle_length / 2) and previous_candle["-123.6"] + error_margin < last_candle["Low"] < previous_candle["Low"]: signal_n += "(FB-B)"
    if last_candle_length > (previous_candle_length / 2) and previous_candle["123.6"] - error_margin > last_candle["High"] > previous_candle["High"]: signal_n += "(FB-S)"

    # --- ✅ Full argrelextrema Logic ---
    if nakel_klines_df is None or nakel_klines_df.empty:
        return signal_n

    try:
        # NOTE: We now analyze the levels of the *last closed candle* using the minor candles within it.
        # This is the correct real-time equivalent of the original script's logic.
        error_margin_advanced = float(1/50 * last_candle_length)

        maxima_indices = argrelextrema(nakel_klines_df['High'].values, np.greater, order=2)[0]
        minima_indices = argrelextrema(nakel_klines_df['Low'].values, np.less, order=2)[0]
        
        for idx in maxima_indices:
            peak_row = nakel_klines_df.iloc[idx]
            if last_candle["76.4"] - error_margin_advanced <= peak_row["High"] <= last_candle["76.4"] + error_margin_advanced:
                if all(nakel_klines_df.iloc[idx:]["High"].values <= peak_row["High"]):
                    if "(S 76.4)" not in signal_n: signal_n += "(S 76.4)🔻🔻"
        
        for idx in minima_indices:
            valley_row = nakel_klines_df.iloc[idx]
            if last_candle["23.6"] - error_margin_advanced <= valley_row["Low"] <= last_candle["23.6"] + error_margin_advanced:
                if all(nakel_klines_df.iloc[idx:]["Low"].values >= valley_row["Low"]):
                    if "(B 23.6)" not in signal_n: signal_n += "(B 23.6)🚀🚀"
    except Exception:
        pass # Fail silently if analysis on the sub-dataframe fails

    return signal_n


# =========================
# 3) DATA STORE
# =========================

class Store:
    def __init__(self, max_rows=MAX_ROWS):
        self.frames = {}; self.max_rows = max_rows; self.lock = Lock()
    def ensure(self, symbol, tf):
        key = (symbol, tf)
        if key not in self.frames:
            self.frames[key] = pd.DataFrame(columns=["Open","High","Low","Close","Volume"])
        return key
    def append_closed(self, symbol, tf, ts, o,h,l,c,v):
        with self.lock:
            key = self.ensure(symbol, tf)
            df = self.frames[key]
            df.loc[ts] = {"Open":o,"High":h,"Low":l,"Close":c,"Volume":v}
            for level, value in fibonacci_levels(h, l).items(): df.loc[ts, level] = value
            self.frames[key] = df.sort_index().iloc[-self.max_rows:]
    def get_df(self, symbol, tf):
        with self.lock: return self.frames.get((symbol, tf), pd.DataFrame()).copy()


# =========================
# 4) SCANNER
# =========================

class FawdaScannerWS:
    WS_URL = "wss://fstream.binance.com/ws"

    def __init__(self, symbols, main_tfs, nakel_minor_for):
        self.symbols = [s.lower() for s in symbols]
        self.main_tfs = main_tfs
        self.nakel_minor_for = nakel_minor_for
        self.store = Store()
        # All timeframes we need to subscribe to
        self.all_tfs = set(main_tfs) | set(nakel_minor_for.values())

    def on_open(self, ws):
        params = [f"{s}@kline_{tf}" for s in self.symbols for tf in self.all_tfs]
        ws.send(json.dumps({"method": "SUBSCRIBE", "params": params, "id": 1}))
        with PRINT_LOCK: print(f"✅ Subscribed to {len(params)} streams for {len(self.symbols)} symbols.")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("e") != "kline": return
            k = data["k"]
            if not k["x"]: return # Process only closed candles

            symbol, tf = data["s"].lower(), k["i"]
            ts_open = to_ts(k["t"])
            o, h, l, c, v = map(float, (k["o"], k["h"], k["l"], k["c"], k["v"]))

            self.store.append_closed(symbol, tf, ts_open, o, h, l, c, v)

            if tf in self.main_tfs:
                # Pass the candle's start and end times for minor TF slicing
                self._run_scanners_for(symbol, tf, k["t"], k["T"])
        except Exception:
            with PRINT_LOCK:
                print("--- ERROR processing message ---"); traceback.print_exc()

    def _run_scanners_for(self, symbol, tf, candle_start_ms, candle_end_ms):
        df = self.store.get_df(symbol, tf)
        if len(df) < 3: return

        nakel_klines_df = None
        minor_tf = self.nakel_minor_for.get(tf)
        if minor_tf:
            minor_df = self.store.get_df(symbol, minor_tf)
            if not minor_df.empty:
                start_ts = to_ts(candle_start_ms)
                end_ts = to_ts(candle_end_ms)
                # ✅ Select only the minor candles that are inside the main candle's duration
                nakel_klines_df = minor_df[(minor_df.index >= start_ts) & (minor_df.index <= end_ts)]

        nakel_signal = Nakel(df, nakel_klines_df)
        hadena_type, hadena_signal, hadena_index = signal_gen(df)

        if nakel_signal or hadena_signal:
            self._print_alert(symbol, tf, df, nakel_signal, hadena_type, hadena_signal, hadena_index)

    def _print_alert(self, symbol, tf, df, nakel_signal, hadena_type, hadena_signal, hadena_index):
        with PRINT_LOCK:
            last_idx, close = df.index[-1], df.iloc[-1]["Close"]
            print("-" * 60)
            print(f"✨ FAWDA SIGNAL ✨ {symbol.upper()} | {tf} | Close: {close} @ {last_idx.strftime('%Y-%m-%d %H:%M')}")
            if nakel_signal: print(f"  - Nakel: {nakel_signal}")
            if hadena_signal: print(f"  - Hadena: {hadena_type} Signal Triggered (from Hadena @ {hadena_index.strftime('%H:%M')})")
            print("-" * 60, "\n")

    def run_forever(self):
        while True:
            try:
                ws = websocket.WebSocketApp(
                    self.WS_URL, on_open=self.on_open, on_message=self.on_message,
                    on_close=lambda *_: print("⚠️ Socket closed, reconnecting in 5s..."),
                    on_error=lambda ws, err: print(f"⚠️ Socket error: {err}, reconnecting..."))
                ws.run_forever(ping_interval=60, ping_timeout=30)
            except Exception as e: print(f"WS app error: {e}")
            time.sleep(5)

# =========================
# 5) BATCH RUNNER
# =========================

def run_multi_scanners(symbols, main_tfs, nakel_minor_for):
    all_tfs = set(main_tfs) | set(nakel_minor_for.values())
    streams_per_symbol = len(all_tfs)
    max_symbols_per_socket = max(1, MAX_STREAMS_PER_SOCKET // streams_per_symbol)
    
    with PRINT_LOCK:
        print(f"⚡ Each symbol requires {streams_per_symbol} streams. Splitting into batches of {max_symbols_per_socket} symbols per socket.")
    
    for i in range(0, len(symbols), max_symbols_per_socket):
        batch = symbols[i:i + max_symbols_per_socket]
        scanner = FawdaScannerWS(batch, main_tfs, nakel_minor_for)
        Thread(target=scanner.run_forever, daemon=True).start()
        with PRINT_LOCK:
            print(f"✅ Started scanner for batch: {', '.join(s.upper() for s in batch)}")

# =========================
# 6) MAIN
# =========================

if __name__ == "__main__":
    print("Fawda Full-Featured WebSocket Scanner starting...")
    run_multi_scanners(SYMBOLS, MAIN_TIMEFRAMES, NAKEL_MINOR_FOR)
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        print("\nScanner shutting down.")