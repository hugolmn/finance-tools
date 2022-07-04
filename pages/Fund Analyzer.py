import streamlit as st
import pandas as pd
import requests
import altair as alt

st.title("ETF Composition")

df = pd.read_csv('data/blackrock_fr.csv')

choice = st.selectbox("Select a fund", df.Fund.unique())

selected_fund = df[df.Fund == choice].drop(columns=['Fund']).copy()
selected_fund['Weight (%)'] = selected_fund['Weight (%)'].round(2)

sectors = selected_fund.groupby('Sector')['Weight (%)'].sum()
regions = selected_fund.groupby('Location')['Weight (%)'].sum()
asset_classes = selected_fund.groupby('Asset Class')['Weight (%)'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Top 10 concentration", value=f"{selected_fund.iloc[:10]['Weight (%)'].sum():.0f}%")
col2.metric("Largest sector", value=f'{sectors.max():.0f}%', delta=sectors.idxmax(), delta_color='off')
col3.metric("Largest region", value=f'{regions.max():.0f}%', delta=regions.idxmax(), delta_color='off')

chart_sector, chart_asset_classes = st.columns(2)

chart_sector.header('Sectors')
c_sectors = alt.Chart(sectors.sort_values().reset_index()).mark_bar().encode(
    x='Weight (%)',
    y=alt.Y('Sector', sort='-x'),
    tooltip=['Sector', 'Weight (%)']
)
chart_sector.altair_chart(c_sectors, use_container_width=True)

chart_asset_classes.header('Asset Classes')
c_asset_classes = alt.Chart(sectors.sort_values().reset_index()).mark_bar().encode(
    x='Weight (%)',
    y='Asset Class',
    tooltip=['Asset Class', 'Weight (%)']
)
chart_asset_classes.altair_chart(c_asset_classes, use_container_width=True)

st.header('Regions')
c = alt.Chart(regions.sort_values().reset_index()).mark_bar().encode(
    x='Weight (%)',
    y=alt.Y('Location', sort='-x'),
    tooltip=['Location', 'Weight (%)']
)
st.altair_chart(c, use_container_width=True)

st.header('Holdings')
st.dataframe(selected_fund)
