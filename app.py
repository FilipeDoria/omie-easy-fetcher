import streamlit as st
import pandas as pd
import requests
from datetime import date
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="OMIE Price Tracker", page_icon="⚡")

# --- Function to fetch data from Energy-Charts API ---
@st.cache_data(ttl=3600)
def get_electricity_prices(selected_date, country_code):
    date_str = selected_date.strftime("%Y-%m-%d")
    bzn = "ES" if country_code == "Spain (ES)" else "PT"
    url = f"https://api.energy-charts.info/price?bzn={bzn}&start={date_str}&end={date_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'unix_seconds' not in data or 'price' not in data:
            return None
            
        df = pd.DataFrame({
            'Timestamp': pd.to_datetime(data['unix_seconds'], unit='s').tz_localize('UTC').tz_convert('Europe/Madrid'),
            'Price': data['price']
        })
        
        # --- CRITICAL FIX: Handle 15-minute resolution ---
        # The API returns 4 values per hour. We average them to get 1 hourly price.
        # This fixes the "400 EUR" Y-axis bug and the "KeyError" crash.
        df = df.set_index('Timestamp').resample('1h').mean().reset_index()

        # Create display columns
        df['Hour_Display'] = df['Timestamp'].dt.strftime('%H:00')
        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# --- App Layout ---
st.title("⚡ Iberian Electricity Prices")
st.markdown("View Day-Ahead Spot Prices using the **Energy-Charts API**.")

# Controls
col1, col2 = st.columns(2)
with col1:
    day_select = st.date_input("Select Date", date.today())
with col2:
    country_choice = st.radio("Country", ["Spain (ES)", "Portugal (PT)"], horizontal=True)

# Fetch Data
df = get_electricity_prices(day_select, country_choice)

if df is not None and not df.empty:
    # --- Metrics ---
    avg_price = df['Price'].mean()
    min_price = df['Price'].min()
    max_price = df['Price'].max()
    
    # Find specific hours for min/max
    best_hour_row = df.loc[df['Price'] == min_price].iloc[0]
    worst_hour_row = df.loc[df['Price'] == max_price].iloc[0]

    st.markdown("### 📊 Daily Summary (EUR/MWh)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Average Price", f"{avg_price:.2f} €")
    m2.metric("Lowest Price", f"{min_price:.2f} €", f"at {best_hour_row['Hour_Display']}", delta_color="inverse")
    m3.metric("Highest Price", f"{max_price:.2f} €", f"at {worst_hour_row['Hour_Display']}", delta_color="normal")

    # --- Chart Section ---
    st.markdown("---")
    
    # Bar Chart: Simple and Clear
    fig = px.bar(
        df, 
        x="Hour_Display", 
        y="Price",
        color="Price",
        color_continuous_scale="RdYlGn_r", # Red-Yellow-Green (reversed)
        title=f"Hourly Prices - {day_select}",
        labels={"Price": "Price (€/MWh)", "Hour_Display": "Hour"}
    )
    
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Price (€/MWh)",
        coloraxis_showscale=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Data Table ---
    with st.expander("View Data Table"):
        # We format the timestamp to be the index so the table looks clean
        display_df = df[['Hour_Display', 'Price']].set_index('Hour_Display')
        
        # This styling caused the crash before, but now that we 'resampled',
        # there are no duplicate hours, so it will work perfectly.
        st.dataframe(
            display_df.style.background_gradient(cmap="RdYlGn_r", subset=['Price']), 
            use_container_width=True
        )

else:
    st.warning(f"⚠️ Data not available for {day_select}.")
    
