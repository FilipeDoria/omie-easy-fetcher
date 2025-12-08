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
        
        # Create a clean integer hour for sorting and a string for display
        df['Hour_Int'] = df['Timestamp'].dt.hour
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

    # --- IMPROVED CHART SECTION ---
    st.markdown("---")
    
    # We use a Bar Chart with conditional coloring
    # 'RdYlGn_r' reverses the scale so Low Price = Green, High Price = Red
    fig = px.bar(
        df, 
        x="Hour_Display", 
        y="Price",
        color="Price",
        color_continuous_scale="RdYlGn_r",
        title=f"Hourly Prices - {day_select}",
        labels={"Price": "Price (€/MWh)", "Hour_Display": "Hour"}
    )
    
    # Clean up the layout
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Price (€/MWh)",
        coloraxis_showscale=False, # Hide the side color bar to save space
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Data Table ---
    # We keep the styling you liked (requires matplotlib in requirements.txt)
    with st.expander("View Data Table"):
        # Format the display dataframe
        display_df = df[['Hour_Display', 'Price']].set_index('Hour_Display')
        st.dataframe(display_df.style.background_gradient(cmap="RdYlGn_r", subset=['Price']), use_container_width=True)

else:
    st.warning(f"⚠️ Data not available for {day_select}.")
    m2.metric("Lowest Price", f"{min_price:.2f} €", f"at {best_hour}", delta_color="inverse") # Green is good (low price)
    m3.metric("Highest Price", f"{max_price:.2f} €", f"at {worst_hour}", delta_color="normal") # Red is bad (high price)

    # --- Interactive Chart ---
    st.markdown("---")
    
    # Create beautiful Plotly chart
    fig = px.line(df, x="Hour", y="Price", title=f"Electricity Price - {day_select} ({country_choice})", markers=True)
    
    # Color regions: Green (Low), Red (High)
    fig.add_hrect(y0=0, y1=min_price + (avg_price - min_price)/3, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_hrect(y0=max_price - (max_price - avg_price)/3, y1=max_price * 1.1, line_width=0, fillcolor="red", opacity=0.1)

    fig.update_layout(yaxis_title="Price (€/MWh)", xaxis_title="Hour", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- Raw Data ---
    with st.expander("View Data Table"):
        st.dataframe(df[['Hour', 'Price']].style.background_gradient(cmap="RdYlGn_r", subset=['Price']))

else:
    st.warning(f"⚠️ Data not available for {day_select}. Prices for tomorrow are usually released after 13:30 CET.")
    
