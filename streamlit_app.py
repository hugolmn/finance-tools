import streamlit as st
import pandas as pd
import requests

st.title("ETF Composition")

df = pd.read_csv('data/fund_compositions.csv')

choice = st.selectbox("Select a fund", df.Fund.unique())

selected_fund = df[df.Fund == choice].copy()
sectors = selected_fund.groupby('Sector')['Weight (%)'].sum()
regions = selected_fund.groupby('Location')['Weight (%)'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Top 10", f"{selected_fund.iloc[:10]['Weight (%)'].sum():.0f}%")
col2.metric("Largest sector", sectors.idxmax(), f'{sectors.max():.0f}%', delta_color='off')
col3.metric("Largest region", regions.idxmax(), f'{regions.max():.0f}%', delta_color='off')

st.header('Holdings')
st.dataframe(selected_fund)
