import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
import altair as alt

st.set_page_config(layout="wide")

# Handling of cookies
@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()
cookies = cookie_manager.get_all()
if not (existing_portfolios := cookie_manager.get(cookie='portfolios')):
  existing_portfolios = {}

st.title("Aggregate portfolio of ETFs and stocks")

# Load ETFs
etfs = pd.read_csv('data/blackrock_fr.csv')
# Load Stocks
stocks = pd.read_csv('data/individual_positions.csv')

use_saved_portfolio = st.checkbox('Use saved portfolio')

if use_saved_portfolio and (len(existing_portfolios) > 0):
  selected_portfolio_name = st.selectbox('Select portfolio', existing_portfolios.keys(), disabled=not use_saved_portfolio)
  portfolio_name = st.text_input('Portfolio name', value=selected_portfolio_name)
  portfolio = existing_portfolios[selected_portfolio_name] 
else:
  portfolio_name = st.text_input('Portfolio name')
  portfolio = {
    'etf_holdings': {},
    'stock_holdings': {}
  }

# Portfolio ETFs
with st.expander(f"ETF holdings"):
  etf_choices = st.multiselect(
    "Select ETFs",
    options=etfs.Fund.unique(),
    default=portfolio['etf_holdings'] if portfolio['etf_holdings'] else None
  )

  portfolio['etf_holdings'] = {
    etf: portfolio['etf_holdings'][etf]
    for etf in portfolio['etf_holdings']
    if etf in etf_choices
  }

  for etf in etf_choices:
    default_value = portfolio['etf_holdings'][etf] if etf in portfolio['etf_holdings'] else 0
    portfolio['etf_holdings'][etf] = st.number_input(
      f'Total value of {etf} holding',
      min_value=0,
      step=100,
      value=default_value
    )

# Portfolio stocks
with st.expander(f"Stock holdings"):
  stock_choices = st.multiselect(
    "Select stocks",
    options=stocks.Name.unique(),
    default=portfolio['stock_holdings'] if portfolio['stock_holdings'] else None
  )

  portfolio['stock_holdings'] = {
    stock: portfolio['stock_holdings'][stock]
    for stock in portfolio['stock_holdings']
    if stock in stock_choices
  }

  for stock in stock_choices:
    default_value = portfolio['stock_holdings'][stock] if stock in portfolio['stock_holdings'] else 0
    portfolio['stock_holdings'][stock] = st.number_input(
      f'Total value of {stock} holding',
      min_value=0,
      step=100,
      value=default_value
    )


# Action buttons
col1, col2, col3 = st.columns(3)
with col1:
  clicked = st.button('Show portfolio',  disabled=len(portfolio_name) == 0)
with col2: 
  saved = st.button('Save portfolio', disabled=len(portfolio_name) == 0)
with col3: 
  delete = st.button('Delete portfolio', disabled=len(portfolio_name) == 0)

if clicked:
  try:
    etf_holdings = etfs[etfs.Fund.isin(etf_choices)].copy()
    for etf, holding in portfolio['etf_holdings'].items():
      st.text(f'{etf}: {holding}€')
      etf_holdings.loc[etf_holdings.Fund == etf, 'Value'] = etf_holdings.loc[etf_holdings.Fund == etf, 'Weight (%)'] * holding / 100
      
    stock_holdings = stocks[stocks.Name.isin(stock_choices)].copy()
    for stock, holding in portfolio['stock_holdings'].items():
      st.text(f'{stock}: {holding}€')
      stock_holdings.loc[stock_holdings.Name == stock, 'Value'] = holding
    
    holdings = pd.concat([etf_holdings, stock_holdings])
    holdings = holdings.drop(columns=['Fund'])
    holdings = holdings.groupby(['Ticker', 'Name', 'Sector', 'Asset Class', 'Location'], as_index=False).Value.sum()
    holdings['Weight (%)'] = holdings.Value.div(holdings.Value.sum()) * 100                              
    holdings['Weight (%)'] = holdings['Weight (%)'].round(2)
    holdings = holdings.sort_values(by='Value', ascending=False)
    
    sectors = holdings.groupby('Sector')[['Value', 'Weight (%)']].sum()
    regions = holdings.groupby('Location')[['Value', 'Weight (%)']].sum()
    asset_classes = holdings.groupby('Asset Class')[['Value', 'Weight (%)']].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric(
      "Top 10 concentration",
      value=f"{holdings.iloc[:10]['Weight (%)'].sum():.0f}%"
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
    st.dataframe(holdings.reset_index(drop=True))
  except:
    st.error('No position found in portfolio')

if saved:
  existing_portfolios[portfolio_name] = portfolio
  cookie_manager.set('portfolios', existing_portfolios, key='existing_portfolios')

if delete:
  del(existing_portfolios[portfolio_name])
  cookie_manager.set('portfolios', existing_portfolios, key='existing_portfolios')
    
