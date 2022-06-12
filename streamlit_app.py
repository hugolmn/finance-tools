import streamlit
import pandas as pd
import requests

streamlit.title("ETF Composition")

try:
  response = requests.get('https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn?dcrPath=/templatedata/config/product-screener-v3/data/en/us-ishares/ishares-product-screener-backend-config&siteEntryPassthrough=true').json()
except:
  streamlit.error()
  
df = pd.DataFrame(response).T

streamlit.dataframe(df)
