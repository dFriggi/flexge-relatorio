import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Configurações da API
API_KEY = st.secrets["API_KEY"]  # A chave da API fica segura no secrets do Streamlit Cloud
BASE_URL = "https://partner-api.flexge.com/external"
HEADERS = {"x-api-key": API_KEY}

# Função para buscar os alunos
def get_students():
    all_students = []
    page = 1

    while True:
        params = {
            "page": page,
            "deleted": False
        }
        response = requests.get(f"{BASE_URL}/students", headers=HEADERS, params=params)
        
        if response.status_code != 200:
            st.error(f"Erro na requisição: {response.status_code}")
            break
        
        data = response.json()
        students = data.get("docs", [])

        if not students:
            break

        all_students.extend(students)
        page += 1

    return all_students

# Função para processar os dados
def process_students(students):
    records = []

    for student in students:
        name = student.get("name", "")
        progress = student.get("studentCourse", {}).get("progress", "")
        course_name = student.get("studentCourse", {}).get("course", {}).get("name", "")
        weekly_hours = student.get("weeklyHoursRequired", "")
        score = student.get("studyQuality", {}).get("score", "")

        records.append({
            "Nome do Aluno": name,
            "Progresso (%)": progress,
            "Nome do Curso": course_name,
            "Horas Semanais Requeridas": weekly_hours,
            "Score de Qualidade de Estudo": score
        })

    return records

# Função principal da página
def main():
    st.title("Gerar Relatório de Alunos - Flexge API")

    if st.button("Gerar Relatório"):
        with st.spinner("Buscando dados..."):
            students = get_students()
            if students:
                student_records = process_students(students)
                df = pd.DataFrame(student_records)

                # Salva em memória o Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)

                # Disponibiliza o download
                st.success("Relatório gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Relatório Excel",
                    data=output,
                    file_name="alunos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhum aluno encontrado.")

if __name__ == "__main__":
    main()
