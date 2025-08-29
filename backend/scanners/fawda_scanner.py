import json
import time
import traceback
from threading import Thread, Lock
from datetime import datetime, timezone
import asyncio
import aiohttp
import sys
import os
from concurrent.futures import ProcessPoolExecutor

# Add project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

import websocket
import pandas as pd
import numpy as np

from scipy.signal import argrelextrema
from backend.supabase_client import insert_signal, update_scanner_status

# =========================
# SIGNAL ENGINE (Nakel + Hadena)
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

def signal_gen(df, is_historical_scan=False):
    if is_historical_scan:
        if len(df) < 3: return None, None, None
        candle_to_check = df.iloc[-2]
    else:
        if len(df) < 2: return None, None, None
        candle_to_check = df.iloc[-1]

    hadena = bullish_hadena = bearish_hadena = df.index[0]
    hadena, bullish_hadena, bearish_hadena = update_hadena(df, hadena, bullish_hadena, bearish_hadena)
    signal, hadena_type = "", None
    if hadena == bearish_hadena:
        hadena_type = "Bearish"
        if candle_to_check['Close'] > df.loc[bearish_hadena, '100']: signal = "Bearish"
    elif hadena == bullish_hadena:
        hadena_type = "Bullish"
        if candle_to_check['Close'] < df.loc[bullish_hadena, '0']: signal = "Bullish"
    if hadena_type == signal: return hadena_type, signal, hadena
    return hadena_type, None, hadena

def Nakel(ohlcv_df, nakel_klines_df, is_historical_scan=False):
    if is_historical_scan:
        if len(ohlcv_df) < 3: return ""
        # For historical, compare the 2nd to last candle against the 3rd to last
        last_candle, previous_candle = ohlcv_df.iloc[-2], ohlcv_df.iloc[-3]
    else:
        if len(ohlcv_df) < 2: return ""
        # For live, compare the latest candle against the previous one
        last_candle, previous_candle = ohlcv_df.iloc[-1], ohlcv_df.iloc[-2]
    last_candle_length = float(last_candle["High"] - last_candle["Low"])
    previous_candle_length = float(previous_candle["High"] - previous_candle["Low"])
    if previous_candle_length == 0: return ""
    error_margin = float(1/50 * previous_candle_length)
    signal_n = ""
    if previous_candle["23.6"] - error_margin <= last_candle["Low"] <= previous_candle["23.6"] + error_margin: signal_n += "(W-B_23_6)🚀"
    if previous_candle["76.4"] - error_margin <= last_candle["High"] <= previous_candle["76.4"] + error_margin: signal_n += "(W-S_76_4)🔻"
    if previous_candle["-123.6"] - error_margin <= last_candle["Low"] <= previous_candle["-123.6"] + error_margin: signal_n += "(B_123_6)🚀"
    if previous_candle["123.6"] - error_margin <= last_candle["High"] <= previous_candle["123.6"] + error_margin: signal_n += "(S_123_6)🔻"
    if previous_candle["152.8"] - error_margin <= last_candle["High"] <= previous_candle["152.8"] + error_margin: signal_n += "(S_152_8)🔻"
    if previous_candle["-152.8"] - error_margin <= last_candle["Low"] <= previous_candle["-152.8"] + error_margin: signal_n += "(B_152_8)🚀"
    if previous_candle["176.4"] - error_margin <= last_candle["High"] <= previous_candle["176.4"] + error_margin: signal_n += "(S_176_4)🔻"
    if previous_candle["-176.4"] - error_margin <= last_candle["Low"] <= previous_candle["-176.4"] + error_margin: signal_n += "(B_176_4)🚀"
    if last_candle_length <= (previous_candle_length / 2) and previous_candle["-123.6"] <= last_candle["Low"] < previous_candle["Low"]: signal_n += "(T-B)"
    if last_candle_length <= (previous_candle_length / 2) and previous_candle["123.6"] >= last_candle["High"] > previous_candle["High"]: signal_n += "(T-S)"
    if last_candle_length > (previous_candle_length / 2) and previous_candle["-123.6"] + error_margin < last_candle["Low"] < previous_candle["Low"]: signal_n += "(FB-B)"
    if last_candle_length > (previous_candle_length / 2) and previous_candle["123.6"] - error_margin > last_candle["High"] > previous_candle["High"]: signal_n += "(FB-S)"
    if nakel_klines_df is None or nakel_klines_df.empty:
        return signal_n
    try:
        error_margin_advanced = float(1/50 * last_candle_length)
        maxima_indices = argrelextrema(nakel_klines_df['High'].values, np.greater, order=2)[0]
        minima_indices = argrelextrema(nakel_klines_df['Low'].values, np.less, order=2)[0]
        for idx in maxima_indices:
            peak_row = nakel_klines_df.iloc[idx]
            if last_candle["76.4"] - error_margin_advanced <= peak_row["High"] <= last_candle["76.4"] + error_margin_advanced:
                if all(nakel_klines_df.iloc[idx:]["High"].values <= peak_row["High"]):
                    if "(S_76_4)" not in signal_n: signal_n += "(S_76_4)🔻🔻"
        for idx in minima_indices:
            valley_row = nakel_klines_df.iloc[idx]
            if last_candle["23.6"] - error_margin_advanced <= valley_row["Low"] <= last_candle["23.6"] + error_margin_advanced:
                if all(nakel_klines_df.iloc[idx:]["Low"].values >= valley_row["Low"]):
                    if "(B_23_6)" not in signal_n: signal_n += "(B_23_6)🚀🚀"
    except Exception:
        pass
    return signal_n

