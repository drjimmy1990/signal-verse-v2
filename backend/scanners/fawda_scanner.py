import json
import time
import traceback
from threading import Thread, Lock
from datetime import datetime, timezone

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
                    if "(S 76.4)" not in signal_n: signal_n += "(S 76.4)🔻🔻"
        for idx in minima_indices:
            valley_row = nakel_klines_df.iloc[idx]
            if last_candle["23.6"] - error_margin_advanced <= valley_row["Low"] <= last_candle["23.6"] + error_margin_advanced:
                if all(nakel_klines_df.iloc[idx:]["Low"].values >= valley_row["Low"]):
                    if "(B 23.6)" not in signal_n: signal_n += "(B 23.6)🚀🚀"
    except Exception:
        pass
    return signal_n

# =========================
# CONFIG
# =========================
SYMBOLS =  ['btcusdt', 'ethusdt', 'bchusdt']
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
def generate_signal(symbol, tf, df, nakel_df=None):
    if len(df) < 3:
        return None
    if "23.6" not in df.columns:
        for i, row in df.iterrows():
            fibs = fibonacci_levels(row["High"], row["Low"])
            for level, value in fibs.items():
                df.loc[i, level] = value
    nakel_signal = Nakel(df, nakel_df)
    hadena_type, hadena_signal, hadena_index = signal_gen(df)
    if not nakel_signal and not hadena_signal:
        return None
    last_close = df.iloc[-1]["Close"]
    signal_codes = []
    if nakel_signal:
        # Split concatenated signals like "(W-B 23.6)🚀(FB-B)" into individual codes
        import re
        matches = re.findall(r"\((.*?)\)", nakel_signal)
        for m in matches:
            # Remove emojis and keep only the code text
            clean_code = re.sub(r"[^\w\s\-\.\%]", "", m).strip()
            if clean_code:
                signal_codes.append(clean_code)
    if hadena_signal:
        signal_codes.append(hadena_type)
    return {
        "scanner_type": "fawda",
        "symbol": symbol.upper(),
        "timeframe": tf,
        "signal_codes": signal_codes,
        "signal_id": f"fawda-{symbol}-{tf}-{int(time.time())}",
        "candle_timestamp": df.index[-1].to_pydatetime().isoformat(),
        "entry_price": last_close,
        "status": "active",
        "metadata": json.dumps({"nakel": nakel_signal, "hadena": hadena_signal})
    }

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
            signal = generate_signal(symbol, tf, df, nakel_df)
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

# =========================
# MANUAL SCAN FUNCTION
# =========================
import requests

def manual_scan_all(limit: int = 10):
    base_url = "https://fapi.binance.com/fapi/v1/klines"
    store = Store()
    for tf in MAIN_TIMEFRAMES:
        minor_tf = NAKEL_MINOR_FOR.get(tf)
        for idx, symbol in enumerate(SYMBOLS):
            try:
                resp = requests.get(base_url, params={"symbol": symbol.upper(), "interval": tf, "limit": limit})
                data = resp.json()
                if isinstance(data, list):
                    df = pd.DataFrame(
                        [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in data],
                        columns=["OpenTime", "Open", "High", "Low", "Close", "Volume"]
                    )
                    df["OpenTime"] = pd.to_datetime(df["OpenTime"], unit="ms", utc=True)
                    df.set_index("OpenTime", inplace=True)
                    for i, row in df.iterrows():
                        store.append_closed(symbol, tf, i, row["Open"], row["High"], row["Low"], row["Close"], row["Volume"])
                if minor_tf:
                    resp_minor = requests.get(base_url, params={"symbol": symbol.upper(), "interval": minor_tf, "limit": limit*50})
                    data_minor = resp_minor.json()
                    if isinstance(data_minor, list):
                        dfm = pd.DataFrame(
                            [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in data_minor],
                            columns=["OpenTime", "Open", "High", "Low", "Close", "Volume"]
                        )
                        dfm["OpenTime"] = pd.to_datetime(dfm["OpenTime"], unit="ms", utc=True)
                        dfm.set_index("OpenTime", inplace=True)
                        for i, row in dfm.iterrows():
                            store.append_closed(symbol, minor_tf, i, row["Open"], row["High"], row["Low"], row["Close"], row["Volume"])
                df_with_fibs = store.get_df(symbol, tf)
                minor_df = store.get_df(symbol, minor_tf) if minor_tf else None
                signal = generate_signal(symbol, tf, df_with_fibs, minor_df)
                if signal:
                    insert_signal(signal)
                    print(f"✨ Manual signal inserted: {signal['signal_id']}")
            except Exception as e:
                print(f"⚠️ Error seeding {symbol.upper()} {tf}: {e}")
            if idx % 50 == 0 and idx > 0:
                time.sleep(0.5)
        time.sleep(0.5)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("Fawda WebSocket Scanner starting...")

    manual_scan_all(limit=10)

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
