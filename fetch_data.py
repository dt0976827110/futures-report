import json
import requests
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

def get_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    return res.json()["chart"]["result"][0]["meta"]

def get_futures(symbol, name, currency):
    try:
        d = get_yahoo(symbol)
        current = round(d["regularMarketPrice"], 2)
        prev = round(d["previousClose"], 2)
        change_pts = round(current - prev, 2)
        change_pct = round((change_pts / prev) * 100, 2)
        return {
            "name": name,
            "current_price": current,
            "previous_close": prev,
            "currency": currency,
            "change_points": change_pts,
            "change_percent": change_pct,
            "volume": str(d.get("regularMarketVolume", 0)),
            "support": round(prev * 0.99, 0),
            "resistance": round(prev * 1.01, 0),
            "support_basis": "前收盤價 -1% 估算",
            "resistance_basis": "前收盤價 +1% 估算",
            "timestamp": now.strftime("%Y-%m-%d %H:%M (台灣時間)")
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
                return {
                    "name": "台灣加權指數期貨",
                    "current_price": current,
                    "previous_close": prev,
                    "currency": "TWD",
                    "change_points": change_pts,
                    "change_percent": change_pct,
                    "volume": volume,
                    "support": round(prev * 0.99, 0),
                    "resistance": round(prev * 1.01, 0),
                    "support_basis": "前收盤價 -1% 估算",
                    "resistance_basis": "前收盤價 +1% 估算",
                    "timestamp": now.strftime("%Y-%m-%d %H:%M (台灣時間)")
                }
        return {"error": "找不到TX資料"}
    except Exception as e:
        return {"error": str(e)}

def get_vix():
    try:
        d = get_yahoo("%5EVIX")
        current = round(d["regularMarketPrice"], 2)
        prev = round(d["chartPreviousClose"], 2)
        change = round(current - prev, 2)
        sign = "+" if change >= 0 else ""
        level = "低" if current < 15 else "中" if current < 20 else "高" if current < 30 else "極高"
        return {
            "value": current,
            "change": f"{sign}{change}",
            "level": level,
            "note": f"VIX 目前 {current}，市場波動{level}。"
        }
    except Exception as e:
        return {"error": str(e)}

def get_dxy():
    try:
        d = get_yahoo("DX-Y.NYB")
        current = round(d["regularMarketPrice"], 2)
        prev = round(d["previousClose"], 2)
        direction = "↑" if current >= prev else "↓"
        return {
            "value": current,
            "direction": direction,
            "note": f"美元指數 {current}，趨勢{'走強' if direction == '↑' else '走弱'}。"
        }
    except Exception as e:
        return {"error": str(e)}

def get_oil():
    try:
        d = get_yahoo("BZ%3DF")
        current = round(d["regularMarketPrice"], 2)
        prev = round(d["previousClose"], 2)
        direction = "↑" if current >= prev else "↓"
        return {
            "value": current,
            "direction": direction,
            "note": f"布蘭特原油 {current} 美元，趨勢{'上漲' if direction == '↑' else '下跌'}。"
        }
    except Exception as e:
        return {"error": str(e)}

data = {
    "fetch_time": now.strftime("%Y-%m-%d %H:%M (台灣時間)"),
    "market_sentiment": {
        "vix": get_vix(),
        "dxy": get_dxy(),
        "oil_brent": get_oil()
    },
    "futures_data": {
        "YM1": get_futures("YM=F", "E-迷你道瓊指數", "USD"),
        "NQ1": get_futures("NQ=F", "E-迷你那斯達克指數", "USD"),
        "TXF1": get_txf()
    }
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("data.json 已產出：", now.strftime("%Y-%m-%d %H:%M"))
