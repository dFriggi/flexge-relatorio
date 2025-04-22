HEADERS = {"x-api-key": st.secrets["API_KEY"]}

response = requests.get(f"{BASE_URL}/students", headers=HEADERS)
