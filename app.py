import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
import plotly.express as px
import pytz

# --- Configuration ---
st.set_page_config(page_title="Iberian Energy Prices", page_icon="⚡", layout="wide")

# --- 🔗 URL PARAMETER HANDLING ---
qp = st.query_params

def get_param(key, default_val, type_func):
    try:
        if key in qp:
            return type_func(qp[key])
        return default_val
    except:
        return default_val

# Defaults
default_lang_idx = get_param("lang_idx", 2, int)
default_vat = get_param("vat", 23.0, float)
default_comm_fee = get_param("comm_fee", 0.025, float)
default_grid_type = get_param("grid_type", "Fixed", str)
default_grid_fixed = get_param("grid_fixed", 0.060, float)
default_grid_p1 = get_param("grid_p1", 0.100, float)
default_grid_p2 = get_param("grid_p2", 0.040, float)
default_grid_p3 = get_param("grid_p3", 0.010, float)
default_show_fixed_comp = get_param("show_fixed_comp", False, lambda x: x.lower() == 'true')
default_fixed_val = get_param("fixed_val", 0.120, float)

# --- 🌍 TRANSLATION ENGINE ---
LANGUAGES = {
    "English": {
        "title": "⚡ Iberian Electricity Prices",
        "config_title": "⚙️ Configuration & Tariff",
        "tab_daily": "📅 Daily View",
        "tab_history": "📈 30-Day Trend",
        "select_date": "Select Date",
        "country": "Country",
        "settings": "Settings",
        "show_raw": "Show Raw Market Price (€/MWh)",
        "comp_toggle": "Compare with Fixed Rate",
        "fixed_input": "Your Fixed Energy Price (€/kWh)",
        "taxes": "Taxes & Fees",
        "vat": "VAT / IVA (%)",
        "comm_fee_label": "Commercial Margin (€/kWh)",
        "comm_help": "Fee charged by your retailer to manage the contract. Usually 0.01 - 0.03 €.",
        "grid_fee_label": "Grid Access Fees",
        "grid_help": "Cost to maintain cables and transport energy. Can be fixed or variable.",
        "grid_type_fixed": "Fixed",
        "grid_type_var": "Variable (Time-of-Use)",
        "grid_fixed_input": "Fixed Grid Fee (€/kWh)",
        "grid_p1_input": "Peak Fee (Punta) (€/kWh)",
        "grid_p2_input": "Standard Fee (Llano) (€/kWh)",
        "grid_p3_input": "Off-Peak Fee (Valle) (€/kWh)",
        "calc_title": "⏱️ Plan Your Usage",
        "calc_appliance": "Select Appliance",
        "calc_custom": "Custom Power...",
        "calc_power": "Power (Watts)",
        "calc_duration": "Duration (Hours)",
        "calc_cost": "Estimated Cost",
        "calc_start": "Best Start:",
        "view_table": "View Detailed Data Table",
        "table_title": "📋 Hourly Data",
        "download_csv": "📥 Download Data as CSV",
        "daily_summary": "Daily Summary",
        "avg_price": "Average Price",
        "min_price": "Lowest Price",
        "max_price": "Highest Price",
        "your_rate": "Your Fixed Rate",
        "tax_applied": "Tax Applied",
        "price_axis": "Price",
        "hour_axis": "Start Hour",
        "interval_col": "Time Interval",
        "price_col": "Price",
        "base_col": "Base Market Price",
        "date_axis": "Date",
        "now_label": "NOW",
        "verdict_good": "✅ Great time to use energy!",
        "verdict_bad": "❌ Expensive! Wait if possible.",
        "verdict_avg": "⚖️ Average Price.",
        "verdict_fixed_win": "✅ Cheaper than your Fixed Rate!",
        "verdict_fixed_loss": "❌ More expensive than Fixed Rate.",
        "zone_valle": "Off-Peak",
        "zone_llano": "Standard",
        "zone_punta": "Peak",
        "data_unavailable": "⚠️ Data not available for",
        "raw_info": "Showing raw market data in €/MWh. Taxes and tariffs are hidden.",
        "hist_title": "Price Evolution (Last 30 Days)",
        "hist_avg_note": "Showing daily average prices.",
        "explain_title": "📝 Price Breakdown",
        "explain_formula": "Calculation Formula",
        "explain_market": "Market Price",
        "explain_comm": "Comm. Margin",
        "explain_grid": "Grid Fees",
        "explain_tax": "VAT"
    },
    "Español": {
        "title": "⚡ Precio de la Luz (OMIE)",
        "config_title": "⚙️ Configuración y Tarifa",
        "tab_daily": "📅 Vista Diaria",
        "tab_history": "📈 Tendencia 30 Días",
        "select_date": "Seleccionar Fecha",
        "country": "País",
        "settings": "Configuración",
        "show_raw": "Ver Precio Mercado (€/MWh)",
        "comp_toggle": "Comparar con Tarifa Fija",
        "fixed_input": "Precio Energía Fijo (€/kWh)",
        "taxes": "Impuestos y Peajes",
        "vat": "IVA (%)",
        "comm_fee_label": "Margen Comercial (€/kWh)",
        "comm_help": "Coste de gestión de la comercializadora. Suele ser 0.01 - 0.03 €.",
        "grid_fee_label": "Peajes de Acceso",
        "grid_help": "Coste de redes y transporte. Puede ser fijo o variable.",
        "grid_type_fixed": "Fijo",
        "grid_type_var": "Variable (Horario)",
        "grid_fixed_input": "Peaje Fijo (€/kWh)",
        "grid_p1_input": "Peaje Punta (P1) (€/kWh)",
        "grid_p2_input": "Peaje Llano (P2) (€/kWh)",
        "grid_p3_input": "Peaje Valle (P3) (€/kWh)",
        "calc_title": "⏱️ Planificador de Consumo",
        "calc_appliance": "Elegir Electrodoméstico",
        "calc_custom": "Potencia Personalizada...",
        "calc_power": "Potencia (W)",
        "calc_duration": "Duración (Horas)",
        "calc_cost": "Coste Estimado",
        "calc_start": "Mejor Hora:",
        "view_table": "Ver Tabla de Datos",
        "table_title": "📋 Datos Horarios",
        "download_csv": "📥 Descargar CSV",
        "daily_summary": "Resumen Diario",
        "avg_price": "Precio Medio",
        "min_price": "Mínimo",
        "max_price": "Máximo",
        "your_rate": "Tu Tarifa Fija",
        "tax_applied": "Impuesto Aplicado",
        "price_axis": "Precio",
        "hour_axis": "Hora Inicio",
        "interval_col": "Intervalo Horario",
        "price_col": "Precio",
        "base_col": "Precio Base Mercado",
        "date_axis": "Fecha",
        "now_label": "AHORA",
        "verdict_good": "✅ ¡Buen momento!",
        "verdict_bad": "❌ Caro. Espera si puedes.",
        "verdict_avg": "⚖️ Precio Normal.",
        "verdict_fixed_win": "✅ ¡Más barato que tu Fija!",
        "verdict_fixed_loss": "❌ Más caro que tu Fija.",
        "zone_valle": "Valle",
        "zone_llano": "Llano",
        "zone_punta": "Punta",
        "data_unavailable": "⚠️ Datos no disponibles para",
        "raw_info": "Mostrando datos crudos en €/MWh. Sin impuestos ni peajes.",
        "hist_title": "Evolución de Precios (Últimos 30 Días)",
        "hist_avg_note": "Mostrando precios medios diarios.",
        "explain_title": "📝 Desglose del Precio",
        "explain_formula": "Fórmula de Cálculo",
        "explain_market": "Precio Mercado",
        "explain_comm": "Margen Comer.",
        "explain_grid": "Peajes",
        "explain_tax": "IVA"
    },
    "Português": {
        "title": "⚡ Preço da Eletricidade (OMIE)",
        "config_title": "⚙️ Configuração e Tarifa",
        "tab_daily": "📅 Visão Diária",
        "tab_history": "📈 Tendência 30 Dias",
        "select_date": "Selecionar Data",
        "country": "País",
        "settings": "Configurações",
        "show_raw": "Ver Preço de Mercado (€/MWh)",
        "comp_toggle": "Comparar com Taxa Fixa",
        "fixed_input": "Seu Preço Fixo (€/kWh)",
        "taxes": "Impostos e Taxas",
        "vat": "IVA (%)",
        "comm_fee_label": "Margem Comercial (€/kWh)",
        "comm_help": "Custo de gestão do comercializador. Geralmente 0.01 - 0.03 €.",
        "grid_fee_label": "Tarifas de Acesso às Redes",
        "grid_help": "Custo de transporte e manutenção da rede. Pode ser fixo ou variável.",
        "grid_type_fixed": "Fixo",
        "grid_type_var": "Variável (Horário)",
        "grid_fixed_input": "Acesso Fixo (€/kWh)",
        "grid_p1_input": "Taxa Ponta (P1) (€/kWh)",
        "grid_p2_input": "Taxa Cheias (P2) (€/kWh)",
        "grid_p3_input": "Taxa Vazio (P3) (€/kWh)",
        "calc_title": "⏱️ Planear Consumo",
        "calc_appliance": "Escolher Eletrodoméstico",
        "calc_custom": "Potência Personalizada...",
        "calc_power": "Potência (W)",
        "calc_duration": "Duração (Horas)",
        "calc_cost": "Custo Estimado",
        "calc_start": "Melhor Início:",
        "view_table": "Ver Tabela de Dados",
        "table_title": "📋 Dados Horários",
        "download_csv": "📥 Baixar CSV",
        "daily_summary": "Resumo Diário",
        "avg_price": "Preço Médio",
        "min_price": "Mínimo",
        "max_price": "Máximo",
        "your_rate": "Sua Taxa Fixa",
        "tax_applied": "Imposto Aplicado",
        "price_axis": "Preço",
        "hour_axis": "Hora Início",
        "interval_col": "Intervalo Horário",
        "price_col": "Preço",
        "base_col": "Preço Base Mercado",
        "date_axis": "Data",
        "now_label": "AGORA",
        "verdict_good": "✅ Bom momento!",
        "verdict_bad": "❌ Caro. Espere se puder.",
        "verdict_avg": "⚖️ Preço Médio.",
        "verdict_fixed_win": "✅ Mais barato que a Fixa!",
        "verdict_fixed_loss": "❌ Mais caro que a Fixa.",
        "zone_valle": "Vazio",
        "zone_llano": "Cheias",
        "zone_punta": "Ponta",
        "data_unavailable": "⚠️ Dados não disponíveis para",
        "raw_info": "Mostrando dados brutos em €/MWh. Sem impostos ou taxas.",
        "hist_title": "Evolução de Preços (Últimos 30 Dias)",
        "hist_avg_note": "Mostrando preços médios diários.",
        "explain_title": "📝 Composição do Preço",
        "explain_formula": "Fórmula de Cálculo",
        "explain_market": "Preço Mercado",
        "explain_comm": "Margem Comer.",
        "explain_grid": "Tarifas Rede",
        "explain_tax": "IVA"
    }
}

