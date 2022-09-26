import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
from utils import load_css
load_css()

st.title('Total return calculator')
col1, col2 = st.columns(2)
ticker = col1.text_input("Ticker", value='MSFT')
period = col2.selectbox("Periodd", options=['1mo', '3mo', '6mo', 'ytd', '1y', '2y', '5y', '10y', 'max'], index=0)

if ticker:
    ticker = yf.Ticker(ticker)
    history = ticker.history(period=period)
    history['CumulativeShares'] = ((history.Dividends / history.Close) + 1).cumprod()
    history['PriceReturn'] = history.Close / history.Close.iloc[0] - 1
    history['TotalReturn'] = history.CumulativeShares * history.Close / history.Close.iloc[0] - 1
    history = history.reset_index()

    col1, col2 = st.columns(2)
    col1.metric(
        label=f"{period} price return",
        value=f"{history.iloc[-1].PriceReturn:+.0%}"
    )
    col2.metric(
        label=f"{period} total return",
        value=f"{history.iloc[-1].TotalReturn:+.0%}"
    )

    history = pd.melt(
        history,
        id_vars=['Date'],
        value_vars=['PriceReturn', 'TotalReturn'],
        var_name='return_type',
        value_name='return_percentage'
    )

    chart = alt.Chart(history).mark_line().encode(
        x='Date:T',
        y=alt.Y(
            'return_percentage:Q',
            axis=alt.Axis(format='%'),
        ),
        color=alt.Color(
            'return_type:N',
            scale=alt.Scale(
                range=[
                    st.secrets["theme"]['primaryColor'],
                    st.secrets["theme"]['secondaryColor']
                ]
            )
        ),
        tooltip=[
            alt.Tooltip('Date:T'),
            alt.Tooltip('return_percentage', title='Return', format='0,.0%'),
            alt.Tooltip('return_type', title='Type')
        ]
    ).interactive(bind_y=False)
    st.altair_chart(chart, use_container_width=True)
