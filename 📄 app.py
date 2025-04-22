import requests
import streamlit as st

# Leia a chave da API do Streamlit Secrets
API_KEY = st.secrets["API_KEY"]

# Defina o cabeçalho da requisição
BASE_URL = "https://partner-api.flexge.com/external"
HEADERS = {"x-api-key": API_KEY}

# Função para testar o acesso à API
def testar_api():
    try:
        # Tente acessar o endpoint de "students" para verificar se a API responde
        params = {"page": 1}
        response = requests.get(f"{BASE_URL}/students", headers=HEADERS)
        
        # Verifique o status da resposta
        if response.status_code == 200:
            st.success("✅ Acesso à API bem-sucedido!")
            st.write(response.json())  # Exibe a resposta para ver os dados recebidos
        else:
            st.error(f"❌ Erro ao acessar a API. Status code: {response.status_code}")
            st.write(response.text)  # Exibe o texto de erro da resposta
    except Exception as e:
        st.error(f"❌ Erro ao acessar a API: {e}")

# Chama a função para testar a API
testar_api()
