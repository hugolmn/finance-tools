import streamlit as st
import yfinance as yf
import altair as alt
import pandas as pd
import numpy as np
import datetime
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
        '1y', '2y', '5y', '10y', 'ytd', 'max'
    ],
    index=2
)

if ticker:
    from utils import generate_dividend_chart
    price_chart, yield_chart, drawdown_chart = generate_dividend_chart(ticker, period)
    st.altair_chart(price_chart, use_container_width=True, theme='streamlit')
    st.altair_chart(yield_chart, use_container_width=True, theme='streamlit')
    st.altair_chart(drawdown_chart, use_container_width=True, theme='streamlit')

    # # Use the st.markdown method to include the Twitter button HTML in your app
    # st.markdown(
        
    #     """
    #     <style>
    #     html {
    #         font-family: Helvetica Neue Arial,sans-serif;
    #         color: #333;
    #     }
    #     a .btn{
    #         outline: 0;
    #         text-decoration: none;
    #         color: white
    #     }
    #     a:visited .btn{
    #         outline: 0;
    #         text-decoration: none;
    #         color: white
    #     }
    #     #count, .btn, .btn .label, .btn-o, .count-o {
    #         display: inline-block;
    #         vertical-align: top;
    #         zoom: 1;
    #     }
    #     .btn {
    #         position: relative;
    #         height: 35px;
    #         width: 79px;
    #         box-sizing: border-box;
    #         padding: 1px 12px 1px 12px;
    #         background-color: #1d9bf0;
    #         color: #fff;
    #         border-radius: 9999px;
    #         font-weight: 500;
    #         cursor: pointer;
    #     }

    #     .btn i {
    #         position: relative;
    #         top: 7.5px;
    #         display: inline-block;
    #         width: 20px;
    #         height: 20px;
    #         background: transparent 0 0 no-repeat;
    #         background-image: url(data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2072%2072%22%3E%3Cpath%20fill%3D%22none%22%20d%3D%22M0%200h72v72H0z%22%2F%3E%3Cpath%20class%3D%22icon%22%20fill%3D%22%23fff%22%20d%3D%22M68.812%2015.14c-2.348%201.04-4.87%201.744-7.52%202.06%202.704-1.62%204.78-4.186%205.757-7.243-2.53%201.5-5.33%202.592-8.314%203.176C56.35%2010.59%2052.948%209%2049.182%209c-7.23%200-13.092%205.86-13.092%2013.093%200%201.026.118%202.02.338%202.98C25.543%2024.527%2015.9%2019.318%209.44%2011.396c-1.125%201.936-1.77%204.184-1.77%206.58%200%204.543%202.312%208.552%205.824%2010.9-2.146-.07-4.165-.658-5.93-1.64-.002.056-.002.11-.002.163%200%206.345%204.513%2011.638%2010.504%2012.84-1.1.298-2.256.457-3.45.457-.845%200-1.666-.078-2.464-.23%201.667%205.2%206.5%208.985%2012.23%209.09-4.482%203.51-10.13%205.605-16.26%205.605-1.055%200-2.096-.06-3.122-.184%205.794%203.717%2012.676%205.882%2020.067%205.882%2024.083%200%2037.25-19.95%2037.25-37.25%200-.565-.013-1.133-.038-1.693%202.558-1.847%204.778-4.15%206.532-6.774z%22%2F%3E%3C%2Fsvg%3E);
    #     }

    #     .btn .label {
    #         margin-left: 4px;
    #         white-space: nowrap;
    #     }
    #     </style>"""
    #         + f"""<a href="https://twitter.com/intent/tweet?text=@DividendChart {ticker} {period}" class="btn"><i></i><span class="label" id="l">Tweet</span></a>""",
    #     unsafe_allow_html=True
    # )