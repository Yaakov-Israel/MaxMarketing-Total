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
# ==============================================================================
# 5. CLASSE PRINCIPAL DA APLICAÇÃO
# ==============================================================================
class MaxMarketingApp:
    def __init__(self, llm_instance, db_firestore_instance):
        """Inicializa a aplicação com as conexões para a IA e o Banco de Dados."""
        self.llm = llm_instance
        self.db = db_firestore_instance

    # --- MÉTODO DE ONBOARDING E BRIEFING ESTRATÉGICO ---
    def exibir_briefing_estrategico(self):
        """
        Exibe um formulário para o usuário preencher o DNA de marketing da sua empresa.
        Essas informações serão o "prompt invertido" principal para todas as ferramentas.
        """
        st.header("🚀 Briefing Estratégico do MaxMarketing Total")
        st.markdown("Para que nossa IA crie campanhas e conteúdos que realmente vendem, precisamos entender a fundo o seu negócio. Suas respostas aqui servirão como base para todas as criações futuras.")
        
        # Vamos usar um dicionário no session_state para guardar os dados do form
        if 'briefing_data' not in st.session_state:
            st.session_state.briefing_data = {}

        with st.form(key="briefing_form"):
            st.subheader("1. Identidade da Empresa")
            st.session_state.briefing_data['company_name'] = st.text_input("Nome da Empresa:", placeholder="Ex: Sapataria do Zé")
            st.session_state.briefing_data['pitch'] = st.text_area("Descreva seu negócio em uma frase (seu pitch):", placeholder="Ex: Vendemos sapatos de couro artesanais para o público masculino em Juiz de Fora.")
            st.session_state.briefing_data['personalidade'] = st.radio("Qual adjetivo melhor descreve a personalidade da sua marca?",
                                                                        ('Divertida e Jovem', 'Séria e Corporativa', 'Acolhedora e Amigável', 'Sofisticada e Premium', 'Técnica e Especialista'))

            st.subheader("2. Produtos & Proposta de Valor")
            st.session_state.briefing_data['produtos'] = st.text_area("Liste seus 3 principais produtos ou serviços:")
            st.session_state.briefing_data['diferencial'] = st.text_input("Qual é o seu principal diferencial competitivo?", placeholder="Ex: Entrega mais rápida da cidade, único com garantia de 2 anos...")

            st.subheader("3. O Cliente Ideal (Público-Alvo)")
            st.session_state.briefing_data['cliente_ideal'] = st.text_area("Descreva seu cliente ideal:", placeholder="Homens de 30-50 anos, que valorizam qualidade e durabilidade...")
            st.session_state.briefing_data['dor_cliente'] = st.text_input("Qual a principal 'dor' ou necessidade do seu cliente que sua empresa resolve?")

            st.subheader("4. Objetivos de Marketing")
            st.session_state.briefing_data['objetivo_principal'] = st.radio("Qual é o seu OBJETIVO Nº 1 com marketing digital?",
                                                                            ('Aumentar seguidores e engajamento', 'Gerar mais leads (contatos)', 'Aumentar as vendas diretas', 'Fortalecer a marca'))

            submitted = st.form_submit_button("✅ Salvar Briefing e Começar a Criar!")
            if submitted:
                with st.spinner("Salvando o DNA de marketing da sua empresa..."):
                    try:
                        user_uid = st.session_state.get('user_uid')
                        if user_uid:
                            # Cria ou atualiza um documento com o ID da empresa do usuário
                            company_ref = self.db.collection(COMPANY_COLLECTION).document(user_uid)
                            company_ref.set(st.session_state.briefing_data, merge=True) # merge=True permite atualizar sem apagar dados antigos
                            
                            # Marca no perfil do usuário que o briefing foi concluído
                            user_ref = self.db.collection(USER_COLLECTION).document(user_uid)
                            user_ref.update({"briefing_completed": True})

                            st.success("Briefing salvo! Estamos prontos para decolar.")
                            time.sleep(2)
                            # Limpa os dados do formulário da memória da sessão
                            del st.session_state['briefing_data']
                            st.rerun()
                        else:
                            st.error("Erro: Usuário não autenticado. Não foi possível salvar o briefing.")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao salvar o briefing: {e}")

    # --- PLACEHOLDERS PARA AS FUNCIONALIDADES ---
    
    # ==============================================================================
    # 6. FUNCIONALIDADES DO APP
    # ==============================================================================

    def exibir_criador_de_posts(self):
        """
        Página para criar posts individuais para diversas plataformas.
        Implementa o conceito de "prompt invertido" para coletar detalhes do post.
        """
        st.header("✍️ Criador de Posts")
        st.markdown("Preencha o briefing abaixo para que o Max crie o post perfeito para você.")

        # Carrega os prompts do nosso arquivo de configuração JSON
        prompts = carregar_prompts_config()
        if not prompts:
            st.error("Não foi possível carregar as configurações de prompt.")
            return

        # Define as opções de canais/plataformas
        canais_disponiveis = [
            'Instagram', 'Facebook', 'Google Ads (Pesquisa)', 
            'YouTube (Shorts)', 'TikTok', 'LinkedIn', 'Marketplace (OLX, etc.)'
        ]

        # Inicia o formulário para evitar que a página recarregue a cada seleção
        with st.form(key="post_briefing_form"):
            st.subheader("1. Definições do Post")
            
            # Seleção de canal e tipo de post
            canal_selecionado = st.selectbox("Para qual canal é este post?", options=canais_disponiveis)
            
            tipo_post = ""
            if canal_selecionado in ['Instagram', 'Facebook']:
                tipo_post = st.radio("Qual o formato?", ['Post de Feed (Imagem/Carrossel)', 'Reels', 'Stories'], horizontal=True)
            
            st.subheader("2. Conteúdo e Objetivo (Prompt Invertido)")
            
            objetivo_post = st.text_input(
                "Qual o objetivo principal DESTE post?", 
                placeholder="Ex: Anunciar uma promoção, gerar cliques no site, aumentar engajamento..."
            )
            produto_servico_foco = st.text_input(
                "Qual produto ou serviço específico você quer promover?",
                help="Seja específico! Ex: 'Sapato de couro modelo Verona, cor marrom'."
            )
            mensagem_central = st.text_area(
                "Qual é a mensagem central que você quer comunicar?",
                placeholder="Ex: Nossa promoção de Dia dos Pais está com 50% de desconto em todos os sapatos."
            )
            cta_especifica = st.text_input(
                "Qual a Chamada para Ação (CTA)?",
                placeholder="Ex: 'Clique no link da bio', 'Comente EU QUERO', 'Visite nossa loja na Rua X'."
            )

            # Botão para enviar o formulário e gerar o conteúdo
            submitted = st.form_submit_button("✨ Gerar Post com Max IA")

        # --- Lógica de Geração e Exibição do Resultado ---
        if submitted:
            with st.spinner("Aguarde... Max está combinando sua estratégia com criatividade para gerar o post ideal! 🚀"):
                try:
                    # Passo 1: Buscar o briefing geral da empresa que salvamos no Firestore
                    # (Vamos criar essa função de busca depois, por enquanto é um placeholder)
                    # company_data = buscar_dados_empresa_do_firestore(self.db, st.session_state.get('user_uid'))
                    
                    # Passo 2: Montar o prompt final para a IA
                    # (Aqui combinamos o briefing da empresa com o briefing específico deste post)
                    # prompt_final = montar_prompt_para_post(
                    #     prompts, company_data, canal_selecionado, tipo_post, 
                    #     objetivo_post, produto_servico_foco, mensagem_central, cta_especifica
                    # )
                    
                    # Passo 3: Chamar a IA para gerar o conteúdo
                    # (Usamos o 'llm' que inicializamos na Parte 4)
                    # resultado_ia = self.llm.invoke(prompt_final)
                    
                    # --- SIMULAÇÃO DO RESULTADO (para fins de desenvolvimento visual) ---
                    st.session_state['post_gerado'] = """
**Título Impactante:** 👞 Seu Pai Merece o Melhor. E o Melhor Está com 50% OFF!

**Texto do Post:**
O presente perfeito para o Dia dos Pais está aqui na Sapataria do Zé! 🎁

Toda a nossa linha de sapatos de couro artesanais, incluindo o nosso campeão de vendas Verona, está com um desconto incrível de 50%. Qualidade, conforto e durabilidade que seu pai vai sentir a cada passo.

Não deixe para a última hora! A promoção é válida somente até sábado.

**Sugestão de Imagem/Vídeo:**
Um vídeo curto e elegante mostrando os detalhes do sapato de couro Verona, com foco na costura e no acabamento. O vídeo termina com o sapato sendo colocado em uma bela caixa de presente.

**Chamada para Ação (CTA):**
Visite nossa loja na Rua X e garanta o presente do seu paizão!

**Hashtags Estratégicas:**
#diadospais #presenteparaopai #sapatomasculino #sapatodecouro #juizdefora #promocao #modamasculina
                    """
                    # --- FIM DA SIMULAÇÃO ---

                except Exception as e:
                    st.error(f"Ocorreu um erro ao gerar o conteúdo: {e}")

        # Se um post foi gerado, exibe na tela
        if 'post_gerado' in st.session_state and st.session_state.post_gerado:
            st.divider()
            st.subheader("✅ Conteúdo Gerado pelo Max:")
            st.markdown(st.session_state.post_gerado)

            st.subheader("Refinamento e Ações")
            col1, col2 = st.columns(2)
            with col1:
                st.button("Salvar no Histórico", type="primary")
            with col2:
                st.download_button("Baixar como .txt", st.session_state.post_gerado, file_name="post_max_marketing.txt")
            
            refinamento = st.text_input("Gostou? Peça um ajuste para o Max:", placeholder="Ex: 'Deixe o texto mais curto', 'Use mais emojis', 'Crie outra opção de título'")
            if st.button("Refinar Texto"):
                # Aqui entraria a lógica para refinar o texto, enviando um novo prompt para a IA
                st.info("Função de refinamento em desenvolvimento.")

    def exibir_criador_de_campanhas(self):
        """Página para criar campanhas completas com múltiplos criativos."""
        st.header("📣 Criador de Campanhas")
        st.info("Funcionalidade em desenvolvimento. Crie campanhas integradas para atingir seus objetivos.")
        pass

    def exibir_construtor_de_ofertas(self): # <<< NOVO PLACEHOLDER ADICIONADO
        """Página para criar um catálogo de ofertas/produtos."""
        st.header("🛍️ Construtor de Ofertas")
        st.info("Funcionalidade em desenvolvimento. Crie seu catálogo de produtos e ofertas para compartilhar.")
        pass

    def exibir_estrategista_de_midia(self):
        """Página com ferramentas de GEO e otimização de anúncios."""
        st.header("📊 Estrategista de Mídia Digital")
        st.info("Funcionalidade em desenvolvimento. Otimize sua presença com GEO e planeje seus anúncios.")
        pass
