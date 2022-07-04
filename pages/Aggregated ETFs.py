import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("ETF Composition")

df = pd.read_csv('data/blackrock_fr.csv')

choices = st.multiselect("Select a fund", df.Fund.unique())

holdings = [st.number_input(f'Total value of {choice} holding', min_value=0, step=10) for choice in choices]
  
clicked = st.button('Show results')

if clicked:
  portfolio = df[df.Fund.isin(choices)]
  for etf, holding in zip(choices, holdings):
    st.text(f'{etf}: {holding}€')
    portfolio.loc[portfolio.Fund == etf, 'Value'] = portfolio.loc[portfolio.Fund == etf, 'Weight (%)'] * holding / 100
    
  st.header('Holdings')
  st.dataframe(selected_fund)
    
