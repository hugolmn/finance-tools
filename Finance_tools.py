import streamlit as st
import pandas as pd
import requests

st.title("Finance tools")

st.write("""
    This streamlit app was built to host some personnal tools I need when it comes to investing.
    It's free to use and will always be."""
)
st.write("""
## Available pages:
- <a href='Dividends' target='_self'>Dividends</a>: Current and historical diviend yields of stocks.
- <a href='ETF_&_Stock_Portfolio' target='_self'>ETF & Stock_Portfolio</a>: Analyze a portfolio's actual holdings when it combines individual positions and ETFs.
- <a href='ETF_Analyzer' target='_self'>ETF_Analyzer</a>: Analyze holdings of BlackRock's ETFs by sector, asset class and regions.
- <a href='Total_Return' target='_self'>Total Return</a>: Visualize price and total returns, drawdown of stocks.
""", unsafe_allow_html=True)

st.write("""
Any suggestion?
Hit me up on twitter <a href='https://twitter.com/hugo_le_moine_'>@hugo_le_moine_</a>.
""", unsafe_allow_html=True)