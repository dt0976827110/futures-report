import json
import datetime
import os
import yfinance as yf
from openai import OpenAI

# 初始化 OpenAI 客戶端
client = OpenAI()

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
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                previous_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                high = hist['High'].iloc[-1]
                low = hist['Low'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                
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
                    "support": round(support, 2),
                    "resistance": round(resistance, 2)
                }
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            
    return results

def get_analysis_from_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "你是一位專業的國際金融分析師。請根據提供的數據生成專業的 JSON 報告。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def main():
    # 獲取當前時間 (台灣時間 GMT+8)
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    report_date = now.strftime("%Y-%m-%d")
    report_time = now.strftime("%Y-%m-%d %H:%M (台灣時間)")
    
    print("Fetching market data...")
    futures_data = fetch_futures_data()
    
    # 外部背景資訊
    context = """
    日期：2026-03-20 (昨日)
    重大事件：
    1. 伊朗戰爭升級：伊朗襲擊科威特煉油廠，以色列擊斃伊朗革命衛隊發言人。
    2. 油價飆升：布蘭特原油維持在 100 美元以上，高盛警告若衝突持續可能突破歷史新高。
    3. 聯準會 (Fed) 動向：3月18日會議維持利率 3.5%-3.75% 不變，但鮑爾表示通膨壓力仍大，點陣圖顯示降息預期減少。
    4. 市場表現：美股三大指數連跌四周，道指與納指逼近回調區間。
    """

    prompt = f"""
    請根據以下數據生成一份專業的國際金融期貨日報 JSON 報告。
    
    期貨數據：{json.dumps(futures_data)}
    背景資訊：{context}
    
    JSON 格式必須嚴格遵守以下結構，不可更改欄位名稱：
    {{
      "report_date": "{report_date}",
      "report_time": "{report_time}",
      "last_update": "{report_time}",
      "futures_data": {{
        "YM1": {{
          "name": "E-迷你道瓊指數",
          "current_price": 數字,
          "previous_close": 數字,
          "currency": "USD",
          "change_points": 數字,
          "change_percent": 數字,
          "volume": "字串",
          "support": 數字,
          "resistance": 數字,
          "timestamp": "{report_time}"
        }},
        "NQ1": {{
          "name": "E-迷你那斯達克100",
          "current_price": 數字,
          "previous_close": 數字,
          "currency": "USD",
          "change_points": 數字,
          "change_percent": 數字,
          "volume": "字串",
          "support": 數字,
          "resistance": 數字,
          "timestamp": "{report_time}"
        }},
        "TXF1": {{
          "name": "台指期",
          "current_price": 數字,
          "previous_close": 數字,
          "currency": "TWD",
          "change_points": 數字,
          "change_percent": 數字,
          "volume": "字串",
          "support": 數字,
          "resistance": 數字,
          "timestamp": "{report_time}"
        }}
      }},
      "yesterday_analysis": {{
        "title": "昨日走勢分析",
        "events": [ {{ "title": "事件標題", "description": "詳細說明" }} ],
        "economic_data": [ {{ "indicator": "指標名稱", "actual": "實際值", "forecast": "預測值", "previous": "前值", "impact": "正面/負面/中性", "note": "簡短備註" }} ]
      }},
      "futures_analysis": {{
        "YM1": {{ "name": "小道瓊", "points": [ {{ "title": "驅動因素標題", "detail": "詳細說明" }}, {{ "title": "驅動因素標題", "detail": "詳細說明" }} ] }},
        "NQ1": {{ "name": "小那斯達克", "points": [ {{ "title": "驅動因素標題", "detail": "詳細說明" }}, {{ "title": "驅動因素標題", "detail": "詳細說明" }} ] }},
        "TXF1": {{ "name": "台指期", "points": [ {{ "title": "驅動因素標題", "detail": "詳細說明" }}, {{ "title": "驅動因素標題", "detail": "詳細說明" }} ] }}
      }},
      "today_probability": {{
        "title": "今日走勢機率評估",
        "summary": "整體市場格局一句話總結",
        "YM1": {{ "up_probability": "XX%", "down_probability": "XX%", "sideways_probability": "XX%", "analysis": "核心理由說明" }},
        "NQ1": {{ "up_probability": "XX%", "down_probability": "XX%", "sideways_probability": "XX%", "analysis": "核心理由說明" }},
        "TXF1": {{ "up_probability": "XX%", "down_probability": "XX%", "sideways_probability": "XX%", "analysis": "核心理由說明" }}
      }},
      "investment_advice": {{
        "short_term_strategy": ["建議1", "建議2", "建議3", "建議4"],
        "trading_opportunities": ["機會1", "機會2", "機會3", "機會4"],
        "risk_avoidance": ["風險1", "風險2", "風險3", "風險4"],
        "position_allocation": ["配置1", "配置2", "配置3", "配置4"]
      }},
      "conclusion": {{
        "summary": "整體市場結論摘要",
        "points": [ {{ "title": "結論標題", "detail": "詳細說明" }}, {{ "title": "結論標題", "detail": "詳細說明" }} ],
        "advice": "操作建議一段話"
      }},
      "news": [ {{ "title": "新聞標題", "description": "摘要50字內", "impact": "高/中/低", "timestamp": "YYYY-MM-DD (台灣時間)" }} ],
      "risk_warning": {{
        "title": "風險提示",
        "items": [ {{ "title": "風險標題", "detail": "詳細說明" }}, {{ "title": "風險標題", "detail": "詳細說明" }}, {{ "title": "風險標題", "detail": "詳細說明" }} ]
      }}
    }}
    
    請確保輸出為純 JSON，不要有任何多餘文字。
    """
    
    print("Generating report via AI...")
    report_json = get_analysis_from_llm(prompt)
    
    # 寫入文件
    with open('report.json', 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    
    print("Report generated successfully.")

if __name__ == "__main__":
    main()
