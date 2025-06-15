# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO INICIAL DA PÁGINA
# ==============================================================================
import streamlit as st
import os
import io
import pyrebase
import base64
import time
import datetime
import firebase_admin
import pandas as pd
from PIL import Image
from docx import Document
from fpdf import FPDF
from langchain_google_genai import ChatGoogleGenerativeAI
from firebase_admin import credentials, firestore as firebase_admin_firestore
import plotly.graph_objects as go

# --- INÍCIO DA CONFIGURAÇÃO DE CAMINHOS E DIRETÓRIOS ---
# Padroniza o diretório de assets para robustez na implantação.
ASSETS_DIR = "assets"

def get_asset_path(asset_name):
    """Constrói o caminho para um asset dentro da pasta 'assets' de forma segura."""
    # Tenta usar o caminho absoluto do script.
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Fallback para ambientes onde __file__ não está definido (como alguns notebooks interativos)
        base_path = os.getcwd()
    return os.path.join(base_path, ASSETS_DIR, asset_name)

# --- CONFIGURAÇÃO DA PÁGINA (STREAMLIT) ---
# Tenta carregar o ícone da página, com fallback para um emoji
try:
    page_icon_path = get_asset_path("carinha-agente-max-ia.png")
    page_icon_obj = Image.open(page_icon_path) if os.path.exists(page_icon_path) else "🚀"
except Exception:
    page_icon_obj = "🚀" # Emoji de foguete, mais alinhado com marketing e growth

# Define as configurações da página com a marca do novo produto
st.set_page_config(
    page_title="MaxMarketing Total",
    page_icon=page_icon_obj,
    layout="wide",
    initial_sidebar_state="collapsed"
)
# --- FIM DA CONFIGURAÇÃO INICIAL ---
