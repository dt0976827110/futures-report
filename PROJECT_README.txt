════════════════════════════════════════════════════════════════
  國際金融期貨日報系統 — 完整說明文件
  futures-report
  最後更新：2026-03-27
════════════════════════════════════════════════════════════════

────────────────────────────────────────
  系統概述
────────────────────────────────────────
每天自動產出一份包含小道瓊（YM1!）、小那斯達克（NQ1!）、
台指期（TXF1!）的專業期貨分析報告，發佈到 GitHub Pages 網站。

核心原則：
- 點位與技術指標由程式抓取計算，確保數據準確
- YM/NQ 收盤價由 TradingView Alert 即時推送，解決來源延遲問題
- 台指期五日歷史由 TAIFEX 官網 POST 請求抓取
- 分析文字由 AI（Manus）撰寫，確保內容有彈性


────────────────────────────────────────
  檔案結構
────────────────────────────────────────

futures-report/
│
├── .github/
│   └── workflows/
│       └── fetch_data.yml      ← GitHub Actions 設定
│                                  只保留 workflow_dispatch
│                                  由 GAS 觸發，不自動排程
│
├── fetch_data.py               ← 爬蟲主腳本
│                                  抓取期貨點位、技術指標
│                                  讀取 YMNQ_data.json 覆蓋收盤價
│                                  產出 data.json + debug_log.json
│
├── data.json                   ← 爬蟲每天自動產出的數據檔
│                                  包含準確點位與技術指標
│                                  供 Manus 讀取使用
│
├── YMNQ_data.json              ← TradingView 推送的收盤價
│                                  由 GAS 接收 TV Alert 後寫入
│                                  包含 YM1 / NQ1 的昨日收盤
│
├── debug_log.json              ← 爬蟲原始抓取資料記錄
│                                  包含歷史收盤、原始 API 數值
│                                  用於確認資料正確性
│
├── template.json               ← report.json 的格式範本
│                                  定義所有欄位名稱與結構
│                                  Manus 參照此格式輸出報告
│
├── report.json                 ← Manus 每天產出的分析報告
│                                  由 Manus 自動推送更新
│                                  網站讀取此檔案顯示報告
│
├── index.html                  ← 報告網站前端
│                                  讀取 report.json 並顯示
│                                  已部署到 GitHub Pages
│
└── CNAME                       ← 自訂網域設定


────────────────────────────────────────
  每日自動流程
────────────────────────────────────────

  美東時間 17:00（台灣時間 06:00）
  美股期貨日盤收盤
       ↓
  TradingView Alert 觸發（YM1! / NQ1! 日K圖）
  barstate.isconfirmed 偵測到K棒收盤
  推送收盤價到 GAS Webhook
       ↓
  GAS doPost 接收數據
  - YM 到達 → C2=1，C3=YM資料（JSON）
  - NQ 到達 → D2=1，D3=NQ資料（JSON）
  - 兩個都到齊 → 推送 YMNQ_data.json 到 GitHub
                  清空 C3 D3
  - 核對 A2 設定時間（5分鐘內）
  - 時間到 → 觸發 GitHub Actions，清空 C2 D2
  - 設定明天時間到 B2，更新觸發條件
       ↓
  GitHub Actions 執行 fetch_data.py
  - 讀取 YMNQ_data.json 取得 YM/NQ 正確收盤價
  - YMNQ time（UTC）+1天 = 台灣日期，補進五日歷史
  - 從 Yahoo Finance 抓取歷史資料、技術指標
  - 從 TAIFEX POST 請求抓取台指期點位與五日歷史
  - 用 ^TWII 計算台指期技術指標
  - 產出 data.json + debug_log.json 推送到 GitHub
       ↓
  Manus 排程執行（設定在爬蟲觸發後）
  - 讀取 data.json（準確數據）
  - 讀取 template.json（輸出格式）
  - 自行搜尋：昨日新聞、經濟數據、市場事件
  - 撰寫分析報告
  - 按 template.json 格式推送 report.json 到 GitHub
       ↓
  報告網站自動顯示最新報告


────────────────────────────────────────
  Google Sheet 定時器說明
────────────────────────────────────────

Sheet 名稱：分析報告定時器
分頁名稱：設定

欄位說明：
  A2  執行時間（格式：HHMM，例如 0700 = 早上 7 點）
  B1  標題「下次執行時間」
  B2  下次 GAS 定時觸發的台灣時間（自動更新）
  C1  標題「YM到達」
  C2  YM 收盤是否已到達（0=未到，1=已到）
  C3  YM 收盤資料（JSON，兩個都到後推送並清空）
  D1  標題「NQ到達」
  D2  NQ 收盤是否已到達（0=未到，1=已到）
  D3  NQ 收盤資料（JSON，兩個都到後推送並清空）


────────────────────────────────────────
  GAS 腳本函式說明
────────────────────────────────────────

doPost(e)
  TV Webhook 接收函式
  接收 YM / NQ 收盤資料，存到 C2/C3 或 D2/D3
  兩個都到齊後推送 YMNQ_data.json，清空 C3 D3
  核對時間後觸發爬蟲，清空 C2 D2

checkAndFire()
  檢查 C2 D2 是否都是 1
  推送 YMNQ_data.json 並清空 C3 D3
  且現在時間在 A2 設定時間的 5 分鐘內
  條件達成則觸發爬蟲，清空 C2 D2，設定明天時間

isTimeReached()
  判斷現在台灣時間是否在 A2 設定時間的 5 分鐘內

