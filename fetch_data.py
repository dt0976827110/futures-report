import json
import requests
import numpy as np
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

TW = timezone(timedelta(hours=8))
now = datetime.now(TW)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/"
}

GITHUB_RAW = "https://raw.githubusercontent.com/dt0976827110/futures-report/main/YMNQ_data.json"

# ─── 讀取 YMNQ_data.json ───────────────────────────────

def get_ymnq_data():
    try:
        res = requests.get(GITHUB_RAW, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"讀取 YMNQ_data.json 失敗：{e}")
    return {}

# ─── 技術指標計算 ───────────────────────────────────────

def calc_rsi(closes, period=14):
    closes = np.array(closes, dtype=float)
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_ma(closes, period):
    if len(closes) < period:
        return None
    return round(float(np.mean(closes[-period:])), 2)

def calc_macd(closes, fast=12, slow=26, signal=9):
    closes = np.array(closes, dtype=float)
    def ema(arr, period):
        k = 2 / (period + 1)
        result = [arr[0]]
        for v in arr[1:]:
            result.append(v * k + result[-1] * (1 - k))
        return np.array(result)
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {
        "macd": round(float(macd_line[-1]), 2),
        "signal": round(float(signal_line[-1]), 2),
        "histogram": round(float(histogram[-1]), 2)
    }

def calc_bollinger(closes, period=20, std_dev=2):
    if len(closes) < period:
        return None
    arr = np.array(closes[-period:], dtype=float)
    middle = np.mean(arr)
    std = np.std(arr)
    return {
        "upper": round(float(middle + std_dev * std), 2),
        "middle": round(float(middle), 2),
        "lower": round(float(middle - std_dev * std), 2)
    }

def calc_atr(highs, lows, closes, period=14):
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        tr_list.append(tr)
    if len(tr_list) < period:
        return None
    return round(float(np.mean(tr_list[-period:])), 2)

def calc_volume_ma(volumes, period=5):
    if len(volumes) < period:
        return None
    return round(float(np.mean(volumes[-period:])), 0)

# ─── 資料抓取 ───────────────────────────────────────────

