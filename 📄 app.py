import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

# Configurações da API
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://partner-api.flexge.com/external"
HEADERS = {"x-api-key": API_KEY}

# Função para converter segundos em HH:MM
def format_seconds_to_hhmm(seconds):
    minutes = seconds // 60
    return f"{minutes // 60}:{minutes % 60}"

# Função para calcular o período da última semana completa (segunda a sexta)
def get_last_full_week():
    today = datetime.today()
    weekday = today.weekday()

    last_friday = today - timedelta(days=weekday + 3)
    last_monday = last_friday - timedelta(days=4)

    return last_monday.date(), last_friday.date()

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

# Função para buscar o tempo de estudo do aluno
def get_student_study_time(student_id, start_date, end_date):
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat()
    }
    response = requests.get(f"{BASE_URL}/students/{student_id}/daily-executions", headers=HEADERS, params=params)

    if response.status_code != 200:
        return 0  # Se erro, retorna zero minutos

    daily_executions = response.json()

    total_studied_time = sum(day.get("studiedTime", 0) for day in daily_executions)
    return total_studied_time
    
#Transforma o progresso em percentual
def formatar_percentual(numero):
    if numero == '':  
        return '0,0%'  
    
    try:
        numero = float(numero)  # Tenta converter para float
        return f"{numero:.1f}%".replace('.', ',')
    except ValueError:
        return 'Valor inválido'
        
#Formata a hora e minuto do tempo
def formatar_hora(numero):
    if ":" not in str(numero):
        return "Formato inválido"

    horas, minutos = str(numero).split(":")
    
    horas = int(float(horas))  # Converte e remove o decimal se houver
    minutos = int(float(minutos))  # Converte e remove o decimal se houver
    
    return f"{horas}:{minutos}"

# Função para processar os dados
def process_students(students, start_date, end_date):
    records = []

    for student in students:
        student_id = student.get("id", "")
        name = student.get("name", "")
        progress = student.get("studentCourse", {}).get("progress", "")
        course_name = student.get("studentCourse", {}).get("course", {}).get("name", "")
        weekly_hours_required = student.get("weeklyHoursRequired", 0)
        study_score = student.get("studyQuality", {}).get("score", 0)

        # Buscar tempo de estudo da semana
        studied_seconds = get_student_study_time(student_id, start_date, end_date)

        #Transforme em percentual
        progress = formatar_percentual(progress)
        
        # Formatar tempos
        studied_time_formatted = format_seconds_to_hhmm(studied_seconds)
        weekly_hours_seconds = weekly_hours_required * 3600
        weekly_hours_formatted = format_seconds_to_hhmm(weekly_hours_seconds)
        weekly_hours_formatted = formatar_hora(weekly_hours_formatted)
        studied_time_formatted = formatar_hora(studied_time_formatted)

        # Formatar semana para o título
        semana_periodo = f"{start_date.day:02}.{start_date.month:02} - {end_date.day:02}.{end_date.month:02}"

        records.append({
            "Nome": name,
            f"Semana {semana_periodo}": "",
            "Progresso (%)": progress,
            "Nível": course_name,
            "Tempo de Estudo": studied_time_formatted,
            "Objetivo de Tempo": weekly_hours_formatted,
            "Qualidade de Estudo": study_score,
            "Tarefa": "",  # Em branco
            "Relatório da Semana": ""  # Em branco
        })

    return records

# Função principal
def main():
    st.title("📊 Gerar Relatório de Alunos - Flexge API")

    if st.button("Gerar Relatório"):
        with st.spinner("Buscando dados..."):
            students = get_students()
            if students:
                start_date, end_date = get_last_full_week()
                student_records = process_students(students, start_date, end_date)
                df = pd.DataFrame(student_records)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)

                st.success("✅ Relatório gerado com sucesso!")
                st.download_button(
                    label="📥 Baixar Relatório Excel",
                    data=output,
                    file_name="Relatório Alunos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Nenhum aluno encontrado.")

if __name__ == "__main__":
    main()
