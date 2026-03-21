import os
import json
import datetime
import sys
from openai import OpenAI
sys.path.append('/opt/.manus/.sandbox-runtime')
from data_api import ApiClient

def get_futures_data():
    client = ApiClient()
    symbols = {
        "YM1": "YM=F",
        "NQ1": "NQ=F",
        "TXF1": "IX0126.TW"
    }
    
    results = {}
    for key, symbol in symbols.items():
        try:
            response = client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'region': 'US' if key != "TXF1" else 'TW',
                'interval': '1d',
                'range': '5d',
                'includeAdjustedClose': True
            })
            
            if response and 'chart' in response and 'result' in response['chart']:
                result = response['chart']['result'][0]
                meta = result['meta']
                
                # 提取數據
                current_price = meta.get('regularMarketPrice', 0)
                previous_close = meta.get('previousClose', 0)
                change_points = current_price - previous_close
                change_percent = (change_points / previous_close * 100) if previous_close != 0 else 0
                volume = str(meta.get('regularMarketVolume', 'N/A'))
                
                # 簡單計算支撐阻力位 (這裡用 5 日高低點作為模擬)
                quotes = result['indicators']['quote'][0]
                highs = [h for h in quotes['high'] if h is not None]
                lows = [l for l in quotes['low'] if l is not None]
                resistance = max(highs) if highs else current_price * 1.01
                support = min(lows) if lows else current_price * 0.99
                
                results[key] = {
                    "name": "E-迷你道瓊指數" if key == "YM1" else ("E-迷你那斯達克100" if key == "NQ1" else "台指期"),
                    "current_price": round(current_price, 2),
                    "previous_close": round(previous_close, 2),
                    "currency": "USD" if key != "TXF1" else "TWD",
                    "change_points": round(change_points, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": volume,
                    "support": round(support, 2),
                    "resistance": round(resistance, 2),
                    "timestamp": (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M (台灣時間)")
                }
        except Exception as e:
            print(f"Error fetching {key}: {e}")
            results[key] = {"error": str(e)}
            
    return results

def generate_report():
    # 1. 獲取真實期貨數據
    futures_data = get_futures_data()
    
    # 2. 獲取當前時間 (GMT+8)
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    report_date = now.strftime("%Y-%m-%d")
    report_time = now.strftime("%Y-%m-%d %H:%M (台灣時間)")
    
    # 3. 調用 AI 進行分析與生成其餘 JSON 內容
    client = OpenAI()
    
    prompt = f"""
    請扮演專業的國際金融分析師，針對昨日的市場走勢生成一份分析報告。
    當前日期：{report_date}
    
    已知期貨數據：
    {json.dumps(futures_data, ensure_ascii=False, indent=2)}
    
    請根據以上數據及昨日（{report_date} 之前一天）的全球金融事件，生成完整的 JSON 報告。
    
    要求：
    1. 【數據收集】抓取昨日重要經濟數據（至少3-5筆），包含指標名稱、實際值、預測值、前值、影響方向、簡短備註。
    2. 【走勢分析】針對每個期貨獨立分析昨晚走勢原因，每個期貨提供 2 個驅動因素，各自附上標題與詳細說明。
    3. 【機率評估】評估三大期貨上漲/下跌/震盪的概率，並提供核心理由，同時給出整體市場格局的一句話總結。
    4. 【投資建議】生成短期策略、交易機會、風險規避、倉位配置四類建議，每類至少 4 條。
    5. 【分析結論】提供整體市場結論摘要、2 個重點結論、以及操作建議一段話。
    6. 【風險提示】列出 3 個獨立風險因素。
    7. 【新聞摘要】收錄 4-5 則重要新聞，每則包含標題、50字以內摘要、影響程度、時間。
    
    輸出格式必須嚴格遵守以下 JSON 結構，不要有任何多餘文字、說明或 markdown 符號：
    {{
      "report_date": "{report_date}",
      "report_time": "{report_time}",
      "last_update": "{report_time}",
      "futures_data": {json.dumps(futures_data, ensure_ascii=False)},
      "yesterday_analysis": {{
        "title": "昨日走勢分析",
        "events": [ {{ "title": "事件標題", "description": "詳細說明" }} ],
        "economic_data": [ {{ "indicator": "指標名稱", "actual": "實際值", "forecast": "預測值", "previous": "前值", "impact": "正面/負面/中性", "note": "簡短備註" }} ]
      }},
      "futures_analysis": {{
        "YM1": {{ "name": "小道瓊", "points": [ {{ "title": "驅動因素標題", "detail": "詳細說明" }} ] }},
        "NQ1": {{ ... }},
        "TXF1": {{ ... }}
      }},
      "today_probability": {{
        "title": "今日走勢機率評估",
        "summary": "整體市場格局一句話總結",
        "YM1": {{ "up_probability": "XX%", "down_probability": "XX%", "sideways_probability": "XX%", "analysis": "核心理由說明" }},
        "NQ1": {{ ... }},
        "TXF1": {{ ... }}
      }},
      "investment_advice": {{
        "short_term_strategy": ["建議1", "建議2", "建議3", "建議4"],
        "trading_opportunities": [...],
        "risk_avoidance": [...],
        "position_allocation": [...]
      }},
      "conclusion": {{
        "summary": "整體市場結論一句話",
        "points": [ {{ "title": "結論標題", "detail": "詳細說明" }} ],
        "advice": "操作建議一段話"
      }},
      "news": [ {{ "title": "新聞標題", "description": "新聞摘要50字以內", "impact": "高", "timestamp": "YYYY-MM-DD (台灣時間)" }} ],
      "risk_warning": {{
        "title": "風險提示",
        "items": [ {{ "title": "風險標題", "detail": "詳細說明" }} ]
      }}
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的金融分析機器人，只輸出 JSON 格式。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    report_json = json.loads(response.choices[0].message.content)
    
    # 確保 futures_data 是最新的
    report_json["futures_data"] = futures_data
    report_json["report_date"] = report_date
    report_json["report_time"] = report_time
    report_json["last_update"] = report_time
    
    # 保存為 report.json
    with open("/home/ubuntu/futures-report/report.json", "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    
    print("Report generated successfully.")

if __name__ == "__main__":
    generate_report()
