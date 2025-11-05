import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="WEG SCAN Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-danger {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_modified' not in st.session_state:
    st.session_state.data_modified = False

# Definir limites de alerta para cada variável
ALERT_LIMITS = {
    'VIBRAÇÃO AXIAL(mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-Y (mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-X (mm/s)': {'min': 0, 'max': 7},
    'TEMPERATURA(°C)': {'min': 0, 'max': 70},
    'CORRENTE ELÉTRICA (A)': {'min': 0, 'max': 100}
}

# Colunas de variáveis medidas
MEASURED_VARIABLES = [
    'VIBRAÇÃO AXIAL(mm/s)',
    'VIBRAÇÃO RADIAL-Y (mm/s)',
    'VIBRAÇÃO RADIAL-X (mm/s)',
    'TEMPERATURA(°C)',
    'CORRENTE ELÉTRICA (A)'
]

# ============================================================================
# FUNÇÕES DE LOG DE ALTERAÇÕES
# ============================================================================

def load_change_log():
    """Carrega o log de alterações do arquivo JSON"""
    log_file = 'alteracoes_log.json'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            return log_data
        except Exception as e:
            st.warning(f"Erro ao carregar log: {e}")
            return []
    return []

def save_change_log(log_data):
    """Salva o log de alterações em arquivo JSON"""
    log_file = 'alteracoes_log.json'
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar log: {e}")

def add_change_log_entry(equipamento, variavel, valor_anterior, novo_valor, usuario="Operador Local"):
    """Adiciona uma entrada ao log de alterações"""
    log_data = load_change_log()
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'equipamento': equipamento,
        'variavel': variavel,
        'valor_anterior': valor_anterior,
        'novo_valor': novo_valor,
        'usuario': usuario
    }
    
    log_data.append(entry)
    save_change_log(log_data)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO E SALVAMENTO DE DADOS
# ============================================================================

# Função para carregar dados do Excel
@st.cache_data
def load_excel_data(file_path):
    """Carrega dados da planilha principal do Excel"""
    try:
        df = pd.read_excel(file_path, sheet_name='Planilha1', header=1)
        # Limpar colunas sem nome
        df = df.dropna(how='all', axis=1)
        df = df.dropna(how='all', axis=0)
        
        # Preencher valores de DATA
        df['DATA'] = df['DATA'].ffill()
        
        # Combinar DATA e HORÁRIO em uma coluna datetime
        df['DateTime'] = pd.to_datetime(
            df['DATA'].astype(str) + ' ' + df['HORÁRIO'].astype(str),
            format='%Y-%m-%d %H:%M:%S',
            errors='coerce'
        )
        
        # Remover linhas com DateTime inválido
        df = df.dropna(subset=['DateTime'])
        
        # Converter colunas numéricas
        for col in MEASURED_VARIABLES:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Adicionar coluna CORRENTE ELÉTRICA se não existir
        if 'CORRENTE ELÉTRICA (A)' not in df.columns:
            df['CORRENTE ELÉTRICA (A)'] = None
        
        # Ordenar por DateTime
        df = df.sort_values('DateTime').reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

# Função para salvar dados em JSON
def save_data_to_json(df):
    """Salva dados em arquivo JSON para persistência"""
    json_file = 'dados_dashboard.json'
    try:
        # Converter DataFrame para JSON
        data_dict = df.to_dict('records')
        # Converter datetime para string
        for record in data_dict:
            if 'DateTime' in record and pd.notna(record['DateTime']):
                record['DateTime'] = str(record['DateTime'])
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

# Função para carregar dados do JSON
def load_data_from_json():
    """Carrega dados do arquivo JSON se existir"""
    json_file = 'dados_dashboard.json'
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            df = pd.DataFrame(data_dict)
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
            return df
        except Exception as e:
            st.warning(f"Erro ao carregar dados salvos: {e}")
            return None
    return None

