import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def get_valid_date_range(interval):
    """선택된 캔들 주기에 따른 유효한 날짜 범위 반환"""
    today = datetime(2025, 2, 19, 13, 20, 37, 106915)
    
    intervals = {
        "1m": {"days": 7, "default": 7-1},
        "2m": {"days": 60, "default": 60-1},
        "5m": {"days": 60, "default": 60-1},
        "15m": {"days": 60, "default": 60-1},
        "30m": {"days": 60, "default": 60-1},
        "60m": {"days": 60, "default": 60-1},
        "90m": {"days": 60, "default": 60-1},
        "1h": {"days": 730, "default": 730-1},
        "1d": {"days": 10000, "default": 365*5},
        "5d": {"days": 10000, "default": 365*5},
        "1wk": {"days": 10000, "default": 365*5},
        "1mo": {"days": 10000, "default": 365*5},
        "3mo": {"days": 10000, "default": 365*5}
    }
    
    return intervals

def collect_stock_data(ticker, interval="1d"):
    """특정 티커의 데이터를 수집하고 저장"""
    intervals = get_valid_date_range(interval)
    today = datetime(2025, 2, 19, 13, 20, 37, 106915)
    
    if interval not in intervals:
        print(f"Invalid interval: {interval}")
        return
    
    # 날짜 범위 계산
    default_days = intervals[interval]["default"]
    start_date = today - timedelta(days=default_days)
    
    try:
        # 데이터 수집
        print(f"Collecting data for {ticker} ({interval})...")
        stock = yf.Ticker(ticker)
        data = stock.history(
            start=start_date,
            end=today,
            interval=interval
        )
        
        if len(data) == 0:
            print(f"No data available for {ticker}")
            return
        
        # 저장 경로 생성
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # 파일명 생성 및 저장
        filename = f'data/{ticker}_{interval}_{start_date.strftime("%Y%m%d")}_{today.strftime("%Y%m%d")}.csv'
        data.to_csv(filename)
        print(f"Data saved to {filename}")
        
        return data
    
    except Exception as e:
        print(f"Error collecting data for {ticker}: {str(e)}")
        return None

def main():
    # 기본 티커 목록
    tickers = {
        # 기술주
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft',
        'GOOGL': 'Alphabet (Google)',
        'AMZN': 'Amazon',
        'META': 'Meta Platforms',
        'NVDA': 'NVIDIA',
        'TSLA': 'Tesla',
        'INTC': 'Intel',
        'AMD': 'Advanced Micro Devices',
        'CRM': 'Salesforce',
        'ADBE': 'Adobe',
        'ORCL': 'Oracle',
        'CSCO': 'Cisco',
        
        # 금융
        'JPM': 'JPMorgan Chase',
        'BAC': 'Bank of America',
        'WFC': 'Wells Fargo',
        'GS': 'Goldman Sachs',
        'V': 'Visa',
        'MA': 'Mastercard',
        
        # 소비재
        'KO': 'Coca-Cola',
        'PEP': 'PepsiCo',
        'MCD': "McDonald's",
        'SBUX': 'Starbucks',
        'NKE': 'Nike',
        'DIS': 'Disney',
        'NFLX': 'Netflix',
        'WMT': 'Walmart',
        'COST': 'Costco',
        'TGT': 'Target',
        
        # 헬스케어
        'JNJ': 'Johnson & Johnson',
        'PFE': 'Pfizer',
        'MRNA': 'Moderna',
        'UNH': 'UnitedHealth',
        'ABT': 'Abbott Laboratories',
        
        # 통신
        'T': 'AT&T',
        'VZ': 'Verizon',
        
        # 에너지
        'XOM': 'ExxonMobil',
        'CVX': 'Chevron',
        
        # 산업재
        'BA': 'Boeing',
        'CAT': 'Caterpillar',
        'GE': 'General Electric',
        'MMM': '3M',
        
        # 자동차
        'F': 'Ford',
        'GM': 'General Motors',
        
        # 반도체
        'TSM': 'Taiwan Semiconductor',
        'QCOM': 'Qualcomm',
        'TXN': 'Texas Instruments',
        
        # 엔터테인먼트/게임
        'EA': 'Electronic Arts',
        'TTWO': 'Take-Two Interactive',
        
        # 기타 테크
        'ZM': 'Zoom',
        'UBER': 'Uber',
        'ABNB': 'Airbnb',
        'SQ': 'Block (Square)',
        'PYPL': 'PayPal',
        'SHOP': 'Shopify'
    }
    
    # 모든 간격 설정
    intervals = [
        "1m", "2m", "5m", "15m", "30m",
        "60m", "90m", "1h",
        "1d", "5d", "1wk", "1mo", "3mo"
    ]
    
    # 진행 상황 표시를 위한 총 작업 수 계산
    total_tasks = len(tickers) * len(intervals)
    completed_tasks = 0
    
    # 각 티커와 간격에 대해 데이터 수집
    for interval in intervals:
        print(f"\nCollecting {interval} data...")
        for ticker in tickers.keys():
            completed_tasks += 1
            print(f"Progress: {completed_tasks}/{total_tasks} ({(completed_tasks/total_tasks)*100:.1f}%)")
            
            collect_stock_data(ticker, interval)
            # API 제한을 위한 대기
            import time
            time.sleep(1)  # 1초 대기
            
            # 분봉 데이터의 경우 더 긴 대기 시간 적용
            if interval in ["1m", "2m", "5m", "15m", "30m"]:
                time.sleep(2)  # 추가 2초 대기

if __name__ == "__main__":
    main() 