# =========================
# CONFIG
# =========================
SYMBOLS =  ['btcusdt', 'ethusdt', 'bchusdt', 'xrpusdt', 'ltcusdt', 'trxusdt', 'etcusdt', 'linkusdt', 'xlmusdt', 'adausdt', 'xmrusdt', 'dashusdt', 'zecusdt', 'xtzusdt', 'bnbusdt', 'atomusdt', 'ontusdt', 'iotausdt', 'batusdt', 'vetusdt', 'neousdt', 'qtumusdt', 'iostusdt', 'thetausdt', 'algousdt', 'zilusdt', 'kncusdt', 'zrxusdt', 'compusdt', 'dogeusdt', 'sxpusdt', 'kavausdt', 'bandusdt', 'rlcusdt', 'mkrusdt', 'snxusdt', 'dotusdt', 'yfiusdt', 'crvusdt', 'trbusdt', 'runeusdt', 'sushiusdt', 'egldusdt', 'solusdt', 'icxusdt', 'storjusdt', 'uniusdt', 'avaxusdt', 'enjusdt', 'flmusdt', 'ksmusdt', 'nearusdt', 'aaveusdt', 'filusdt', 'rsrusdt', 'lrcusdt', 'belusdt', 'axsusdt', 'alphausdt', 'zenusdt', 'sklusdt', 'grtusdt', '1inchusdt', 'chzusdt', 'sandusdt', 'ankrusdt', 'rvnusdt', 'sfpusdt', 'cotiusdt', 'chrusdt', 'manausdt', 'aliceusdt', 'hbarusdt', 'oneusdt', 'dentusdt', 'celrusdt', 'hotusdt', 'mtlusdt', 'ognusdt', 'nknusdt', '1000shibusdt', 'bakeusdt', 'gtcusdt', 'btcdomusdt', 'iotxusdt', 'c98usdt', 'maskusdt', 'atausdt', 'dydxusdt', '1000xecusdt', 'galausdt', 'celousdt', 'arusdt', 'arpausdt', 'ctsiusdt', 'lptusdt', 'ensusdt', 'peopleusdt', 'roseusdt', 'duskusdt', 'flowusdt', 'imxusdt', 'api3usdt', 'gmtusdt', 'apeusdt', 'woousdt', 'jasmyusdt', 'opusdt', 'injusdt', 'stgusdt', 'spellusdt', '1000luncusdt', 'luna2usdt', 'ldousdt', 'icpusdt', 'aptusdt', 'qntusdt', 'fetusdt', 'fxsusdt', 'hookusdt', 'magicusdt', 'tusdt', 'highusdt', 'minausdt', 'astrusdt', 'phbusdt', 'gmxusdt', 'cfxusdt', 'stxusdt', 'achusdt', 'ssvusdt', 'ckbusdt', 'perpusdt', 'truusdt', 'lqtyusdt', 'usdcusdt', 'idusdt', 'arbusdt', 'joeusdt', 'tlmusdt', 'leverusdt', 'rdntusdt', 'hftusdt', 'xvsusdt', 'blurusdt', 'eduusdt', 'suiusdt', '1000pepeusdt', '1000flokiusdt', 'umausdt', 'nmrusdt', 'mavusdt', 'xvgusdt', 'wldusdt', 'pendleusdt', 'arkmusdt', 'agldusdt', 'yggusdt', 'dodoxusdt', 'bntusdt', 'oxtusdt', 'seiusdt', 'cyberusdt', 'hifiusdt', 'arkusdt', 'bicousdt', 'bigtimeusdt', 'waxpusdt', 'bsvusdt', 'rifusdt', 'polyxusdt', 'gasusdt', 'powrusdt', 'tiausdt', 'cakeusdt', 'memeusdt', 'twtusdt', 'tokenusdt', 'ordiusdt', 'steemusdt', 'ilvusdt', 'ntrnusdt', 'kasusdt', 'beamxusdt', '1000bonkusdt', 'pythusdt', 'superusdt', 'ustcusdt', 'ongusdt', 'ethwusdt', 'jtousdt', '1000satsusdt', 'auctionusdt', '1000ratsusdt', 'aceusdt', 'movrusdt', 'nfpusdt', 'aiusdt', 'xaiusdt', 'wifusdt', 'mantausdt', 'ondousdt', 'lskusdt', 'altusdt', 'jupusdt', 'zetausdt', 'roninusdt', 'dymusdt', 'omusdt', 'pixelusdt', 'strkusdt', 'glmusdt', 'portalusdt', 'tonusdt', 'axlusdt', 'myrousdt', 'metisusdt', 'aevousdt', 'vanryusdt', 'bomeusdt', 'ethfiusdt', 'enausdt', 'wusdt', 'tnsrusdt', 'sagausdt', 'taousdt', 'omniusdt', 'rezusdt', 'bbusdt', 'notusdt', 'turbousdt', 'iousdt', 'zkusdt', 'mewusdt', 'listausdt', 'zrousdt', 'renderusdt', 'bananausdt', 'rareusdt', 'gusdt', 'synusdt', 'sysusdt', 'voxelusdt', 'brettusdt', 'popcatusdt', 'sunusdt', 'dogsusdt', 'mboxusdt', 'chessusdt', 'fluxusdt', 'bswusdt', 'quickusdt', 'neiroethusdt', 'rplusdt', 'polusdt', 'uxlinkusdt', '1mbabydogeusdt', 'neirousdt', 'kdausdt', 'fidausdt', 'fiousdt', 'catiusdt', 'ghstusdt', 'hmstrusdt', 'reiusdt', 'cosusdt', 'eigenusdt', 'diausdt', '1000catusdt', 'scrusdt', 'goatusdt', 'moodengusdt', 'safeusdt', 'santosusdt', 'ponkeusdt', 'cowusdt', 'cetususdt', '1000000mogusdt', 'grassusdt', 'driftusdt', 'swellusdt', 'actusdt', 'pnutusdt', 'hippousdt', '1000xusdt', 'degenusdt', 'banusdt', 'aktusdt', 'slerfusdt', 'scrtusdt', '1000cheemsusdt', '1000whyusdt', 'theusdt', 'morphousdt', 'chillguyusdt', 'kaiausdt', 'aerousdt', 'acxusdt', 'orcausdt', 'moveusdt', 'raysolusdt', 'komausdt', 'virtualusdt', 'spxusdt', 'meusdt', 'avausdt', 'degousdt', 'velodromeusdt', 'mocausdt', 'vanausdt', 'penguusdt', 'lumiausdt', 'usualusdt', 'aixbtusdt', 'fartcoinusdt', 'kmnousdt', 'cgptusdt', 'hiveusdt', 'dexeusdt', 'phausdt', 'dfusdt', 'griffainusdt', 'ai16zusdt', 'zerebrousdt', 'biousdt', 'cookieusdt', 'alchusdt', 'swarmsusdt', 'sonicusdt', 'dusdt', 'promusdt', 'susdt', 'solvusdt', 'arcusdt', 'avaaiusdt', 'trumpusdt', 'melaniausdt', 'vthousdt', 'animeusdt', 'vineusdt', 'pippinusdt', 'vvvusdt', 'berausdt', 'tstusdt', 'layerusdt', 'heiusdt', 'b3usdt', 'ipusdt', 'gpsusdt', 'shellusdt', 'kaitousdt', 'redusdt', 'vicusdt', 'epicusdt', 'bmtusdt', 'mubarakusdt', 'formusdt', 'bidusdt', 'tutusdt', 'broccoli714usdt', 'broccolif3busdt', 'sirenusdt', 'bananas31usdt', 'brusdt', 'plumeusdt', 'nilusdt', 'partiusdt', 'jellyjellyusdt', 'maviausdt', 'paxgusdt', 'walusdt', 'btcusdt_250926', 'ethusdt_250926', 'funusdt', 'mlnusdt', 'gunusdt', 'athusdt', 'babyusdt', 'forthusdt', 'promptusdt', 'xcnusdt', 'stousdt', 'fheusdt', 'kernelusdt', 'wctusdt', 'initusdt', 'aergousdt', 'bankusdt', 'eptusdt', 'deepusdt', 'hyperusdt', 'fisusdt', 'jstusdt', 'signusdt', 'pundixusdt', 'ctkusdt', 'aiotusdt', 'dolousdt', 'haedalusdt', 'sxtusdt', 'asrusdt', 'alpineusdt', 'b2usdt', 'milkusdt', 'syrupusdt', 'obolusdt', 'doodusdt', 'ogusdt', 'zkjusdt', 'skyaiusdt', 'nxpcusdt', 'cvcusdt', 'agtusdt', 'aweusdt', 'busdt', 'soonusdt', 'humausdt', 'ausdt', 'sophusdt', 'merlusdt', 'hypeusdt', 'bdxnusdt', 'pufferusdt', 'port3usdt', '1000000bobusdt', 'lausdt', 'skateusdt', 'homeusdt', 'resolvusdt', 'taikousdt', 'sqdusdt', 'pumpbtcusdt', 'spkusdt', 'myxusdt', 'fusdt', 'newtusdt', 'dmcusdt', 'husdt', 'olusdt', 'saharausdt', 'btcusdt_251226', 'ethusdt_251226', 'icntusdt', 'bullausdt', 'idolusdt', 'musdt', 'tanssiusdt', 'pumpusdt', 'crossusdt', 'ainusdt', 'cusdt', 'velvetusdt', 'tacusdt', 'erausdt', 'tausdt', 'cvxusdt', 'slpusdt', 'zorausdt', 'tagusdt', 'zrcusdt', 'esportsusdt', 'treeusdt', 'a2zusdt', 'playusdt', 'naorisusdt', 'townsusdt', 'proveusdt', 'allusdt', 'inusdt', 'yalausdt', 'carvusdt', 'aiousdt', 'xnyusdt', 'uselessusdt', 'damusdt', 'cudisusdt', 'sapienusdt', 'xplusdt', 'wlfiusdt', 'somiusdt', 'basusdt', 'btrusdt']
MAIN_TIMEFRAMES = ["15m", "1h", "4h", "1d"]
NAKEL_MINOR_FOR = {
    "15m": "1m",
    "1h": "1m",
    "4h": "5m",
    "1d": "15m",
}
MAX_STREAMS_PER_SOCKET = 200
PRINT_LOCK = Lock()
SCANNER_ID = "fawda_scanner_v1"

