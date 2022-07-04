import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("ETF Composition")

df = pd.read_csv('data/blackrock_fr.csv')

choice = st.multiselect("Select a fund", df.Fund.unique())

