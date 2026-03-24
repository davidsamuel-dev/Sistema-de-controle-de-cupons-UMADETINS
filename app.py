import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account 
import json
import pandas as pd
import plotly.express as px
from relatorios import gerar_pdf_filtrado
from datetime import datetime
import time
import os

# --- CONEXÃO COM FIREBASE (VERSÃO CORRIGIDA) ---
@st.cache_resource
def get_db():
    # 1. Tenta carregar do arquivo local primeiro (Para não dar erro de Secrets no Windows)
    if os.path.exists('chave.json'):
        with open('chave.json') as f:
            key_dict = json.load(f)
        creds = service_account.Credentials.from_service_account_info(key_dict)
    # 2. Se não houver arquivo, tenta os segredos da Web (Streamlit Cloud)
    else:
        try:
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
        except Exception as e:
            st.error("Erro: Arquivo 'chave.json' não encontrado e segredos da web ausentes.")
            st.stop()
    
    return firestore.Client(credentials=creds)

db = get_db()

# --- FUNÇÕES DE CRUD FIREBASE ---
def salvar_participante(dados):
    db.collection("participantes").document(dados['cpf']).set(dados)

def buscar_participantes():
    docs = db.collection("participantes").stream()
    lista = [doc.to_dict() for doc in docs]
    return pd.DataFrame(lista)

def excluir_participante(cpf):
    db.collection("participantes").document(cpf).delete()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SCCUADP 2026", layout="wide", page_icon="🎫")

# --- CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #001F3F !important; border-right: 2px solid #87CEEB; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #FFFFFF !important; }
    .stTextInput > div > div > input, .stSelectbox > div > div > div { border-radius: 10px !important; border: 1px solid #87CEEB !important; }
    [data-testid="stMetric"] { background-color: #f0f8ff; padding: 15px; border-radius: 15px; border-left: 5px solid #87CEEB; }
    div.stButton > button:first-child { background-color: #87CEEB !important; color: #001F3F !important; font-weight: bold; border-radius: 20px; width: 100%; }
    .sidebar-title { color: #87CEEB !important; text-align: center; font-weight: bold; font-size: 26px; margin-bottom: 0px; }
    .sidebar-sub { color: #FFFFFF !important; text-align: center; font-size: 14px; margin-bottom: 20px; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">⛪ AD PARAÍSO</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-sub">SCCUADP 2026</p>', unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=80)
    st.markdown("---")
    choice = st.radio("NAVEGAÇÃO PRINCIPAL", ["📊 Dashboard", "📝 Novo Cadastro", "📋 Gestão de Registros"])
    st.markdown("---")
    st.caption("📍 Paraíso do Tocantins - TO")

# --- MÓDULO DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Painel de Indicadores")
    df = buscar_participantes()

    if not df.empty:
        valor_pago = df[df['pago'] == 'Pago']['qtd_cupons'].sum() * 2
        valor_pendente = df[df['pago'] == 'Pendente']['qtd_cupons'].sum() * 2
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Financeiro Pago", f"R$ {valor_pago},00", f"Pendente: R$ {valor_pendente}")
        m2.metric("Passageiros Ônibus", len(df[df['transporte'] == 'Ônibus']))
        m3.metric("Alojamento", len(df[df['alojamento'] == 'Sim']))
        m4.metric("Total Inscritos", len(df))

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📦 Distribuição de Blocos")
            df_counts = df['qtd_cupons'].value_counts().reset_index()
            df_counts.columns = ['Tipo', 'Qtd']
            fig = px.bar(df_counts, x='Tipo', y='Qtd', color='Tipo', color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("🌍 Regional/Unidade")
            fig_un = px.pie(df, names='unidade', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_un, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado no Firebase.")

# --- MÓDULO CADASTRO ---
elif choice == "📝 Novo Cadastro":
    st.title("📝 Novo Cadastro")
    with st.form("cadastro_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo").upper()
            cpf = st.text_input("CPF (Somente números)")
            unidade = st.selectbox("Regional", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            dept = st.selectbox("Departamento", ["JGE", "AGE", "Outro"])
        with col2:
            qtd = st.selectbox("Tipo de Bloco", [100, 150, 0])
            transp = "Ônibus" if qtd == 150 else "Carro"
            st.info(f"💡 Logística: {transp} | Valor: R$ {qtd*2},00")
            aloj = st.radio("Alojamento?", ["Sim", "Não"], horizontal=True)
            bloco = st.selectbox("Retirou Bloco?", ["Sim", "Não"])
            pago = st.selectbox("Status", ["Pendente", "Pago"])

        if st.form_submit_button("🚀 Finalizar Inscrição"):
            if nome and cpf:
                dados = {
                    "nome": nome, "cpf": cpf, "unidade": unidade, 
                    "departamento": dept, "transporte": transp, 
                    "alojamento": aloj, "retirou_bloco": bloco, 
                    "qtd_cupons": qtd, "pago": pago, 
                    "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                salvar_participante(dados)
                st.success(f"✅ {nome} cadastrado com sucesso!")
                st.snow()
            else:
                st.warning("Preencha Nome e CPF.")

# --- MÓDULO GESTÃO ---
elif choice == "📋 Gestão de Registros":
    st.title("📋 Gestão e Relatórios")
    df = buscar_participantes()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        if st.button("📄 Gerar Relatório PDF"):
            pdf_bytes = gerar_pdf_filtrado(df)
            st.download_button("⬇️ Baixar PDF", data=pdf_bytes, file_name="Relatorio_SCCUADP.pdf")
        
        cpf_del = st.text_input("Digite o CPF para excluir")
        if st.button("❌ Excluir"):
            excluir_participante(cpf_del)
            st.warning("Registro removido.")
            time.sleep(1)
            st.rerun()
    else:
        st.info("O banco de dados está vazio.")