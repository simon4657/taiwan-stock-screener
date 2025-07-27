#!/usr/bin/env python3
"""
台股主力資金進入篩選器 - Render部署版本
"""

import os
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests

# 導入自定義模組
from stock_data_collector import StockDataCollector
from banker_signal_calculator import BankerEntrySignalCalculator

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建Flask應用
app = Flask(__name__)
CORS(app)

# 全域變數
collector = None
calculator = None
stocks_data = {}
last_update_time = None
is_updating = False

def initialize_components():
    """初始化組件"""
    global collector, calculator
    
    try:
        logger.info("開始初始化組件...")
        
        # 初始化資料收集器
        logger.info("初始化資料收集器...")
        collector = StockDataCollector()
        
        # 初始化計算器
        logger.info("初始化計算器...")
        calculator = BankerEntrySignalCalculator()
        
        logger.info("組件初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"組件初始化失敗: {e}")
        return False

def error_handler(f):
    """錯誤處理裝飾器"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API錯誤 {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': '伺服器處理請求時發生錯誤'
            }), 500
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/api/stocks/update', methods=['POST'])
@error_handler
def update_stocks():
    """更新股票資料API"""
    global stocks_data, last_update_time, is_updating
    
    if is_updating:
        return jsonify({
            'success': False,
            'message': '資料更新正在進行中，請稍後再試'
        })
    
    def update_task():
        global stocks_data, last_update_time, is_updating
        
        try:
            is_updating = True
            logger.info("開始更新股票資料...")
            
            # 限制股票數量以適應Render的資源限制
            max_stocks = 20  # Render免費方案資源有限
            stocks_data = collector.update_all_stocks_data(max_stocks=max_stocks)
            last_update_time = datetime.now()
            
            logger.info(f"股票資料更新完成，成功獲取 {len(stocks_data)} 支股票資料")
            
        except Exception as e:
            logger.error(f"更新股票資料時發生錯誤: {e}")
        finally:
            is_updating = False
    
    # 在背景執行更新任務
    threading.Thread(target=update_task, daemon=True).start()
    
    return jsonify({
        'success': True,
        'message': '股票資料更新已開始',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stocks/screen', methods=['POST'])
@error_handler
def screen_stocks():
    """篩選股票API"""
    global stocks_data, calculator
    
    if not stocks_data:
        return jsonify({
            'success': False,
            'message': '請先更新股票資料',
            'data': []
        })
    
    if is_updating:
        return jsonify({
            'success': False,
            'message': '資料更新中，請稍後再試',
            'data': []
        })
    
    try:
        # 獲取篩選參數
        data = request.get_json() or {}
        top_n = data.get('top_n', 5)
        
        logger.info(f"開始篩選股票，目標數量: {top_n}")
        
        # 執行篩選
        results = calculator.get_top_banker_entry_stocks(stocks_data, top_n=top_n)
        
        if not results:
            return jsonify({
                'success': False,
                'message': '未找到符合條件的股票',
                'data': []
            })
        
        # 格式化結果
        formatted_results = []
        for stock in results:
            formatted_results.append({
                'code': stock['code'],
                'name': stock['name'],
                'latest_price': round(stock['latest_price'], 2),
                'price_change_pct': round(stock['price_change_pct'], 2),
                'fund_flow_trend': round(stock['fund_flow_trend'], 2),
                'bull_bear_line': round(stock['bull_bear_line'], 2),
                'banker_entry_signal': round(stock['banker_entry_signal'], 2),
                'entry_score': round(stock['entry_score'], 2)
            })
        
        return jsonify({
            'success': True,
            'message': f'成功篩選出 {len(formatted_results)} 支股票',
            'data': formatted_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"篩選股票時發生錯誤: {e}")
        return jsonify({
            'success': False,
            'message': f'篩選失敗: {str(e)}',
            'data': []
        })

@app.route('/api/status')
@error_handler
def get_status():
    """獲取系統狀態"""
    global stocks_data, last_update_time, is_updating
    
    return jsonify({
        'success': True,
        'data': {
            'stocks_count': len(stocks_data),
            'last_update_time': last_update_time.isoformat() if last_update_time else None,
            'is_updating': is_updating,
            'components_initialized': collector is not None and calculator is not None
        }
    })

@app.route('/health')
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'taiwan-stock-screener'
    })

@app.route('/version')
def version():
    """版本資訊"""
    return jsonify({
        'version': '1.0.0',
        'service': 'taiwan-stock-screener',
        'platform': 'render'
    })

@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': '請求的資源不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': '伺服器內部錯誤'
    }), 500

@app.after_request
def after_request(response):
    """添加安全標頭"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def keep_alive():
    """保持服務活躍，避免Render休眠"""
    app_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url:
        return
    
    while True:
        try:
            time.sleep(25 * 60)  # 每25分鐘ping一次
            requests.get(f"{app_url}/health", timeout=10)
            logger.info("Keep-alive ping sent")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")

if __name__ == '__main__':
    # 獲取環境變數
    PORT = int(os.environ.get('PORT', 10000))  # Render使用PORT環境變數
    HOST = '0.0.0.0'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info("台股主力資金進入篩選器啟動中...")
    
    # 初始化組件
    if initialize_components():
        logger.info("組件初始化成功，啟動 Flask 應用")
        
        # 啟動keep-alive線程（僅在Render環境）
        if os.environ.get('RENDER'):
            threading.Thread(target=keep_alive, daemon=True).start()
            logger.info("Keep-alive thread started")
        
        # 啟動應用
        logger.info(f"啟動台股主力資金進入篩選器，端口: {PORT}")
        app.run(host=HOST, port=PORT, debug=DEBUG)
    else:
        logger.error("組件初始化失敗，無法啟動應用")
        exit(1)

