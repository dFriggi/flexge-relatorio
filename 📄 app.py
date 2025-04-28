import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import io
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment

# CONFIGURAÇÕES DA API
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://partner-api.flexge.com/external"
HEADERS = {"x-api-key": API_KEY}

# FUNÇÕES AUXILIARES
def buscar_alunos():
    url = f"{BASE_URL}/students"
    params = {"deleted": False}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["docs"]

def buscar_tempo_estudo(student_id, start_date, end_date):
    url = f"{BASE_URL}/students/{student_id}/daily-executions"
    params = {"from": start_date.isoformat(), "to": end_date.isoformat()}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    daily_data = response.json()
    total_seconds = sum(day["studiedTime"] for day in daily_data)
    return total_seconds

def formatar_tempo(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{int(hours):02}:{int(minutes):02}"

def formatar_progresso(progress):
    return f"{progress:.2f}%"

def obter_periodo_semana():
    hoje = datetime.now()
    ultima_sexta = hoje - timedelta(days=(hoje.weekday() + 3) % 7 + 2)
    ultima_segunda = ultima_sexta - timedelta(days=4)
    return ultima_segunda.date(), ultima_sexta.date()

# STREAMLIT APP
st.title("Relatório Flexge - Exportação de Alunos")

if st.button("Gerar Relatório"):
    alunos = buscar_alunos()
    segunda, sexta = obter_periodo_semana()
    semana_str = f"Semana {segunda.strftime('%d.%m')} - {sexta.strftime('%d.%m')}"

    dados = []
    for aluno in alunos:
        student_id = aluno["id"]
        nome = aluno["name"]
        progresso = aluno.get("studentCourse", {}).get("progress", 0)
        nome_curso = aluno.get("studentCourse", {}).get("course", {}).get("name", "")
        objetivo_tempo = aluno.get("weeklyHoursRequired", 0)
        qualidade_estudo = aluno.get("studyQuality", {}).get("score", 0)

        tempo_estudo_segundos = buscar_tempo_estudo(student_id, segunda, sexta)
        tempo_estudo = formatar_tempo(tempo_estudo_segundos)

        objetivo_tempo_minutos = int(objetivo_tempo * 60)
        objetivo_tempo_formatado = formatar_tempo(objetivo_tempo_minutos * 60)

        dados.append({
            "Nome": nome,
            semana_str: "",
            "Progresso (%)": formatar_progresso(progresso),
            "Nível": nome_curso,
            "Tempo de Estudo": tempo_estudo,
            "Objetivo de Tempo": objetivo_tempo_formatado,
            "Score de Qualidade de Estudo": qualidade_estudo,
            "Tarefa": "",
            "Relatório da Semana":""
        })

    df = pd.DataFrame(dados)
    df = df.sort_values(by=["Nome do Aluno"]).reset_index(drop=True)

    # Criar arquivo Excel
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active

    # Adicionar cabeçalho e dados
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    # Ajustar largura das colunas e alinhamento
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
        adjusted_width = (length + 2)
        ws.column_dimensions[column_cells[0].column_letter].width = adjusted_width
        for cell in column_cells:
            cell.alignment = Alignment(horizontal='center', vertical='center')

    wb.save(output)
    output.seek(0)

    st.download_button(
        label="Baixar Relatório em Excel",
        data=output,
        file_name="relatorio_flexge.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