triggerGithubActions()
  呼叫 GitHub API 觸發 fetch_data.yml（workflow_dispatch）

scheduledTrigger()
  定時觸發（備用）
  TV Alert 沒送來時的保底機制
  時間到且 C2 D2 都是 1 才觸發爬蟲
  執行後自動呼叫 setDailyTrigger()

setDailyTrigger()
  讀取 A2 時間，設定明天那個時間的觸發條件
  觸發爬蟲後自動呼叫，確保每天循環

showNextTriggerTime()
  讀取下次觸發時間顯示到 B2

cleanAndReset()
  清除所有舊觸發條件並重新設定
  首次設定或有問題時手動執行

testYM() / testNQ()
  模擬 TV 送資料進來，測試用


────────────────────────────────────────
  fetch_data.py 資料來源說明
────────────────────────────────────────

YM1!（小道瓊）
  current_price：YMNQ_data.json 的 YM1.close
                 （TV 推送的昨日日盤收盤價）
  previous_close：Yahoo Finance YM=F 歷史資料 closes[-2]
                  （前天日盤收盤價）
  五日歷史：Yahoo Finance 歷史 + YMNQ 補最新一天
            YMNQ time（UTC）+1天 = 台灣收盤日期
  技術指標：Yahoo Finance YM=F 歷史資料（6個月）+ YMNQ close

NQ1!（小那指）
  same as YM1，使用 NQ=F

TXF1!（台指期）
  current_price：TAIFEX 官網 futDailyMarketReport（POST）
                 06:00 前 = 夜盤收盤（05:00）
                 13:45 後 = 日盤收盤（13:45）
  previous_close：current - 漲跌點（反推）
  五日歷史：TAIFEX 官網 futDailyMarketReport（POST）
            往前找最近 5 個交易日，各自送一次 POST 請求
  技術指標：Yahoo Finance ^TWII 歷史資料（6個月）
            加權指數趨勢方向與台指期高度一致

VIX：Yahoo Finance ^VIX（regularMarketPrice）
DXY：Yahoo Finance DX-Y.NYB
布蘭特原油：Yahoo Finance BZ=F


────────────────────────────────────────
  技術指標說明
────────────────────────────────────────

RSI14     相對強弱指標（14日）
MA5       5日均線
MA20      20日均線
MA60      60日均線
MACD      MACD 值（12/26/9）
MACD Signal  Signal 線
MACD Histogram  柱狀圖
BB Upper  布林通道上軌（20日，2倍標準差）
BB Middle 布林通道中軌
BB Lower  布林通道下軌
ATR14     平均真實波幅（14日）
Volume MA5  成交量 5日均量


────────────────────────────────────────
  TradingView Alert 設定
────────────────────────────────────────

指標名稱：收盤價推送
圖表時間框架：日K
觸發條件：barstate.isconfirmed（K棒收盤確認）
觸發設定：每根K線收盤時觸發一次

需掛 Alert 的商品：
  YM1!（小道瓊）
  NQ1!（小那斯達克）

Webhook URL：GAS Web App 部署 URL
訊息格式：
  {"symbol":"{{ticker}}","close":{{close}},
   "high":{{high}},"low":{{low}},
   "volume":{{volume}},"time":"{{time}}"}

注意：TXF1 不需要掛 Alert，直接從 TAIFEX 抓取


────────────────────────────────────────
  Manus 排程設定
────────────────────────────────────────

執行時間：設定在爬蟲觸發後約 10-15 分鐘
Prompt 讀取：
  data.json    → 準確數據來源
  template.json → 輸出格式

Manus 負責：
  - 讀取 data.json 的準確數據（不自行查詢點位）
  - 自行搜尋昨日新聞、經濟數據
  - 撰寫走勢分析、機率評估、投資建議
  - 按 template.json 格式輸出 report.json
  - 推送到 GitHub

Manus 不負責：
  - 查詢任何點位（全部由 data.json 提供）
  - 計算任何技術指標（全部由 data.json 提供）


────────────────────────────────────────
  常見問題排解
────────────────────────────────────────

Q：YMNQ_data.json 沒有更新？
A：確認 TV Alert 有觸發（TV 通知欄查看）
   確認 GAS doPost 有執行（Apps Script 執行記錄）
   確認 GAS Web App URL 跟 TV Webhook URL 一致

Q：data.json 沒有更新？
A：確認 GitHub Actions 有成功執行
   去 Actions 頁面查看最新一次執行狀態

Q：TXF1 顯示 error？
A：TAIFEX 網站可能維護中或格式有變動
   手動跑一次 Actions 重試
   查看 debug_log.json 的 TXF1_taifex 欄位

Q：TXF1 五日歷史是空的？
A：查看 debug_log.json 的 TXF1_five_day_raw 欄位
   確認 TAIFEX POST 請求有回傳資料

Q：YM/NQ 的 current_price 不對？
A：確認 YMNQ_data.json 的 close 是否正確
   查看 debug_log.json 的 YMNQ_data 欄位

Q：想改變觸發時間？
A：修改 Sheet A2 的時間
   在 GAS 執行一次 cleanAndReset()
   B2 會顯示新的下次執行時間

Q：GAS 定時觸發設定消失？
A：在 GAS 執行 cleanAndReset() 重新設定

Q：TV Webhook 顯示失敗但 Sheet 有更新？
A：正常現象，GAS 處理時間較長導致 TV 超時
   Sheet 有更新代表 GAS 實際上已收到資料

════════════════════════════════════════════════════════════════