# --- Appliance Library ---
APPLIANCES = {
    "Custom / Personalizado": 0,
    "Washing Machine / Máquina Roupa": 2000,
    "Dishwasher / Máquina Loiça": 1500,
    "Oven / Forno": 2500,
    "EV Charger (Slow) / Carregador Carro": 3700,
    "EV Charger (Fast) / Carregador Rápido": 7400,
    "Heater / Aquecedor": 1500,
    "AC / Ar Condicionado": 1000
}

# --- Function to determine Tariff Period ---
def get_tariff_period(hour, is_weekend, texts):
    if is_weekend: return texts["zone_valle"], "rgba(0, 0, 255, 0.1)"
    if 0 <= hour < 8: return texts["zone_valle"], "rgba(0, 0, 255, 0.1)"
    elif (8 <= hour < 10) or (14 <= hour < 18) or (22 <= hour < 24): return texts["zone_llano"], "rgba(255, 255, 0, 0.1)"
    else: return texts["zone_punta"], "rgba(255, 0, 0, 0.1)"

def get_period_key(hour, is_weekend):
    if is_weekend: return "P3"
    if 0 <= hour < 8: return "P3"
    elif (8 <= hour < 10) or (14 <= hour < 18) or (22 <= hour < 24): return "P2"
    else: return "P1"

