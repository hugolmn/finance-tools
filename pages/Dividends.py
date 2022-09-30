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
        '5y', '10y', '15y', '20y', '25y', 'max'
    ],
    index=2
)

if ticker:
    ticker = yf.Ticker(ticker)
    history = ticker.history(period=period, auto_adjust=False)
    dividends = history.loc[history.Dividends > 0, 'Dividends'].to_frame()

    # Number of distributions per year
    dist_per_year = dividends.Dividends.resample('365d').count().mode()[0]

    # Rolling median of Dividends over 5 distributions to ignore special dividends
    # Might not be 100% accurate
    dividends['SmoothedDividends'] = (dividends
        .Dividends
        .rolling(5, center=True)
        .median()
    )

    dividends = dividends.loc[dividends.SmoothedDividends.first_valid_index():]
    dividends['SmoothedDividends'] = dividends.SmoothedDividends.combine_first(dividends.Dividends)
    dividends['YearlyDividends'] = dividends.SmoothedDividends * dist_per_year

    # Growth in dividends since beginning of timeframe
    dividends['DivGrowth'] = dividends['SmoothedDividends'] / dividends['SmoothedDividends'].iloc[0] - 1
    dividends = dividends.reset_index()

    # Number of years between first and last dividend in timeframe
    n_years = (dividends.iloc[-1].Date - dividends.iloc[0].Date) / datetime.timedelta(365.2425)
    # CAGR of dividend
    div_cagr = (1 + dividends.iloc[-1].DivGrowth) ** (1 / n_years) - 1

    df = pd.merge(
        left=history.reset_index(),
        right=dividends.drop(columns=['Dividends']),
        on='Date',
        how='left'
    ).ffill()

    df['DividendYieldTTM'] = df.YearlyDividends / df.Close

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label=f"Last 12m dividend",
        value=f"${df.YearlyDividends.iloc[-1]:,.2f}"
    )
    col2.metric(
        label=f"Current Yield",
        value=f"{df.DividendYieldTTM.iloc[-1]:,.2%}"
    )
    col3.metric(
        label=f"{period} Average Yield",
        value=f"{df.DividendYieldTTM.dropna().mean():,.2%}"
    )
    col4.metric(
        label=f"{period} Dividend CAGR",
        value=f"{div_cagr:+,.1%}"
    )

    base = alt.Chart(df).mark_line(interpolate='step-after').encode(
        x=alt.X('Date:T')
    )

    dividend_chart = base.encode(
        y=alt.Y(
            'YearlyDividends:Q',
            title='Yearly Dividends',
            axis=alt.Axis(format='$.2f'),
            scale=alt.Scale(zero=False)
        ),
        color=alt.value(st.secrets["theme"]['primaryColor'])
    )

    price_chart = base.encode(
        y=alt.Y(
            'Close:Q',
            title='Stock Price',
            axis=alt.Axis(format='$.2f'),
            scale=alt.Scale(zero=False)
        ),
        color=alt.value(st.secrets["theme"]['secondaryColor'])
    )

    chart = alt.layer(dividend_chart, price_chart).resolve_scale(
        y = 'independent'
    ).interactive(bind_y=False)

    st.altair_chart(chart, use_container_width=True)
    
