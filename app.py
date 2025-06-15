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
