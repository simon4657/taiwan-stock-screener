import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import logging
from tqdm import tqdm

class StockDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_taiwan_stock_list(self):
        """獲取台灣股票清單，使用多重備用方案"""
        try:
            # 方法1: 從台灣證券交易所獲取
            stock_list = self._get_stock_list_from_twse()
            if not stock_list.empty:
                self.logger.info(f"從TWSE獲取到 {len(stock_list)} 支股票")
                return stock_list
        except Exception as e:
            self.logger.warning(f"從TWSE獲取股票清單失敗: {e}")
        
        try:
            # 方法2: 從櫃買中心獲取
            stock_list = self._get_stock_list_from_tpex()
            if not stock_list.empty:
                self.logger.info(f"從TPEX獲取到 {len(stock_list)} 支股票")
                return stock_list
        except Exception as e:
            self.logger.warning(f"從TPEX獲取股票清單失敗: {e}")
        
        # 方法3: 使用預設股票清單
        self.logger.info("使用預設股票清單")
        return self._get_default_stock_list()
    
    def _get_stock_list_from_twse(self):
        """從台灣證券交易所獲取股票清單"""
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            if not tables:
                raise Exception("找不到股票資料表格")
            
            # 解析股票資料
            stocks = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # 跳過標題行
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        code_name = cols[0].text.strip()
                        if '　' in code_name:
                            code, name = code_name.split('　', 1)
                            if code.isdigit() and len(code) == 4:
                                stocks.append({
                                    'stock_id': code,
                                    'stock_name': name.strip(),
                                    'market': 'TWSE'
                                })
            
            return pd.DataFrame(stocks)
            
        except Exception as e:
            self.logger.error(f"從TWSE獲取股票清單失敗: {e}")
            return pd.DataFrame()
    
    def _get_stock_list_from_tpex(self):
        """從櫃買中心獲取股票清單"""
        url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=json"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            stocks = []
            if 'aaData' in data:
                for item in data['aaData']:
                    if len(item) >= 2:
                        code = item[0].strip()
                        name = item[1].strip()
                        if code.isdigit() and len(code) == 4:
                            stocks.append({
                                'stock_id': code,
                                'stock_name': name,
                                'market': 'TPEX'
                            })
            
            return pd.DataFrame(stocks)
            
        except Exception as e:
            self.logger.error(f"從TPEX獲取股票清單失敗: {e}")
            return pd.DataFrame()
    
    def _get_default_stock_list(self):
        """預設的重要台股清單"""
        default_stocks = [
            # 權值股
            ('2330', '台積電'), ('2317', '鴻海'), ('2454', '聯發科'), ('2881', '富邦金'),
            ('2882', '國泰金'), ('2886', '兆豐金'), ('2891', '中信金'), ('2892', '第一金'),
            ('2884', '玉山金'), ('2885', '元大金'), ('2887', '台新金'), ('2888', '新光金'),
            ('2890', '永豐金'), ('2883', '開發金'), ('2880', '華南金'), ('2889', '國票金'),
            
            # 科技股
            ('2303', '聯電'), ('2308', '台達電'), ('2382', '廣達'), ('2357', '華碩'),
            ('2409', '友達'), ('2474', '可成'), ('3008', '大立光'), ('2412', '中華電'),
            ('3711', '日月光投控'), ('2379', '瑞昱'), ('2395', '研華'), ('6505', '台塑化'),
            
            # 傳統產業
            ('1301', '台塑'), ('1303', '南亞'), ('1326', '台化'), ('2002', '中鋼'),
            ('2207', '和泰車'), ('2301', '光寶科'), ('2324', '仁寶'), ('2327', '國巨'),
            ('2408', '南亞科'), ('2603', '長榮'), ('2609', '陽明'), ('2615', '萬海'),
            
            # ETF
            ('0050', '元大台灣50'), ('0056', '元大高股息'), ('006208', '富邦台50'),
            ('00878', '國泰永續高股息'), ('00881', '國泰台灣5G+'), ('00885', '富邦越南'),
            
            # 其他重要個股
            ('2912', '統一超'), ('2801', '彰銀'), ('2823', '中壽'), ('2834', '臺企銀'),
            ('3045', '台灣大'), ('4938', '和碩'), ('6415', '矽力-KY'), ('6669', '緯穎')
        ]
        
        stocks = []
        for code, name in default_stocks:
            stocks.append({
                'stock_id': code,
                'stock_name': name,
                'market': 'DEFAULT'
            })
        
        return pd.DataFrame(stocks)
    
    def get_stock_data(self, stock_code, period="1y"):
        """獲取股票歷史資料，使用多期間策略"""
        periods = ["1y", "6mo", "3mo", "1mo"]
        
        for attempt_period in periods:
            try:
                # 添加.TW後綴
                symbol = f"{stock_code}.TW"
                
                # 使用yfinance獲取資料
                stock = yf.Ticker(symbol)
                hist = stock.history(period=attempt_period)
                
                if not hist.empty and len(hist) > 20:  # 至少需要20天的資料
                    self.logger.debug(f"成功獲取股票 {stock_code} 的 {attempt_period} 資料")
                    return hist
                    
            except Exception as e:
                self.logger.debug(f"獲取股票 {stock_code} 的 {attempt_period} 資料失敗: {e}")
                continue
        
        # 所有期間都失敗
        self.logger.warning(f"無法獲取股票 {stock_code} 的歷史資料")
        return pd.DataFrame()
    
    def update_all_stocks_data(self, max_stocks=None):
        """更新所有股票資料"""
        stock_list = self.get_taiwan_stock_list()
        
        if stock_list.empty:
            self.logger.error("無法獲取股票清單")
            return {}
        
        # 限制處理的股票數量（用於測試）
        if max_stocks:
            stock_list = stock_list.head(max_stocks)
            self.logger.info(f"限制處理 {max_stocks} 支股票進行測試")
        
        all_data = {}
        successful_count = 0
        
        self.logger.info(f"開始更新 {len(stock_list)} 支股票的資料")
        
        # 使用tqdm顯示進度
        for index, row in tqdm(stock_list.iterrows(), total=len(stock_list), desc="更新股票資料"):
            stock_code = row['stock_id']
            stock_name = row['stock_name']
            
            try:
                data = self.get_stock_data(stock_code)
                if not data.empty:
                    all_data[stock_code] = {
                        'name': stock_name,
                        'data': data,
                        'market': row.get('market', 'UNKNOWN')
                    }
                    successful_count += 1
                else:
                    self.logger.warning(f"無法獲取股票 {stock_code} 的歷史資料")
                    
            except Exception as e:
                self.logger.error(f"處理股票 {stock_code} 時發生錯誤: {e}")
                continue
            
            # 添加延遲避免API限制
            time.sleep(0.1)
        
        self.logger.info(f"股票資料更新完成，成功獲取 {successful_count}/{len(stock_list)} 支股票資料")
        return all_data

