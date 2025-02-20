import streamlit as st
import pandas as pd
from strategy_analysis import analyze_strategy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf
import time

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

def plot_analysis_streamlit(ohlcv, signals, ema_period, ma_long_period, ma_mid_periods):
    # 인터랙티브 차트 생성
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.7, 0.3])

    # 캔들스틱 차트 추가
    fig.add_trace(
        go.Candlestick(
            x=ohlcv.index,
            open=ohlcv['open'],
            high=ohlcv['high'],
            low=ohlcv['low'],
            close=ohlcv['close'],
            name=st.session_state.current_ticker
        ),
        row=1, col=1
    )

    # 이동평균선 추가
    colors = {
        f'EMA{ema_period}': 'blue',
        f'MA{ma_long_period}': 'red',
        f'MA{ma_mid_periods[0]}': 'green',
        f'MA{ma_mid_periods[1]}': 'orange',
        f'MA{ma_mid_periods[2]}': 'purple'
    }
    
    for ma_name, color in colors.items():
        line_width = 3 if ma_name == f'EMA{ema_period}' or ma_name == f'MA{ma_long_period}' else 1

        fig.add_trace(
            go.Scatter(
                x=ohlcv.index,
                y=ohlcv[ma_name],
                name=ma_name,
                line=dict(color=color, width=line_width),
                opacity=0.7
            ),
            row=1, col=1
        )

    # 시그널 포인트 추가
    signal_points = ohlcv[signals]['close']
    fig.add_trace(
        go.Scatter(
            x=signal_points.index,
            y=signal_points+10,
            mode='markers',
            name='Signal',
            marker=dict(
                symbol='triangle-down',
                size=10,
                color='red'
            )
        ),
        row=1, col=1
    )

    # 거래량 차트 추가
    colors = ['red' if row['close'] < row['open'] else 'green' 
             for i, row in ohlcv.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=ohlcv.index,
            y=ohlcv['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.5
        ),
        row=2, col=1
    )
    # 차트 레이아웃 설정
    fig.update_layout(
        title='Trading Strategy Analysis',
        yaxis_title='Price',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    # 차트 스타일 설정
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
    yfinance api 제한으로 인해 날짜 선택 불가능
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
    
    # 티커 선택
    default_tickers = {
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
    
    # 설명 추가
    st.sidebar.subheader("현재 전략 설명")
    st.sidebar.markdown("1) EMA와 장기 MA가 평행한 구간 찾기(허용오차내)")
    st.sidebar.markdown("2) 중기 MA들이 모두 양의 기울기")
    st.sidebar.markdown("3) 눌림목 찾기(눌림목 확인 기간, 눌림목 허용 범위)")
    # 전략 파라미터 설정
    st.sidebar.subheader('이동평균선 파라미터')
    ema_period = st.sidebar.slider('EMA 기간', 50, 200, 120, 1)
    ma_long_period = st.sidebar.slider('장기 MA 기간', 50, 200, 111, 1)


    # 중기 이동평균선 기간 설정
    st.sidebar.subheader('중기 이동평균선 기간')
    ma_period1 = st.sidebar.slider('첫 번째 MA 기간', 20, 100, 25, 1)
    ma_period2 = st.sidebar.slider('두 번째 MA 기간', 20, 100, 33, 1)
    ma_period3 = st.sidebar.slider('세 번째 MA 기간', 20, 100, 49, 1)
    ma_mid_periods = (ma_period1, ma_period2, ma_period3)
    
    st.sidebar.subheader('전략 파라미터')
    tolerance = st.sidebar.slider('평행 허용 오차', 0.0000, 5e-5, 1e-6, 1e-6, format='%.6f')
    compression_period = st.sidebar.slider('눌림목 확인 기간', 5, 50, 20)
    compression_threshold = st.sidebar.slider('눌림목 허용 범위', 0.01, 0.20, 0.05, format='%.2f')
    
    ### calculation of signal counts for all tickers
    # 현재 파라미터 저장
    current_params = {
        'tolerance': tolerance,
        'compression_period': compression_period,
        'compression_threshold': compression_threshold,
        'ema_period': ema_period,
        'ma_long_period': ma_long_period,
        'ma_mid_periods': ma_mid_periods
    }
    
    # 캔들 주기가 변경되었거나 파라미터가 변경되었을 때 시그널 재계산
    if st.session_state.last_interval != interval or \
       st.session_state.last_params != current_params or \
       not st.session_state.signal_counts:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(default_tickers.keys()):
            status_text.text(f'분석 중... {ticker}')
            count = calculate_signals_for_ticker(ticker, start_date, end_date, current_params)
            st.session_state.signal_counts[ticker] = count
            progress_bar.progress((i + 1) / len(default_tickers))
            time.sleep(1)
        
        status_text.empty()
        progress_bar.empty()
        st.session_state.last_params = current_params
        st.session_state.last_interval = interval  # 현재 interval 저장
    
    # 시그널 수에 따라 티커 정렬
    sorted_tickers = sorted(
        default_tickers.keys(),
        key=lambda x: st.session_state.signal_counts.get(x, 0),
        reverse=True
    )
    


    # 섹터별로 정렬된 리스트 생성
    st.sidebar.subheader('종목 선택')
    sorted_tickers = sorted(default_tickers.keys())

    selected_ticker = st.sidebar.selectbox(
        '분석할 종목 선택',
        options=sorted_tickers,
        format_func=lambda x: f'{x} - {default_tickers[x]} ({st.session_state.signal_counts.get(x, 0)}개 시그널)'
    )
    
    # 시그널 수가 있는 종목만 보기 옵션
    show_only_signals = st.sidebar.checkbox('시그널이 있는 종목만 보기')
    if show_only_signals:
        filtered_tickers = [t for t in sorted_tickers if st.session_state.signal_counts.get(t, 0) > 0]
        if filtered_tickers:
            selected_ticker = st.sidebar.selectbox(
                '시그널이 있는 종목',
                options=filtered_tickers,
                format_func=lambda x: f'{x} - {default_tickers[x]} ({st.session_state.signal_counts.get(x, 0)}개 시그널)'
            )
        else:
            st.sidebar.warning('현재 조건에서 시그널이 있는 종목이 없습니다.')


    # 사용자 정의 티커 입력
    custom_ticker = st.sidebar.text_input('다른 종목 티커 입력 (예: IBM)', '')
    ticker = custom_ticker if custom_ticker else selected_ticker


    # 세션 상태 체크를 티커 변경도 포함하도록 수정
    if st.session_state.ohlcv_data is None or \
       (st.session_state.start_date != start_date or \
        st.session_state.end_date != end_date or \
        st.session_state.current_ticker != ticker or \
        st.session_state.current_interval != interval):
        try:
            with st.spinner('데이터를 불러오는 중...'):
                # 로컬 데이터 경로 설정
                data_path = f'data/{ticker}_{interval}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
                
                try:
                    # 로컬에서 데이터 불러오기 시도
                    st.session_state.ohlcv_data = pd.read_csv(data_path, index_col=0, parse_dates=True)
                    st.info(f'로컬 데이터를 불러왔습니다: {data_path}')
                except FileNotFoundError:
                    # 로컬 데이터가 없는 경우 yfinance에서 데이터 가져오기
                    st.warning('로컬 데이터가 없어 yfinance에서 데이터를 가져와야합니다.')
                    

                # stock = yf.Ticker(ticker)
                # st.session_state.ohlcv_data = stock.history(
                #     start=start_date,
                #     end=end_date,
                #     interval=interval
                # )
                # time.sleep(1)
                if len(st.session_state.ohlcv_data) == 0:
                    st.error(f'데이터가 없습니다: {ticker}')
                    return
                st.session_state.ohlcv_data.columns = st.session_state.ohlcv_data.columns.str.lower()
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date
                st.session_state.current_ticker = ticker
                st.session_state.current_interval = interval
        except Exception as e:
            st.error(f'데이터 로딩 중 오류 발생: {str(e)}')
            return
    
    # 데이터가 있으면 분석 실행
    if st.session_state.ohlcv_data is not None:
        try:
            # 전략 분석
            ohlcv, signals = analyze_strategy(
                st.session_state.ohlcv_data.copy(),
                tolerance=tolerance,
                compression_period=compression_period,
                compression_threshold=compression_threshold,
                ema_period=ema_period,
                ma_long_period=ma_long_period,
                ma_mid_periods=ma_mid_periods
            )
            
            # 시그널 통계
            total_signals = signals.sum()
            st.sidebar.metric("발견된 시그널 수", total_signals)
            
            # 차트 표시
            plot_analysis_streamlit(ohlcv, signals, ema_period, ma_long_period, ma_mid_periods)
            
            # 시그널 날짜 표시
            if total_signals > 0:
                st.subheader('시그널 발생 날짜')
                signal_dates = []
                for idx in ohlcv[signals].index:
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
