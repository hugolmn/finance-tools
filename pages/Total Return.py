import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
import numpy as np
import datetime
from utils import load_css
load_css()

def load_ticker_return(ticker, period):
    ticker = yf.Ticker(ticker)
    history = ticker.history(period=period, auto_adjust=False)
    history['CumulativeShares'] = ((history.Dividends / history.Close) + 1).cumprod()
    history['PriceReturn'] = history['Close'] / history['Close'].iloc[0] - 1
    history['TotalReturn'] = history['Adj Close'] / history['Adj Close'].iloc[0] - 1
    history['PriceDrawdown'] = history['Close'] / history['Close'].cummax() - 1
    history['TotalDrawdown'] = history['Adj Close'] / history['Adj Close'].cummax() - 1
    history = history.reset_index()
    return history

st.title('Total return calculator')
col1, col2, col3 = st.columns(3)
ticker = col1.text_input("Ticker")
period = col2.selectbox("Period", options=[
        '1mo', '3mo', '6mo', 'ytd', '1y', '2y',
        '5y', '10y', '15y', '20y', '25y', 'max'
    ],
    index=6
)
index = col3.selectbox(label='Index', options=[None, 'SPY', 'QQQ'])

if ticker:
    history = load_ticker_return(ticker, period)

    if index:
        history_index = load_ticker_return(index, period)
        history_index = history_index[['TotalReturn', 'TotalDrawdown']]
        history_index.columns = ['Index'+col for col in history_index.columns]
        history = pd.concat([history, history_index], axis=1)

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
        value_vars=history.columns[history.columns.str.contains('Return')],
        var_name='return_type',
        value_name='return_percentage'
    )

    # Selection for legend
    selection = alt.selection_multi(fields=['return_type'], bind='legend')
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['Date'], empty='none')

    # The basic line
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
                    st.secrets["theme"]['secondaryColor'],
                    'white'
                ],
                domain=[
                    'TotalReturn',
                    'PriceReturn',
                    'IndexTotalReturn'
                ]
            ),
            legend=alt.Legend(
                orient='top',
            )
        ),
        # tooltip=[
        #     alt.Tooltip('Date:T'),
        #     alt.Tooltip('return_percentage', title='Return', format='0,.0%'),
        #     alt.Tooltip('return_type', title='Type')
        # ],
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(returns).mark_point().encode(
        x='Date:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw text labels near the points, and highlight based on selection
    alt.Chart().mark_text()
    text = chart.mark_text(align='left', dx=5, dy=-15, filled=True).encode(
        text=alt.condition(nearest, 'return_percentage:Q', alt.value(''), format='.0%')
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(returns).mark_rule(color='gray').encode(
        x='Date:T',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    st.altair_chart(alt.layer(
            chart, selectors, rules, text
        ).interactive(bind_y=False),
        use_container_width=True
    )

    col1, col2 = st.columns(2)
    col1.metric(
        label=f"{period} max drawdown",
        value=f"{history.TotalDrawdown.min():+,.0%}"
    )
    col2.metric(
        label=f"Current drawdown",
        value=f"{history.iloc[-1].TotalDrawdown:+,.0%}"
    )

    drawdown = pd.melt(
        history,
        id_vars=['Date'],
        value_vars=history.columns[history.columns.str.contains('Drawdown')],
        var_name='drawdown_type',
        value_name='drawdown_percentage'
    )

    selection = alt.selection_multi(fields=['drawdown_type'], bind='legend')
    chart = alt.Chart(drawdown).mark_line().encode(
        x='Date:T',
        y=alt.Y(
            'drawdown_percentage:Q',
            title='Return', 
            axis=alt.Axis(format='%'),
        ),
        color=alt.Color(
            'drawdown_type:N',
            title='Drawdown Type:',
            scale=alt.Scale(
                range=[
                    st.secrets["theme"]['primaryColor'],
                    st.secrets["theme"]['secondaryColor'],
                    'white'
                ],
                domain=[
                    'TotalDrawdown',
                    'PriceDrawdown',
                    'IndexTotalDrawdown'
                ]
            ),
            legend=alt.Legend(orient='top')
        ),
        tooltip=[
            alt.Tooltip('Date:T'),
            alt.Tooltip('drawdown_percentage', title='Drawdown', format='0,.0%'),
            alt.Tooltip('drawdown_type', title='Type')
        ],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.15))
    ).add_selection(
        selection
    ).interactive(bind_y=False)
    st.altair_chart(chart, use_container_width=True)