# =========================
# UTILITIES
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
# SIGNAL ENGINE (Nakel + Hadena integrated)
# =========================
def generate_signal(symbol, tf, df, nakel_df=None, is_historical_scan=False):
    # Determine the correct candle to check based on the context
    if is_historical_scan:
        if len(df) < 3: return None
        candle_to_check = df.iloc[-2]
        candle_timestamp = df.index[-2]
    else:
        if len(df) < 2: return None
        candle_to_check = df.iloc[-1]
        candle_timestamp = df.index[-1]

    if "23.6" not in df.columns:
        for i, row in df.iterrows():
            fibs = fibonacci_levels(row["High"], row["Low"])
            for level, value in fibs.items():
                df.loc[i, level] = value

    # --- Signal Processing ---
    nakel_signal_str = Nakel(df, nakel_df, is_historical_scan=is_historical_scan)
    hadena_type, hadena_signal, hadena_index = signal_gen(df, is_historical_scan=is_historical_scan)

    signal_codes = []
    if nakel_signal_str:
        ascii_str = nakel_signal_str.encode('ascii', 'ignore').decode('ascii')
        codes = ascii_str.replace('(', ' ').replace(')', ' ').split()
        signal_codes.extend(codes)

    # If a hadena SIGNAL is triggered, add its type to the codes.
    if hadena_signal:
        signal_codes.append(hadena_type)

    # --- Final Check ---
    # A record should be generated if there is ANY Nakel or Hadena signal.
    if not nakel_signal_str and not hadena_signal:
        return None

    # --- Construct Final Object ---
    entry_price = candle_to_check["Close"]
    final_signal = {
        "scanner_type": "fawda",
        "symbol": symbol.upper(),
        "timeframe": tf,
        "signal_codes": signal_codes,
        "signal_id": f"fawda-{symbol}-{tf}-{int(time.time())}",
        "candle_timestamp": candle_timestamp.to_pydatetime().isoformat(),
        "entry_price": entry_price,
        "status": "active",
        "hadena_timestamp": hadena_index.to_pydatetime().isoformat(),
        "metadata": json.dumps({"hadena_type": hadena_type})
    }

    return final_signal

