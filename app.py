import streamlit as st
import pandas as pd
import requests
from datetime import date
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="OMIE Price Tracker", page_icon="⚡", layout="wide")

# --- Sidebar: User Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. Unit Toggle
    use_kwh = st.toggle("Show Prices in €/kWh", value=True)
    
    # 2. Tax & Fee Configuration
    st.subheader("Taxes & Fees")
    st.info("Adjust these to match your electricity bill.")
    
    # Defaults based on typical Iberian values (approximate)
    tax_value = st.number_input("VAT / IVA (%)", value=21.0, step=1.0) / 100
    access_fee = st.number_input("Grid Fees / Peajes (€/kWh)", value=0.040, step=0.001, format="%.3f")
    
    st.markdown("---")
    st.markdown("Created with **Streamlit** & **Energy-Charts API**")

# --- Function to fetch data ---
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
            'Raw_Price_MWh': data['price'] # Store original market price
        })
        
        # Resample to Hourly (Fixes 15-min glitch)
        df = df.set_index('Timestamp').resample('1h').mean().reset_index()
        df['Hour_Display'] = df['Timestamp'].dt.strftime('%H:00')
        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# --- Main App Layout ---
st.title("⚡ Iberian Electricity Prices")

# Controls (Top Bar)
col1, col2 = st.columns(2)
with col1:
    day_select = st.date_input("Select Date", date.today())
with col2:
    country_choice = st.radio("Country", ["Spain (ES)", "Portugal (PT)"], horizontal=True)

# Fetch Data
df = get_electricity_prices(day_select, country_choice)

if df is not None and not df.empty:
    
    # --- CALCULATION ENGINE ---
    # Apply the user settings to the data
    if use_kwh:
        # Formula: (Market Price / 1000 + Fees) * Tax
        df['Display_Price'] = (df['Raw_Price_MWh'] / 1000 + access_fee) * (1 + tax_value)
        unit_label = "€/kWh"
        fmt = "%.3f €" # 3 decimal places for kWh (e.g. 0.142 €)
    else:
        # Standard Market Price (usually excludes taxes/fees in wholesale view, 
        # but you can choose to add them if you want. Here we keep it raw for MWh view).
        df['Display_Price'] = df['Raw_Price_MWh']
        unit_label = "€/MWh"
        fmt = "%.2f €"

    # --- Metrics ---
    avg_price = df['Display_Price'].mean()
    min_price = df['Display_Price'].min()
    max_price = df['Display_Price'].max()
    
    best_hour = df.loc[df['Display_Price'] == min_price, 'Hour_Display'].iloc[0]
    worst_hour = df.loc[df['Display_Price'] == max_price, 'Hour_Display'].iloc[0]

    st.markdown(f"### 📊 Daily Summary ({unit_label})")
    
    # Dynamic coloring for metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Average Price", fmt % avg_price)
    m2.metric("Lowest Price", fmt % min_price, f"at {best_hour}", delta_color="inverse")
    m3.metric("Highest Price", fmt % max_price, f"at {worst_hour}", delta_color="normal")

    # --- Interactive Chart ---
    st.markdown("---")
    
    # Create Bar Chart
    fig = px.bar(
        df, 
        x="Hour_Display", 
        y="Display_Price",
        color="Display_Price",
        color_continuous_scale="RdYlGn_r",
        title=f"Electricity Prices - {day_select}",
        labels={"Display_Price": f"Price ({unit_label})", "Hour_Display": "Hour"}
    )
    
    # Add a horizontal line for the user's "Break Even" or average
    fig.add_hline(y=avg_price, line_dash="dot", annotation_text="Avg", line_color="gray")

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=f"Price ({unit_label})",
        coloraxis_showscale=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Data Table ---
    with st.expander("View Detailed Data Table"):
        # Show both raw and final price for transparency
        table_df = df[['Hour_Display', 'Display_Price', 'Raw_Price_MWh']].copy()
        table_df.columns = ['Hour', f'Final Price ({unit_label})', 'Market Price (€/MWh)']
        
        st.dataframe(
            table_df.set_index('Hour').style.background_gradient(cmap="RdYlGn_r", subset=[f'Final Price ({unit_label})']),
            use_container_width=True
        )

else:
    st.warning(f"⚠️ Data not available for {day_select}.")
    
