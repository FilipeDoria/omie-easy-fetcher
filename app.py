import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
import plotly.express as px
import pytz

# --- Configuration ---
st.set_page_config(page_title="Iberian Energy Prices", page_icon="⚡", layout="wide")

# --- 🌍 TRANSLATION ENGINE ---
LANGUAGES = {
    "English": {
        "title": "⚡ Iberian Electricity Prices",
        "select_date": "Select Date",
        "country": "Country",
        "settings": "⚙️ Settings",
        "show_raw": "Show Raw Market Price (€/MWh)",
        "tariff_type": "Select Tariff Type:",
        "tariff_pvpc": "Market Price (PVPC)",
        "tariff_fixed": "Fixed Rate",
        "fixed_price_label": "Your Fixed Price (€/kWh)",
        "taxes": "Taxes & Fees",
        "vat": "VAT / IVA (%)",
        "fees": "Grid Fees / Peajes (€/kWh)",
        "calc_title": "⏱️ Plan Your Usage",
        "calc_power": "Power (Watts)",
        "calc_duration": "Duration (Hours)",
        "calc_cost": "Estimated Cost",
        "calc_start": "Best Start:",
        "calc_anytime": "Start Anytime",
        "view_table": "View Detailed Data Table",
        "download_csv": "📥 Download Data as CSV",
        "daily_summary": "Daily Summary",
        "avg_price": "Average Price",
        "min_price": "Lowest Price",
        "max_price": "Highest Price",
        "your_rate": "Your Rate",
        "tax_applied": "Tax Applied",
        "price_axis": "Price",
        "hour_axis": "Hour",
        "now_label": "NOW",
        "verdict_good": "✅ Great time to use energy!",
        "verdict_bad": "❌ Expensive! Wait if possible.",
        "verdict_avg": "⚖️ Average Price.",
        "zone_valle": "Valle (Off-Peak)",
        "zone_llano": "Llano (Standard)",
        "zone_punta": "Punta (Peak)",
        "data_unavailable": "⚠️ Data not available for",
        "raw_info": "Showing raw market data in €/MWh. Taxes and tariffs are hidden."
    },
    "Español": {
        "title": "⚡ Precio de la Luz (OMIE)",
        "select_date": "Seleccionar Fecha",
        "country": "País",
        "settings": "⚙️ Configuración",
        "show_raw": "Ver Precio Mercado (€/MWh)",
        "tariff_type": "Tipo de Tarifa:",
        "tariff_pvpc": "Precio Mercado (PVPC)",
        "tariff_fixed": "Tarifa Fija",
        "fixed_price_label": "Tu Precio Fijo (€/kWh)",
        "taxes": "Impuestos y Peajes",
        "vat": "IVA (%)",
        "fees": "Peajes / Cargos (€/kWh)",
        "calc_title": "⏱️ Planificador de Consumo",
        "calc_power": "Potencia (W)",
        "calc_duration": "Duración (Horas)",
        "calc_cost": "Coste Estimado",
        "calc_start": "Mejor Hora:",
        "calc_anytime": "Cualquier hora",
        "view_table": "Ver Tabla de Datos",
        "download_csv": "📥 Descargar CSV",
        "daily_summary": "Resumen Diario",
        "avg_price": "Precio Medio",
        "min_price": "Mínimo",
        "max_price": "Máximo",
        "your_rate": "Tu Tarifa",
        "tax_applied": "Impuesto Aplicado",
        "price_axis": "Precio",
        "hour_axis": "Hora",
        "now_label": "AHORA",
        "verdict_good": "✅ ¡Buen momento!",
        "verdict_bad": "❌ Caro. Espera si puedes.",
        "verdict_avg": "⚖️ Precio Normal.",
        "zone_valle": "Valle",
        "zone_llano": "Llano",
        "zone_punta": "Punta",
        "data_unavailable": "⚠️ Datos no disponibles para",
        "raw_info": "Mostrando datos crudos en €/MWh. Sin impuestos ni peajes."
    },
    "Português": {
        "title": "⚡ Preço da Eletricidade (OMIE)",
        "select_date": "Selecionar Data",
        "country": "País",
        "settings": "⚙️ Configurações",
        "show_raw": "Ver Preço de Mercado (€/MWh)",
        "tariff_type": "Tipo de Tarifa:",
        "tariff_pvpc": "Preço de Mercado (Indexado)",
        "tariff_fixed": "Taxa Fixa",
        "fixed_price_label": "Seu Preço Fixo (€/kWh)",
        "taxes": "Impostos e Taxas",
        "vat": "IVA (%)",
        "fees": "Taxas de Acesso (€/kWh)",
        "calc_title": "⏱️ Planejar Consumo",
        "calc_power": "Potência (W)",
        "calc_duration": "Duração (Horas)",
        "calc_cost": "Custo Estimado",
        "calc_start": "Melhor Início:",
        "calc_anytime": "Qualquer hora",
        "view_table": "Ver Tabela de Dados",
        "download_csv": "📥 Baixar CSV",
        "daily_summary": "Resumo Diário",
        "avg_price": "Preço Médio",
        "min_price": "Mínimo",
        "max_price": "Máximo",
        "your_rate": "Sua Tarifa",
        "tax_applied": "Imposto Aplicado",
        "price_axis": "Preço",
        "hour_axis": "Hora",
        "now_label": "AGORA",
        "verdict_good": "✅ Bom momento!",
        "verdict_bad": "❌ Caro. Espere se puder.",
        "verdict_avg": "⚖️ Preço Médio.",
        "zone_valle": "Vazio (Valle)",
        "zone_llano": "Cheias (Llano)",
        "zone_punta": "Ponta (Punta)",
        "data_unavailable": "⚠️ Dados não disponíveis para",
        "raw_info": "Mostrando dados brutos em €/MWh. Sem impostos ou taxas."
    }
}

