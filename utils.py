import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
import seaborn as sns
import datetime

def load_css():
    return st.markdown(
        """
        <style>
        div[data-testid="metric-container"] {
        background-color: rgba(59, 151, 243, 0.05);
        border: 1px solid rgba(59, 151, 243, 0.25);
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        }
        div[data-testid="metric-container"] > div[style*="color: rgb(9, 171, 59);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #3B97F3 !important;
        }
        div[data-testid="metric-container"] > div[style*="color: rgb(255, 43, 43);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #F27716 !important;
        }
        div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: white !important;
        }
        div[data-baseweb="tab-list"] > div[data-baseweb="tab-highlight"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
           background-color: #3B97F3 !important;
        }
        # div[class*="stSelectbox"] > div[aria-expanded="trus"] > div {
        #    overflow-wrap: break-word;
        #    white-space: break-spaces;
        #    background-color: #3B97F3 !important;
        # }
        .st-dr{
            border-color: #3B97F3
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def streamlit_theme():
    font = "Lato"
    primary_color = "#FAFAFA"
    font_color = "#FAFAFA"
    grey_color = "#49494a"
    label_color = "#787878"
    base_size = 16
    lg_font = base_size * 1.20
    sm_font = base_size * 0.8
    xl_font = base_size * 2

    config = {
        "config": {
            "padding": 20,
            "background": "#0e1117",
            "title": {
                "font": font,
                "fontSize": xl_font,
                "color": font_color,
            },
            "axis": {
                "titleFont": font,
                "titleColor": font_color,
                "titleFontSize": lg_font,
                "labelFont": font,
                "labelColor": label_color,
                "labelFontSize": sm_font,
                "gridColor": grey_color,
                "domainColor": grey_color,
                "tickColor": grey_color,
            },
            "axisX": {
                "labelAngle": -90,
            },
            "axisY": {
                "orient": "left",
                # "titleX": -1200,
                "titleY": -5,
                "titleX": -35,
                "titleAngle": 0,
                "titleAlign": "left",
                # "position": 10
                # "offset": 10,
                # "labelOffset": 10
                "labelPadding": 5
            },
            "header": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": base_size,
                "titleFontSize": base_size,
            },
            "legend": {
                "padding": 25,
                "titleFont": font,
                "titleColor": label_color,
                "titleFontSize": base_size,
                "titleOrient": "left",
                "labelFont": font,
                "labelColor": label_color,
                "labelFontSize": base_size,
            },
            "view": {
                "strokeWidth": 0
            },
            "text": {
                "color": font_color,
                "align": "left",
                "baseline": "middle",
                "fontWeight": "bold",
                "fontSize": lg_font,
                "dx": 3
            }
        }
    }
    return config

alt.themes.register("test", streamlit_theme)
alt.themes.enable("test")
alt.data_transformers.disable_max_rows()

def load_ticker_data(ticker: str, period: str) -> pd.DataFrame:
    """
    Returns stock history from a ticker and a period.

    Parameters:
    ----------
    - ticker: str
        Ticker from yahoo finance
    - period: str
        Period to collect data from (ytd, 1wk, 1m, 6m, 1y, 10y, ..., max)

    Returns:
    -------
    - pd.DataFrame containing stock historical data
    """
    return yf.Ticker(ticker).history(
        period=period,
        auto_adjust=False
    )

def process_dividend_history(history: pd.DataFrame) -> pd.DataFrame:
    # Get df with dividend distributions
    dividends = history.loc[history.Dividends > 0, 'Dividends'].to_frame()

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
    #dividends = dividends.loc[dividends.index > dividends.index[0] + datetime.timedelta(days=365)]

    # Growth in dividends since beginning of timeframe
    dividends['DivGrowth'] = dividends['YearlyDividends'] / dividends['YearlyDividends'].iloc[0] - 1
    dividends = dividends.reset_index()
    
    return dividends

def generate_dividend_chart(ticker, period, currency_symbol='$'):
    # Load historical data
    history = load_ticker_data(
        ticker=ticker,
        period=f"{int(period.split('y')[0])}y" if 'y' in period else period
    )

    dividends = process_dividend_history(history)

    # Merge dividends with price history
    df = pd.merge(
        left=history.reset_index(),
        right=dividends.drop(columns=['Dividends']),
        on='Date',
        how='left'
    ).ffill(limit=300).fillna(0)

    df['Drawdown'] = df.Close / df.Close.cummax() - 1

    # Keep data from first dividend
    index_first_dividend = df[df.YearlyDividends > 0].index[0]
    df = df.loc[index_first_dividend:]

    # Drop where dividends is null
    df = df[df.YearlyDividends.notna()]
    # Calculate dividend yield base on TTM distributions
    df['DividendYield'] = df.YearlyDividends / df.Close

    # Calculate quantiles of dividend yield
    quantiles = df.DividendYield.quantile(q=np.arange(0, 1.1, .1))
    yield_df = pd.DataFrame(df.YearlyDividends.to_numpy()[:, None] / quantiles.to_numpy(), index=df.Date)
    yield_df.columns = [f"{decile * 10}%" for decile in yield_df.columns[::-1]]
    yield_df = yield_df.reset_index()

    # Set locale options
    if currency_symbol in ['€', 'CHF']:
        alt.renderers.set_embed_options(
            formatLocale={ 
                'currency': ['', f'\u00a0{currency_symbol}']
            }
        )
    else:
        alt.renderers.set_embed_options(
            formatLocale={
                'currency': [f'\u00a0{currency_symbol}', '']
            }
        )

    # Create color palette and scale for legend
    palette = sns.color_palette("vlag_r", len(quantiles)-1).as_hex()
    scale = alt.Scale(domain=yield_df.columns[1:-1].tolist(), range=palette)


    upside_downside = df.DividendYield.iloc[-1] / df.DividendYield.quantile(q=0.5)
    if upside_downside > 1: 
        upside_downside_str = f'{upside_downside - 1: .0%} upside to median yield (~{currency_symbol}{upside_downside * df.Close.iloc[-1]:.0f}).'
    else:
        upside_downside_str = f'{upside_downside - 1: .0%} downside to median yield (~{currency_symbol}{upside_downside * df.Close.iloc[-1]:.0f}).'

    # Create layers for chart
    def make_layer(yield_df, col1, col2):
        return alt.Chart(yield_df.assign(color=col1)).mark_area().encode(
            x=alt.X(
                'Date:T',
                title='',
                axis=alt.Axis(format='%Y', tickCount='year')
            ),
        ).encode(
            y=alt.Y(
                f"{col1}:Q",
                title=f'Price: {upside_downside_str}',
                axis=alt.Axis(format='$.0f'),
                scale=alt.Scale(zero=False, domain=[df.Close.min()*0.9, df.Close.max()*1.15], clamp=True),
            ),
            y2=alt.Y2(
                f"{col2}:Q",
            ),
            color=alt.Color(
                f"color:N",
                title='Yield percentile',
                scale=scale,
                legend=None,
                # legend=alt.Legend(
                #     legendX=465,
                #     legendY=-25,
                #     orient='none',
                #     direction='horizontal',
                # )
            ),
            opacity=alt.value(0.75),
            tooltip=alt.value(None)
        )

    layers=[]
    for col1, col2 in zip(yield_df.columns[1:-1], yield_df.columns[2:]):
        layers.append(make_layer(yield_df, col1, col2))

    price = alt.Chart(df).mark_line(color="white").encode(
        x=alt.X(
            'Date:T',
            axis=alt.Axis(
                format='%Y',
                labels=True,
                ticks=False,
                domain=True,
                tickCount='year'
            ),
        ),
        y=alt.Y(
            'Close:Q',
            scale=alt.Scale(zero=False),
        ),
        tooltip=alt.value(None)
    )
    layers.append(price)

    price_text = alt.Chart(df.tail(1)).mark_text().encode(
        x=alt.X(
            'Date:T',
            title='',
            axis=alt.Axis(format='%Y', labels=False, ticks=False, domain=False, tickCount='year'),
        ),
        y=alt.Y('Close:Q', scale=alt.Scale(zero=False)),
        text=alt.Text('Close:Q', format='$.0f')
    )
    layers.append(price_text)

    yield_chart = price.encode(
        y=alt.Y(
            'DividendYield:Q',
            axis=alt.Axis(format='.1%',),
            scale=alt.Scale(zero=False),
            title=f'Dividend yield: higher than {df.DividendYield.rank(pct=True).iloc[-1]:.0%} of the period (median {df.DividendYield.quantile(q=0.5):.2%}).',
        ),
        tooltip=alt.value(None)
    )
    median_yield = price.mark_rule(
        color='white',
        strokeDash=[16, 16],
        strokeWidth=.5
        # opacity=.5,
    ).encode(
        x=alt.X(),
        y='median(DividendYield):Q'
    )
     
    yield_text = price_text.encode(
        y=alt.Y('DividendYield:Q', scale=alt.Scale(zero=False)),
        text=alt.Text('DividendYield:Q', format='.1%')
    )

    drawdown_chart = price.encode(
        x=alt.X(
            'Date:T',
            title='',
            axis=alt.Axis(
                format='%Y',
                labels=True,
                tickCount='year'
            ),
        ),
        y=alt.Y(
            'Drawdown:Q',
            axis=alt.Axis(
                format='.0%',
            ),
            scale=alt.Scale(zero=False)
        ),
        tooltip=alt.value(None)
    )
    drawdown_text = price_text.encode(
        y=alt.Y('Drawdown:Q', scale=alt.Scale(zero=False)),
        text=alt.Text('Drawdown:Q', format='.0%')
    )

    percentile = int((1 - df.DividendYield.rank(pct=True).iloc[-1]) * 100)
    def format_percentile(percentile):
        if (4 <= percentile <= 20) or (percentile % 10 not in [1, 2, 3]):
            return str(percentile) + 'th'
        if percentile % 10 == 1:
            return str(percentile) + 'st'
        if percentile % 10 == 2:
            return str(percentile) + 'nd'
        if percentile % 10 == 3:
            return str(percentile) + 'rd'
            
    percentile_string = format_percentile(percentile)

    price_chart = alt.layer(*layers).properties(
        width=1200,
        height=400,
        # title=f"""{ticker} {period} Chart • Price: ${
        #             df.iloc[-1].Close:.2f} • Yield: {
        #             df.iloc[-1].DividendYield:.2%} ({
        #             percentile_string} percentile) • Drawdown: {
        #                 df.Drawdown.iloc[-1]:.0%}""",
    )
    yield_chart = yield_chart.properties(
        width=1200,
        height=300
    )
    drawdown_chart = drawdown_chart.properties(
        width=1200,
        height=300
    )

    chart = alt.vconcat(
        price_chart,
        (yield_chart + yield_text + median_yield),
        (drawdown_chart + drawdown_text),
        spacing=0
    )
    chart = chart.properties(
        title=f"""Ticker: {ticker}  •  Period: {df.Date.dt.year.max() - df.Date.dt.year.min() + 1}y"""
    )
    chart = chart.configure(
        font='Lato'
    )
    
    return price_chart, yield_chart, drawdown_chart
