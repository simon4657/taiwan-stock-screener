import pandas as pd
import numpy as np
import logging

class BankerEntrySignalCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_fund_flow_trend(self, data, window=20):
        """計算主力資金流向趨勢"""
        try:
            if data.empty or len(data) < window:
                return 0
            
            # 計算價格變化百分比
            price_change = data['Close'].pct_change()
            
            # 計算成交量變化百分比
            volume_change = data['Volume'].pct_change()
            
            # 計算資金流向指標
            fund_flow = price_change * volume_change
            
            # 計算移動平均
            fund_flow_ma = fund_flow.rolling(window=window).mean()
            
            # 返回最新的資金流向趨勢
            latest_trend = fund_flow_ma.iloc[-1] if not pd.isna(fund_flow_ma.iloc[-1]) else 0
            
            return float(latest_trend * 100)  # 轉換為百分比
            
        except Exception as e:
            self.logger.error(f"計算資金流向趨勢時發生錯誤: {e}")
            return 0
    
    def calculate_bull_bear_line(self, data, short_window=5, long_window=20):
        """計算多空線指標"""
        try:
            if data.empty or len(data) < long_window:
                return 0
            
            # 計算短期和長期移動平均
            short_ma = data['Close'].rolling(window=short_window).mean()
            long_ma = data['Close'].rolling(window=long_window).mean()
            
            # 計算多空線
            bull_bear = ((short_ma - long_ma) / long_ma * 100)
            
            # 返回最新的多空線值
            latest_value = bull_bear.iloc[-1] if not pd.isna(bull_bear.iloc[-1]) else 0
            
            return float(latest_value)
            
        except Exception as e:
            self.logger.error(f"計算多空線時發生錯誤: {e}")
            return 0
    
    def calculate_banker_entry_signal(self, data, volume_threshold=1.5):
        """計算主力進場信號"""
        try:
            if data.empty or len(data) < 25:
                return 0
            
            # 計算成交量比率
            volume_ma = data['Volume'].rolling(window=20).mean()
            volume_ratio = data['Volume'] / volume_ma
            
            # 找出成交量異常放大的日子
            high_volume_days = volume_ratio > volume_threshold
            
            # 計算這些日子的價格表現
            price_change = data['Close'].pct_change()
            
            # 計算主力進場信號強度
            signal_strength = 0
            recent_days = min(25, len(data))
            
            for i in range(-recent_days, 0):
                if high_volume_days.iloc[i] and price_change.iloc[i] > 0:
                    # 成交量放大且價格上漲，可能是主力進場
                    signal_strength += volume_ratio.iloc[i] * price_change.iloc[i]
            
            return float(signal_strength * 100)
            
        except Exception as e:
            self.logger.error(f"計算主力進場信號時發生錯誤: {e}")
            return 0
    
    def calculate_entry_score(self, data):
        """計算綜合進場評分"""
        try:
            if data.empty:
                return 0
            
            # 計算各項指標
            fund_flow = self.calculate_fund_flow_trend(data)
            bull_bear = self.calculate_bull_bear_line(data)
            banker_signal = self.calculate_banker_entry_signal(data)
            
            # 計算價格動能
            price_momentum = self._calculate_price_momentum(data)
            
            # 綜合評分 (權重可調整)
            entry_score = (
                fund_flow * 0.3 +
                bull_bear * 0.2 +
                banker_signal * 0.3 +
                price_momentum * 0.2
            )
            
            return float(entry_score)
            
        except Exception as e:
            self.logger.error(f"計算進場評分時發生錯誤: {e}")
            return 0
    
    def _calculate_price_momentum(self, data, window=10):
        """計算價格動能"""
        try:
            if len(data) < window:
                return 0
            
            # 計算價格變化率
            price_change = data['Close'].pct_change(window)
            latest_momentum = price_change.iloc[-1] if not pd.isna(price_change.iloc[-1]) else 0
            
            return float(latest_momentum * 100)
            
        except Exception as e:
            self.logger.error(f"計算價格動能時發生錯誤: {e}")
            return 0
    
    def get_top_banker_entry_stocks(self, stocks_data, top_n=5):
        """獲取主力進場評分最高的股票"""
        try:
            if not stocks_data:
                self.logger.warning("沒有股票資料可供分析")
                return []
            
            results = []
            
            for stock_code, stock_info in stocks_data.items():
                try:
                    data = stock_info['data']
                    name = stock_info['name']
                    
                    if data.empty:
                        continue
                    
                    # 計算各項指標
                    fund_flow = self.calculate_fund_flow_trend(data)
                    bull_bear = self.calculate_bull_bear_line(data)
                    banker_signal = self.calculate_banker_entry_signal(data)
                    entry_score = self.calculate_entry_score(data)
                    
                    # 獲取最新價格和漲跌幅
                    latest_price = float(data['Close'].iloc[-1])
                    price_change = float(data['Close'].pct_change().iloc[-1] * 100) if len(data) > 1 else 0
                    
                    results.append({
                        'code': stock_code,
                        'name': name,
                        'latest_price': latest_price,
                        'price_change_pct': price_change,
                        'fund_flow_trend': fund_flow,
                        'bull_bear_line': bull_bear,
                        'banker_entry_signal': banker_signal,
                        'entry_score': entry_score
                    })
                    
                except Exception as e:
                    self.logger.error(f"分析股票 {stock_code} 時發生錯誤: {e}")
                    continue
            
            # 按進場評分排序
            results.sort(key=lambda x: x['entry_score'], reverse=True)
            
            # 返回前N名
            top_results = results[:top_n]
            
            self.logger.info(f"成功分析 {len(results)} 支股票，返回前 {len(top_results)} 名")
            
            return top_results
            
        except Exception as e:
            self.logger.error(f"獲取頂級主力進場股票時發生錯誤: {e}")
            return []