# --- Function to determine Tariff Period (2.0TD Spain Logic) ---
def get_tariff_period(hour, is_weekend, texts):
    if is_weekend:
        return texts["zone_valle"], "rgba(0, 0, 255, 0.1)"
    if 0 <= hour < 8:
        return texts["zone_valle"], "rgba(0, 0, 255, 0.1)"
    elif (8 <= hour < 10) or (14 <= hour < 18) or (22 <= hour < 24):
        return texts["zone_llano"], "rgba(255, 255, 0, 0.1)"
    else:
        return texts["zone_punta"], "rgba(255, 0, 0, 0.1)"

# --- Sidebar: Settings ---
with st.sidebar:
    # Language Selector
    lang_choice = st.selectbox("Language / Idioma", ["English", "Español", "Português"])
    t = LANGUAGES[lang_choice] # Load translation dictionary
    
    st.header(t["settings"])
    
    # Show Raw Toggle
    show_raw = st.toggle(t["show_raw"], value=False)
    
    if not show_raw:
        tariff_type = st.radio(t["tariff_type"], [t["tariff_pvpc"], t["tariff_fixed"]], index=0)
        
        if tariff_type == t["tariff_fixed"]:
            fixed_price = st.number_input(t["fixed_price_label"], value=0.060, step=0.001, format="%.3f")
        
        st.divider()
        st.subheader(t["taxes"])
        tax_value = st.number_input(t["vat"], value=21.0, step=1.0) / 100
        
        if tariff_type == t["tariff_pvpc"]:
            access_fee = st.number_input(t["fees"], value=0.040, step=0.001, format="%.3f")
        else:
            access_fee = 0.0
    else:
        st.info(t["raw_info"])
        
    st.divider()
    show_calculator = st.checkbox(t["calc_title"], value=False)
    st.markdown("---")
    st.caption("Created with **Streamlit** & **Energy-Charts API**")

# --- DATE LOGIC: Prevent Future Dates ---
# OMIE prices for tomorrow are usually released around 13:30 CET
now_cet = datetime.now(pytz.timezone('Europe/Madrid'))
if now_cet.hour >= 13 and now_cet.minute >= 30:
    max_allowed_date = now_cet.date() + timedelta(days=1)
else:
    max_allowed_date = now_cet.date()

