import streamlit as st

# Teste se a chave foi lida corretamente
st.write(f"Sua API_KEY é: {st.secrets.get('API_KEY', 'Chave não encontrada')}")
