import requests
import streamlit as st

# Definindo a chave da API
API_KEY = st.secrets["API_KEY"]  # Ou apenas a chave diretamente, se for o caso
BASE_URL = "https://partner-api.flexge.com/external"

# Cabeçalho HTTP com a chave da API
HEADERS = {"x-api-key": API_KEY}

# Função para testar o acesso à API
def testar_api():
    try:
        # Exibir a chave para verificar
        st.write(f"Chave da API: {API_KEY}")  # Verifique se a chave está correta
        
        # Parâmetros para paginação
        params = {"page": 1, "limit": 20}  # Exemplo com página 1 e 20 itens por página
        response = requests.get(f"{BASE_URL}/students", headers=HEADERS, params=params)
        
        # Verificando a resposta da API
        if response.status_code == 200:
            st.success("✅ Acesso à API bem-sucedido!")
            st.write(response.json())  # Exibe a resposta recebida
        else:
            st.error(f"❌ Erro ao acessar a API. Status code: {response.status_code}")
            st.write(response.text)  # Exibe o erro retornado pela API

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao acessar a API: {e}")

# Chama a função para testar a API
testar_api()
