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
        """
        Página para criar campanhas de marketing completas, com múltiplos criativos
        para diversas plataformas, baseadas em um único objetivo estratégico.
        """
        st.header("📣 Criador de Campanhas Completas")
        st.markdown("Defina a estratégia da sua campanha e deixe o Max criar todas as peças de comunicação para você de forma integrada.")

        # Define as opções de canais para a campanha
        canais_disponiveis = [
            'Instagram', 'Facebook', 'E-mail Marketing', 'Google Ads (Pesquisa)', 'WhatsApp'
        ]

        with st.form(key="campaign_briefing_form"):
            st.subheader("1. Estratégia da Campanha")
            
            nome_campanha = st.text_input(
                "Qual o nome ou tema da sua campanha?", 
                placeholder="Ex: Lançamento Coleção de Inverno, Promoção de Aniversário da Loja"
            )
            
            objetivo_campanha = st.selectbox(
                "Qual o objetivo principal DESTA CAMPANHA?",
                options=[
                    'Gerar vendas de um produto/serviço específico',
                    'Aumentar o reconhecimento da marca (branding)',
                    'Capturar leads (e-mails, contatos de WhatsApp)',
                    'Promover um evento ou uma data especial'
                ]
            )
            
            oferta_central = st.text_area(
                "Qual é a oferta principal ou mensagem-chave da campanha?",
                placeholder="Ex: 'Toda a linha de inverno com 20% de desconto e frete grátis', 'Inscreva-se na nossa masterclass gratuita sobre marketing digital'."
            )
            
            st.subheader("2. Canais e Criativos")
            
            canais_selecionados = st.multiselect(
                "Em quais canais esta campanha será veiculada?",
                options=canais_disponiveis,
                help="O Max irá gerar um pacote de conteúdo apropriado para cada canal selecionado."
            )

            # Botão para enviar o formulário
            submitted = st.form_submit_button("🚀 Gerar Pacote da Campanha")

        # --- Lógica de Geração e Exibição do Resultado ---
        if submitted:
            if not nome_campanha or not oferta_central or not canais_selecionados:
                st.warning("Por favor, preencha o nome, a oferta e selecione pelo menos um canal para a campanha.")
            else:
                with st.spinner(f"Orquestrando a campanha '{nome_campanha}'... O Max está preparando um pacote completo de criativos! 🧠✨"):
                    # Aqui entraria a lógica complexa para montar o prompt,
                    # chamar a IA e salvar o resultado.
                    # Por enquanto, vamos simular o resultado para fins visuais.
                    
                    # --- SIMULAÇÃO DO RESULTADO ---
                    st.session_state['campanha_gerada'] = {
                        "nome": nome_campanha,
                        "objetivo": objetivo_campanha,
                        "oferta": oferta_central,
                        "pacote_criativos": """
### 📣 Pacote para Instagram
**Post para Feed (Sugestão 1):**
- **Texto:** Prepare-se para o inverno com estilo! ❄️ Nossa nova coleção acaba de chegar com 20% de DESCONTO e frete grátis. Jaquetas, botas e tudo que você precisa para ficar aquecido e elegante. Toque no link da bio para conferir!
- **Imagem:** Um carrossel de fotos com modelos vestindo as peças da nova coleção em um cenário de inverno.

**Ideia para Stories (Sequência de 3):**
1.  **Story 1 (Enquete):** Foto de duas peças da coleção. "Qual combina mais com você? 🤔"
2.  **Story 2 (Vídeo):** Vídeo curto mostrando os detalhes de uma jaqueta. Texto sobreposto: "Qualidade nos mínimos detalhes."
3.  **Story 3 (CTA):** Print da página da promoção no site. Sticker de "Clique Aqui" com o link direto.

---
### 📣 Pacote para E-mail Marketing
**Assunto:** ❄️ Chegou o Inverno! E sua nova coleção favorita também (com 20% OFF).
**Corpo do E-mail:**
Olá [Nome do Cliente],

O frio chegou e com ele a oportunidade de renovar seu guarda-roupa com peças incríveis.

Nossa Nova Coleção de Inverno foi pensada para quem não abre mão de estilo e conforto. E para celebrar, estamos oferecendo **20% de desconto em todas as peças + frete grátis** por tempo limitado.

[Botão: Ver a Coleção Agora]

Não perca essa chance de se aquecer com elegância.

Abraços,
Equipe MaxMarketing Total
"""
                    }
                    # --- FIM DA SIMULAÇÃO ---

        # Se uma campanha foi gerada, exibe na tela
        if 'campanha_gerada' in st.session_state:
            st.divider()
            st.subheader(f"✅ Pacote de Criativos para a Campanha: '{st.session_state['campanha_gerada']['nome']}'")
            
            # Usamos um expander para não poluir a tela, o usuário abre se quiser ver os detalhes
            with st.expander("Ver pacote de criativos gerados", expanded=True):
                st.markdown(st.session_state['campanha_gerada']['pacote_criativos'])

            col1, col2 = st.columns(2)
            with col1:
                st.button("Salvar Campanha no Histórico", type="primary")
            with col2:
                st.download_button(
                    "Baixar como .txt", 
                    st.session_state['campanha_gerada']['pacote_criativos'], 
                    file_name=f"campanha_{st.session_state['campanha_gerada']['nome']}.txt"
                )

    def exibir_construtor_de_ofertas(self):
        st.header("🛍️ Construtor de Ofertas")
        st.markdown("Crie um catálogo visual com suas principais ofertas e produtos. Salve seu progresso e depois baixe como um PDF profissional ou compartilhe nas redes.")
        st.markdown("---")

        # <<< MUDANÇA: Carrega o catálogo do Firestore ou inicializa um novo
        if 'catalogo_ofertas' not in st.session_state:
            # st.session_state.catalogo_ofertas = self.carregar_catalogo_do_firestore()
            # SIMULAÇÃO: Enquanto a função de carregar não está pronta, inicializamos um vazio
            st.session_state.catalogo_ofertas = {
                'theme_color': 'Roxo Inovação', 'theme_font': 'Montserrat', 'logo_b64': None,
                'header_pitch': 'Confira nossas ofertas especiais!', 'whatsapp': '',
                'ofertas': [], 'footer_text': f"© {datetime.date.today().year} Sua Empresa"
            }
        
        state = st.session_state.catalogo_ofertas

        # --- Layout de duas colunas ---
        col1, col2 = st.columns([1, 1.2])

        # --- COLUNA 1: Painel de Controle ---
        with col1:
            st.subheader("Painel de Controle 🎛️")

            with st.expander("1. Design do Catálogo", expanded=True):
                state['theme_color'] = st.selectbox("Paleta de Cores", ["Roxo Inovação", "Azul Moderno", "Verde Crescimento", "Cinza Corporativo"])
                state['theme_font'] = st.selectbox("Fonte", ["Montserrat", "Poppins", "Roboto", "Lato"])
                uploaded_logo = st.file_uploader("Sua Logomarca (PNG, JPG)", type=['png', 'jpg'])
                if uploaded_logo:
                    state['logo_b64'] = base64.b64encode(uploaded_logo.getvalue()).decode()

            with st.expander("2. Títulos e Contato", expanded=True):
                state['header_pitch'] = st.text_area("Título Principal do Catálogo", value=state['header_pitch'])
                state['whatsapp'] = st.text_input("Nº WhatsApp para Contato (Opcional)", value=state['whatsapp'], placeholder="Ex: 5532912345678")
                state['footer_text'] = st.text_input("Texto do Rodapé", value=state['footer_text'])

            with st.expander("3. Adicionar Ofertas (até 18)", expanded=True):
                with st.form("offer_form", clear_on_submit=True):
                    st.write("**Adicionar nova oferta/produto**")
                    offer_name = st.text_input("Nome da Oferta")
                    offer_photo = st.file_uploader("Foto da Oferta", type=['png', 'jpg'])
                    offer_desc = st.text_area("Descrição (Preço, detalhes, etc.)")
                    submitted = st.form_submit_button("Adicionar Oferta ao Catálogo")
                    
                    if submitted and offer_name and offer_photo and offer_desc:
                        if len(state['ofertas']) < 18:
                            photo_b64 = base64.b64encode(offer_photo.getvalue()).decode()
                            state['ofertas'].append({'name': offer_name, 'photo_b64': photo_b64, 'desc': offer_desc})
                            st.success(f"Oferta '{offer_name}' adicionada!")
                        else:
                            st.warning("Limite de 18 ofertas atingido.")
                
                if state['ofertas']:
                    st.write("**Ofertas Adicionadas:**")
                    for i, offer in enumerate(state['ofertas']):
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"_{offer['name']}_")
                        if c2.button("Remover", key=f"del_offer_{i}", use_container_width=True):
                            state['ofertas'].pop(i)
                            st.rerun()

            # <<< MUDANÇA: Botão para salvar o progresso no Firestore
            if st.button("💾 Salvar Catálogo", type="primary", use_container_width=True):
                with st.spinner("Salvando seu catálogo no banco de dados..."):
                    # self.salvar_catalogo_no_firestore(state)
                    time.sleep(1) # Simulação
                    st.success("Catálogo salvo com sucesso!")

        # --- COLUNA 2: Pré-visualização e Download ---
        with col2:
            st.subheader("Pré-visualização do Catálogo 📄")

            color_map = {
                'Roxo Inovação': {'primary': (124, 58, 237), 'secondary': (243, 232, 255), 'text': (88, 28, 135), 'bg': '#faf5ff'},
                'Azul Moderno': {'primary': (37, 99, 235), 'secondary': (219, 234, 254), 'text': (30, 64, 175), 'bg': '#eff6ff'},
                'Verde Crescimento': {'primary': (22, 163, 74), 'secondary': (220, 252, 231), 'text': (20, 83, 45), 'bg': '#f0fdf4'},
                'Cinza Corporativo': {'primary': (71, 85, 105), 'secondary': (226, 232, 240), 'text': (30, 41, 59), 'bg': '#f8fafc'},
            }
            font_family = state['theme_font']
            colors = color_map[state['theme_color']]

            # Lógica para paginação na pré-visualização
            total_ofertas = len(state['ofertas'])
            page_size = 6
            total_pages = (total_ofertas + page_size - 1) // page_size if total_ofertas > 0 else 1
            
            page_num = st.number_input('Ver Página', min_value=1, max_value=total_pages, value=1, step=1) if total_pages > 1 else 1
            start_index = (page_num - 1) * page_size
            end_index = start_index + page_size
            ofertas_para_exibir = state['ofertas'][start_index:end_index]
            
            # Montando o HTML para o st.markdown
            # ... (O código HTML e a classe PDF FPDF são praticamente os mesmos do MaxConstrutor,
            #    apenas trocando 'product' por 'offer' e ajustando os campos conforme necessário)
            # Para manter a resposta focada, omiti a repetição do HTML e da classe PDF,
            # pois a estrutura é idêntica. Você pode copiar e colar do seu código original.

            if st.download_button(
                label="📥 Baixar Catálogo em PDF", data=b"simulacao_pdf", file_name="meu_catalogo_de_ofertas.pdf",
                mime="application/pdf", use_container_width=True
            ):
                # A lógica real de geração de PDF seria chamada aqui
                pass

   def exibir_estrategista_de_midia(self):
        """
        Página com um conjunto de ferramentas para análise e planejamento de mídia paga e orgânica,
        incluindo GEO (Generative Engine Optimization) e otimização de anúncios.
        """
        st.header("📊 Estrategista de Mídia Digital")
        st.markdown("Analise sua presença online, planeje seus investimentos em anúncios e otimize seus criativos com o poder da IA.")

        # Criação das abas para organizar as ferramentas
        tab1, tab2, tab3 = st.tabs(["📈 Plano de Mídia", "🌐 Análise GEO", "✍️ Otimizador de Anúncios"])

        # --- Aba 1: Plano de Mídia (Adaptado do seu Estrategista) ---
        with tab1:
            st.subheader("Planejador de Orçamento e Canais")
            st.write("Defina seu objetivo e orçamento para receber uma recomendação estratégica de investimento.")

            with st.form("media_plan_form"):
                objetivo = st.selectbox(
                    "Qual o principal objetivo do seu investimento?",
                    ["Aumentar as vendas online", "Levar mais clientes à loja física", "Gerar mais contatos (leads)", "Fortalecer a marca"]
                )
                orcamento = st.number_input("Qual o seu orçamento total de mídia (R$)?", min_value=100, value=500, step=100)
                duracao = st.slider("A campanha durará quantos dias?", 7, 90, 15)
                
                submitted = st.form_submit_button("🧠 Montar Plano de Mídia")
                if submitted:
                    with st.spinner("Max está analisando os melhores canais para o seu objetivo e orçamento..."):
                        # Lógica para chamar a IA e gerar um plano de mídia.
                        # SIMULAÇÃO:
                        st.session_state['media_plan_result'] = f"""
                        #### 🎯 Plano de Ação para '{objetivo}'

                        Com um orçamento de **R$ {orcamento:.2f}** para **{duracao} dias** (aprox. R$ {orcamento/duracao:.2f}/dia), esta é a minha recomendação estratégica:

                        **1. Alocação de Orçamento:**
                        * **60% (R$ {orcamento*0.6:.2f}) em Meta Ads (Instagram/Facebook):** Ideal para segmentação precisa do seu público local e para gerar desejo com criativos visuais. Foco em anúncios de tráfego e conversão.
                        * **40% (R$ {orcamento*0.4:.2f}) em Google Ads (Rede de Pesquisa):** Essencial para capturar a demanda de pessoas que já estão procurando ativamente pelo seu produto/serviço.

                        **2. Foco do Público-Alvo:**
                        * **Meta Ads:** Criar um público de 'Interesses' baseado no seu briefing e um público de 'Remarketing' para re-impactar quem visitou seu site ou perfil.
                        * **Google Ads:** Focar em palavras-chave de 'cauda longa' e com intenção de compra, como "melhor [seu produto] em [sua cidade]".

                        **3. Próximo Passo Sugerido:**
                        * Use o **Otimizador de Anúncios** (na próxima aba) para criar os textos e headlines para esta campanha.
                        """
            
            if 'media_plan_result' in st.session_state:
                st.markdown("---")
                st.subheader("✅ Seu Plano de Mídia Estratégico:")
                st.markdown(st.session_state['media_plan_result'], unsafe_allow_html=True)


        # --- Aba 2: Análise GEO (Nova funcionalidade) ---
        with tab2:
            st.subheader("Analisador de Presença Local (GEO)")
            st.write("Otimize seu conteúdo para ser encontrado por IAs e mecanismos de busca quando clientes locais procurarem por você.")

            with st.form("geo_analysis_form"):
                st.write("Vamos analisar e otimizar sua principal página de serviço.")
                url_pagina = st.text_input("Cole a URL da sua principal página de produto/serviço:", placeholder="https://seusite.com.br/servico-principal")
                
                submitted_geo = st.form_submit_button("🔍 Analisar para GEO")
                if submitted_geo and url_pagina:
                    with st.spinner("Max está lendo sua página e identificando pontos de otimização para GEO..."):
                        # Lógica para a IA analisar a URL
                        # SIMULAÇÃO:
                        st.session_state['geo_result'] = """
                        #### ✅ Análise GEO da sua página:

                        **Pontos Fortes:**
                        * O título da página menciona seu serviço principal.
                        * As imagens têm texto alternativo, o que ajuda na acessibilidade.

                        **Oportunidades de Melhoria para IAs:**
                        1.  **Crie uma seção de FAQ:** Responda diretamente às 5 perguntas mais comuns sobre seu serviço. IAs adoram o formato de Pergunta e Resposta. Sugestão de pergunta: "Qual o preço do [seu serviço]?"
                        2.  **Adicione Dados Estruturados:** Inclua o endereço e o telefone da sua empresa de forma clara e explícita no rodapé da página.
                        3.  **Use Tópicos Locais:** Adicione um parágrafo sobre a história da sua empresa na sua cidade ou como seu serviço atende especificamente à comunidade local.
                        """

            if 'geo_result' in st.session_state:
                st.markdown("---")
                st.subheader("💡 Recomendações de Otimização GEO:")
                st.markdown(st.session_state['geo_result'])

        # --- Aba 3: Otimizador de Anúncios (Adaptado do seu Especialista Google) ---
        with tab3:
            st.subheader("Criador e Otimizador de Anúncios para Google")
            st.write("Crie rapidamente os textos para seus anúncios na Rede de Pesquisa do Google.")

            with st.form("ads_creator_form"):
                termo_busca = st.text_input("O que seu cliente ideal digitaria no Google para te achar?", placeholder="Ex: Sapataria artesanal em Juiz de Fora")
                
                submitted_ads = st.form_submit_button("✍️ Gerar Textos do Anúncio")
                if submitted_ads and termo_busca:
                    with st.spinner("Max está criando headlines e descrições de alta conversão..."):
                        # Lógica para chamar a IA e gerar os anúncios
                        # SIMULAÇÃO:
                        st.session_state['ads_result'] = f"""
                        #### ✅ Textos para Anúncios de Pesquisa:

                        **Sugestão de Palavras-Chave:**
                        * `{termo_busca}`
                        * `loja de sapatos artesanais juiz de fora`
                        * `onde comprar sapato de couro em jf`

                        ---
                        **Opção de Anúncio 1 (Foco em Qualidade):**
                        * **Título 1:** Sapatos Artesanais em Juiz de Fora
                        * **Título 2:** Couro Legítimo e Durabilidade
                        * **Título 3:** Qualidade em Cada Detalhe
                        * **Descrição:** Conheça nossa coleção exclusiva de sapatos feitos à mão. Conforto e estilo que duram. Visite nossa loja no centro!

                        **Opção de Anúncio 2 (Foco em Exclusividade):**
                        * **Título 1:** {termo_busca.title()}
                        * **Título 2:** Modelos Únicos e Exclusivos
                        * **Título 3:** Atendimento Personalizado
                        * **Descrição:** Cansado do mesmo? Encontre sapatos com personalidade e design autoral. Estoque limitado. Garanta já o seu par!
                        """

            if 'ads_result' in st.session_state:
                st.markdown("---")
                st.subheader("📝 Seus Anúncios para o Google:")
                st.markdown(st.session_state['ads_result'])
