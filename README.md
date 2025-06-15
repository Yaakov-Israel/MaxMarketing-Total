# MaxMarketing Total 🚀

> Seu especialista de marketing digital com IA, pronto para transformar ideias em resultados.

## Sobre o Projeto

O **MaxMarketing Total** é o primeiro módulo comercial da suíte Max IA Empresarial. Nosso objetivo é democratizar o acesso a ferramentas de marketing digital de alta performance para Pequenas e Médias Empresas (PMEs) no Brasil, combinando uma interface intuitiva com o poder da Inteligência Artificial generativa do Google.

Este projeto é desenvolvido de forma modular para garantir agilidade, qualidade e entrega de valor contínua aos nossos clientes.

## 🎯 Principais Funcionalidades (MVP)

* **🤖 Criador de Posts para Redes Sociais:** Gera conteúdo completo (texto, título, hashtags, sugestão de imagem) para Instagram, Facebook e outras redes.
* **✉️ Gerador de Email Marketing:** Cria textos persuasivos para campanhas de email, desde newsletters a funis de venda.
* **🎓 Max Trainer (Integrado):** Uma área de aprendizado com tutoriais e dicas para ajudar o usuário a extrair o máximo de cada ferramenta.
* **🔐 Autenticação Segura:** Sistema completo de login, cadastro e gerenciamento de contas de usuário.

## 🛠️ Tecnologias Utilizadas

* **Backend & Frontend:** Python 3.11+ com [Streamlit](https.streamlit.io/)
* **Inteligência Artificial:** Google Gemini API
* **Containerização:** [Docker](https://www.docker.com/)
* **Hospedagem (Planejada):** [Google Cloud Run](https://cloud.google.com/run)

---

## 🚀 Como Começar (Setup do Ambiente)

Para configurar o ambiente de desenvolvimento localmente, siga estes passos:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Yaakov-Israel/MaxMarketing-Total.git](https://github.com/Yaakov-Israel/MaxMarketing-Total.git)
    cd MaxMarketing-Total
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Para Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione sua chave de API do Google neste formato:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_DE_API_SECRETA_AQUI"
        ```
    * **Importante:** Adicione o arquivo `.env` ao seu `.gitignore` para nunca expor suas chaves secretas!

## ▶️ Como Executar o Projeto

### Localmente

Após instalar as dependências, execute o seguinte comando no seu terminal:

```bash
streamlit run streamlit_app.py
