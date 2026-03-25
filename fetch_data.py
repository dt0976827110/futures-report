import json
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

TW = timezone(timedelta(hours=8))
now = datetime.now(TW)

def get_futures(symbol, name, currency):
    try:
        t = yf.Ticker(symbol)
        info = t.fast_info
        current = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
        change_pts = round(current - prev, 2)
        change_pct = round((change_pts / prev) * 100, 2)
        return {
            "name": name,
            "current_price": current,
            "previous_close": prev,
            "currency": currency,
            "change_points": change_pts,
            "change_percent": change_pct,
            "volume": str(int(info.three_month_average_volume or 0)),
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
        url = "https://www.taifex.com.tw/cht/3/futContractsDate"
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tr")
        for i, row in enumerate(rows[:20]):
            cols = [td.get_text(strip=True) for td in row.select("td")]
            if cols:
                print(f"Row {i}: {cols}")
        return {"error": "debug mode"}
    except Exception as e:
        return {"error": str(e)}

def get_vix():
    try:
        t = yf.Ticker("^VIX")
        info = t.fast_info
        current = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
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
        t = yf.Ticker("DX-Y.NYB")
        info = t.fast_info
        current = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
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
        t = yf.Ticker("BZ=F")
        info = t.fast_info
        current = round(info.last_price, 2)
        prev = round(info.previous_close, 2)
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
