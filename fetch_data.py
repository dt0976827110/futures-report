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

debug_log = {"fetch_time": now.strftime("%Y-%m-%d %H:%M (台灣時間)")}

def get_hourly(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1h&range=10d"
        res = requests.get(url, headers=HEADERS, timeout=10)
        result = res.json()["chart"]["result"][0]
        quotes = result["indicators"]["quote"][0]
        timestamps = result["timestamp"]
        closes  = quotes["close"]
        volumes = quotes.get("volume", [0] * len(closes))

        rows = []
        for t, c, v in zip(timestamps, closes, volumes):
            if c is None:
                continue
            dt_utc = datetime.utcfromtimestamp(t)
            dt_tw  = datetime.utcfromtimestamp(t + 8*3600)
            rows.append({
                "datetime_utc": dt_utc.strftime('%Y-%m-%d %H:%M'),
                "datetime_tw":  dt_tw.strftime('%Y-%m-%d %H:%M'),
                "close": round(c, 2),
                "volume": v
            })
        return rows
    except Exception as e:
        return {"error": str(e)}

debug_log["YM_hourly"] = get_hourly("YM=F")
debug_log["NQ_hourly"] = get_hourly("NQ=F")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump({}, f)

with open("debug_log.json", "w", encoding="utf-8") as f:
    json.dump(debug_log, f, ensure_ascii=False, indent=2)

print("debug_log.json 已產出：", now.strftime("%Y-%m-%d %H:%M"))