# =========================
# DATA STORE
# =========================
class Store:
    def __init__(self, max_rows=1500):
        self.frames = {}
        self.max_rows = max_rows
        self.lock = Lock()
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
            fibs = fibonacci_levels(h, l)
            for level, value in fibs.items():
                df.loc[ts, level] = value
            self.frames[key] = df.sort_index().iloc[-self.max_rows:]
    def get_df(self, symbol, tf):
        with self.lock:
            return self.frames.get((symbol, tf), pd.DataFrame()).copy()

# =========================
# SCANNER
# =========================
class FawdaScannerWS:
    WS_URL = "wss://fstream.binance.com/ws"

    def __init__(self, symbols, main_tfs):
        self.symbols = [s.lower() for s in symbols]
        self.main_tfs = main_tfs
        self.store = Store()

    def on_open(self, ws):
        params = [f"{s}@kline_{tf}" for s in self.symbols for tf in self.main_tfs]
        ws.send(json.dumps({"method": "SUBSCRIBE", "params": params, "id": 1}))
        with PRINT_LOCK:
            print(f"✅ Subscribed to {len(params)} streams for {len(self.symbols)} symbols.")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("e") != "kline": return
            k = data["k"]
            if not k["x"]: return

            symbol, tf = data["s"].lower(), k["i"]
            ts_open = to_ts(k["t"])
            o, h, l, c, v = map(float, (k["o"], k["h"], k["l"], k["c"], k["v"]))

            self.store.append_closed(symbol, tf, ts_open, o, h, l, c, v)

            df = self.store.get_df(symbol, tf)
            minor_tf = NAKEL_MINOR_FOR.get(tf)
            nakel_df = None
            if minor_tf:
                nakel_df = self.store.get_df(symbol, minor_tf)
            signal = generate_signal(symbol, tf, df, nakel_df, is_historical_scan=False)
            if signal:
                insert_signal(signal)
                with PRINT_LOCK:
                    print(f"✨ Signal inserted: {signal['signal_id']}")
        except Exception:
            with PRINT_LOCK:
                print("--- ERROR processing message ---")
                traceback.print_exc()
                update_scanner_status(SCANNER_ID, "error", traceback.format_exc())

    def run_forever(self):
        while True:
            try:
                ws = websocket.WebSocketApp(
                    self.WS_URL, on_open=self.on_open, on_message=self.on_message,
                    on_close=lambda *_: print("⚠️ Socket closed, reconnecting in 5s..."),
                    on_error=lambda ws, err: print(f"⚠️ Socket error: {err}, reconnecting..."))
                ws.run_forever(ping_interval=60, ping_timeout=30)
            except Exception as e:
                print(f"WS app error: {e}")
            time.sleep(5)

