import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def get_valid_date_range(interval):
    """선택된 캔들 주기에 따른 유효한 날짜 범위 반환"""        
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
    today = datetime(2025, 3, 31, 13, 20, 37, 106915)
    
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
    # 코스피 200 주요 종목 목록
    tickers = {
        # 반도체/전자
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '066570.KS': 'LG전자',
        '009150.KS': '삼성전기',
        
        # 자동차/배터리
        '005380.KS': '현대차',
        '000270.KS': '기아',
        '012330.KS': '현대모비스',
        '373220.KS': 'LG에너지솔루션',
        '006400.KS': '삼성SDI',
        
        # 화학/에너지
        '051910.KS': 'LG화학',
        '096770.KS': 'SK이노베이션',
        '034730.KS': 'SK',
        '010950.KS': 'S-Oil',
        
        # 바이오/제약
        '207940.KS': '삼성바이오로직스',
        '068270.KS': '셀트리온',
        '326030.KS': 'SK바이오팜',
        
        # 금융
        '055550.KS': '신한지주',
        '086790.KS': '하나금융지주',
        '316140.KS': '우리금융지주',
        '024110.KS': '기업은행',
        
        # 통신/인터넷
        '017670.KS': 'SK텔레콤',
        '030200.KS': 'KT',
        '035420.KS': 'NAVER',
        '035720.KS': '카카오',
        
        # 철강/소재
        '005490.KS': 'POSCO홀딩스',
        '010130.KS': '고려아연',
        '004020.KS': '현대제철',
        
        # 유통/소비재
        '005930.KS': '삼성전자',
        '139480.KS': '이마트',
        '004170.KS': '신세계',
        '097950.KS': 'CJ제일제당',
        
        # 건설
        '000720.KS': '현대건설',
        '028260.KS': '삼성물산',
        '047040.KS': '대우건설',
        
        # 항공/운송
        '003490.KS': '대한항공',
        '011200.KS': 'HMM',
        '180640.KS': '한진칼'
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