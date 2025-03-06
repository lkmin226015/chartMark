import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import plotly.io as pio

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """MACD 및 Signal 계산"""
    macd = ta.trend.MACD(
        close=data['close'], 
        window_slow=slow_period, 
        window_fast=fast_period, 
        window_sign=signal_period
    )
    return macd.macd(), macd.macd_signal()

def calculate_cci(data, period=14, signal_period=9):
    """CCI 및 Signal 계산"""
    cci = ta.trend.CCIIndicator(
        high=data['high'],
        low=data['low'],
        close=data['close'],
        window=period
    ).cci()
    cci_signal = cci.rolling(window=signal_period).mean()
    return cci, cci_signal

def calculate_rsi(data, period=14, signal_period=9):
    """RSI 및 Signal 계산"""
    rsi = ta.momentum.RSIIndicator(
        close=data['close'],
        window=period
    ).rsi()
    rsi_signal = rsi.rolling(window=signal_period).mean()
    return rsi, rsi_signal

def analyze_strategy(data, macd_fast=12, macd_slow=26, macd_signal=9,
                    cci_period=14, cci_signal=9,
                    rsi_period=14, rsi_signal=9):
    """전략 분석"""
    # 데이터 복사
    df = data.copy()
    
    # MACD 계산
    df['macd'], df['macd_signal'] = calculate_macd(
        df, macd_fast, macd_slow, macd_signal
    )
    
    # CCI 계산
    df['cci'], df['cci_signal'] = calculate_cci(
        df, cci_period, cci_signal
    )
    
    # RSI 계산
    df['rsi'], df['rsi_signal'] = calculate_rsi(
        df, rsi_period, rsi_signal
    )
    
    # 크로스 시그널 계산
    df['macd_cross'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df['cci_cross'] = (df['cci'] > df['cci_signal']) & (df['cci'].shift(1) <= df['cci_signal'].shift(1))
    df['rsi_cross'] = (df['rsi'] > df['rsi_signal']) & (df['rsi'].shift(1) <= df['rsi_signal'].shift(1))
    
    # 모든 시그널이 동시에 발생하는 지점 찾기
    df['signals'] = df['macd_cross'] & df['cci_cross'] & df['rsi_cross']
    
    return df, df['signals']
