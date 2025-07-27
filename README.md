# 台股主力資金進入篩選器

一個基於Python Flask的台灣股票主力資金進入信號篩選工具，專為Render平台優化部署。

## 功能特色

- 🔍 **智能篩選**: 自動篩選出主力資金進入信號最強的台股
- 📊 **多重指標**: 整合資金流向趨勢、多空線、主力進場信號等技術指標
- 🚀 **即時更新**: 支援股票資料即時更新
- 📱 **響應式設計**: 支援桌面和行動裝置
- ☁️ **雲端部署**: 專為Render平台優化

## 技術指標說明

### 主力資金流向趨勢 (Fund Flow Trend)
根據價格位置百分比的加權移動平均計算，反映主力資金的流向趨勢。

### 多空線 (Bull Bear Line)
基於典型價格相對於高低點位置的指數移動平均，作為判斷多空方向的基準線。

### 主力進場信號 (Banker Entry Signal)
當趨勢線向上穿越多空線且多空線低於25時產生，表示主力資金可能正在進場。

### 進場評分 (Entry Score)
綜合考量趨勢強度、價格深幅和進場時間的綜合評分。

## 技術架構

- **後端**: Python Flask
- **前端**: HTML5 + CSS3 + JavaScript
- **資料來源**: Yahoo Finance API
- **部署平台**: Render

## 本地開發

### 環境需求
- Python 3.11+
- pip

### 安裝步驟

1. 克隆專案
```bash
git clone <your-repo-url>
cd taiwan_stock_render
```

2. 安裝依賴
```bash
pip install -r requirements.txt
```

3. 啟動應用
```bash
python app.py
```

4. 開啟瀏覽器訪問 `http://localhost:10000`

## Render部署

### 自動部署
1. 將程式碼推送到GitHub
2. 在Render連接GitHub倉庫
3. 設定以下配置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

### 環境變數
- `PORT`: 應用端口（Render自動設定）
- `DEBUG`: 除錯模式（預設: False）
- `RENDER`: Render環境標識（自動設定）

## 使用說明

1. **更新股票資料**: 點擊「更新股票資料」按鈕獲取最新股票資訊
2. **開始篩選**: 點擊「開始篩選」按鈕執行主力資金進入信號分析
3. **查看結果**: 系統會顯示評分最高的5支股票及其詳細指標

## 注意事項

- 免費版Render有資源限制，建議限制同時處理的股票數量
- 30分鐘無活動會自動休眠，首次喚醒可能需要較長時間
- 資料來源依賴Yahoo Finance API，可能受到網路狀況影響

## 授權

本專案僅供學習和研究使用，不構成投資建議。

## 版本歷史

- v1.0.0: 初始版本，支援基本篩選功能
- v1.0.1: 優化Render部署配置
- v1.0.2: 增加keep-alive機制，減少休眠問題