# Função para criar gráfico de tendência
def create_trend_chart(df, equipment, variable, title):
    """Cria gráfico de linha com tendência para uma variável"""
    try:
        # Filtrar dados do equipamento
        df_equipment = df[df['EQUIPAMENTO'] == equipment].copy()
        
        if df_equipment.empty:
            st.warning(f"Sem dados para {equipment}")
            return None
        
        # Remover valores NaN
        df_equipment = df_equipment.dropna(subset=[variable])
        
        if df_equipment.empty:
            st.warning(f"Sem dados válidos para {equipment} - {variable}")
            return None
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar linha de dados
        fig.add_trace(go.Scatter(
            x=df_equipment['DateTime'],
            y=df_equipment[variable],
            mode='lines+markers',
            name=variable,
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Adicionar linha de tendência (média móvel)
        if len(df_equipment) > 1:
            df_equipment['Trend'] = df_equipment[variable].rolling(window=min(3, len(df_equipment)), center=True).mean()
            fig.add_trace(go.Scatter(
                x=df_equipment['DateTime'],
                y=df_equipment['Trend'],
                mode='lines',
                name='Tendência',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        # Adicionar limites de alerta
        if variable in ALERT_LIMITS:
            limits = ALERT_LIMITS[variable]
            fig.add_hline(y=limits['max'], line_dash="dash", line_color="red", 
                         annotation_text=f"Limite Máx: {limits['max']}", annotation_position="right")
            fig.add_hline(y=limits['min'], line_dash="dash", line_color="green",
                         annotation_text=f"Limite Mín: {limits['min']}", annotation_position="right")
        
        # Atualizar layout
        fig.update_layout(
            title=f"{title} - {equipment}",
            xaxis_title="Data/Hora",
            yaxis_title=variable,
            hovermode='x unified',
            height=400,
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {e}")
        return None

# Função para calcular estatísticas
def calculate_statistics(df, equipment, variable):
    """Calcula estatísticas para uma variável"""
    df_equipment = df[df['EQUIPAMENTO'] == equipment].copy()
    df_equipment = df_equipment.dropna(subset=[variable])
    
    if df_equipment.empty:
        return None
    
    stats = {
        'Média': df_equipment[variable].mean(),
        'Máximo': df_equipment[variable].max(),
        'Mínimo': df_equipment[variable].min(),
        'Desvio Padrão': df_equipment[variable].std(),
        'Última Leitura': df_equipment[variable].iloc[-1]
    }
    
    return stats

# Função para verificar alertas
def check_alerts(df, equipment, variable):
    """Verifica se há valores fora dos limites"""
    df_equipment = df[df['EQUIPAMENTO'] == equipment].copy()
    df_equipment = df_equipment.dropna(subset=[variable])
    
    if df_equipment.empty or variable not in ALERT_LIMITS:
        return []
    
    limits = ALERT_LIMITS[variable]
    alerts = []
    
    for idx, row in df_equipment.iterrows():
        value = row[variable]
        if value > limits['max']:
            alerts.append({
                'type': 'danger',
                'message': f"⚠️ {variable}: {value:.2f} (Acima do limite máximo: {limits['max']})",
                'datetime': row['DateTime']
            })
        elif value < limits['min']:
            alerts.append({
                'type': 'warning',
                'message': f"⚠️ {variable}: {value:.2f} (Abaixo do limite mínimo: {limits['min']})",
                'datetime': row['DateTime']
            })
    
    return alerts

# Função para exportar dados para Excel
def export_to_excel(df):
    """Exporta dados para arquivo Excel"""
    try:
        output_file = 'dados_exportados.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Planilha principal
            df_export = df[['DateTime', 'EQUIPAMENTO'] + MEASURED_VARIABLES].copy()
            df_export.columns = ['Data/Hora', 'Equipamento'] + [
                'Vibração Axial (mm/s)',
                'Vibração Radial-Y (mm/s)',
                'Vibração Radial-X (mm/s)',
                'Temperatura (°C)',
                'Corrente Elétrica (A)'
            ]
            df_export.to_excel(writer, sheet_name='Dados', index=False)
            
            # Planilha de resumo por equipamento
            summary_data = []
            for equipment in df['EQUIPAMENTO'].unique():
                df_eq = df[df['EQUIPAMENTO'] == equipment]
                summary_row = {
                    'Equipamento': equipment,
                    'Registros': len(df_eq)
                }
                for var in MEASURED_VARIABLES:
                    summary_row[f'{var} (Média)'] = df_eq[var].mean()
                summary_data.append(summary_row)
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Resumo', index=False)
        
        return output_file
    except Exception as e:
        st.error(f"Erro ao exportar dados: {e}")
        return None

# Função para exportar gráfico como PNG
def export_chart_as_png(fig, filename):
    """Exporta gráfico Plotly como PNG"""
    try:
        fig.write_image(filename, width=1200, height=600)
        return filename
    except Exception as e:
        st.warning(f"Não foi possível exportar como PNG: {e}. Instale kaleido para esta funcionalidade.")
        return None

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

# Header
st.markdown("# 📊 WEG SCAN Dashboard")
st.markdown("Sistema de monitoramento e análise de dados de equipamentos com visualização de tendências")

# Sidebar - Controles
with st.sidebar:
    st.markdown("## ⚙️ Controles")
    
    # Carregar dados
    if st.button("🔄 Carregar Dados do Excel", use_container_width=True):
        st.session_state.data = load_excel_data('DADOSWEGSCAN.xlsx')
        st.success("Dados carregados com sucesso!")
    
    # Se não há dados em session_state, tentar carregar do JSON
    if st.session_state.data is None:
        json_data = load_data_from_json()
        if json_data is not None:
            st.session_state.data = json_data
        else:
            # Tentar carregar do Excel automaticamente
            st.session_state.data = load_excel_data('DADOSWEGSCAN.xlsx')
    
    st.markdown("---")
    
    # Filtros
    if st.session_state.data is not None:
        st.markdown("### 🔍 Filtros")
        
        # Filtro de equipamento
        equipamentos = sorted(st.session_state.data['EQUIPAMENTO'].unique())
        selected_equipment = st.multiselect(
            "Equipamentos",
            equipamentos,
            default=equipamentos
        )
        
        # Filtro de período
        st.markdown("**Período**")
        col1, col2 = st.columns(2)
        with col1:
            date_min = st.date_input(
                "De",
                st.session_state.data['DateTime'].min().date()
            )
        with col2:
            date_max = st.date_input(
                "Até",
                st.session_state.data['DateTime'].max().date()
            )
        
        # Filtro de variável
        selected_variables = st.multiselect(
            "Variáveis",
            MEASURED_VARIABLES,
            default=MEASURED_VARIABLES
        )
        
        st.markdown("---")
        
        # Opções de exportação
        st.markdown("### 📥 Exportar Dados")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("📊 Excel", use_container_width=True):
                export_file = export_to_excel(st.session_state.data)
                if export_file:
                    with open(export_file, 'rb') as f:
                        st.download_button(
                            label="⬇️ Baixar",
                            data=f.read(),
                            file_name="dados_weg_scan.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
        
        with col_export2:
            if st.button("📋 CSV", use_container_width=True):
                csv_data = st.session_state.data[['DateTime', 'EQUIPAMENTO'] + MEASURED_VARIABLES].to_csv(index=False)
                st.download_button(
                    label="⬇️ Baixar",
                    data=csv_data,
                    file_name="dados_weg_scan.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        
        # Entrada de novos dados
        st.markdown("### ➕ Adicionar Novo Registro")
        
        with st.form("form_novo_registro"):
            new_datetime = st.date_input("📅 Data", value=datetime.now().date())
            new_time = st.time_input("🕐 Hora", value=datetime.now().time())
            new_equipment = st.selectbox("⚙️ Equipamento", equipamentos)
            
            st.markdown("**Medições:**")
            col1, col2 = st.columns(2)
            
            with col1:
                new_vib_axial = st.number_input("Vibração Axial (mm/s)", min_value=0.0, step=0.01, format="%.2f")
                new_vib_radial_y = st.number_input("Vibração Radial-Y (mm/s)", min_value=0.0, step=0.01, format="%.2f")
                new_vib_radial_x = st.number_input("Vibração Radial-X (mm/s)", min_value=0.0, step=0.01, format="%.2f")
            
            with col2:
                new_temp = st.number_input("Temperatura (°C)", min_value=-50.0, step=0.1, format="%.1f")
                new_current = st.number_input("Corrente Elétrica (A)", min_value=0.0, step=0.1, format="%.1f")
            
            submitted = st.form_submit_button("✅ Adicionar Registro", use_container_width=True)
            
            if submitted:
                # Validar entrada
                if new_vib_axial < 0 or new_vib_radial_y < 0 or new_vib_radial_x < 0:
                    st.error("❌ Valores de vibração não podem ser negativos!")
                else:
                    # Criar novo registro
                    new_record = {
                        'DateTime': pd.Timestamp(datetime.combine(new_datetime, new_time)),
                        'DATA': new_datetime,
                        'HORÁRIO': new_time,
                        'EQUIPAMENTO': new_equipment,
                        'VIBRAÇÃO AXIAL(mm/s)': new_vib_axial,
                        'VIBRAÇÃO RADIAL-Y (mm/s)': new_vib_radial_y,
                        'VIBRAÇÃO RADIAL-X (mm/s)': new_vib_radial_x,
                        'TEMPERATURA(°C)': new_temp,
                        'CORRENTE ELÉTRICA (A)': new_current
                    }
                    
                    # Registrar alterações no log
                    for var in MEASURED_VARIABLES:
                        add_change_log_entry(
                            equipamento=new_equipment,
                            variavel=var,
                            valor_anterior=None,
                            novo_valor=new_record[var]
                        )
                    
                    # Adicionar ao DataFrame
                    new_df = pd.DataFrame([new_record])
                    st.session_state.data = pd.concat([st.session_state.data, new_df], ignore_index=True)
                    st.session_state.data = st.session_state.data.sort_values('DateTime').reset_index(drop=True)
                    
                    # Salvar em JSON
                    save_data_to_json(st.session_state.data)
                    
                    st.success("✅ Registro adicionado com sucesso!")
                    st.rerun()

# Conteúdo principal
if st.session_state.data is not None:
    # Filtrar dados
    df_filtered = st.session_state.data[
        (st.session_state.data['EQUIPAMENTO'].isin(selected_equipment)) &
        (st.session_state.data['DateTime'].dt.date >= date_min) &
        (st.session_state.data['DateTime'].dt.date <= date_max)
    ].copy()
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # Tabs para diferentes visualizações
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Gráficos", "📊 Estatísticas", "⚠️ Alertas", "📋 Dados", "🕓 Histórico"])
        
        with tab1:
            st.markdown("## Gráficos de Tendência")
            
            # Criar gráficos para cada variável
            for variable in selected_variables:
                st.markdown(f"### {variable}")
                
                cols = st.columns(len(selected_equipment))
                for idx, equipment in enumerate(selected_equipment):
                    with cols[idx]:
                        fig = create_trend_chart(df_filtered, equipment, variable, variable)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown("## Estatísticas por Equipamento")
            
            for equipment in selected_equipment:
                st.markdown(f"### {equipment}")
                
                cols = st.columns(len(selected_variables))
                for idx, variable in enumerate(selected_variables):
                    with cols[idx]:
                        stats = calculate_statistics(df_filtered, equipment, variable)
                        if stats:
                            st.metric(f"{variable}", f"{stats['Última Leitura']:.2f}")
                            with st.expander("Ver detalhes"):
                                st.write(f"**Média:** {stats['Média']:.2f}")
                                st.write(f"**Máximo:** {stats['Máximo']:.2f}")
                                st.write(f"**Mínimo:** {stats['Mínimo']:.2f}")
                                st.write(f"**Desvio Padrão:** {stats['Desvio Padrão']:.2f}")
                
                st.markdown("---")
        
        with tab3:
            st.markdown("## Alertas de Valores Fora de Limites")
            
            all_alerts = []
            for equipment in selected_equipment:
                for variable in selected_variables:
                    alerts = check_alerts(df_filtered, equipment, variable)
                    all_alerts.extend(alerts)
            
            if all_alerts:
                # Ordenar alertas por data (mais recentes primeiro)
                all_alerts.sort(key=lambda x: x['datetime'], reverse=True)
                
                for alert in all_alerts[-10:]:  # Mostrar últimos 10 alertas
                    if alert['type'] == 'danger':
                        st.markdown(f"<div class='alert-danger'>{alert['message']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='alert-warning'>{alert['message']}</div>", unsafe_allow_html=True)
            else:
                st.success("✅ Nenhum alerta no período selecionado!")
        
        with tab4:
            st.markdown("## Visualização de Dados")
            
            # Mostrar tabela de dados
            df_display = df_filtered[['DateTime', 'EQUIPAMENTO'] + MEASURED_VARIABLES].copy()
            df_display.columns = ['Data/Hora', 'Equipamento', 'Vibração Axial (mm/s)',
                                 'Vibração Radial-Y (mm/s)', 'Vibração Radial-X (mm/s)', 
                                 'Temperatura (°C)', 'Corrente Elétrica (A)']
            
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Estatísticas gerais
            st.markdown("### Resumo Geral")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Registros", len(df_filtered))
            with col2:
                st.metric("Equipamentos", len(df_filtered['EQUIPAMENTO'].unique()))
            with col3:
                st.metric("Período (dias)", (df_filtered['DateTime'].max() - df_filtered['DateTime'].min()).days + 1)
            with col4:
                st.metric("Última Atualização", df_filtered['DateTime'].max().strftime("%d/%m/%Y %H:%M"))
        
        with tab5:
            st.markdown("## Histórico de Alterações")
            
            # Carregar log de alterações
            log_data = load_change_log()
            
            if log_data:
                # Converter para DataFrame
                df_log = pd.DataFrame(log_data)
                df_log['timestamp'] = pd.to_datetime(df_log['timestamp'])
                
                # Filtros para o histórico
                col1, col2 = st.columns(2)
                
                with col1:
                    filter_equipment_log = st.multiselect(
                        "Filtrar por Equipamento",
                        df_log['equipamento'].unique(),
                        default=df_log['equipamento'].unique(),
                        key="filter_eq_log"
                    )
                
                with col2:
                    filter_variable_log = st.multiselect(
                        "Filtrar por Variável",
                        df_log['variavel'].unique(),
                        default=df_log['variavel'].unique(),
                        key="filter_var_log"
                    )
                
                # Aplicar filtros
                df_log_filtered = df_log[
                    (df_log['equipamento'].isin(filter_equipment_log)) &
                    (df_log['variavel'].isin(filter_variable_log))
                ]
                
                # Ordenar por timestamp (mais recentes primeiro)
                df_log_filtered = df_log_filtered.sort_values('timestamp', ascending=False)
                
                # Formatar para exibição
                df_log_display = df_log_filtered.copy()
                df_log_display['timestamp'] = df_log_display['timestamp'].dt.strftime("%d/%m/%Y %H:%M:%S")
                df_log_display['valor_anterior'] = df_log_display['valor_anterior'].apply(
                    lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x is not None else "N/A"
                )
                df_log_display['novo_valor'] = df_log_display['novo_valor'].apply(
                    lambda x: f"{x:.2f}" if isinstance(x, (int, float)) and x is not None else "N/A"
                )
                
                df_log_display.columns = ['Timestamp', 'Equipamento', 'Variável', 'Valor Anterior', 'Novo Valor', 'Usuário']
                
                st.dataframe(df_log_display, use_container_width=True, height=500)
                
                st.markdown(f"**Total de alterações:** {len(df_log_filtered)}")
            else:
                st.info("📝 Nenhuma alteração registrada ainda.")

else:
    st.info("👈 Clique em 'Carregar Dados do Excel' no painel lateral para começar!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>WEG SCAN Dashboard v2.0 | Monitoramento de Equipamentos | Desenvolvido com Streamlit</p>
</div>
""", unsafe_allow_html=True)
