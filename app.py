import streamlit as st
import pandas as pd
from strategy_analysis import analyze_strategy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf
import time
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="wide")

# 세션 상태 초기화
if 'ohlcv_data' not in st.session_state:
    st.session_state.ohlcv_data = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'signal_counts' not in st.session_state:
    st.session_state.signal_counts = {}
if 'last_params' not in st.session_state:
    st.session_state.last_params = None
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'current_interval' not in st.session_state:
    st.session_state.current_interval = None
if 'last_interval' not in st.session_state:
    st.session_state.last_interval = None

def plot_analysis_streamlit(df, signals):
    # 인터랙티브 차트 생성 (4개의 subplot)
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.4, 0.2, 0.2, 0.2],
        specs=[[{"secondary_y": True}],
               [{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )

    # 캔들스틱 차트 추가
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=st.session_state.current_ticker
        ),
        row=1, col=1
    )

    # 거래량 바 추가
    colors = ['red' if row['close'] < row['open'] else 'green' 
             for i, row in df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.3
        ),
        row=1, col=1,
        secondary_y=True
    )

    # 매수 시그널 표시
    signal_points = df[signals]['close']
    fig.add_trace(
        go.Scatter(
            x=signal_points.index,
            y=signal_points,
            mode='markers',
            name='Buy Signal',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='red'
            )
        ),
        row=1, col=1
    )

    # MACD 차트
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['macd'],
            name='MACD',
            line=dict(color='blue')
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['macd_signal'],
            name='MACD Signal',
            line=dict(color='orange')
        ),
        row=2, col=1
    )

    # CCI 차트
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['cci'],
            name='CCI',
            line=dict(color='purple')
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['cci_signal'],
            name='CCI Signal',
            line=dict(color='pink')
        ),
        row=3, col=1
    )

    # RSI 차트
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['rsi'],
            name='RSI',
            line=dict(color='green')
        ),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['rsi_signal'],
            name='RSI Signal',
            line=dict(color='lightgreen')
        ),
        row=4, col=1
    )

    # 차트 레이아웃 설정
    fig.update_layout(
        title='Trading Strategy Analysis',
        xaxis_rangeslider_visible=False,
        height=900,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        hovermode='x unified'
    )

    # Y축 제목 설정
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="CCI", row=3, col=1)
    fig.update_yaxes(title_text="RSI", row=4, col=1)

    # 그리드 설정
    fig.update_xaxes(gridcolor='lightgrey', gridwidth=0.5)
    fig.update_yaxes(gridcolor='lightgrey', gridwidth=0.5)
    
    # Streamlit에 차트 표시
    st.plotly_chart(fig, use_container_width=True)

