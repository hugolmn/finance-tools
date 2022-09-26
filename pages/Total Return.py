import streamlit as st
import yfinance as yf

st.title('Total return calculator')
ticker = st.text_input("Ticker")
if ticker:
    history = yf.Ticker(ticker).history(period='5y')
    history['CumulativeShares'] = ((history.Dividends / history.Close) + 1).cumprod()
    history['PriceReturn'] = history.Close / history.Close.iloc[0]
    history['TotalReturn'] = history.CumulativeShares * history.Close / history.Close.iloc[0]

    st.dataframe(history)


    # history.PriceReturn.plot()
    # history.TotalReturn.plot()
