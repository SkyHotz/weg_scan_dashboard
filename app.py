import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# Configuração da página
st.set_page_config(
    page_title="WEG SCAN Dashboard (Melhorado)",
    page_icon="📊",
    layout="wide",
)

# Limites de alerta
ALERT_LIMITS = {
    "VIBRAÇÃO AXIAL(mm/s)": {"min": 0, "max": 5},
    "VIBRAÇÃO RADIAL-Y (mm/s)": {"min": 0, "max": 5},
    "VIBRAÇÃO RADIAL-X (mm/s)": {"min": 0, "max": 7},
    "TEMPERATURA(°C)": {"min": 0, "max": 70},
    "CORRENTE ELÉTRICA (A)": {"min": 0, "max": 100},
}

DATA_FILE = "dados_dashboard.json"
LOG_FILE = "alteracoes_log.json"

if "data" not in st.session_state:
    st.session_state.data = None


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_json(DATA_FILE)
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
        return df
    return pd.DataFrame(columns=[
        "DateTime", "EQUIPAMENTO", "VIBRAÇÃO AXIAL(mm/s)", "VIBRAÇÃO RADIAL-Y (mm/s)",
        "VIBRAÇÃO RADIAL-X (mm/s)", "TEMPERATURA(°C)", "CORRENTE ELÉTRICA (A)"
    ])


def save_data(df):
    df.to_json(DATA_FILE, orient="records", indent=2, force_ascii=False)


def append_log(entry):
    logs = []
    if os.path.exists(LOG_FILE):
        logs = json.load(open(LOG_FILE, "r", encoding="utf-8"))
    logs.append(entry)
    json.dump(logs, open(LOG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def create_trend_chart(df, equipment, variable):
    df_eq = df[df["EQUIPAMENTO"] == equipment]
    if df_eq.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_eq["DateTime"], y=df_eq[variable], mode="lines+markers", name=variable))
    if variable in ALERT_LIMITS:
        limits = ALERT_LIMITS[variable]
        fig.add_hline(y=limits["max"], line_dash="dash", line_color="red")
        fig.add_hline(y=limits["min"], line_dash="dash", line_color="green")
    fig.update_layout(title=f"{variable} - {equipment}", xaxis_title="Data/Hora", yaxis_title=variable)
    return fig


st.title("📊 WEG SCAN Dashboard Melhorado")

# Carregar dados existentes
st.session_state.data = load_data()

# Formulário de novo registro
with st.form("novo_registro"):
    st.subheader("Adicionar Novo Registro")
    date = st.date_input("Data", value=datetime.now().date())
    time = st.time_input("Hora", value=datetime.now().time())
    equipamento = st.text_input("Equipamento")
    col1, col2, col3 = st.columns(3)
    vib_ax = col1.number_input("Vibração Axial (mm/s)", min_value=0.0, step=0.01)
    vib_ry = col2.number_input("Vibração Radial-Y (mm/s)", min_value=0.0, step=0.01)
    vib_rx = col3.number_input("Vibração Radial-X (mm/s)", min_value=0.0, step=0.01)
    col4, col5 = st.columns(2)
    temp = col4.number_input("Temperatura (°C)", min_value=-50.0, step=0.1)
    corrente = col5.number_input("Corrente Elétrica (A)", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Salvar")
    if submitted:
        dt = pd.Timestamp(datetime.combine(date, time))
        new_row = pd.DataFrame([{ "DateTime": dt, "EQUIPAMENTO": equipamento, "VIBRAÇÃO AXIAL(mm/s)": vib_ax,
                                  "VIBRAÇÃO RADIAL-Y (mm/s)": vib_ry, "VIBRAÇÃO RADIAL-X (mm/s)": vib_rx,
                                  "TEMPERATURA(°C)": temp, "CORRENTE ELÉTRICA (A)": corrente }])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        save_data(st.session_state.data)
        append_log({"timestamp": str(datetime.now()), "equipamento": equipamento, "variavel": "TODAS",
                    "novo_valor": new_row.to_dict("records")[0], "usuario": "Operador Local"})
        st.success("Registro adicionado e log atualizado!")

# Exibir dados e gráficos
if not st.session_state.data.empty:
    equipamentos = st.multiselect("Equipamentos", st.session_state.data["EQUIPAMENTO"].unique())
    variaveis = ["VIBRAÇÃO AXIAL(mm/s)", "VIBRAÇÃO RADIAL-Y (mm/s)", "VIBRAÇÃO RADIAL-X (mm/s)", "TEMPERATURA(°C)", "CORRENTE ELÉTRICA (A)"]
    for eq in equipamentos:
        for var in variaveis:
            fig = create_trend_chart(st.session_state.data, eq, var)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

st.subheader("🕓 Histórico de Alterações")
if os.path.exists(LOG_FILE):
    logs = json.load(open(LOG_FILE, "r", encoding="utf-8"))
    st.dataframe(pd.DataFrame(logs))
else:
    st.info("Nenhum log registrado ainda.")