def get_tariff_period_display(hour, is_weekend, texts):
    key = get_period_key(hour, is_weekend)
    if key == "P3": return texts["zone_valle"], "rgba(0, 0, 255, 0.1)"
    elif key == "P2": return texts["zone_llano"], "rgba(255, 255, 0, 0.1)"
    else: return texts["zone_punta"], "rgba(255, 0, 0, 0.1)"

# --- DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_daily_prices(selected_date, country_code):
    date_str = selected_date.strftime("%Y-%m-%d")
    bzn = "ES" if country_code == "Spain (ES)" else "PT"
    target_tz = 'Europe/Lisbon' if bzn == "PT" else 'Europe/Madrid'
    url = f"https://api.energy-charts.info/price?bzn={bzn}&start={date_str}&end={date_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'unix_seconds' not in data or 'price' not in data: return None, None
        
        df = pd.DataFrame({
            'Timestamp': pd.to_datetime(data['unix_seconds'], unit='s').tz_localize('UTC').tz_convert(target_tz),
            'Raw_Price_MWh': data['price']
        })
        df = df.set_index('Timestamp').resample('1h').mean().reset_index()
        # Create clear Interval String
        df['Hour_Start'] = df['Timestamp'].dt.strftime('%H:00')
        df['Hour_End'] = (df['Timestamp'] + pd.Timedelta(hours=1)).dt.strftime('%H:00')
        df['Hour_Range'] = df['Hour_Start'] + " - " + df['Hour_End']
        df['Hour_Int'] = df['Timestamp'].dt.hour
        return df, target_tz
    except: return None, None

