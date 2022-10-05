import streamlit as st
from streamlit.runtime.legacy_caching.caching import F
import yfinance as yf
import altair as alt
import pandas as pd
import numpy as np
import datetime
import seaborn as sns
from utils import load_css

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
    ).bfill().ffill()

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
st.title('Dividends')
col1, col2 = st.columns(2)
ticker = col1.text_input("Ticker", value='MSFT')
period = col2.selectbox("Periodd", options=[
        '5y', '10y', '15y', '20y', '25y', '30y', '35y', '40y', 'max'
    ],
    index=2
)

if ticker:
    # Load historical data
    history = load_ticker_data(
        ticker=ticker,
        period=f"{int(period.split('y')[0]) + 1}y" if 'y' in period else period
    )

    dividends = process_dividend_history(history)

    # Number of years between first and last dividend in timeframe
    n_years = (dividends.iloc[-1].Date - dividends.iloc[0].Date) / datetime.timedelta(365.2425)
    # CAGR of dividend
    div_cagr = (1 + dividends.iloc[-1].DivGrowth) ** (1 / n_years) - 1

    # Merge dividends with price history
    df = pd.merge(
        left=history.reset_index(),
        right=dividends.drop(columns=['Dividends']),
        on='Date',
        how='left'
    ).ffill(limit=300).fillna(0)

    index_first_dividend = df[df.YearlyDividends > 0].index[0]
    df = df.loc[index_first_dividend:]

    # Drop where dividends is null
    df = df[df.YearlyDividends.notna()]
    # Calculate dividend yield base on TTM distributions
    df['DividendYield'] = df.YearlyDividends / df.Close

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label=f"Annual dividends",
        value=f"${df.YearlyDividends.iloc[-1]:,.2f}"
    )
    col2.metric(
        label=f"Current Yield",
        value=f"{df.DividendYield.iloc[-1]:,.2%}"
    )
    col3.metric(
        label=f"{period} Median Yield",
        value=f"{df.DividendYield.dropna().median():,.2%}"
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

    # Calculate quantiles of dividend yield
    quantiles = df.DividendYield.quantile(q=np.arange(0, 1.1, .1))
    yield_df = pd.DataFrame(df.YearlyDividends.to_numpy()[:, None] / quantiles.to_numpy(), index=df.Date)
    yield_df.columns = [f"Top {decile * 10}%" for decile in yield_df.columns[::-1]]
    yield_df = yield_df.reset_index()

    # Create color palette and scale for legend
    palette = sns.color_palette("vlag_r", len(quantiles)-1).as_hex()
    scale = alt.Scale(domain=yield_df.columns[1:-1].tolist(), range=palette)

    st.header(f"{ticker} {period} Yield Percentile Chart")
    st.write(f"Current Yield: {df.iloc[-1].DividendYield:.2%} \
        (Top {1 - df.DividendYield.rank(pct=True).iloc[-1]:.0%})")

    # Create layers for chart
    def make_layer(yield_df, col1, col2):
        return alt.Chart(yield_df.assign(color=col1)).mark_area().encode(
            x=alt.X('Date:T', title='', axis=alt.Axis(format='%Y')),
        ).encode(
            y=alt.Y(
                f"{col1}:Q",
                title='Stock Price',
                axis=alt.Axis(format='$.0f'),
                scale=alt.Scale(zero=False)
            ),
            y2=alt.Y2(
                f"{col2}:Q",
                title='Stock Price'
            ),
            color=alt.Color(
                f"color:N",
                title='Yield',
                scale=scale,
                legend=alt.Legend(
                    titleFontSize=15,
                    labelFontSize=10,
                    titleLimit=0
                )
            ),
            opacity=alt.value(0.8)
        )

    layers=[]
    for col1, col2 in zip(yield_df.columns[1:-1], yield_df.columns[2:]):
        layers.append(make_layer(yield_df, col1, col2))

    price = alt.Chart(df).mark_line(color='black').encode(
        x='Date:T',
        y='Close:Q'
    )
    layers.append(price)
    
    chart = alt.layer(
            *layers
        ).configure(
            font='Lato'
        ).configure_axisY(
            labelFontSize=15,
            titleFontSize=10
        ).configure_axisX(
            labelAngle=-45,
            labelFontSize=15
        )

    st.altair_chart(
        chart.interactive(bind_y=False),
        use_container_width=True
    )
