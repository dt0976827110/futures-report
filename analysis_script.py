import os
import json
import datetime
from openai import OpenAI

def generate_report():
    # 1. 準備期貨數據 (根據 2026-03-21 實測數據)
    # 數據來源：TradingView 2026-03-21 13:22 GMT+8 觀察值
    futures_data = {
        "YM1": {
            "name": "E-迷你道瓊指數",
            "current_price": 45893.0,
            "previous_close": 46341.0,
            "currency": "USD",
            "change_points": -448.0,
            "change_percent": -0.97,
            "volume": "154.22K",
            "support": 45500.0,
            "resistance": 46200.0,
            "timestamp": "2026-03-21 13:22 (台灣時間)"
        },
        "NQ1": {
            "name": "E-迷你那斯達克100",
            "current_price": 24101.5,
            "previous_close": 24580.0,
            "currency": "USD",
            "change_points": -478.5,
            "change_percent": -1.95,
            "volume": "584.46K",
            "support": 23800.0,
            "resistance": 24400.0,
            "timestamp": "2026-03-21 13:22 (台灣時間)"
        },
        "TXF1": {
            "name": "台指期",
            "current_price": 32737.0,
            "previous_close": 33559.0,
            "currency": "TWD",
            "change_points": -822.0,
            "change_percent": -2.45,
            "volume": "266.30K",
            "support": 32400.0,
            "resistance": 33200.0,
            "timestamp": "2026-03-21 13:22 (台灣時間)"
        }
    }
    
    # 2. 準備昨日經濟數據與事件背景
    context_data = {
        "date": "2026-03-20",
        "economic_indicators": [
            {"indicator": "美國聯準會(Fed)通膨預期", "actual": "2.7%", "forecast": "2.4%", "previous": "2.4%", "impact": "負面", "note": "Fed上調通膨預期，引發市場對高利率維持更久的擔憂。"},
            {"indicator": "美國GDP增長預測", "actual": "2.1%", "forecast": "2.3%", "previous": "2.3%", "impact": "負面", "note": "受戰爭影響，經濟增長預期遭到下修。"},
            {"indicator": "全球原油價格 (WTI)", "actual": "$92.5", "forecast": "$88.0", "previous": "$87.5", "impact": "負面", "note": "中東局勢緊張導致油價飆升，加劇通膨壓力。"}
        ],
        "major_events": [
            "伊朗戰爭持續，波斯灣能源基礎設施遭到攻擊，引發全球供應鏈中斷擔憂。",
            "以色列與伊朗衝突升級，市場避險情緒極度高漲，資金流向黃金與美元。",
            "聯準會官員發表鷹派言論，強調在通膨未見明顯回落前不會降息。"
        ]
    }

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    report_date = now.strftime("%Y-%m-%d")
    report_time = now.strftime("%Y-%m-%d %H:%M (台灣時間)")
    
    client = OpenAI()
    
    prompt = f"""
    請扮演專業的國際金融分析師，針對昨日（{context_data['date']}）的市場走勢生成一份分析報告。
    
    已知期貨數據 (引用自 TradingView)：
    {json.dumps(futures_data, ensure_ascii=False, indent=2)}
    
    昨日背景資訊：
    - 經濟數據：{json.dumps(context_data['economic_indicators'], ensure_ascii=False)}
    - 重大事件：{json.dumps(context_data['major_events'], ensure_ascii=False)}
    
    請根據以上資訊，生成完整的 JSON 報告。
    
    要求：
    1. 【走勢分析】針對每個期貨獨立分析昨晚走勢原因，每個期貨提供 2 個驅動因素。
    2. 【機率評估】評估今日（{report_date}）三大期貨上漲/下跌/震盪的概率。
    3. 【投資建議】短期策略、交易機會、風險規避、倉位配置（各4條）。
    4. 【分析結論】整體市場結論摘要、2 個重點結論、以及操作建議一段話。
    5. 【風險提示】列出 3 個獨立風險因素。
    6. 【新聞摘要】收錄 4-5 則重要新聞，每則包含標題、50字以內摘要、影響程度（高/中/低）、時間（格式：YYYY-MM-DD）。
    
    輸出格式必須嚴格遵守以下 JSON 結構，不要有任何多餘文字或 Markdown 符號：
    {{
      "report_date": "{report_date}",
      "report_time": "{report_time}",
      "last_update": "{report_time}",
      "futures_data": {{ ...已提供數據... }},
      "yesterday_analysis": {{
        "title": "昨日走勢分析",
        "events": [ {{ "title": "...", "description": "..." }} ],
        "economic_data": [ {{ "indicator": "...", "actual": "...", "forecast": "...", "previous": "...", "impact": "...", "note": "..." }} ]
      }},
      "futures_analysis": {{
        "YM1": {{ "name": "小道瓊", "points": [ {{ "title": "...", "detail": "..." }} ] }},
        "NQ1": {{ ... }},
        "TXF1": {{ ... }}
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
        "points": [ {{ "title": "...", "detail": "..." }} ],
        "advice": "..."
      }},
      "news": [ {{ "title": "...", "description": "...", "impact": "...", "timestamp": "..." }} ],
      "risk_warning": {{
        "title": "風險提示",
        "items": [ {{ "title": "...", "detail": "..." }} ]
      }}
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的金融分析機器人，只輸出純 JSON 格式，不包含任何 Markdown 標籤或多餘文字。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    report_json = json.loads(response.choices[0].message.content)
    
    # 確保期貨數據與時間戳記正確
    report_json["futures_data"] = futures_data
    report_json["report_date"] = report_date
    report_json["report_time"] = report_time
    report_json["last_update"] = report_time
    
    # 寫入文件
    output_path = "/home/ubuntu/futures-report/report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    
    print(f"Report generated successfully at {output_path}")

if __name__ == "__main__":
    generate_report()
