import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="OMIE Price Tracker", page_icon="⚡")

# --- Function to fetch data from OMIE ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to avoid spamming OMIE
def get_omie_prices(selected_date):
    # OMIE URL structure: marginalpdbc_YYYYMMDD.1
    date_str = selected_date.strftime("%Y%m%d")
    url = f"https://www.omie.es/es/file-download-system/daily_market/daily_market_price/marginalpdbc_{date_str}.1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # The OMIE file format is a semicolon-separated text file.
        # It usually has a header line we skip, and the last line is a footer.
        data = response.text.splitlines()
        
        # Parse the raw text data
        parsed_data = []
        for line in data[1:-1]: # Skip first (header) and last (footer)
            parts = line.split(';')
            if len(parts) >= 6:
                # Structure: Year; Month; Day; Hour; Price_PT; Price_ES; ...
                hour = int(parts[3])
                price_pt = float(parts[4].replace(',', '.')) # Portugal
                price_es = float(parts[5].replace(',', '.')) # Spain
                
                parsed_data.append({
                    "Hour": f"{hour-1:02d}:00", # Formatting hour (0-23)
                    "Price (PT)": price_pt,
                    "Price (ES)": price_es
                })
                
        if not parsed_data:
            return None

        return pd.DataFrame(parsed_data)

    except requests.exceptions.HTTPError:
        return None
    except Exception as e:
        st.error(f"Error parsing data: {e}")
        return None

# --- App Layout ---
st.title("⚡ Iberian Electricity Prices (OMIE)")
st.markdown("View the **Day-Ahead Spot Prices** for Spain and Portugal.")

# Date Picker (Default to Today)
col1, col2 = st.columns([1, 3])
with col1:
    day_select = st.date_input("Select Date", date.today())
    
# Fetch Data
df = get_omie_prices(day_select)

if df is not None:
    # --- Metrics Section ---
    # Prices are usually the same for ES/PT, so we use ES for the main metric
    avg_price = df['Price (ES)'].mean()
    min_price = df['Price (ES)'].min()
    max_price = df['Price (ES)'].max()
    
    # Determine best and worst hours
    best_hour = df.loc[df['Price (ES)'] == min_price, 'Hour'].iloc[0]
    worst_hour = df.loc[df['Price (ES)'] == max_price, 'Hour'].iloc[0]

    st.markdown("### 📊 Daily Summary (EUR/MWh)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Average Price", f"{avg_price:.2f} €", delta_color="off")
    m2.metric("Lowest Price", f"{min_price:.2f} €", f"at {best_hour}")
    m3.metric("Highest Price", f"{max_price:.2f} €", f"at {worst_hour}", delta_color="inverse")

    # --- Chart Section ---
    st.markdown("---")
    country_choice = st.radio("Select Country:", ["Spain (ES)", "Portugal (PT)"], horizontal=True)
    price_col = "Price (ES)" if "Spain" in country_choice else "Price (PT)"

    # Plotly Line Chart
    fig = px.line(df, x="Hour", y=price_col, title=f"Electricity Price - {day_select}", markers=True)
    fig.update_layout(yaxis_title="Price (€/MWh)", xaxis_title="Hour of Day")
    
    # Add a red line for the max price and green for min
    fig.add_hline(y=max_price, line_dash="dot", annotation_text="Max", annotation_position="top right", line_color="red")
    fig.add_hline(y=min_price, line_dash="dot", annotation_text="Min", annotation_position="bottom right", line_color="green")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Data Table ---
    with st.expander("View Raw Data Table"):
        st.dataframe(df.style.highlight_max(axis=0, color='#ffcccc').highlight_min(axis=0, color='#ccffcc'))

else:
    st.warning("⚠️ Data not available for this date yet. (OMIE usually updates prices for tomorrow after 13:30 CET).")
