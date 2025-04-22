import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Configurações da API
API_KEY = st.secrets["API_KEY"]  # A chave da API armazenada no secrets
BASE_URL = "https://partner-api.flexge.com/external"
HEADERS = {"x-api-key": API_KEY}

# Função para fazer requisições à API com paginação
def get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# Função para pegar os alunos com paginação
def get_students():
    params = {"page": 1, "limit": 100}  # Ajuste conforme necessário
    students = []
    while True:
        data = get("/students", params=params)
        students.extend(data.get("docs", []))
        
        # Verifica se há mais páginas
        if len(data.get("docs", [])) < params["limit"]:
            break
        params["page"] += 1

    return students

# Função para pegar o progresso de tempo de estudo da semana
def get_week_study_progress():
    params = {"page": 1, "limit": 100}  # Ajuste conforme necessário
    data = get("/students/reports/studied-time-progress", params=params)
    return {student["id"]: student["currentWeekTime"]["studiedTime"] for student in data.get("docs", [])}

# Função para pegar as necessidades de gramática
def get_grammar_needs():
    params = {"page": 1, "limit": 100}  # Ajuste conforme necessário
    data = get("/students/reports/grammar-needs", params=params)
    grammar_map = {}
    for grammar in data.get("students", []):
        student_id = grammar["id"]
        grammar_map[student_id] = {
            "grammar_issues": grammar.get("errorCount", 0),
            "grammar_error_pct": grammar.get("errorPercentage", 0),
        }
    return grammar_map

# Função para pegar os detalhes do aluno
def get_overview(student_id):
    return get(f"/students/{student_id}/overview")

def get_daily_executions(student_id):
    return get(f"/students/{student_id}/daily-executions")

def get_studied_grammars(student_id):
    return get(f"/students/{student_id}/studied-grammars")

# Função para processar os dados de cada aluno
def process_student(student, week_time_data, grammar_needs_map):
    student_id = student["id"]
    name = student.get("name")
    email = student.get("email")

    # Detalhes do aluno
    overview = get_overview(student_id)
    course_name = overview.get("studentCourse", {}).get("course", {}).get("name")
    course_progress = overview.get("studentCourse", {}).get("progress")
    study_quality = overview.get("studyQuality", {}).get("score")

    # Execuções diárias
    daily = get_daily_executions(student_id)
    total_time_30d = sum(day.get("studiedTime", 0) for day in daily)
    total_points_30d = sum(day.get("points", 0) for day in daily)

    # Gramática
    grammars = get_studied_grammars(student_id)
    total_grammars = len(grammars)
    total_grammar_errors = sum(g.get("errorCount", 0) for g in grammars)

    # Dados semanais
    week_time = week_time_data.get(student_id, 0)
    grammar_extra = grammar_needs_map.get(student_id, {})

    return {
        "Nome": name,
        "Email": email,
        "Curso": course_name,
        "Progresso no curso (%)": course_progress,
        "Qualidade de estudo": study_quality,
        "Tempo estudado (últimos 30 dias)": round(total_time_30d / 60, 2),
        "Pontos obtidos (últimos 30 dias)": total_points_30d,
        "Tempo estudado (semana atual)": round(week_time / 60, 2),
        "Gramáticas estudadas": total_grammars,
        "Erros em gramática (total)": total_grammar_errors,
        "Gramática: erros críticos": grammar_extra.get("grammar_issues", 0),
        "Gramática: % de erro (crítica)": grammar_extra.get("grammar_error_pct", 0),
    }

# Função para gerar a planilha
def gerar_planilha():
    alunos = get_students()
    week_time_data = get_week_study_progress()
    grammar_needs_map = get_grammar_needs()
    dados = []

    for aluno in alunos:
        try:
            dados.append(process_student(aluno, week_time_data, grammar_needs_map))
        except Exception as e:
            st.warning(f"Erro com aluno {aluno.get('name')}: {e}")

    df = pd.DataFrame(dados)
    hoje = datetime.now().strftime("%Y-%m-%d")
    filename = f"relatorio_alunos_flexge_{hoje}.xlsx"
    df.to_excel(filename, index=False)
    return filename

# Interface Streamlit
st.title("📊 Gerador de Relatórios - Flexge")

if st.button("📥 Gerar planilha de alunos"):
    with st.spinner("Gerando planilha..."):
        try:
            arquivo = gerar_planilha()
            st.success("✅ Planilha gerada com sucesso!")
            with open(arquivo, "rb") as f:
                st.download_button("📎 Baixar planilha", f, file_name=arquivo)
        except Exception as e:
            st.error(f"❌ Erro ao gerar planilha: {e}")
