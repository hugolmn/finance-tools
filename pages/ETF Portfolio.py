import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("Aggregate portfolio of ETFs")

df = pd.read_csv('data/blackrock_fr.csv')

choices = st.multiselect("Select a fund", df.Fund.unique())

holdings = [st.number_input(f'Total value of {choice} holding', min_value=0, step=10) for choice in choices]
  
clicked = st.button('Show results')

if clicked:
  portfolio = df[df.Fund.isin(choices)].copy()
  for etf, holding in zip(choices, holdings):
    st.text(f'{etf}: {holding}€')
    portfolio.loc[portfolio.Fund == etf, 'Value'] = portfolio.loc[portfolio.Fund == etf, 'Weight (%)'] * holding / 100
    
  portfolio = portfolio.drop(columns=['Fund'])
  portfolio = portfolio.groupby(['Ticker', 'Name', 'Sector', 'Asset Class', 'Location'], as_index=False).Value.sum()
  portfolio['Weight (%)'] = portfolio.Value.div(portfolio.Value.sum()) * 100                              
  portfolio['Weight (%)'] = portfolio['Weight (%)'].round(2)
  portfolio = portfolio.sort_values(by='Value', ascending=False)
  
  sectors = portfolio.groupby('Sector')[['Value', 'Weight (%)']].sum()
  regions = portfolio.groupby('Location')[['Value', 'Weight (%)']].sum()
  asset_classes = portfolio.groupby('Asset Class')[['Value', 'Weight (%)']].sum()

  col1, col2, col3 = st.columns(3)
  col1.metric(
    "Top 10 concentration",
    value=f"{portfolio.iloc[:10]['Weight (%)'].sum():.0f}%"
  )
  col2.metric(
    "Largest sector",
    value=f"{sectors['Weight (%)'].max():.0f}%",
    delta=sectors['Weight (%)'].idxmax(),
    delta_color='off'
  )
  col3.metric(
    "Largest region", 
    value=f"{regions['Weight (%)'].max():.0f}%",
    delta=regions['Weight (%)'].idxmax(),
    delta_color='off'
  )

  st.header('Sectors')
  c_sectors = alt.Chart(sectors.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y=alt.Y('Sector', sort='-x'),
      tooltip=['Sector', 'Weight (%)', 'Value']
  )
  st.altair_chart(c_sectors, use_container_width=True)

  st.header('Asset Classes')
  c_asset_classes = alt.Chart(asset_classes.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y='Asset Class',
      tooltip=['Asset Class', 'Weight (%)', 'Value']
  )
  st.altair_chart(c_asset_classes, use_container_width=True)

  st.header('Regions')
  c = alt.Chart(regions.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y=alt.Y('Location', sort='-x'),
      tooltip=['Location', 'Weight (%)', 'Value']
  )
  st.altair_chart(c, use_container_width=True)
  
  st.header('Holdings')
  st.dataframe(portfolio)
    