@st.cache_data(ttl=3600)
def get_historical_prices(end_date, country_code, days=30):
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    bzn = "ES" if country_code == "Spain (ES)" else "PT"
    url = f"https://api.energy-charts.info/price?bzn={bzn}&start={start_str}&end={end_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'unix_seconds' not in data or 'price' not in data: return None
        
        df = pd.DataFrame({
            'Timestamp': pd.to_datetime(data['unix_seconds'], unit='s'),
            'Raw_Price_MWh': data['price']
        })
        df['Date'] = df['Timestamp'].dt.date
        daily_avg = df.groupby('Date')['Raw_Price_MWh'].mean().reset_index()
        return daily_avg
    except: return None

# --- MAIN APP START ---
st.title("⚡ Iberian Electricity Prices")

# --- CONSOLIDATED CONFIGURATION (Top Expander) ---
# We initialize translation based on default first, then update after selection
lang_options = ["English", "Español", "Português"]
safe_idx = default_lang_idx if 0 <= default_lang_idx < 3 else 2

# We need to load 't' before the expander to get the title
t_pre = LANGUAGES[lang_options[safe_idx]]

with st.expander(t_pre["config_title"], expanded=False):
    # Column Layout for Settings
    col_set1, col_set2, col_set3 = st.columns([1, 1, 1])
    
    with col_set1:
        st.markdown("##### 🌍 Region")
        lang_choice = st.selectbox("Language / Idioma", lang_options, index=safe_idx)
        t = LANGUAGES[lang_choice] # Update translation immediately
        st.query_params["lang_idx"] = lang_options.index(lang_choice)
        
        show_raw = st.toggle(t["show_raw"], value=False, help=t["raw_info"])
        # Calculator Toggle
        show_calculator = st.toggle(t["calc_title"], value=True)

    fixed_price_final = 0.0
    access_fee = 0.0
    
    # Logic: If Raw is OFF, show Tariff & Tax settings
    if not show_raw:
        with col_set2:
            st.markdown("##### 🧾 Tariff")
            show_fixed = st.toggle(t["comp_toggle"], value=default_show_fixed_comp)
            st.query_params["show_fixed_comp"] = str(show_fixed)
            
            if show_fixed:
                fixed_val_input = st.number_input(t["fixed_input"], value=default_fixed_val, step=0.001, format="%.3f")
                st.query_params["fixed_val"] = fixed_val_input
                
            comm_input = st.number_input(t["comm_fee_label"], value=default_comm_fee, step=0.001, format="%.3f", help=t["comm_help"])
            st.query_params["comm_fee"] = comm_input

        with col_set3:
            st.markdown(f"##### 🏛️ {t['taxes']}")
            tax_input = st.number_input(t["vat"], value=default_vat, step=1.0)
            st.query_params["vat"] = tax_input
            tax_value = tax_input / 100
            
            st.markdown(f"**{t['grid_fee_label']}**", help=t["grid_help"])
            grid_options = [t["grid_type_fixed"], t["grid_type_var"]]
            grid_type_idx = 0 if default_grid_type == "Fixed" else 1
            grid_type_sel = st.radio("Grid Type", grid_options, index=grid_type_idx, horizontal=True, label_visibility="collapsed")
            
            grid_fee_p1, grid_fee_p2, grid_fee_p3 = 0.0, 0.0, 0.0
            
            if grid_type_sel == t["grid_type_fixed"]:
                st.query_params["grid_type"] = "Fixed"
                grid_fixed_val = st.number_input(t["grid_fixed_input"], value=default_grid_fixed, step=0.001, format="%.3f")
                st.query_params["grid_fixed"] = grid_fixed_val
                grid_fee_p1 = grid_fee_p2 = grid_fee_p3 = grid_fixed_val
            else:
                st.query_params["grid_type"] = "Variable"
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    grid_fee_p1 = st.number_input("P1", value=default_grid_p1, step=0.001, format="%.3f", help=t["grid_p1_input"])
                with sc2:
                    grid_fee_p2 = st.number_input("P2", value=default_grid_p2, step=0.001, format="%.3f", help=t["grid_p2_input"])
                with sc3:
                    grid_fee_p3 = st.number_input("P3", value=default_grid_p3, step=0.001, format="%.3f", help=t["grid_p3_input"])
                
                st.query_params["grid_p1"] = grid_fee_p1
                st.query_params["grid_p2"] = grid_fee_p2
                st.query_params["grid_p3"] = grid_fee_p3

        if show_fixed:
            fixed_price_final = fixed_val_input * (1 + tax_value)

