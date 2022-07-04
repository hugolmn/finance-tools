import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("ETF Composition")

df = pd.read_csv('data/blackrock_fr.csv')

choices = st.multiselect("Select a fund", df.Fund.unique())

holdings = [st.number_input(f'Total value of {choice} holding', min_value=0, step=10) for choice in choices]
  

