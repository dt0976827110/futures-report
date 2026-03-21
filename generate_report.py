import json
import datetime

def generate_report():
    # 讀取原始數據
    with open('raw_data.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    now = datetime.datetime.now()
    report_date = now.strftime("%Y-%m-%d")
    report_time = now.strftime("%Y-%m-%d %H:%M (台灣時間)")
    
    # 構造最終 JSON
    report = {
        "report_date": report_date,
        "report_time": report_time,
        "last_update": report_time,
        "futures_data": {
            "YM1": {
                "name": "E-迷你道瓊指數",
                "current_price": raw['futures']['YM1']['current_price'],
                "previous_close": raw['futures']['YM1']['previous_close'],
                "currency": "USD",
                "change_points": raw['futures']['YM1']['change_points'],
                "change_percent": raw['futures']['YM1']['change_percent'],
                "volume": raw['futures']['YM1']['volume'],
                "support": raw['futures']['YM1']['support'],
                "resistance": raw['futures']['YM1']['resistance'],
                "timestamp": report_time
            },
            "NQ1": {
                "name": "E-迷你那斯達克100指數",
                "current_price": raw['futures']['NQ1']['current_price'],
                "previous_close": raw['futures']['NQ1']['previous_close'],
                "currency": "USD",
                "change_points": raw['futures']['NQ1']['change_points'],
                "change_percent": raw['futures']['NQ1']['change_percent'],
                "volume": raw['futures']['NQ1']['volume'],
                "support": raw['futures']['NQ1']['support'],
                "resistance": raw['futures']['NQ1']['resistance'],
                "timestamp": report_time
            },
            "TXF1": {
                "name": "台指期",
                "current_price": raw['futures']['TXF1']['current_price'],
                "previous_close": raw['futures']['TXF1']['previous_close'],
                "currency": "TWD",
                "change_points": raw['futures']['TXF1']['change_points'],
                "change_percent": raw['futures']['TXF1']['change_percent'],
                "volume": raw['futures']['TXF1']['volume'],
                "support": raw['futures']['TXF1']['support'],
                "resistance": raw['futures']['TXF1']['resistance'],
                "timestamp": report_time
            }
        },
        "yesterday_analysis": {
            "title": "昨日走勢分析",
            "events": [
                { "title": "中東地緣政治緊張局勢升溫", "description": "伊朗局勢不穩引發市場對能源供應中斷的擔憂，避險情緒急劇升溫，導致美股三大指數大幅收跌。" },
                { "title": "聯準會官員言論影響降息預期", "description": "聯準會官員 Waller 表示雖然不急於降息，但也排除了升息可能，市場仍在消化高利率環境的持續時間。" }
            ],
            "economic_data": raw['economic_data']
        },
        "futures_analysis": {
            "YM1": {
                "name": "小道瓊",
                "points": [
                    { "title": "避險情緒主導", "detail": "地緣政治風險導致傳統藍籌股受壓，投資者轉向防禦性資產。" },
                    { "title": "利率敏感性", "detail": "強勁的就業數據令市場擔憂聯準會維持高利率更久，壓制道瓊指數表現。" }
                ]
            },
            "NQ1": {
                "name": "小那斯達克",
                "points": [
                    { "title": "科技股領跌", "detail": "高估值科技股對利率預期極為敏感，NQ1! 跌至六個月低點，顯示技術面轉弱。" },
                    { "title": "避險資金撤出", "detail": "市場恐慌情緒下，資金從高成長板塊撤出，導致那指跌幅大於道指。" }
                ]
            },
            "TXF1": {
                "name": "台指期",
                "points": [
                    { "title": "美股連動效應", "detail": "受美股特別是科技股重挫影響，台指期開盤即面臨巨大拋壓。" },
                    { "title": "外資調節壓力", "detail": "全球避險情緒升溫導致外資在台股市場進行部位調節，加劇跌勢。" }
                ]
            }
        },
        "today_probability": {
            "title": "今日走勢機率評估",
            "summary": "市場目前處於地緣政治恐慌與利率擔憂的雙重壓力下，短期格局偏空。",
            "YM1": {
                "up_probability": "20%",
                "down_probability": "60%",
                "sideways_probability": "20%",
                "analysis": "道指在 46000 關口失守後，技術面轉向空頭，需關注地緣政治是否有緩和跡象。"
            },
            "NQ1": {
                "up_probability": "15%",
                "down_probability": "70%",
                "sideways_probability": "15%",
                "analysis": "那指跌破關鍵支撐，短期內科技股拋售潮可能持續，下行壓力巨大。"
            },
            "TXF1": {
                "up_probability": "10%",
                "down_probability": "80%",
                "sideways_probability": "10%",
                "analysis": "受美股重挫影響，台指期今日大概率維持弱勢震盪，需防範進一步下探風險。"
            }
        },
        "investment_advice": {
            "short_term_strategy": ["建議觀望，不宜盲目抄底", "嚴格執行止損，保護本金安全", "關注避險資產如黃金、美元的表現", "利用反彈機會減持高槓桿部位"],
            "trading_opportunities": ["關注能源股與國防板塊的逆勢機會", "尋找超跌後的技術性反彈短線交易", "利用波動率指數 (VIX) 進行避險操作", "關注台幣匯率變動對台指期的影響"],
            "risk_avoidance": ["避開高估值且無實質業績支撐的科技股", "防範地緣政治衝突突然升級的極端風險", "注意流動性風險，避免在市場劇烈波動時重倉", "警惕聯準會官員突發的鷹派言論"],
            "position_allocation": ["降低整體持倉水位至 30% 以下", "增加現金比例，等待市場底部信號明確", "配置部分資金於防禦性高股息板塊", "適度配置反向型 ETF 進行部位對沖"]
        },
        "conclusion": {
            "summary": "全球市場進入避險模式，短期內期貨市場將維持高波動與下行趨勢。",
            "points": [
                { "title": "地緣政治為核心變數", "detail": "中東局勢的發展將直接決定市場情緒的修復速度。" },
                { "title": "技術面全面轉弱", "detail": "三大期貨均跌破關鍵均線，短期內需時間築底。" }
            ],
            "advice": "操作上應以保本為主，耐心等待市場情緒穩定後再行佈局。"
        },
        "news": raw['news'],
        "risk_warning": {
            "title": "風險提示",
            "items": [
                { "title": "地緣政治衝突擴大", "detail": "若中東衝突進一步升級，可能引發能源危機與全球股市崩盤。" },
                { "title": "通膨數據超預期", "detail": "若後續通膨數據反彈，聯準會可能重啟升息討論，對市場造成二次打擊。" },
                { "title": "系統性流動性風險", "detail": "市場劇烈波動可能引發連鎖平倉潮，導致流動性枯竭風險。" }
            ]
        }
    }
    
    # 輸出 JSON
    with open('report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("Report generated successfully.")

if __name__ == "__main__":
    generate_report()