# Date Blocker
now_cet = datetime.now(pytz.timezone('Europe/Madrid'))
if now_cet.hour > 13 or (now_cet.hour == 13 and now_cet.minute >= 30):
    max_allowed = now_cet.date() + timedelta(days=1)
else:
    max_allowed = now_cet.date()

# --- MAIN CONTROLS (Date & Country) ---
col1, col2 = st.columns(2)
with col1:
    day_select = st.date_input(t["select_date"], date.today(), max_value=max_allowed)
with col2:
    default_country_idx = 1 if lang_choice == "Português" else 0
    country_choice = st.radio(t["country"], ["Spain (ES)", "Portugal (PT)"], index=default_country_idx, horizontal=True)

# --- TABS LAYOUT ---
tab1, tab2 = st.tabs([t["tab_daily"], t["tab_history"]])

# === TAB 1: DAILY VIEW ===
with tab1:
    df, current_tz = get_daily_prices(day_select, country_choice)

    if df is not None and not df.empty:
        # --- CALCULATION LOGIC ---
        if show_raw:
            df['Display_Price'] = df['Raw_Price_MWh']
            unit_label, chart_colors = "€/MWh", "RdYlGn_r"
            fmt_str = "{:.2f} €" 
            title_label = "MWh"
        else:
            unit_label = "€/kWh"
            fmt_str = "{:.2f} €" 
            title_label = "PVPC"
            chart_colors = "RdYlGn_r"
            
            is_weekend = day_select.weekday() >= 5
            def apply_grid_fee(row):
                p_key = get_period_key(row['Hour_Int'], is_weekend)
                if p_key == "P1": return grid_fee_p1
                if p_key == "P2": return grid_fee_p2
                return grid_fee_p3

            df['Grid_Fee_Applied'] = df.apply(apply_grid_fee, axis=1)
            df['Display_Price'] = ((df['Raw_Price_MWh'] / 1000) + comm_input + df['Grid_Fee_Applied']) * (1 + tax_value)

        # --- LIVE STATUS ---
        if day_select == date.today():
            now_local = datetime.now(pytz.timezone(current_tz))
            curr_row = df.loc[df['Hour_Int'] == now_local.hour]
            if not curr_row.empty:
                cp = curr_row['Display_Price'].values[0]
                avg = df['Display_Price'].mean()
                
                if not show_raw and show_fixed:
                    if cp < fixed_price_final:
                        v_txt, v_col = t["verdict_fixed_win"], "green"
                        delta_val = cp - fixed_price_final
                    else:
                        v_txt, v_col = t["verdict_fixed_loss"], "red"
                        delta_val = cp - fixed_price_final
                    delta_text = f"{delta_val:.2f} vs Fixed"
                else:
                    if cp < avg * 0.9: v_txt, v_col = t["verdict_good"], "green"
                    elif cp > avg * 1.1: v_txt, v_col = t["verdict_bad"], "red"
                    else: v_txt, v_col = t["verdict_avg"], "orange"
                    delta_text = f"{cp - avg:.2f} vs Avg"

                st.markdown(f"### {t['now_label']} ({now_local.strftime('%H:%M')})")
                c1, c2 = st.columns([1, 2])
                c1.metric(t['price_axis'], fmt_str.format(cp), delta=delta_text, delta_color="inverse")
                c2.markdown(f"#### :{v_col}[{v_txt}]")
                st.divider()

        avg_price = df['Display_Price'].mean()
        min_price = df['Display_Price'].min()
        max_price = df['Display_Price'].max()
        best_h_idx = df['Display_Price'].idxmin()
        best_h_range = df.loc[best_h_idx, 'Hour_Range']

        st.markdown(f"### 📊 {t['daily_summary']} ({unit_label})")
        m1, m2, m3 = st.columns(3)
        m1.metric(t["avg_price"], fmt_str.format(avg_price))
        m2.metric(t["min_price"], fmt_str.format(min_price), f"at {best_h_range}", delta_color="inverse")
        m3.metric(t["max_price"], fmt_str.format(max_price), delta_color="normal")

        # --- FORMULA EXPLAINER ---
        if not show_raw:
            with st.expander(t["explain_title"]):
                st.latex(r"\text{" + t["price_axis"] + r"} = (\text{" + t["explain_market"] + r"} + \text{" + t["explain_comm"] + r"} + \text{" + t["explain_grid"] + r"}) \times (1 + \text{" + t["explain_tax"] + r"})")
                
                avg_mkt = df['Raw_Price_MWh'].mean() / 1000
                avg_grid = df['Grid_Fee_Applied'].mean()
                
                c_ex1, c_ex2, c_ex3, c_ex4 = st.columns(4)
                c_ex1.metric(t["explain_market"], f"{avg_mkt:.3f} €")
                c_ex2.metric(f"+ {t['explain_comm']}", f"{comm_input:.3f} €")
                c_ex3.metric(f"+ {t['explain_grid']} (Avg)", f"{avg_grid:.3f} €")
                c_ex4.metric(f"x {t['explain_tax']}", f"{int(tax_value*100)}%")
                
                st.info(f"**Total Avg:** {avg_price:.3f} €/kWh")

        st.markdown("---")
        
        # --- CHART ---
        fig = px.bar(
            df, 
            x="Hour_Start", 
            y="Display_Price", 
            color="Display_Price", 
            color_continuous_scale=chart_colors, 
            title=f"{title_label} - {day_select}", 
            labels={"Display_Price": f"{t['price_axis']} ({unit_label})", "Hour_Start": t['hour_axis']},
            custom_data=['Hour_Range', 'Raw_Price_MWh']
        )
        
        # Tooltips - UPDATED to remove deprecation warning
        if show_raw:
             fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Price: <b>%{y:.2f} €/MWh</b><extra></extra>")
        else:
             fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Final: <b>%{y:.2f} €/kWh</b><br>Market Base: %{customdata[1]:.2f} €/MWh<extra></extra>")

        if not show_raw and show_fixed:
            fig.add_hline(y=fixed_price_final, line_dash="dash", line_color="#2E86C1", line_width=3, annotation_text=f"{t['your_rate']} ({fixed_price_final:.2f})")

        if not show_raw:
            is_weekend = day_select.weekday() >= 5
            for i in range(24):
                p_name, bg_col = get_tariff_period_display(i, is_weekend, t)
                fig.add_shape(type="rect", x0=i-0.5, x1=i+0.5, y0=0, y1=1, xref="x", yref="paper", fillcolor=bg_col, line_width=0, layer="below")
            
            if not is_weekend:
                fig.add_annotation(x=3, y=1.07, text=f"🟦 {t['zone_valle']}", showarrow=False, xref="x", yref="paper", font=dict(color="blue", size=10))
                fig.add_annotation(x=10, y=1.07, text=f"🟨 {t['zone_llano']}", showarrow=False, xref="x", yref="paper", font=dict(color="#b5b500", size=10))
                fig.add_annotation(x=17, y=1.07, text=f"🟥 {t['zone_punta']}", showarrow=False, xref="x", yref="paper", font=dict(color="red", size=10))
            else:
                fig.add_annotation(x=12, y=1.07, text=f"🟦 {t['zone_valle']}", showarrow=False, xref="x", yref="paper", font=dict(color="blue", size=10))
        
        if day_select == date.today():
            now_str = datetime.now(pytz.timezone(current_tz)).strftime('%H:00')
            fig.add_vline(x=now_str, line_width=2, line_dash="dash", line_color="black")

        fig.update_layout(xaxis=dict(fixedrange=True, title=t['hour_axis']), yaxis=dict(fixedrange=True, title=None), coloraxis_showscale=False, hovermode="x unified", margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, width=None, use_container_width=True, config={'displayModeBar': False})

        # --- CALCULATOR ---
        if show_calculator and not show_raw:
            st.markdown(f"### {t['calc_title']}")
            c1, c2, c3 = st.columns(3)
            with c1: 
                app_list = list(APPLIANCES.keys())
                selected_app = st.selectbox(t["calc_appliance"], app_list, index=0)
                preset_power = APPLIANCES[selected_app]
                
                if preset_power == 0:
                    ap = st.number_input(t["calc_power"], value=2000, step=100)
                else:
                    ap = st.number_input(t["calc_power"], value=preset_power)
                    
            with c2: dh = st.number_input(t["calc_duration"], value=2, min_value=1)
            
            df['Roll'] = df['Display_Price'].rolling(window=dh).mean().shift(1 - dh)
            if not df['Roll'].dropna().empty:
                cost = (ap/1000)*dh*df['Roll'].min()
                with c3:
                    best_idx = df['Roll'].idxmin()
                    st.success(f"**{t['calc_start']}** {df.loc[best_idx, 'Hour_Range']}")
                    st.metric(t["calc_cost"], fmt_str.format(cost))

        # --- DATA TABLE ---
        st.markdown(f"### {t['table_title']}")
        with st.expander(t["view_table"]):
            view_df = df[['Hour_Range', 'Display_Price']].copy()
            view_df.columns = [t['interval_col'], f"{t['price_col']} ({unit_label})"]
            if not show_raw:
                view_df[f"{t['base_col']} (€/MWh)"] = df['Raw_Price_MWh']
            st.dataframe(view_df.style.format(precision=2), width=None, use_container_width=True, hide_index=True)
    else:
        st.error(f"{t['data_unavailable']} {day_select}.")