from concurrent.futures import ProcessPoolExecutor

# =========================
# MANUAL SCAN FUNCTION (REFACTORED FOR PARALLELISM)
# =========================

# This function needs to be at the top level for multiprocessing to work.
# It's a self-contained task that processes one symbol/timeframe combination.
def run_process_for_symbol(args):
    """
    Worker function to be executed in a separate process.
    Fetches klines and generates a signal for a single symbol/timeframe.
    """
    symbol, tf, limit = args
    # asyncio.run is used to execute the async logic within this synchronous worker process.
    try:
        signal = asyncio.run(fetch_and_process_single(symbol, tf, limit))
        return signal
    except Exception as e:
        # print(f"Error processing {symbol} {tf}: {e}") # Optional: for debugging
        return None

async def fetch_and_process_single(symbol, tf, limit):
    """
    The core async logic for fetching and processing data for one task.
    """
    local_store = Store() # Each process gets its own in-memory store.
    
    async with aiohttp.ClientSession() as session:
        main_data = await fetch_klines(session, symbol, tf, limit)
        if not isinstance(main_data, list) or len(main_data) < 3:
            return None

        # Process main timeframe data
        df = pd.DataFrame(
            [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in main_data],
            columns=["OpenTime", "Open", "High", "Low", "Close", "Volume"]
        )
        df["OpenTime"] = pd.to_datetime(df["OpenTime"], unit="ms", utc=True)
        df.set_index("OpenTime", inplace=True)
        for i, row in df.iterrows():
            local_store.append_closed(symbol, tf, i, row["Open"], row["High"], row["Low"], row["Close"], row["Volume"])

        # Process minor timeframe data for Nakel
        minor_tf = NAKEL_MINOR_FOR.get(tf)
        minor_df = None
        if minor_tf:
            minor_data = await fetch_klines(session, symbol, minor_tf, limit * 50)
            if isinstance(minor_data, list):
                dfm = pd.DataFrame(
                    [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in minor_data],
                    columns=["OpenTime", "Open", "High", "Low", "Close", "Volume"]
                )
                dfm["OpenTime"] = pd.to_datetime(dfm["OpenTime"], unit="ms", utc=True)
                dfm.set_index("OpenTime", inplace=True)
                minor_df = dfm

    # Generate signal using the locally built dataframes
    df_with_fibs = local_store.get_df(symbol, tf)
    signal = generate_signal(symbol, tf, df_with_fibs, minor_df, is_historical_scan=True)
    
    return signal


