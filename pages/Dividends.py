import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
import datetime
from utils import load_css
load_css()

st.title('Dividends')
col1, col2 = st.columns(2)
ticker = col1.text_input("Ticker", value='MSFT')
period = col2.selectbox("Periodd", options=[
        '1mo', '3mo', '6mo', 'ytd', '1y', '2y',
        '5y', '10y', '15y', '20y', '25y', 'max'
    ],
    index=6
)

if ticker:
    ticker = yf.Ticker(ticker)
    history = ticker.history(period=period, auto_adjust=False)
    dividends = history.loc[history.Dividends > 0, 'Dividends'].to_frame()

    # Number of distributions per year
    dist_per_year = dividends.Dividends.resample('365d').count().mode()[0]

    # Rolling sum of dividends with smoothing to ignore special dividends.
    # Might not be 100% accurate
    dividends['SmoothedYearlyDiv'] = (dividends
        .Dividends
        .rolling('365d')
        .apply(lambda x: pd.Series.mode(x)[0])
        .rolling('350d', min_periods=dist_per_year-1)
        .sum()
    )
    # Growth in dividends since beginning of timeframe
    dividends['DivGrowth'] = dividends['Dividends'] / dividends['Dividends'].iloc[0] - 1
    dividends = dividends.reset_index()

    # Number of years between first and last dividend in timeframe
    n_years = (dividends.iloc[-1].Date - dividends.iloc[0].Date) / datetime.timedelta(365.2425)
    # CAGR of dividend
    div_cagr = (1 + dividends.iloc[-1].DivGrowth) ** (1 / n_years) - 1

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label=f"Last 12m dividend",
        value=f"${dividends.SmoothedYearlyDiv.iloc[-1]:,.2f}"
    )
    col2.metric(
        label=f"Current Yield",
        value=f"{dividends.SmoothedYearlyDiv.iloc[-1] / history.iloc[-1].Close:,.2%}"
    )
    col3.metric(
        label=f"Average Yield",
        value=f"TBD"
    )
    col4.metric(
        label=f"{period} Dividend CAGR",
        value=f"{div_cagr:+,.1%}"
    )

    chart = alt.Chart(dividends).mark_line(color=st.secrets["theme"]['primaryColor']).encode(
        x=alt.X('Date:T'),
        y=alt.Y(
            'SmoothedYearlyDiv',
            title='TTM dividends',
            axis=alt.Axis(format='$.2f')
        )
    )
    st.altair_chart(chart, use_container_width=True)
