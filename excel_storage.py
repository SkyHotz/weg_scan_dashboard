"""
Módulo para persistência de dados em arquivo Excel
Salva dados diretamente no arquivo DADOSWEGSCAN.xlsx
"""

import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
import os

EXCEL_FILE = 'DADOSWEGSCAN.xlsx'

def load_data_from_excel():
    """Carrega dados do arquivo Excel DADOSWEGSCAN.xlsx"""
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Arquivo {EXCEL_FILE} nao encontrado!")
        return None
    
    try:
        # Ler com header na linha 1 (0-indexed)
        df = pd.read_excel(EXCEL_FILE, sheet_name='Planilha1', header=1)
        
        # Remover coluna sem nome (indice)
        df = df.drop(columns=['Unnamed: 0'], errors='ignore')
        
        # Remover linhas vazias
        df = df.dropna(how='all')
        
        # Converter coluna DATA para datetime primeiro
        if 'DATA' in df.columns:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        
        # Remover linhas com DATA invalida
        df = df.dropna(subset=['DATA'])
        
        # Converter DATA para date
        if 'DATA' in df.columns:
            df['DATA'] = df['DATA'].dt.date
        
        if 'HORÁRIO' in df.columns:
            df['HORÁRIO'] = df['HORÁRIO'].astype(str)
        
        # Adicionar coluna CORRENTE ELETRICA se nao existir
        if 'CORRENTE ELETRICA (A)' not in df.columns:
            df['CORRENTE ELETRICA (A)'] = 0.0
        
        # Criar coluna DateTime combinando DATA e HORÁRIO
        if 'DATA' in df.columns and 'HORÁRIO' in df.columns:
            df['DateTime'] = pd.to_datetime(
                df['DATA'].astype(str) + ' ' + df['HORÁRIO'].astype(str),
                errors='coerce'
            )
            # Remover linhas com DateTime invalido
            df = df.dropna(subset=['DateTime'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return None

def save_data_to_excel(df):
    """Salva dados no arquivo Excel DADOSWEGSCAN.xlsx"""
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Arquivo {EXCEL_FILE} nao encontrado!")
        return False
    
    try:
        # Converter colunas de data para string para salvar no Excel
        df_save = df.copy()
        
        # Remover coluna DateTime (nao precisa salvar, sera recriada ao carregar)
        df_save = df_save.drop(columns=['DateTime'], errors='ignore')
        
        if 'DATA' in df_save.columns:
            df_save['DATA'] = pd.to_datetime(df_save['DATA']).dt.strftime('%Y-%m-%d')
        
        # Salvar na planilha 'Planilha1'
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
            df_save.to_excel(writer, sheet_name='Planilha1', index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar Excel: {e}")
        return False

def add_record_to_excel(data, horario, equipamento, vibracao_axial, 
                        vibracao_radial_y, vibracao_radial_x, temperatura, corrente_eletrica):
    """Adiciona um novo registro ao arquivo Excel"""
    try:
        # Carregar dados existentes
        df = load_data_from_excel()
        
        if df is None:
            st.error("Erro ao carregar dados do Excel")
            return False
        
        # Remover coluna DateTime (sera recriada)
        df = df.drop(columns=['DateTime'], errors='ignore')
        
        # Criar novo registro
        new_record = {
            'DATA': data,
            'HORÁRIO': horario,
            'EQUIPAMENTO': equipamento,
            'VIBRACAO AXIAL(mm/s)': vibracao_axial,
            'VIBRACAO RADIAL-Y (mm/s)': vibracao_radial_y,
            'VIBRACAO RADIAL-X (mm/s)': vibracao_radial_x,
            'TEMPERATURA(C)': temperatura,
            'CORRENTE ELETRICA (A)': corrente_eletrica
        }
        
        # Adicionar novo registro
        new_df = pd.DataFrame([new_record])
        df = pd.concat([df, new_df], ignore_index=True)
        
        # Salvar no Excel
        success = save_data_to_excel(df)
        
        if success:
            st.success("Registro salvo no Excel com sucesso!")
        
        return success
    except Exception as e:
        st.error(f"Erro ao adicionar registro: {e}")
        return False

def get_excel_file_path():
    """Retorna o caminho do arquivo Excel"""
    return os.path.abspath(EXCEL_FILE)

def export_excel():
    """Retorna o arquivo Excel para download"""
    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, 'rb') as f:
            return f.read()
    return None
