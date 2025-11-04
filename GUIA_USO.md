# 📊 Guia de Uso - WEG SCAN Dashboard

## Visão Geral

O **WEG SCAN Dashboard** é um sistema interativo de monitoramento e análise de dados de equipamentos desenvolvido em Python com Streamlit. Ele permite visualizar tendências de vibração e temperatura, gerenciar dados manualmente e exportar relatórios.

---

## 🚀 Iniciar o Dashboard

### Requisitos

- Python 3.7 ou superior

- Dependências: `streamlit`, `pandas`, `plotly`, `openpyxl`, `kaleido`

### Instalação de Dependências

```bash
pip install streamlit pandas plotly openpyxl kaleido
```

### Executar a Aplicação

```bash
cd /home/ubuntu/weg_scan_dashboard
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

---

## 📖 Funcionalidades Principais

### 1. **Carregar Dados do Excel**

- Clique no botão **"🔄 Carregar Dados do Excel"** no painel lateral

- O sistema carregará automaticamente os dados da planilha principal do arquivo `DADOSWEGSCAN.xlsx`

- Os dados são armazenados em memória e também salvos em JSON para persistência entre sessões

### 2. **Filtros Dinâmicos**

O painel lateral oferece três tipos de filtros:

#### **Equipamentos**

- Selecione um ou mais equipamentos para visualizar:
  - B OLEO 2302
  - FB 0011
  - FB 0012
  - GARO 09
  - GARO 10

#### **Período**

- **De**: Data inicial do período a analisar

- **Até**: Data final do período a analisar

- Os gráficos e estatísticas atualizam automaticamente

#### **Variáveis**

- Selecione quais medições deseja visualizar:
  - Vibração Axial (mm/s)
  - Vibração Radial-Y (mm/s)
  - Vibração Radial-X (mm/s)
  - Temperatura (°C)

### 3. **Visualizações - Abas Principais**

#### **📈 Gráficos**

Exibe gráficos de linha interativos com:

- **Linha de Dados**: Valores medidos em azul

- **Linha de Tendência**: Média móvel em laranja (tracejada)

- **Limites de Alerta**: Linhas vermelha (máximo) e verde (mínimo)

**Interações:**

- Passe o mouse para ver valores exatos

- Clique no ícone de câmera para baixar o gráfico como PNG

- Use os botões de zoom e pan para explorar os dados

#### **📊 Estatísticas**

Mostra métricas resumidas por equipamento:

- **Última Leitura**: Valor mais recente

- **Média**: Valor médio do período

- **Máximo**: Valor máximo registrado

- **Mínimo**: Valor mínimo registrado

- **Desvio Padrão**: Variabilidade dos dados

Clique em **"Ver detalhes"** para expandir e visualizar todas as métricas.

#### **⚠️ Alertas**

Lista valores que ultrapassaram os limites definidos:

- **Vermelho**: Valores acima do limite máximo

- **Amarelo**: Valores abaixo do limite mínimo

Limites padrão:

| Variável | Mín | Máx |
| --- | --- | --- |
| Vibração Axial | 0 | 5 mm/s |
| Vibração Radial-Y | 0 | 5 mm/s |
| Vibração Radial-X | 0 | 7 mm/s |
| Temperatura | 0 | 70 °C |

#### **📋 Dados**

Exibe tabela completa com:

- Todos os registros filtrados

- Opção de download como CSV

- Resumo geral com indicadores-chave

### 4. **Adicionar Novo Registro**

No painel lateral, preencha o formulário:

1. **📅 Data**: Selecione a data da medição

1. **🕐 Hora**: Selecione a hora da medição

1. **⚙️ Equipamento**: Escolha o equipamento

1. **Medições**: Insira os valores:
  - Vibração Axial (mm/s)
  - Vibração Radial-Y (mm/s)
  - Vibração Radial-X (mm/s)
  - Temperatura (°C)

Clique em **"✅ Adicionar Registro"** para salvar. O novo registro será:

- Adicionado ao dataset

- Ordenado cronologicamente

- Salvo em JSON para persistência

- Refletido imediatamente nos gráficos

### 5. **Exportar Dados**

#### **📊 Excel**

- Clique no botão **"📊 Excel"**

- Baixe arquivo com duas planilhas:
  - **Dados**: Todos os registros com colunas formatadas
  - **Resumo**: Estatísticas agregadas por equipamento

#### **📋 CSV**

- Clique no botão **"📋 CSV"**

- Baixe arquivo de texto com valores separados por vírgula

- Compatível com Excel, Python, R e outras ferramentas

---

## 🎯 Casos de Uso Comuns

### Monitorar Tendência de um Equipamento

1. Selecione apenas o equipamento desejado nos filtros

1. Acesse a aba **"📈 Gráficos"**

1. Observe a evolução das medições ao longo do tempo

### Comparar Equipamentos

1. Selecione múltiplos equipamentos

1. Escolha uma variável específica

1. Compare os gráficos lado a lado

### Investigar Anomalias

1. Acesse a aba **"⚠️ Alertas"**

1. Identifique valores fora dos limites

1. Use os filtros de período para investigar o contexto

### Gerar Relatório

1. Filtre os dados desejados (período, equipamentos, variáveis)

1. Acesse a aba **"📋 Dados"** para visualizar a tabela

1. Exporte em Excel ou CSV

1. Use em ferramentas de apresentação ou análise

---

## 💾 Persistência de Dados

O dashboard salva automaticamente novos registros em:

- **Arquivo JSON**: `dados_dashboard.json` (para rápido carregamento)

- **Arquivo Excel**: `dados_exportados.xlsx` (para compartilhamento)

Ao reiniciar a aplicação, os dados salvos em JSON são carregados automaticamente.

---

## ⚙️ Personalização

### Modificar Limites de Alerta

Edite a seção `ALERT_LIMITS` no arquivo `app.py`:

```python
ALERT_LIMITS = {
    'VIBRAÇÃO AXIAL(mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-Y (mm/s)': {'min': 0, 'max': 5},
    'VIBRAÇÃO RADIAL-X (mm/s)': {'min': 0, 'max': 7},
    'TEMPERATURA(°C)': {'min': 0, 'max': 70}
}
```

### Adicionar Novo Equipamento

1. Insira um registro com o novo equipamento

1. O equipamento aparecerá automaticamente nos filtros

### Alterar Cores e Estilos

Modifique as seções de estilo CSS no início do arquivo `app.py`:

```python
st.markdown("""
    <style>
    .metric-card { ... }
    .alert-danger { ... }
    .alert-warning { ... }
    </style>
""", unsafe_allow_html=True)
```

---

## 🐛 Solução de Problemas

### Dados não aparecem após carregar

- Verifique se o arquivo `DADOSWEGSCAN.xlsx` está no diretório do projeto

- Clique novamente em **"🔄 Carregar Dados do Excel"**

### Gráficos vazios

- Verifique se há dados para o período e equipamento selecionados

- Ajuste os filtros de período

### Erro ao exportar como PNG

- Instale a biblioteca `kaleido`: `pip install kaleido`

- Use a exportação em CSV ou Excel como alternativa

### Aplicação lenta

- Reduza o período de análise

- Selecione apenas os equipamentos necessários

- Reinicie a aplicação

---

## 📞 Suporte

Para reportar problemas ou sugerir melhorias, consulte a documentação do Streamlit:

- [https://docs.streamlit.io/](https://docs.streamlit.io/)

---

## 📄 Estrutura de Arquivos

```
weg_scan_dashboard/
├── app.py                    # Aplicação principal
├── DADOSWEGSCAN.xlsx         # Arquivo de dados original
├── dados_dashboard.json      # Dados persistidos (gerado automaticamente)
├── dados_exportados.xlsx     # Último export em Excel (gerado automaticamente)
├── GUIA_USO.md              # Este arquivo
└── streamlit.log            # Log da aplicação
```

---

**Versão**: 1.0**Última Atualização**: Novembro 2025**Desenvolvido com**: Streamlit, Pandas, Plotly

