import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
import plotly.io as pio

def analyze_strategy(ohlcv, tolerance=0.0001, compression_period=20, compression_threshold=0.02,
                    ema_period=120, ma_long_period=111, ma_mid_periods=(25, 33, 49)):
    # 이동평균선 계산
    ohlcv[f'EMA{ema_period}'] = ta.trend.ema_indicator(ohlcv['close'], window=ema_period)
    ohlcv[f'MA{ma_long_period}'] = ta.trend.sma_indicator(ohlcv['close'], window=ma_long_period)
    
    # 중기 이동평균선 계산
    for period in ma_mid_periods:
        ohlcv[f'MA{period}'] = ta.trend.sma_indicator(ohlcv['close'], window=period)
    
    # 각 이동평균선의 기울기 계산
    ma_columns = [f'EMA{ema_period}', f'MA{ma_long_period}'] + [f'MA{period}' for period in ma_mid_periods]
    for col in ma_columns:
        ohlcv[f'{col}_slope'] = ohlcv[col].diff() / ohlcv.index.to_series().diff().dt.total_seconds()
    
    # 조건 1: EMA와 장기 MA가 평행한 구간 찾기
    slope_diff = abs(ohlcv[f'EMA{ema_period}_slope'] - ohlcv[f'MA{ma_long_period}_slope'])
    condition1 = slope_diff < tolerance

    # 조건 2: 중기 MA들이 모두 양의 기울기, EMA와 장기 MA가 양의 기울기
    condition2 = (ohlcv[f'EMA{ema_period}_slope'] > 0) & (ohlcv[f'MA{ma_long_period}_slope'] > 0)
    for period in ma_mid_periods:
        condition2 &= ohlcv[f'MA{period}_slope'] > 0

    # 조건 3: 눌림목 찾기 (수정된 로직)
    def find_pullback_breakout(df, period=compression_period, threshold=compression_threshold):
        signals = pd.Series(False, index=df.index)
        
        for i in range(period, len(df)):
            # 현재 구간의 데이터
            window = df.iloc[i-period:i]
            current_price = df.iloc[i]
            
            # 1. 이전 고점 찾기
            previous_high = window['high'].max()
            previous_close = window['close'].iloc[-1]
            high_idx = window['high'].idxmax()
            
            # 2. 고점 이후 EMA120까지 하락했는지 확인
            # after_high = df.loc[high_idx:df.index[i]]
            # touched_ema = any(abs(after_high['low'] - after_high[f'EMA{ema_period}']) < (after_high[f'EMA{ema_period}'] * threshold))
            
            # 3. 현재 가격이 이전 고점 보다 낮은지 확인
            breakout1 = current_price['open'] < previous_close* (1-threshold)
            breakout2 =  current_price['open'] < previous_high
            # 4. 현재 가격이 EMA와 장기 MA 사이에 있는지 확인
            # above_mas = (current_price['close'] < current_price[f'EMA{ema_period}']) & \
            #            (current_price['close'] > current_price[f'MA{ma_long_period}'])
                    #    (current_price['close'] > current_price[f'MA{ma_mid_periods[0]}']) & \
                    #    (current_price['close'] > current_price[f'MA{ma_mid_periods[1]}']) & \
                    #    (current_price['close'] > current_price[f'MA{ma_mid_periods[2]}'])
            
            # 모든 조건을 만족하면 시그널 생성
            # signals.iloc[i] = touched_ema and breakout and above_mas
            signals.iloc[i] = breakout1 and breakout2
        return signals
    
    condition3 = find_pullback_breakout(ohlcv)
    
    # 모든 조건을 만족하는 구간
    signals = condition1 & condition2 & condition3
    
    return ohlcv, signals