# --- Main App Layout ---
st.title(t["title"])

col1, col2 = st.columns(2)
with col1:
    day_select = st.date_input(t["select_date"], date.today(), max_value=max_allowed_date)
with col2:
    country_choice = st.radio(t["country"], ["Spain (ES)", "Portugal (PT)"], horizontal=True)

# --- Fetch Data Function (Correct Timezones) ---
@st.cache_data(ttl=3600)
def get_electricity_prices(selected_date, country_code):
    date_str = selected_date.strftime("%Y-%m-%d")
    bzn = "ES" if country_code == "Spain (ES)" else "PT"
    
    # IMPORTANT: Set the correct timezone for the chart
    target_tz = 'Europe/Lisbon' if bzn == "PT" else 'Europe/Madrid'
    
    url = f"https://api.energy-charts.info/price?bzn={bzn}&start={date_str}&end={date_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'unix_seconds' not in data or 'price' not in data:
            return None, None
            
        df = pd.DataFrame({
            'Timestamp': pd.to_datetime(data['unix_seconds'], unit='s').tz_localize('UTC').tz_convert(target_tz),
            'Raw_Price_MWh': data['price']
        })
        
        # Resample to Hourly
        df = df.set_index('Timestamp').resample('1h').mean().reset_index()
        df['Hour_Display'] = df['Timestamp'].dt.strftime('%H:00')
        df['Hour_Int'] = df['Timestamp'].dt.hour
        return df, target_tz

    except Exception as e:
        return None, None

df, current_tz = get_electricity_prices(day_select, country_choice)

