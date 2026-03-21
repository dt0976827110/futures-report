import json
import datetime
import os
import sys
import requests
from openai import OpenAI

# Try to import yfinance for GitHub Actions, or use a simple request if not available
try:
    import yfinance as yf
except ImportError:
    # In GitHub Actions, we'll install it in the workflow
    yf = None

def fetch_futures_data():
    # Mapping Yahoo Finance symbols to our report keys
    symbols_map = {
        'YM=F': 'YM1',
        'NQ=F': 'NQ1',
        '^TWII': 'TXF1'
    }
    
    results = {}
    for sym, key in symbols_map.items():
        try:
            if yf:
                ticker = yf.Ticker(sym)
                info = ticker.info
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                    high = hist['High'].iloc[-1]
                    low = hist['Low'].iloc[-1]
                    volume = hist['Volume'].iloc[-1]
                else:
                    current_price = info.get('regularMarketPrice', 0)
                    previous_close = info.get('previousClose', 0)
                    high = info.get('dayHigh', current_price * 1.01)
                    low = info.get('dayLow', current_price * 0.99)
                    volume = info.get('volume', 0)
            else:
                # Fallback or mock if yfinance is not available (should be installed in GH Actions)
                current_price, previous_close, high, low, volume = 0, 0, 0, 0, 0

            change_points = current_price - previous_close
            change_percent = (change_points / previous_close * 100) if previous_close else 0
            
            # Simple support/resistance calculation (Pivot Points)
            pivot = (high + low + current_price) / 3
            resistance = 2 * pivot - low
            support = 2 * pivot - high

            results[key] = {
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "change_points": round(change_points, 2),
                "change_percent": round(change_percent, 2),
                "volume": f"{int(volume):,}",
                "currency": "USD" if key != "TXF1" else "TWD",
                "support": round(support, 2),
                "resistance": round(resistance, 2)
            }
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            results[key] = {
                "current_price": 0, "previous_close": 0, "change_points": 0, "change_percent": 0,
                "volume": "0", "currency": "USD" if key != "TXF1" else "TWD", "support": 0, "resistance": 0
            }
            
    return results

def get_ai_analysis(futures_data):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found. Using mock analysis.")
        return generate_mock_report(futures_data)
        
    client = OpenAI(api_key=api_key)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    今天是 {today}。請根據以下期貨數據和當前國際金融局勢（中東局勢緊張、油價波動、美債收益率上升、TSMC 財報指引等），生成一份專業的國際金融期貨日報。
    
    期貨數據：
    {json.dumps(futures_data, indent=2)}
    
    請嚴格按照以下 JSON 格式輸出，不要有任何額外文字或 Markdown 符號：
    {{
      "report_date": "{today}",
      "report_time": "{today} 06:00 (台灣時間)",
      "last_update": "{today} 06:00 (台灣時間)",
      "futures_data": {{
        "YM1": {{ "name": "E-迷你道瓊指數", ... }},
        "NQ1": {{ "name": "E-迷你那斯達克100指數", ... }},
        "TXF1": {{ "name": "台指期", ... }}
      }},
      "yesterday_analysis": {{
        "title": "昨日走勢分析",
        "events": [ {{ "title": "...", "description": "..." }} ],
        "economic_data": [ {{ "indicator": "...", "actual": "...", "forecast": "...", "previous": "...", "impact": "...", "note": "..." }} ]
      }},
      "futures_analysis": {{
        "YM1": {{ "name": "小道瓊", "points": [ {{ "title": "...", "detail": "..." }}, {{ "title": "...", "detail": "..." }} ] }},
        "NQ1": {{ "name": "小那斯達克", "points": [ ... ] }},
        "TXF1": {{ "name": "台指期", "points": [ ... ] }}
      }},
      "today_probability": {{
        "title": "今日走勢機率評估",
        "summary": "...",
        "YM1": {{ "up_probability": "XX%", "down_probability": "XX%", "sideways_probability": "XX%", "analysis": "..." }},
        "NQ1": {{ ... }},
        "TXF1": {{ ... }}
      }},
      "investment_advice": {{
        "short_term_strategy": ["...", "...", "...", "..."],
        "trading_opportunities": ["...", "...", "...", "..."],
        "risk_avoidance": ["...", "...", "...", "..."],
        "position_allocation": ["...", "...", "...", "..."]
      }},
      "conclusion": {{
        "summary": "...",
        "points": [ {{ "title": "...", "detail": "..." }}, {{ "title": "...", "detail": "..." }} ],
        "advice": "..."
      }},
      "news": [ {{ "title": "...", "description": "...", "impact": "...", "timestamp": "..." }} ],
      "risk_warning": {{
        "title": "風險提示",
        "items": [ {{ "title": "...", "detail": "..." }}, {{ "title": "...", "detail": "..." }}, {{ "title": "...", "detail": "..." }} ]
      }}
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Use a standard model name for general compatibility
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        return generate_mock_report(futures_data)

def generate_mock_report(futures_data):
    # Fallback mock report structure if AI fails
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return {
        "report_date": today,
        "report_time": f"{today} 06:00 (台灣時間)",
        "last_update": f"{today} 06:00 (台灣時間)",
        "futures_data": {
            "YM1": {"name": "E-迷你道瓊指數", **futures_data.get("YM1", {})},
            "NQ1": {"name": "E-迷你那斯達克100指數", **futures_data.get("NQ1", {})},
            "TXF1": {"name": "台指期", **futures_data.get("TXF1", {})}
        },
        "yesterday_analysis": {"title": "昨日走勢分析", "events": [], "economic_data": []},
        "futures_analysis": {"YM1": {"name": "小道瓊", "points": []}, "NQ1": {"name": "小那斯達克", "points": []}, "TXF1": {"name": "台指期", "points": []}},
        "today_probability": {"title": "今日走勢機率評估", "summary": "數據獲取失敗，請檢查 API 設置。", "YM1": {}, "NQ1": {}, "TXF1": {}},
        "investment_advice": {"short_term_strategy": [], "trading_opportunities": [], "risk_avoidance": [], "position_allocation": []},
        "conclusion": {"summary": "分析暫不可用。", "points": [], "advice": ""},
        "news": [],
        "risk_warning": {"title": "風險提示", "items": []}
    }

def generate_report():
    print("Fetching futures data...")
    raw_futures = fetch_futures_data()
    
    print("Generating AI analysis...")
    report = get_ai_analysis(raw_futures)
    
    # Ensure the futures_data in report uses the latest fetched values
    for key in ["YM1", "NQ1", "TXF1"]:
        if key in report["futures_data"] and key in raw_futures:
            report["futures_data"][key].update(raw_futures[key])
            report["futures_data"][key]["timestamp"] = report["report_time"]

    with open('report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("Report generated successfully.")

if __name__ == "__main__":
    generate_report()
