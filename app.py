# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO INICIAL DA PÁGINA
# ==============================================================================
import streamlit as st
import os
from PIL import Image

# Demais importações que usaremos futuramente
# import io
# import pyrebase
# import base64
# import time
# import datetime
# import firebase_admin
# import pandas as pd
# from docx import Document
# from fpdf import FPDF
# from langchain_google_genai import ChatGoogleGenerativeAI
# from firebase_admin import credentials, firestore as firebase_admin_firestore
# import plotly.graph_objects as go

# Importa as funções que centralizamos no nosso arquivo de utilidades
from utils import get_asset_path, carregar_prompts_config

# --- CONFIGURAÇÃO DA PÁGINA (STREAMLIT) ---
try:
    # Usa a função importada de utils.py para encontrar o caminho do ícone
    page_icon_path = get_asset_path("carinha_max_marketing_total.png") # Lembre-se de usar o nome do seu novo logo
    page_icon_obj = Image.open(page_icon_path) if os.path.exists(page_icon_path) else "🚀"
except Exception as e:
    st.error(f"Erro ao carregar o ícone da página: {e}")
    page_icon_obj = "🚀"

# Define as configurações da página com a marca do novo produto
st.set_page_config(
    page_title="MaxMarketing Total",
    page_icon=page_icon_obj,
    layout="wide",
    initial_sidebar_state="collapsed"
)
# --- FIM DA CONFIGURAÇÃO INICIAL ---

st.success("Configuração inicial do App carregada com sucesso!")

# ==============================================================================
# 2. CONSTANTES E CARREGAMENTO DE SECRETS
# ==============================================================================

# --- Constantes do Projeto ---
# Sugestão: Usar um prefixo que identifique o app atual.
APP_NAME = "MaxMarketing Total"
APP_KEY_SUFFIX = "mmt_app_v1.0" # MMT = MaxMarketing Total
USER_COLLECTION = "users" # Nome da coleção para os usuários no Firestore
COMPANY_COLLECTION = "companies" # Nome da coleção para os dados das empresas dos usuários
SALES_PAGE_URL = "https://sua-pagina-de-vendas.com.br" # IMPORTANTE: Substituir pela URL real de vendas

# --- Configuração de Ambiente ---
# Evita avisos de paralelismo de algumas bibliotecas de IA.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --- Carregamento de Chaves e Configurações (Secrets) ---
# O Streamlit carrega o arquivo secrets.toml automaticamente para este objeto.
# Adicionamos verificações para garantir que as chaves essenciais estão presentes.

try:
    # Carrega a chave da API do Google AI (Gemini)
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

    # Carrega o objeto de configuração do Firebase
    FIREBASE_CONFIG = st.secrets["firebase_config"]
    
    # Carrega o objeto da conta de serviço do Google Cloud
    GCP_SERVICE_ACCOUNT = st.secrets["gcp_service_account"]

except KeyError as e:
    st.error(f"Erro Crítico: A chave '{e}' não foi encontrada no arquivo secrets.toml.")
    st.info("Por favor, verifique se o arquivo .streamlit/secrets.toml está completo e correto.")
    st.stop() # Interrompe a execução do app se uma chave essencial estiver faltando

st.success("Constantes e secrets carregados com sucesso!")
