"""
Módulo de alertas por e-mail
Envia notificações quando medições ultrapassam limites de segurança
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os

# Limites de alerta para cada variável
ALERT_LIMITS = {
    'VIBRAÇÃO AXIAL(mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-Y (mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-X (mm/s)': {'min': 0, 'max': 7},
    'TEMPERATURA(°C)': {'min': 0, 'max': 70},
    'CORRENTE ELÉTRICA (A)': {'min': 0, 'max': 100}
}

def get_email_config():
    """Obtém configuração de e-mail dos secrets"""
    return {
        'sender_email': st.secrets.get("EMAIL_SENDER", None),
        'sender_password': st.secrets.get("EMAIL_PASSWORD", None),
        'recipient_emails': st.secrets.get("EMAIL_RECIPIENTS", "").split(','),
        'smtp_server': st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
        'smtp_port': int(st.secrets.get("SMTP_PORT", "587"))
    }

def is_alert_triggered(variavel, valor):
    """Verifica se o valor ultrapassa os limites de alerta"""
    if variavel not in ALERT_LIMITS or valor is None:
        return False, None
    
    limits = ALERT_LIMITS[variavel]
    
    if valor > limits['max']:
        return True, f"acima do limite máximo ({limits['max']})"
    elif valor < limits['min']:
        return True, f"abaixo do limite mínimo ({limits['min']})"
    
    return False, None

def send_alert_email(equipamento, variavel, valor, motivo, data, horario):
    """Envia e-mail de alerta"""
    config = get_email_config()
    
    # Validar configuração
    if not config['sender_email'] or not config['sender_password']:
        st.warning("⚠️ E-mail não configurado. Configure EMAIL_SENDER e EMAIL_PASSWORD nos secrets.")
        return False
    
    if not config['recipient_emails'] or config['recipient_emails'][0] == '':
        st.warning("⚠️ Destinatários não configurados. Configure EMAIL_RECIPIENTS nos secrets.")
        return False
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(config['recipient_emails'])
        msg['Subject'] = f"🚨 ALERTA WEG SCAN - {equipamento} - {variavel}"
        
        # Corpo do e-mail em HTML
        limits = ALERT_LIMITS.get(variavel, {})
        
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f5f5f5; }}
                    .alert-box {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; }}
                    .info-box {{ background-color: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin: 10px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                    .label {{ font-weight: bold; width: 30%; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 ALERTA DE SEGURANÇA</h1>
                        <p>Medição fora dos limites de segurança detectada</p>
                    </div>
                    
                    <div class="content">
                        <div class="alert-box">
                            <h2>{variavel}</h2>
                            <p><strong>Valor:</strong> {valor:.2f}</p>
                            <p><strong>Status:</strong> {motivo}</p>
                        </div>
                        
                        <div class="info-box">
                            <table>
                                <tr>
                                    <td class="label">Equipamento:</td>
                                    <td>{equipamento}</td>
                                </tr>
                                <tr>
                                    <td class="label">Data:</td>
                                    <td>{data}</td>
                                </tr>
                                <tr>
                                    <td class="label">Horário:</td>
                                    <td>{horario}</td>
                                </tr>
                                <tr>
                                    <td class="label">Limite Máximo:</td>
                                    <td>{limits.get('max', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td class="label">Limite Mínimo:</td>
                                    <td>{limits.get('min', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td class="label">Timestamp:</td>
                                    <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <p style="margin-top: 20px; color: #d32f2f;">
                            <strong>⚠️ Ação Recomendada:</strong> Verifique o equipamento imediatamente.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>Este é um e-mail automático do WEG SCAN Dashboard</p>
                        <p>Não responda este e-mail</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Enviar e-mail
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        # Registrar envio
        log_alert_sent(equipamento, variavel, valor, motivo)
        
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

def log_alert_sent(equipamento, variavel, valor, motivo):
    """Registra alertas enviados em arquivo JSON"""
    log_file = 'alertas_enviados.json'
    
    try:
        # Carregar log existente
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
        else:
            alerts = []
        
        # Adicionar novo alerta
        alerts.append({
            'timestamp': datetime.now().isoformat(),
            'equipamento': equipamento,
            'variavel': variavel,
            'valor': float(valor),
            'motivo': motivo
        })
        
        # Manter apenas últimos 1000 alertas
        alerts = alerts[-1000:]
        
        # Salvar
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass

def get_recent_alerts(limit=10):
    """Retorna alertas recentes"""
    log_file = 'alertas_enviados.json'
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            return alerts[-limit:]
    except Exception as e:
        pass
    
    return []

def check_and_send_alerts(equipamento, data, horario, vibracao_axial, 
                          vibracao_radial_y, vibracao_radial_x, temperatura, corrente_eletrica):
    """Verifica todas as medições e envia alertas se necessário"""
    
    medições = {
        'VIBRAÇÃO AXIAL(mm/s)': vibracao_axial,
        'VIBRAÇÃO RADIAL-Y (mm/s)': vibracao_radial_y,
        'VIBRAÇÃO RADIAL-X (mm/s)': vibracao_radial_x,
        'TEMPERATURA(°C)': temperatura,
        'CORRENTE ELÉTRICA (A)': corrente_eletrica
    }
    
    alertas_enviados = []
    
    for variavel, valor in medições.items():
        if valor is not None and valor != '':
            try:
                valor_float = float(valor)
                triggered, motivo = is_alert_triggered(variavel, valor_float)
                
                if triggered:
                    success = send_alert_email(equipamento, variavel, valor_float, motivo, data, horario)
                    if success:
                        alertas_enviados.append(f"{variavel}: {valor_float} ({motivo})")
            except (ValueError, TypeError):
                pass
    
    return alertas_enviados
