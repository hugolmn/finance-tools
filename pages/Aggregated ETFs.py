import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("ETF Composition")

df = pd.read_csv('data/blackrock_fr.csv')

choices = st.multiselect("Select a fund", df.Fund.unique())

for choice in choices:
  st.number_input(f'Total value of {choice} holding')