# === TAB 2: HISTORY VIEW ===
with tab2:
    hist_df = get_historical_prices(day_select, country_choice)
    if hist_df is not None:
        if show_raw:
            hist_df['Display_Price'] = hist_df['Raw_Price_MWh']
            h_unit = "€/MWh"
            fmt_hist = "{:.2f} €"
        else:
            h_unit = "€/kWh"
            fmt_hist = "{:.2f} €"
            if st.query_params.get("grid_type") == "Fixed": proxy_grid = default_grid_fixed
            else: proxy_grid = default_grid_p2 
            hist_df['Display_Price'] = ((hist_df['Raw_Price_MWh'] / 1000) + comm_input + proxy_grid) * (1 + tax_value)

        st.markdown(f"### {t['hist_title']}")
        st.caption(t['hist_avg_note'])
        
        fig_h = px.line(hist_df, x="Date", y="Display_Price", markers=True, title=f"Average {h_unit}", labels={"Display_Price": t['price_axis'], "Date": t['date_axis']})
        fig_h.update_traces(hovertemplate="<b>%{x}</b><br>Price: <b>%{y:.2f} " + h_unit + "</b><extra></extra>")
        fig_h.update_layout(xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), hovermode="x unified")
        st.plotly_chart(fig_h, width=None, use_container_width=True, config={'displayModeBar': False})
        
        h_avg = hist_df['Display_Price'].mean()
        h_min = hist_df['Display_Price'].min()
        h_max = hist_df['Display_Price'].max()
        
        hc1, hc2, hc3 = st.columns(3)
        hc1.metric(f"30-Day Avg", fmt_hist.format(h_avg))
        hc2.metric("Min (Day)", fmt_hist.format(h_min))
        hc3.metric("Max (Day)", fmt_hist.format(h_max))
    else:
        st.warning("History data not available.")
