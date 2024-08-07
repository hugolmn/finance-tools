import streamlit as st
from streamlit.runtime.legacy_caching.caching import F
import yfinance as yf
import altair as alt
import pandas as pd
import numpy as np
import datetime
import seaborn as sns
from utils import load_css

st.set_page_config(layout="wide")

def load_ticker_data(ticker, period):
    return yf.Ticker(ticker).history(
        period=period,
        auto_adjust=False
    )

def process_dividend_history(history):
    # Get df with dividend distributions
    dividends = history.loc[history.Dividends > 0, 'Dividends'].to_frame()

    # Keep one distribution per month
    dividends['Month'] = dividends.index.to_period('1M')
    dividends = (dividends
        .reset_index()
        .groupby('Month', as_index=False)
        .first()
        .set_index('Date')
        .drop(columns=['Month'])
    )

    # Count distributions per year
    yearly_distributions = dividends.groupby(dividends.index.year).Dividends.count()
    # First and current year do not have all distributions, use next and previous year's numbers
    yearly_distributions.iloc[0] = yearly_distributions.iloc[1]
    yearly_distributions.iloc[-1] = yearly_distributions.iloc[-2]
    # Map values
    dividends['AnnualDividendCount'] = dividends.index.year.map(yearly_distributions)
    dividends['AnnualDividendCount'] = pd.cut(
        dividends.AnnualDividendCount,
        bins=[-np.inf, 0, 1, 2, 3, 4, 8, 12],
        labels=[0, 1, 2, 4, 4, 4, 12],
        ordered=False,
    ).astype(int)

    dividends['SmoothedDividends'] = (dividends
        .Dividends
        .rolling(5, center=True)
        .median()
    )
    # ).bfill().ffill()
    dividends['SmoothedDividends'] = dividends.SmoothedDividends.combine_first(dividends.Dividends)

    # dividends['YearlyDividends'] = dividends.SmoothedDividends * dividends.AnnualDividendCount

    dividends['YearlyDividends']= np.where(
        dividends.AnnualDividendCount <= 3, 
        dividends.index.year.map(dividends.groupby(dividends.index.year).Dividends.sum()),
        dividends.SmoothedDividends * dividends.AnnualDividendCount
    )

    # Get at least one full year
    dividends = dividends.loc[dividends.index > dividends.index[0] + datetime.timedelta(days=365)]

    # Growth in dividends since beginning of timeframe
    dividends['DivGrowth'] = dividends['YearlyDividends'] / dividends['YearlyDividends'].iloc[0] - 1
    dividends = dividends.reset_index()
    
    return dividends

load_css()
st.title('Dividend Chart')
st.markdown("""
    - Subscribe to [the newsletter](https://dividendchart.substack.com/) to be the first to receive the most interesting charts!
    - Follow me on Twitter [@DividendChart](https://twitter.com/DividendChart).
""")
col1, col2 = st.columns(2)
ticker = col1.text_input("Ticker", value='MSFT')
period = col2.selectbox("Period", options=[
        '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
    ],
    index=2
)

if ticker:
    from utils import generate_dividend_chart
    price_chart, yield_chart, drawdown_chart = generate_dividend_chart(ticker, period)
    st.altair_chart(price_chart, use_container_width=True, theme='streamlit')
    st.altair_chart(yield_chart, use_container_width=True, theme='streamlit')
    st.altair_chart(drawdown_chart, use_container_width=True, theme='streamlit')