if df is not None and not df.empty:
    
    # --- CALCULATION ENGINE ---
    if show_raw:
        df['Display_Price'] = df['Raw_Price_MWh']
        price_label = "MWh"
        unit_label = "€/MWh"
        fmt = "%.2f €" # 2 decimals for MWh
        chart_colors = "RdYlGn_r"
    else:
        unit_label = "€/kWh"
        fmt = "%.4f €" # 4 decimals for consumer precision
        if tariff_type == t["tariff_fixed"]:
            df['Display_Price'] = fixed_price * (1 + tax_value)
            price_label = t["tariff_fixed"]
            chart_colors = ["#2E86C1", "#2E86C1"]
        else:
            df['Display_Price'] = (df['Raw_Price_MWh'] / 1000 + access_fee) * (1 + tax_value)
            price_label = t["tariff_pvpc"]
            chart_colors = "RdYlGn_r"

    # --- 🟢 LIVE STATUS SECTION ---
    if day_select == date.today():
        # Get current time in the selected country's timezone
        now_local = datetime.now(pytz.timezone(current_tz))
        current_hour_int = now_local.hour
        
        current_row = df.loc[df['Hour_Int'] == current_hour_int]
        
        if not current_row.empty:
            curr_price = current_row['Display_Price'].values[0]
            avg_price_today = df['Display_Price'].mean()
            
            if curr_price < avg_price_today * 0.9:
                verdict = t["verdict_good"]
                verdict_color = "green"
            elif curr_price > avg_price_today * 1.1:
                verdict = t["verdict_bad"]
                verdict_color = "red"
            else:
                verdict = t["verdict_avg"]
                verdict_color = "orange"

            st.markdown(f"### {t['now_label']} ({now_local.strftime('%H:%M')})")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric(t['price_axis'], fmt % curr_price, delta=f"{curr_price - avg_price_today:.3f}", delta_color="inverse")
            with c2:
                st.markdown(f"#### :{verdict_color}[{verdict}]")
            st.divider()

    # --- Metrics ---
    avg_price = df['Display_Price'].mean()
    min_price = df['Display_Price'].min()
    max_price = df['Display_Price'].max()
    best_hour = df.loc[df['Display_Price'] == min_price, 'Hour_Display'].iloc[0]

    st.markdown(f"### 📊 {t['daily_summary']} ({unit_label})")
    m1, m2, m3 = st.columns(3)
    m1.metric(t["avg_price"], fmt % avg_price)
    
    if show_raw or (not show_raw and tariff_type == t["tariff_pvpc"]):
        m2.metric(t["min_price"], fmt % min_price, f"at {best_hour}", delta_color="inverse")
        m3.metric(t["max_price"], fmt % max_price, delta_color="normal")
    else:
        m2.metric(t["your_rate"], fmt % df['Display_Price'].iloc[0])
        m3.metric(t["tax_applied"], f"{int(tax_value*100)}%")

    # --- Interactive Chart ---
    st.markdown("---")
    
    fig = px.bar(
        df, x="Hour_Display", y="Display_Price",
        color="Display_Price", 
        color_continuous_scale=chart_colors,
        title=f"{price_label} - {day_select}",
        labels={"Display_Price": f"{t['price_axis']} ({unit_label})", "Hour_Display": t['hour_axis']}
    )
    
    # --- ADD BACKGROUND ZONES (With Translated Legend) ---
    if not show_raw:
        is_weekend = day_select.weekday() >= 5
        for i in range(24):
            period_name, bg_color = get_tariff_period(i, is_weekend, t)
            fig.add_shape(type="rect", x0=i-0.5, x1=i+0.5, y0=0, y1=1, xref="x", yref="paper", fillcolor=bg_color, line_width=0, layer="below")
        
        # Legend (Translated)
        if not is_weekend:
            fig.add_annotation(x=3, y=1.07, text=f"🟦 {t['zone_valle']}", showarrow=False, xref="x", yref="paper", font=dict(color="blue", size=10))
            fig.add_annotation(x=10, y=1.07, text=f"🟨 {t['zone_llano']}", showarrow=False, xref="x", yref="paper", font=dict(color="#b5b500", size=10))
            fig.add_annotation(x=17, y=1.07, text=f"🟥 {t['zone_punta']}", showarrow=False, xref="x", yref="paper", font=dict(color="red", size=10))
        else:
            fig.add_annotation(x=12, y=1.07, text=f"🟦 {t['zone_valle']}", showarrow=False, xref="x", yref="paper", font=dict(color="blue", size=10))

    # --- NOW LINE (Timezone Corrected) ---
    if day_select == date.today():
        now_local = datetime.now(pytz.timezone(current_tz))
        now_hour_str = now_local.strftime('%H:00')
        fig.add_vline(x=now_hour_str, line_width=2, line_dash="dash", line_color="black")
        fig.add_annotation(x=now_hour_str, y=1.02, text=t["now_label"], showarrow=False, xref="x", yref="paper", font=dict(color="black", size=10, weight="bold"))

    fig.update_layout(
        xaxis=dict(fixedrange=True, title=None),
        yaxis=dict(fixedrange=True, title=None),
        coloraxis_showscale=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- CALCULATOR ---
    if show_calculator and not show_raw:
        st.markdown(f"### {t['calc_title']}")
        c1, c2, c3 = st.columns(3)
        with c1:
            appliance_power = st.number_input(t["calc_power"], value=2000, step=100)
        with c2:
            duration_hours = st.number_input(t["calc_duration"], value=2, min_value=1, max_value=12)
        
        df['Rolling_Avg'] = df['Display_Price'].rolling(window=duration_hours).mean().shift(1 - duration_hours)
        if not df['Rolling_Avg'].dropna().empty:
            best_val = df['Rolling_Avg'].min()
            best_idx = df['Rolling_Avg'].idxmin()
            best_time = df.loc[best_idx, 'Hour_Display']
            cost = (appliance_power / 1000) * duration_hours * best_val
            with c3:
                if tariff_type == t["tariff_pvpc"]:
                    st.success(f"**{t['calc_start']}** {best_time}")
                else:
                    st.info(f"**{t['calc_anytime']}**")
                st.metric(t["calc_cost"], fmt % cost)

    # --- Data Table & Download ---
    with st.expander(t["view_table"]):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t["download_csv"], data=csv, file_name=f"prices_{day_select}.csv", mime="text/csv")
        st.dataframe(df[['Hour_Display', 'Display_Price']].style.format({"Display_Price": fmt}), use_container_width=True)

else:
    st.error(f"{t['data_unavailable']} {day_select}.")
        