def calculate_signals_for_ticker(ticker, start_date, end_date, params):
    """특정 티커의 시그널 수를 계산하는 함수"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        if len(data) == 0:
            return 0
        data.columns = data.columns.str.lower()
        
        # 전략 분석
        _, signals = analyze_strategy(
            data,
            tolerance=params['tolerance'],
            compression_period=params['compression_period'],
            compression_threshold=params['compression_threshold'],
            ema_period=params['ema_period'],
            ma_long_period=params['ma_long_period'],
            ma_mid_periods=params['ma_mid_periods']
        )
        return int(signals.sum())
    except:
        return 0

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
    
    max_days = intervals[interval]["days"]
    default_days = intervals[interval]["default"]
    
    default_start = today - pd.Timedelta(days=default_days)
    min_start = today - pd.Timedelta(days=max_days)
    
    return min_start, default_start, today

def main():
    st.title('주식 전략 분석기')
    
    # 캔들 주기 선택
    st.sidebar.subheader('캔들 주기 설정')
    interval_options = {
        "1분": "1m", "2분": "2m", "5분": "5m", "15분": "15m", "30분": "30m",
        "60분": "60m", "90분": "90m", "1시간": "1h", 
        "1일": "1d", "5일": "5d", "1주": "1wk", "1달": "1mo", "3달": "3mo"
    }
    selected_interval_name = st.sidebar.selectbox(
        '캔들 주기',
        options=list(interval_options.keys()),
        index=8  # 기본값 1일
    )
    interval = interval_options[selected_interval_name]
    
    # 선택된 캔들 주기에 따른 유효한 날짜 범위 계산
    min_start, default_start, today = get_valid_date_range(interval)
    
    # 날짜 선택 (캔들 주기에 따른 제한 적용)
    # col1, col2 = st.sidebar.columns(2)
    # with col1:
    #     start_date = st.date_input(
    #         '시작일', 
    #         value=default_start,
    #         min_value=min_start,
    #         max_value=today
    #     )
    # with col2:
    #     end_date = st.date_input(
    #         '종료일',
    #         value=today,
    #         min_value=start_date,
    #         max_value=today
    #     )
    """
    yfinance api 제한으로 인해 날짜 선택 불가능 (추후 수정 예정)
    """
    start_date = default_start
    end_date = today

    # 날짜 범위 경고
    max_days = (today - min_start).days
    selected_days = (end_date - start_date).days
    if selected_days > max_days:
        st.sidebar.warning(f'{selected_interval_name} 캔들은 최대 {max_days}일 동안의 데이터만 조회할 수 있습니다.')
        return
    
    # 사이드바에 파라미터 설정
    st.sidebar.header('분석 파라미터')
    
    # 코스피 200 주요 종목 목록
    default_tickers = {
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
    
    # 설명 추가
    st.sidebar.subheader("현재 전략 설명")
    st.sidebar.markdown("1) EMA와 장기 MA가 평행한 구간 찾기(허용오차내)")
    st.sidebar.markdown("2) 중기 MA들이 모두 양의 기울기")
    st.sidebar.markdown("3) 눌림목 찾기(눌림목 확인 기간, 눌림목 허용 범위)")
    # 전략 파라미터 설정
    st.sidebar.subheader('MACD 파라미터')
    macd_fast = st.sidebar.slider('MACD Fast Period', 5, 30, 12)
    macd_slow = st.sidebar.slider('MACD Slow Period', 15, 50, 26)
    macd_signal = st.sidebar.slider('MACD Signal Period', 5, 20, 9)

    st.sidebar.subheader('CCI 파라미터')
    cci_period = st.sidebar.slider('CCI Period', 5, 30, 14)
    cci_signal = st.sidebar.slider('CCI Signal Period', 5, 20, 9)

    st.sidebar.subheader('RSI 파라미터')
    rsi_period = st.sidebar.slider('RSI Period', 5, 30, 14)
    rsi_signal = st.sidebar.slider('RSI Signal Period', 5, 20, 9)

    # 전략 분석 실행 부분 수정
    if st.session_state.ohlcv_data is not None:
        try:
            # 전략 분석
            df, signals = analyze_strategy(
                st.session_state.ohlcv_data.copy(),
                macd_fast=macd_fast,
                macd_slow=macd_slow,
                macd_signal=macd_signal,
                cci_period=cci_period,
                cci_signal=cci_signal,
                rsi_period=rsi_period,
                rsi_signal=rsi_signal
            )
            
            # 시그널 통계
            total_signals = signals.sum()
            st.sidebar.metric("발견된 시그널 수", total_signals)
            
            # 차트 표시
            plot_analysis_streamlit(df, signals)
            
            # 시그널 날짜 표시
            if total_signals > 0:
                st.subheader('시그널 발생 날짜')
                signal_dates = []
                for idx in df[signals].index:
                    try:
                        # datetime 객체로 변환 시도
                        if isinstance(idx, str):
                            date_str = pd.to_datetime(idx).strftime('%Y-%m-%d')
                        else:
                            date_str = idx.strftime('%Y-%m-%d')
                        signal_dates.append(date_str)
                    except:
                        # 변환 실패시 문자열 그대로 사용
                        signal_dates.append(str(idx))
                st.write(signal_dates)
                
        except Exception as e:
            st.error(f'분석 중 오류 발생: {str(e)}')

if __name__ == "__main__":
    main() 
