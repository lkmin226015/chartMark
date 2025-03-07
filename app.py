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

    # # 매수 시그널 표시 - marker
    # signal_points = df[signals]['close']
    # fig.add_trace(
    #     go.Scatter(
    #         x=signal_points.index,
    #         y=signal_points,
    #         mode='markers',
    #         name='Buy Signal',
    #         marker=dict(
    #             symbol='triangle-up',
    #             size=12,
    #             color='red'
    #         )
    #     ),
    #     row=1, col=1
    # )

    # 매수 시그널 각각을 빨간색 수직선으로 표시
    signal_points = df[signals]['close']
    for signal_index in signal_points.index:
        fig.add_trace(
            go.Scatter(
                x=[signal_index, signal_index],
                y=[df['low'].min(), df['high'].max()],
                mode='lines',
                name='Buy Signal',
                line=dict(
                    color='blue',
                    width=1
                ),
                showlegend=False  # 범례에 중복 표시되지 않도록 설정
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
        hovermode='x unified',
        hoversubplots='axis'
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
            macd_fast=params['macd_fast'],
            macd_slow=params['macd_slow'],
            macd_signal=params['macd_signal'],
            cci_period=params['cci_period'],
            cci_signal=params['cci_signal'],
            rsi_period=params['rsi_period'],
            rsi_signal=params['rsi_signal']
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

def analyze_signal_performance(df, signals, lookback_period, target_return, max_loss):
    """
    시그널 발생 후 수익률 분석 - 목표 수익률 또는 손절 수익률 도달 시 거래 종료
    """
    signal_dates = df[signals].index
    success_count = 0
    loss_count = 0
    max_returns = []
    min_returns = []
    days_to_target = []
    days_to_loss = []
    
    for signal_date in signal_dates:
        idx = df.index.get_loc(signal_date)
        if idx + lookback_period >= len(df):
            continue
            
        # 시그널 발생 시점부터 lookback_period 동안의 데이터
        signal_price = df.iloc[idx]['close']
        forward_slice = df.iloc[idx:idx + lookback_period + 1]
        
        # 각 캔들에서 목표 수익률과 손절 수익률 도달 여부 확인
        for i, row in forward_slice.iterrows():
            high_return = ((row['high'] - signal_price) / signal_price * 100)
            low_return = ((row['low'] - signal_price) / signal_price * 100)
            
            # 같은 캔들에서 고가가 목표 수익률, 저가가 손절 수익률에 도달한 경우
            # 고가가 먼저 도달한 것으로 간주
            if high_return >= target_return:
                success_count += 1
                days = (i - signal_date).days
                days_to_target.append(days)
                max_returns.append(high_return)
                break
            elif low_return <= -max_loss:
                loss_count += 1
                days = (i - signal_date).days
                days_to_loss.append(days)
                min_returns.append(low_return)
                break
            
            # 마지막 캔들까지 목표 수익률이나 손절 수익률에 도달하지 못한 경우
            if i == forward_slice.index[-1]:
                # 최종 수익률 기록
                max_return = ((forward_slice['high'].max() - signal_price) / signal_price * 100)
                min_return = ((forward_slice['low'].min() - signal_price) / signal_price * 100)
                max_returns.append(max_return)
                min_returns.append(min_return)
    
    total_signals = len(signal_dates)
    if total_signals == 0:
        return {
            'success_rate': 0,
            'loss_rate': 0,
            'avg_max_return': 0,
            'avg_min_return': 0,
            'avg_days_to_target': 0,
            'avg_days_to_loss': 0,
            'total_signals': 0,
            'success_count': 0,
            'loss_count': 0,
            'timeout_count': 0
        }
    
    timeout_count = total_signals - success_count - loss_count
    
    return {
        'success_rate': (success_count / total_signals * 100) if total_signals > 0 else 0,
        'loss_rate': (loss_count / total_signals * 100) if total_signals > 0 else 0,
        'timeout_rate': (timeout_count / total_signals * 100) if total_signals > 0 else 0,
        'avg_max_return': sum(max_returns) / len(max_returns) if max_returns else 0,
        'avg_min_return': sum(min_returns) / len(min_returns) if min_returns else 0,
        'avg_days_to_target': sum(days_to_target) / len(days_to_target) if days_to_target else 0,
        'avg_days_to_loss': sum(days_to_loss) / len(days_to_loss) if days_to_loss else 0,
        'total_signals': total_signals,
        'success_count': success_count,
        'loss_count': loss_count,
        'timeout_count': timeout_count
    }

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
    st.sidebar.subheader("현재 전략 설명 - 아래 조건을 모두 만족하는 경우 시그널 발생")
    st.sidebar.markdown("1) MACD가 Signal 이상으로 상승")
    st.sidebar.markdown("2) CCI가 Signal 이상으로 상승")
    st.sidebar.markdown("3) RSI가 Signal 이상으로 상승")
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

    # 전략 파라미터 설정 섹션 아래에 수익률 분석 파라미터 추가
    st.sidebar.subheader('수익률 분석 파라미터')
    col1, col2 = st.sidebar.columns(2)
    with col1:
        lookback_period = st.slider('분석 기간 (캔들 수)', 1, 100, 20)
    with col2:
        target_return = st.slider('목표 수익률 (%)', 1, 50, 5)
        max_loss = st.slider('손절 수익률 (%)', 1, 50, 5)

    ### calculation of signal counts for all tickers
    # 현재 파라미터 저장
    current_params = {
        'macd_fast': macd_fast,
        'macd_slow': macd_slow,
        'macd_signal': macd_signal,
        'cci_period': cci_period,
        'cci_signal': cci_signal,
        'rsi_period': rsi_period,
        'rsi_signal': rsi_signal
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

    ticker = selected_ticker

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
                    #st.info(f'로컬 데이터를 불러왔습니다: {data_path}')
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
            
            # 수익률 분석 결과 표시
            if total_signals > 0:
                st.subheader('시그널 성과 분석')
                performance = analyze_signal_performance(df, signals, lookback_period, target_return, max_loss)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("##### 수익 분석")
                    st.metric(
                        f"{lookback_period}캔들 내 {target_return}% 달성",
                        f"{performance['success_rate']:.1f}%"
                    )
                    if performance['success_count'] > 0:
                        st.metric(
                            "목표 수익률 달성까지 평균 소요 기간",
                            f"{performance['avg_days_to_target']:.1f}캔들"
                        )
                
                with col2:
                    st.markdown("##### 손실 분석")
                    st.metric(
                        f"{lookback_period}캔들 내 {max_loss}% 손실",
                        f"{performance['loss_rate']:.1f}%"
                    )
                    if performance['loss_count'] > 0:
                        st.metric(
                            "손절 수익률 도달까지 평균 소요 기간",
                            f"{performance['avg_days_to_loss']:.1f}캔들"
                        )
                
                with col3:
                    st.markdown("##### 미달성 분석")
                    st.metric(
                        "목표/손절 미달성 비율",
                        f"{performance['timeout_rate']:.1f}%"
                    )
                    st.metric(
                        "평균 최종 수익률",
                        f"{performance['avg_max_return']:.1f}%"
                    )
            
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
