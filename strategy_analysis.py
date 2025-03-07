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

def analyze_strategy(df, macd_fast=12, macd_slow=26, macd_signal=9,
                    cci_period=14, cci_signal=9,
                    rsi_period=14, rsi_signal=9,
                    use_macd=True, use_cci=True, use_rsi=True):
    """
    각 지표의 사용 여부를 선택할 수 있도록 수정된 전략 분석 함수
    선택된 지표들이 동시에 시그널선을 상향돌파하는 지점을 시그널로 생성
    """
    # 각 지표별 시그널을 저장할 변수들
    macd_buy = pd.Series(True, index=df.index)
    cci_buy = pd.Series(True, index=df.index)
    rsi_buy = pd.Series(True, index=df.index)
    
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

    if use_macd:
        # MACD가 시그널선을 상향돌파하는 지점
        macd_buy = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    
    if use_cci:
        # CCI가 시그널선을 상향돌파하는 지점
        cci_buy = (df['cci'] > df['cci_signal']) & (df['cci'].shift(1) <= df['cci_signal'].shift(1))
    
    if use_rsi:
        # RSI가 시그널선을 상향돌파하는 지점
        rsi_buy = (df['rsi'] > df['rsi_signal']) & (df['rsi'].shift(1) <= df['rsi_signal'].shift(1))
    # 선택된 지표들의 상향돌파 시점이 겹치는 지점을 시그널로 생성
    signals_df = pd.DataFrame(index=df.index)
    if use_macd:
        signals_df['macd'] = macd_buy
    if use_cci:
        signals_df['cci'] = cci_buy
    if use_rsi:
        signals_df['rsi'] = rsi_buy

    # 모든 선택된 지표가 동시에 상향돌파하는 지점 찾기
    signals = signals_df.all(axis=1)
    
    return df, signals
