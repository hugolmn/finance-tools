import streamlit as st
import pandas as pd
import requests

st.title("ETF Composition")

df = pd.read_csv('data/fund_compositions.csv')

choice = st.selectbox(df.Fund.unique())

st.dataframe(df)
