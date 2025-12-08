import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
import plotly.express as px
import pytz

# --- Configuration ---
st.set_page_config(page_title="Preço da Eletricidade", page_icon="⚡", layout="wide")

# --- 🎨 FORCE WHITE BACKGROUND (CSS) ---
st.markdown("""
    <style>
        .stApp {
            background-color: #FFFFFF;
            color: #000000;
        }
    </style>
""", unsafe_allow_html=True)

# --- 🌍 TRANSLATION ENGINE ---
LANGUAGES = {
    "Português": {
        "title": "⚡ Preço da Eletricidade (OMIE)",
        "tab_daily": "📅 Visão Diária",
        "tab_history": "📈 Tendência 30 Dias",
        "select_date": "Selecionar Data",
        "country": "País",
        "settings": "⚙️ Configurações",
        "show_raw": "Ver Preço de Mercado (€/MWh)",
        "tariff_type": "Tipo de Tarifa:",
        "tariff_pvpc": "Indexado (Mercado)",
        "tariff_fixed": "Taxa Fixa",
        "fixed_price_label": "Seu Preço Fixo (€/kWh)",
        "taxes": "Impostos e Taxas",
        "mismatch": "Ajuste / Perdas (%)",
        "vat": "IVA (%)",
        "fees": "Taxas de Acesso / Spread (€/kWh)",
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
        "tax_
        
