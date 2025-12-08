import streamlit as st
import pandas as pd
import requests
from datetime import date
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="OMIE Price Tracker", page_icon="⚡", layout="wide")

# --- Function to determine Tariff Period (2.0TD Spain) ---
def get_tariff_period(hour, is_weekend):
    """Returns the period (Punta, Llano, Valle) and color for a given hour."""
    if is_weekend:
        return "Valle", "rgba(0, 0, 255, 0.1)" # Blue-ish for Weekend
    
    # Mon-Fri Schedule
    if 0 <= hour < 8:
        return "Valle", "rgba(0, 0, 255, 0.1)" # Blue
    elif (8 <= hour < 10) or (14 <= hour < 18) or (22 <= hour < 24):
        return "Llano", "rgba(255, 255, 0, 0.1)" # Yellow
    else:
        # 10-14 and 18-22
        return "Punta", "rgba(255, 0, 0, 0.1)"   # Red

# --- Sidebar: User Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. Tariff Selection
    tariff_type = st.radio("Select Tariff Type:", ["Market Price (PVPC)", "Fixed Rate"], index=0)
    
    # 2. Tariff Specific Inputs
    if tariff_type == "Fixed Rate":
        fixed_price = st.number_input("Your Fixed Price (€/kWh)", value=0.060, step=0.001, format="%.3f")
        st.caption("Enter the 'Energy Price' from your contract.")
    else:
        st.info("Using real-time OMIE market data.")
    
    st.divider()
    
    # 3. Common Taxes & Fees
    st.subheader("Taxes & Fees")
    tax_value = st.number_input("VAT / IVA (%)", value=21.0, step=1.0) / 100
    
    # Access fees are usually included in Fixed Rates, but separate in PVPC.
    if tariff_type == "Market Price (PVPC)":
        access_fee = st.number_input("Grid Fees / Peajes (€/kWh)", value=0.040, step=0.001, format="%.3f")
    else:
        access_fee = 0.0 
        
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
            'Raw_Price_MWh': data['price']
        })
        
        # Resample to Hourly
        df = df.set_index('Timestamp').resample('1h').mean().reset_index()
        df['Hour_Int'] = df['Timestamp'].dt.hour
        df['Hour_Display'] = df['Timestamp'].dt.strftime('%H:00')
        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# --- Main App Layout ---
st.title("⚡ Iberian Electricity Prices")

col1, col2 = st.columns(2)
with col1:
    day_select = st.date_input("Select Date", date.today())
with col2:
    country_choice = st.radio("Country", ["Spain (ES)", "Portugal (PT)"], horizontal=True)

df = get_electricity_prices(day_select, country_choice)

if df is not None and not df.empty:
    
    # --- CALCULATION ENGINE ---
    if tariff_type == "Fixed Rate":
        df['Display_Price'] = fixed_price * (1 + tax_value)
        price_label = "Fixed Rate"
    else:
        df['Display_Price'] = (df['Raw_Price_MWh'] / 1000 + access_fee) * (1 + tax_value)
        price_label = "PVPC Price"

    # --- Metrics ---
    avg_price = df['Display_Price'].mean()
    min_price = df['Display_Price'].min()
    max_price = df['Display_Price'].max()
    best_hour = df.loc[df['Display_Price'] == min_price, 'Hour_Display'].iloc[0]

    st.markdown(f"### 📊 Daily Summary ({price_label} incl. Tax)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Average Price", f"{avg_price:.3f} €/kWh")
    if tariff_type == "Market Price (PVPC)":
        m2.metric("Lowest Price", f"{min_price:.3f} €/kWh", f"at {best_hour}", delta_color="inverse")
        m3.metric("Highest Price", f"{max_price:.3f} €/kWh", delta_color="normal")
    else:
        m2.metric("Your Rate", f"{fixed_price:.3f} €/kWh")
        m3.metric("Tax Applied", f"{int(tax_value*100)}%")

    # --- Interactive Chart ---
    st.markdown("---")
    
    # Determine Colors (Fix for ZeroDivisionError)
    if tariff_type == "Market Price (PVPC)":
        chart_colors = "RdYlGn_r"
    else:
        # Must provide at least TWO colors for a continuous scale, even if identical
        chart_colors = ["#2E86C1", "#2E86C1"]

    fig = px.bar(
        df, x="Hour_Display", y="Display_Price",
        color="Display_Price", 
        color_continuous_scale=chart_colors,
        title=f"Electricity Prices ({tariff_type}) - {day_select}",
        labels={"Display_Price": "Price (€/kWh)", "Hour_Display": "Hour"}
    )
    
    # --- ADD BACKGROUND ZONES ---
    is_weekend = day_select.weekday() >= 5
    for i in range(24):
        period_name, bg_color = get_tariff_period(i, is_weekend)
        fig.add_shape(
            type="rect",
            x0=i-0.5, x1=i+0.5,
            y0=0, y1=1, xref="x", yref="paper",
            fillcolor=bg_color,
            line_width=0,
            layer="below"
        )

    # Legend for Zones
    if not is_weekend:
        fig.add_annotation(x=4, y=1.05, text="🟦 Valle", showarrow=False, xref="x", yref="paper", font=dict(color="blue"))
        fig.add_annotation(x=9, y=1.05, text="🟨 Llano", showarrow=False, xref="x", yref="paper", font=dict(color="#b5b500"))
        fig.add_annotation(x=12, y=1.05, text="🟥 Punta", showarrow=False, xref="x", yref="paper", font=dict(color="red"))
    else:
        fig.add_annotation(x=12, y=1.05, text="🟦 Weekend (All Valle)", showarrow=False, xref="x", yref="paper", font=dict(color="blue"))

    fig.update_layout(xaxis_title=None, yaxis_title="Price (€/kWh)", coloraxis_showscale=False, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- APPLIANCE PLANNER ---
    st.markdown("### ⏱️ Plan Your Usage")
    st.info("Calculate cost based on your selected tariff.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        appliance_power = st.number_input("Power (Watts)", value=2000, step=100)
    with c2:
        duration_hours = st.number_input("Duration (Hours)", value=2, min_value=1, max_value=12)
    
    # Logic: Find best window
    df['Rolling_Avg'] = df['Display_Price'].rolling(window=duration_hours).mean().shift(1 - duration_hours)
    
    if not df['Rolling_Avg'].dropna().empty:
        best_window_price = df['Rolling_Avg'].min()
        best_start_idx = df['Rolling_Avg'].idxmin()
        best_start_time = df.loc[best_start_idx, 'Hour_Display']
        
        total_trip_cost = (appliance_power / 1000) * duration_hours * best_window_price

        with c3:
            if tariff_type == "Market Price (PVPC)":
                st.success(f"**Best Start:** {best_start_time}")
            else:
                st.info(f"**Start Anytime** (Fixed Rate)")
            st.metric("Estimated Cost", f"{total_trip_cost:.2f} €")
    
    # --- Data Table ---
    with st.expander("View Detailed Data Table"):
        st.dataframe(df[['Hour_Display', 'Display_Price']].style.format({"Display_Price": "{:.4f} €"}), use_container_width=True)

else:
    st.warning(f"⚠️ Data not available for {day_select}.")
    
