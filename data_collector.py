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
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'INTC', 'AMD',
        'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA',
        'KO', 'PEP', 'MCD', 'SBUX', 'NKE', 'DIS', 'NFLX'
    ]
    
    # 수집할 간격 설정
    intervals = ["1d"]  # 필요한 간격 추가 가능
    
    # 각 티커와 간격에 대해 데이터 수집
    for interval in intervals:
        print(f"\nCollecting {interval} data...")
        for ticker in tickers:
            collect_stock_data(ticker, interval)
            # API 제한을 위한 대기
            import time
            time.sleep(1)

if __name__ == "__main__":
    main() 