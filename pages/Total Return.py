import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
import datetime
from utils import load_css
load_css()

st.title('Total return calculator')
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
    history['CumulativeShares'] = ((history.Dividends / history.Close) + 1).cumprod()
    history['PriceReturn'] = history['Close'] / history['Close'].iloc[0] - 1
    history['TotalReturn'] = history['Adj Close'] / history['Adj Close'].iloc[0] - 1
    history['PriceDrawdown'] = history['Close'] / history['Close'].cummax() - 1
    history['TotalDrawdown'] = history['Adj Close'] / history['Adj Close'].cummax() - 1
    history = history.reset_index()

    n_years = (history.iloc[-1].Date - history.iloc[0].Date) / datetime.timedelta(365.2425)


    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label=f"{period} price return",
        value=f"{history.iloc[-1].PriceReturn:+,.0%}"
    )
    col2.metric(
        label=f"{period} total return",
        value=f"{history.iloc[-1].TotalReturn:+,.0%}"
    )
    annualized_return = (1 + history.iloc[-1].TotalReturn) ** (1 / n_years) - 1
    col3.metric(
        label='Annulized total return',
        value=f"{annualized_return:.1%}"
    )
    col4.metric(
        label='Share count',
        value=f"{history.CumulativeShares.iloc[-1] - 1:+.0%}"
    )

    returns = pd.melt(
        history,
        id_vars=['Date'],
        value_vars=['PriceReturn', 'TotalReturn'],
        var_name='return_type',
        value_name='return_percentage'
    )

    chart = alt.Chart(returns).mark_line().encode(
        x='Date:T',
        y=alt.Y(
            'return_percentage:Q',
            title='Return',
            axis=alt.Axis(format='%'),
        ),
        color=alt.Color(
            'return_type:N',
            title='Return Type:',
            scale=alt.Scale(
                range=[
                    st.secrets["theme"]['primaryColor'],
                    st.secrets["theme"]['secondaryColor']
                ]
            ),
            legend=alt.Legend(
                orient='top',
            )
        ),
        tooltip=[
            alt.Tooltip('Date:T'),
            alt.Tooltip('return_percentage', title='Return', format='0,.0%'),
            alt.Tooltip('return_type', title='Type')
        ]
    ).interactive(bind_y=False)
    st.altair_chart(chart, use_container_width=True)

    drawdown = pd.melt(
        history,
        id_vars=['Date'],
        value_vars=['PriceDrawdown', 'TotalDrawdown'],
        var_name='return_type',
        value_name='return_percentage'
    )

    chart = alt.Chart(drawdown).mark_line().encode(
        x='Date:T',
        y=alt.Y(
            'return_percentage:Q',
            title='Return', 
            axis=alt.Axis(format='%'),
        ),
        color=alt.Color(
            'return_type:N',
            title='',
            scale=alt.Scale(
                range=[
                    st.secrets["theme"]['primaryColor'],
                    st.secrets["theme"]['secondaryColor']
                ]
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip('Date:T'),
            alt.Tooltip('return_percentage', title='Drawdown', format='0,.0%'),
            alt.Tooltip('return_type', title='Type')
        ]
    ).interactive(bind_y=False)
    st.altair_chart(chart, use_container_width=True)
