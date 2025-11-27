"""
Módulo simples de persistência com GitHub
Salva dados em arquivo CSV no repositório GitHub
"""

import streamlit as st
import pandas as pd
import os
import subprocess
from datetime import datetime

def get_github_token():
    """Obtém token do GitHub dos secrets"""
    return st.secrets.get("GITHUB_TOKEN", None)

def load_data_from_github_csv():
    """Carrega dados do arquivo CSV no repositório local"""
    csv_file = 'dados_medicoes.csv'
    
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            
            # Converter colunas de data/hora
            if 'DATA' in df.columns:
                df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce').dt.date
            if 'HORÁRIO' in df.columns:
                df['HORÁRIO'] = df['HORÁRIO'].astype(str)
            
            return df
        except Exception as e:
            st.warning(f"Erro ao carregar CSV: {e}")
    
    return None

def save_data_to_github_csv(df):
    """Salva dados em arquivo CSV e faz commit no GitHub"""
    try:
        csv_file = 'dados_medicoes.csv'
        
        # Salvar em CSV local
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Tentar fazer commit e push no GitHub (se configurado)
        token = get_github_token()
        if token:
            try:
                # Configurar git
                os.system(f'git config --global user.email "dashboard@weg.local"')
                os.system(f'git config --global user.name "WEG Dashboard"')
                
                # Adicionar arquivo
                os.system(f'git add {csv_file}')
                
                # Commit
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                os.system(f'git commit -m "Atualização de dados - {timestamp}" 2>/dev/null')
                
                # Push (com token no URL)
                # Nota: Isso requer que o repositório esteja clonado com HTTPS
                os.system(f'git push 2>/dev/null')
            except Exception as e:
                # Se falhar o push, não é problema - dados estão salvos localmente
                pass
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

def add_record_to_csv(data, horario, equipamento, vibracao_axial, 
                      vibracao_radial_y, vibracao_radial_x, temperatura, corrente_eletrica):
    """Adiciona um novo registro ao CSV"""
    try:
        csv_file = 'dados_medicoes.csv'
        
        # Criar novo registro
        new_record = {
            'DATA': data,
            'HORÁRIO': horario,
            'EQUIPAMENTO': equipamento,
            'VIBRAÇÃO AXIAL(mm/s)': vibracao_axial,
            'VIBRAÇÃO RADIAL-Y (mm/s)': vibracao_radial_y,
            'VIBRAÇÃO RADIAL-X (mm/s)': vibracao_radial_x,
            'TEMPERATURA(°C)': temperatura,
            'CORRENTE ELÉTRICA (A)': corrente_eletrica
        }
        
        # Carregar dados existentes
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
        else:
            df = pd.DataFrame(columns=new_record.keys())
        
        # Adicionar novo registro
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        
        # Salvar
        save_data_to_github_csv(df)
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar registro: {e}")
        return False

def load_change_log_from_csv():
    """Carrega log de alterações do arquivo CSV"""
    log_file = 'alteracoes_log.csv'
    
    if os.path.exists(log_file):
        try:
            df = pd.read_csv(log_file)
            return df.to_dict('records')
        except Exception as e:
            st.warning(f"Erro ao carregar log: {e}")
    
    return []

def add_change_log_entry(equipamento, variavel, valor_anterior, novo_valor, usuario="Operador Local"):
    """Adiciona entrada ao log de alterações"""
    try:
        log_file = 'alteracoes_log.csv'
        
        # Criar nova entrada
        new_entry = {
            'timestamp': datetime.now().isoformat(),
            'equipamento': equipamento,
            'variavel': variavel,
            'valor_anterior': str(valor_anterior),
            'novo_valor': str(novo_valor),
            'usuario': usuario
        }
        
        # Carregar log existente
        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
        else:
            df = pd.DataFrame(columns=new_entry.keys())
        
        # Adicionar nova entrada
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        
        # Salvar
        df.to_csv(log_file, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        st.error(f"Erro ao registrar alteração: {e}")
        return False
