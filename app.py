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
# ==============================================================================
# 3. FUNÇÕES AUXILIARES GLOBAIS
# ==============================================================================

# Adicionado o st.cache_data para otimizar o carregamento da imagem.
# O Streamlit guardará o resultado em cache e não precisará reler o arquivo do disco toda vez.
@st.cache_data
def convert_image_to_base64(image_name):
    """Lê um arquivo de imagem e o converte para uma string Base64."""
    try:
        image_path = get_asset_path(image_name)
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        else:
            # Mostra um aviso no app se a imagem não for encontrada.
            st.warning(f"Arquivo de imagem não encontrado: {image_path}")
            return None
    except Exception as e:
        # Mostra um erro no app se ocorrer outro problema.
        st.error(f"Erro ao converter a imagem '{image_name}': {e}")
        return None

st.success("Funções auxiliares carregadas com sucesso!")
# ==============================================================================
# 4. INICIALIZAÇÃO DE SERVIÇOS E AUTENTICAÇÃO
# ==============================================================================

@st.cache_resource
def initialize_firebase_services():
    """
    Inicializa e retorna os clientes do Firebase para autenticação e banco de dados.
    Usa @st.cache_resource para garantir que a conexão seja estabelecida apenas uma vez.
    """
    try:
        # Carrega as credenciais do arquivo secrets.toml
        firebase_config = dict(st.secrets["firebase_config"])
        service_account_creds = dict(st.secrets["gcp_service_account"])

        # Inicializa o Pyrebase para autenticação do lado do cliente (login, registro)
        firebase_client = pyrebase.initialize_app(firebase_config)
        pb_auth_client = firebase_client.auth()

        # Inicializa o Firebase Admin SDK para operações de backend (acesso ao Firestore)
        # A verificação "if not firebase_admin._apps" impede a reinicialização do app.
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_creds)
            firebase_admin.initialize_app(cred)
        
        firestore_db_client = firebase_admin_firestore.client()
        
        return pb_auth_client, firestore_db_client

    except Exception as e:
        st.error(f"Erro crítico na inicialização do Firebase: {e}")
        st.info("Verifique se as seções [firebase_config] e [gcp_service_account] estão corretas no seu arquivo secrets.toml.")
        st.stop()
        return None, None

# Inicializa os serviços e os armazena em variáveis globais
pb_auth_client, firestore_db = initialize_firebase_services()

@st.cache_resource
def get_llm():
    """Inicializa e retorna o cliente do modelo de linguagem (Gemini)."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # Configura o LLM com a chave e uma temperatura para respostas criativas
        return ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=api_key, temperature=0.75)
    except Exception as e:
        st.error(f"Erro crítico ao inicializar a IA do Google: {e}")
        st.info("Verifique se a GOOGLE_API_KEY está correta no seu arquivo secrets.toml.")
        st.stop()
        return None

# Inicializa o LLM
llm = get_llm()

def get_current_user_status():
    """
    Verifica se existe uma sessão de usuário válida e atualiza o estado do aplicativo.
    Retorna o status de autenticação e as informações básicas do usuário.
    """
    # Define uma chave única para os dados da sessão do usuário
    session_key = f'{APP_KEY_SUFFIX}_user_session_data'
    
    # Verifica se os dados da sessão existem
    if 'user_session' in st.session_state and st.session_state.user_session:
        try:
            # Tenta usar o token da sessão para obter informações da conta.
            # Isso valida se o token ainda é válido.
            user_info = pb_auth_client.get_account_info(st.session_state.user_session['idToken'])
            
            # Se for bem-sucedido, extrai os dados do usuário
            uid = user_info['users'][0]['localId']
            email = user_info['users'][0].get('email')
            
            # Atualiza o estado da sessão com os dados confirmados
            st.session_state.update({
                'user_is_authenticated': True,
                'user_uid': uid,
                'user_email': email
            })
            return True, uid, email
            
        except Exception:
            # Se o token for inválido/expirado, limpa a sessão e desloga o usuário.
            st.session_state.clear()
            return False, None, None
            
    return False, None, None

st.success("Serviços de autenticação e IA carregados com sucesso!")
