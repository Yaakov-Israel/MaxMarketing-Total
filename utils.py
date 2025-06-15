import streamlit as st
import json
import os

# --- INÍCIO DA CONFIGURAÇÃO DE CAMINHOS ---
# Pega o diretório onde o projeto está sendo executado.
# Isso garante que os caminhos funcionarão em qualquer computador ou servidor.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define os caminhos para as pastas de primeiro nível que realmente existem no projeto.
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")
# --- FIM DA CONFIGURAÇÃO DE CAMINHOS ---


# --- INÍCIO DAS FUNÇÕES UTILITÁRIAS ---

@st.cache_data
def carregar_prompts_config():
    """Carrega o arquivo de configuração de prompts (prompts.json) de forma segura."""
    caminho_arquivo = os.path.join(PROMPTS_DIR, "prompts.json")
    if not os.path.exists(caminho_arquivo):
        st.error(f"FATAL: Arquivo de prompts não encontrado em '{caminho_arquivo}'. Verifique a estrutura de pastas.")
        return None
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"FATAL: Erro ao carregar ou decodificar '{caminho_arquivo}'. Erro: {e}")
        return None

def get_asset_path(file_name):
    """
    Função ÚNICA e universal para construir o caminho para qualquer arquivo
    dentro da pasta '/assets/'.
    """
    return os.path.join(ASSETS_DIR, file_name)