def get_yahoo_meta(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    return res.json()["chart"]["result"][0]["meta"]

def get_yahoo_history(symbol, range_period="6mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={range_period}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    result = res.json()["chart"]["result"][0]
    quotes = result["indicators"]["quote"][0]
    timestamps = result["timestamp"]
    closes  = quotes["close"]
    highs   = quotes["high"]
    lows    = quotes["low"]
    volumes = quotes.get("volume", [0] * len(closes))
    data = [
        (t, c, h, l, v)
        for t, c, h, l, v in zip(timestamps, closes, highs, lows, volumes)
        if c is not None and h is not None and l is not None
    ]
    return data

def get_futures(symbol, name, currency, ymnq_close=None):
    try:
        history    = get_yahoo_history(symbol, "6mo")
        closes     = [d[1] for d in history]
        highs      = [d[2] for d in history]
        lows       = [d[3] for d in history]
        volumes    = [d[4] for d in history]
        timestamps = [d[0] for d in history]

        # 原始的 current 和 prev
        raw_current = round(closes[-2], 2)
        raw_prev    = round(closes[-3], 2)

        # 如果有 YMNQ_data 的收盤價，用它覆蓋
        if ymnq_close is not None:
            current = round(float(ymnq_close), 2)
            prev    = raw_current  # 原本的 current 變成 previous
        else:
            current = raw_current
            prev    = raw_prev

        change_pts = round(current - prev, 2)
        change_pct = round((change_pts / prev) * 100, 2)

        # 五日歷史：原本的五日 + 補上 YMNQ 的那一天
        five_day_raw = [
            {
                "date":  datetime.utcfromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
                "close": round(closes[i], 2)
            }
            for i in range(-6, -1)
        ]

        if ymnq_close is not None:
            # 移掉最舊一筆，補上最新收盤
            five_day = five_day_raw[1:] + [{
                "date":  now.strftime("%Y-%m-%d"),
                "close": current
            }]
        else:
            five_day = five_day_raw

        # 技術指標用原始歷史資料計算（含最新收盤）
        closes_for_indicator = closes[:-1]
        if ymnq_close is not None:
            closes_for_indicator = closes[:-1] + [current]

        macd_data = calc_macd(closes_for_indicator)
        bb_data   = calc_bollinger(closes_for_indicator)

        return {
            "name":           name,
            "current_price":  current,
            "previous_close": prev,
            "currency":       currency,
            "change_points":  change_pts,
            "change_percent": change_pct,
            "volume":         str(int(volumes[-2]) if volumes[-2] else 0),
            "support":        round(prev * 0.99, 0),
            "resistance":     round(prev * 1.01, 0),
            "support_basis":  "前收盤價 -1% 估算",
            "resistance_basis": "前收盤價 +1% 估算",
            "timestamp":      now.strftime("%Y-%m-%d %H:%M (台灣時間)"),
            "five_day_history": five_day,
            "indicators": {
                "rsi14":          calc_rsi(closes_for_indicator),
                "ma5":            calc_ma(closes_for_indicator, 5),
                "ma20":           calc_ma(closes_for_indicator, 20),
                "ma60":           calc_ma(closes_for_indicator, 60),
                "macd":           macd_data["macd"] if macd_data else None,
                "macd_signal":    macd_data["signal"] if macd_data else None,
                "macd_histogram": macd_data["histogram"] if macd_data else None,
                "bb_upper":       bb_data["upper"] if bb_data else None,
                "bb_middle":      bb_data["middle"] if bb_data else None,
                "bb_lower":       bb_data["lower"] if bb_data else None,
                "atr14":          calc_atr(highs[:-1], lows[:-1], closes[:-1]),
                "volume_ma5":     calc_volume_ma(volumes[:-1])
            }
        }
    except Exception as e:
        return {"error": str(e)}

def get_txf():
    try:
        url = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tr")
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.select("td")]
            if len(cols) > 8 and cols[0] == "TX":
                current = float(cols[5].replace(",", ""))
                raw_chg = cols[6].replace(",", "")
                is_down = "▽" in raw_chg
                change_pts = float(raw_chg.replace("▲", "").replace("▽", ""))
                if is_down:
                    change_pts = -change_pts
                prev = round(current - change_pts, 0)
                raw_pct = cols[7].replace(",", "").replace("%", "")
                is_down_pct = "▽" in raw_pct
                change_pct = float(raw_pct.replace("▲", "").replace("▽", ""))
                if is_down_pct:
                    change_pct = -change_pct
                volume = cols[8].replace(",", "")

                try:
                    history    = get_yahoo_history("%5ETWII", "6mo")
                    closes     = [d[1] for d in history]
                    highs      = [d[2] for d in history]
                    lows       = [d[3] for d in history]
                    volumes    = [d[4] for d in history]
                    timestamps = [d[0] for d in history]

                    five_day = [
                        {
                            "date":  datetime.utcfromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
                            "close": round(closes[i], 2)
                        }
                        for i in range(-6, -1)
                    ]
                    macd_data  = calc_macd(closes)
                    bb_data    = calc_bollinger(closes)
                    indicators = {
                        "rsi14":          calc_rsi(closes),
                        "ma5":            calc_ma(closes, 5),
                        "ma20":           calc_ma(closes, 20),
                        "ma60":           calc_ma(closes, 60),
                        "macd":           macd_data["macd"] if macd_data else None,
                        "macd_signal":    macd_data["signal"] if macd_data else None,
                        "macd_histogram": macd_data["histogram"] if macd_data else None,
                        "bb_upper":       bb_data["upper"] if bb_data else None,
                        "bb_middle":      bb_data["middle"] if bb_data else None,
                        "bb_lower":       bb_data["lower"] if bb_data else None,
                        "atr14":          calc_atr(highs, lows, closes),
                        "volume_ma5":     calc_volume_ma(volumes)
                    }
                except Exception as e2:
                    five_day   = []
                    indicators = {"error": str(e2)}

                return {
                    "name":           "台灣加權指數期貨",
                    "current_price":  current,
                    "previous_close": prev,
                    "currency":       "TWD",
                    "change_points":  change_pts,
                    "change_percent": change_pct,
                    "volume":         volume,
                    "support":        round(prev * 0.99, 0),
                    "resistance":     round(prev * 1.01, 0),
                    "support_basis":  "前收盤價 -1% 估算",
                    "resistance_basis": "前收盤價 +1% 估算",
                    "timestamp":      now.strftime("%Y-%m-%d %H:%M (台灣時間)"),
                    "five_day_history": five_day,
                    "indicators":     indicators
                }
        return {"error": "找不到TX資料"}
    except Exception as e:
        return {"error": str(e)}

def get_vix():
    try:
        meta    = get_yahoo_meta("%5EVIX")
        current = round(meta["regularMarketPrice"], 2)
        prev    = round(meta["chartPreviousClose"], 2)
        change  = round(current - prev, 2)
        sign    = "+" if change >= 0 else ""
        level   = "低" if current < 15 else "中" if current < 20 else "高" if current < 30 else "極高"
        return {
            "value":  current,
            "change": f"{sign}{change}",
            "level":  level,
            "note":   f"VIX 目前 {current}，市場波動{level}。"
        }
    except Exception as e:
        return {"error": str(e)}

def get_dxy():
    try:
        meta      = get_yahoo_meta("DX-Y.NYB")
        current   = round(meta["regularMarketPrice"], 2)
        prev      = round(meta["previousClose"], 2)
        direction = "↑" if current >= prev else "↓"
        return {
            "value":     current,
            "direction": direction,
            "note":      f"美元指數 {current}，趨勢{'走強' if direction == '↑' else '走弱'}。"
        }
    except Exception as e:
        return {"error": str(e)}

def get_oil():
    try:
        meta      = get_yahoo_meta("BZ%3DF")
        current   = round(meta["regularMarketPrice"], 2)
        prev      = round(meta["previousClose"], 2)
        direction = "↑" if current >= prev else "↓"
        return {
            "value":     current,
            "direction": direction,
            "note":      f"布蘭特原油 {current} 美元，趨勢{'上漲' if direction == '↑' else '下跌'}。"
        }
    except Exception as e:
        return {"error": str(e)}

# ─── 主程式 ────────────────────────────────────────────

# 讀取 YMNQ_data.json
ymnq = get_ymnq_data()
ym_close = ymnq.get("YM1", {}).get("close")
nq_close = ymnq.get("NQ1", {}).get("close")

if ym_close:
    print(f"使用 YMNQ_data YM close：{ym_close}")
else:
    print("YMNQ_data 無 YM 資料，使用歷史資料")

if nq_close:
    print(f"使用 YMNQ_data NQ close：{nq_close}")
else:
    print("YMNQ_data 無 NQ 資料，使用歷史資料")

data = {
    "fetch_time": now.strftime("%Y-%m-%d %H:%M (台灣時間)"),
    "market_sentiment": {
        "vix":       get_vix(),
        "dxy":       get_dxy(),
        "oil_brent": get_oil()
    },
    "futures_data": {
        "YM1":  get_futures("YM=F",  "E-迷你道瓊指數",     "USD", ym_close),
        "NQ1":  get_futures("NQ=F",  "E-迷你那斯達克指數",  "USD", nq_close),
        "TXF1": get_txf()
    }
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("data.json 已產出：", now.strftime("%Y-%m-%d %H:%M"))