async def fetch_klines(session, symbol, tf, limit):
    base_url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol.upper(), "interval": tf, "limit": limit}
    try:
        async with session.get(base_url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()
    except aiohttp.ClientError:
        return None

def manual_scan_all(limit: int = 10):
    """
    Uses a ProcessPoolExecutor to run the initial scan in parallel across multiple CPU cores.
    """
    print("Preparing tasks for parallel processing...")
    tasks = [(symbol, tf, limit) for tf in MAIN_TIMEFRAMES for symbol in SYMBOLS]
    
    all_signals = []
    
    with ProcessPoolExecutor(max_workers=5) as executor:
        results = executor.map(run_process_for_symbol, tasks)
        
        for signal in results:
            if signal:
                all_signals.append(signal)

    if all_signals:
        print(f"Found {len(all_signals)} signals in total. Performing batch insert...")
        try:
            insert_signal(all_signals)
            print(f"✅ Successfully inserted {len(all_signals)} signals.")
        except Exception as e:
            print(f"❌ Error during batch insert: {e}")
    else:
        print("No signals found during initial scan.")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("Fawda WebSocket Scanner starting...")

    # The initial scan can be very slow. Use --no-scan to skip it.
    if "--no-scan" not in sys.argv:
        print("Starting initial scan for historical data. This may take a while...")
        print("To skip this in the future, run with the --no-scan flag.")
        manual_scan_all(limit=10)
        print("Initial scan complete.")
    else:
        print("Skipping initial scan.")

    streams_per_symbol = len(MAIN_TIMEFRAMES)
    max_symbols_per_socket = max(1, MAX_STREAMS_PER_SOCKET // streams_per_symbol)

    print(f"⚡ Each symbol requires {streams_per_symbol} streams. Splitting into batches of {max_symbols_per_socket} symbols per socket.")

    for i in range(0, len(SYMBOLS), max_symbols_per_socket):
        batch = SYMBOLS[i:i + max_symbols_per_socket]
        scanner = FawdaScannerWS(batch, MAIN_TIMEFRAMES)
        Thread(target=scanner.run_forever, daemon=True).start()
        with PRINT_LOCK:
            print(f"✅ Started scanner for batch: {', '.join(s.upper() for s in batch)}")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScanner shutting down.")

