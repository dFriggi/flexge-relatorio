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
    return f"{minutes // 60:02}:{minutes % 60:02}"

# Função para calcular a última semana completa (segunda a sexta)
def get_last_full_week():
    today = datetime.today()
    weekday = today.weekday()

    last_friday = today - timedelta(days=weekday + 3)
    last_monday = last_friday - timedelta(days=4)

    return last_monday.date(), last_friday.date()

# Função para buscar alunos
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

# Função para buscar tempo de estudo
def get_student_study_time(student_id, start_date, end_date):
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat()
    }
    response = requests.get(f"{BASE_URL}/students/{student_id}/daily-executions", headers=HEADERS, params=params)

    if response.status_code != 200:
        return 0

    daily_executions = response.json()
    total_studied_time = sum(day.get("studiedTime", 0) for day in daily_executions)
    return total_studied_time

# Função para processar os alunos
def process_students(students, start_date, end_date):
    records = []

    for student in students:
        student_id = student.get("id", "")
        name = student.get("name", "")
        progress = student.get("studentCourse", {}).get("progress", "")
        course_name = student.get("studentCourse", {}).get("course", {}).get("name", "")
        weekly_hours_required = student.get("weeklyHoursRequired", 0)
        study_score = student.get("studyQuality", {}).get("score", 0)

        studied_seconds = get_student_study_time(student_id, start_date, end_date)

        studied_time_formatted = format_seconds_to_hhmm(studied_seconds)
        weekly_hours_seconds = weekly_hours_required * 3600
        weekly_hours_formatted = format_seconds_to_hhmm(weekly_hours_seconds)

        records.append({
            "Nome do Aluno": name,
            "Semana": "",  # coluna vazia
            "Progresso (%)": progress,
            "Nome do Curso": course_name,
            "Tempo de Estudo (hh:mm)": studied_time_formatted,
            "Objetivo de Tempo (hh:mm)": weekly_hours_formatted,
            "Score de Qualidade de Estudo": study_score,
            "Tarefa": "",
            "Relatório da Semana": ""
        })

    return records

# Ajustar largura automática das colunas
def adjust_column_widths(workbook):
    worksheet = workbook.active
    for column_cells in worksheet.columns:
        max_length = 0
        column = column_cells[0].column_letter  # pega a letra da coluna
        for cell in column_cells:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width

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

                # Ordenar as colunas em ordem alfabética
                df = df.reindex(sorted(df.columns), axis=1)

                # Salva em memória
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Alunos")
                    workbook = writer.book
                    adjust_column_widths(workbook)

                output.seek(0)

                # Texto do título da semana
                semana_periodo = f"Semana {start_date.day:02}.{start_date.month:02} - {end_date.day:02}.{end_date.month:02}"
                st.success(f"✅ Relatório gerado para {semana_periodo}!")

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
