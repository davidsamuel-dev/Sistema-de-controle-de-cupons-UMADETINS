import streamlit as st
import pandas as pd
import json
import time
import os
import plotly.express as px  # <--- CERTIFIQUE-SE QUE ESTA LINHA ESTÁ AQUI
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
from relatorios import gerar_pdf_filtrado

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

# --- MÓDULO CADASTRO (VERSÃO ATUALIZADA 2026) ---
elif choice == "📝 Novo Cadastro":
    st.title("📝 Novo Cadastro - UMADETINS 2026")
    
    with st.form("cadastro_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo").upper()
            cpf = st.text_input("CPF (Somente números)")
            unidade = st.selectbox("Regional", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            is_crianca = st.checkbox("É criança? (Isento de inscrição)")
            
        with col2:
            transp = st.radio("Logística de Transporte", ["Ônibus", "Carro"], horizontal=True)
            aloj = st.radio("Necessita Alojamento?", ["Não", "Sim"], horizontal=True)
            bloco = st.selectbox("Retirou Bloco?", ["Não", "Sim (100 cupons)", "Sim (150 cupons)"])
            pago = st.selectbox("Status de Pagamento", ["Pendente", "Pago"])
         

        # --- LÓGICA DE CÁLCULO DE VALORES ---
        valor_total = 0
        
        if is_crianca:
            # Regra 2: Crianças pagam apenas passagem (R$ 137) se forem de ônibus
            valor_total = 137 if transp == "Ônibus" else 0
            info_msg = f"👶 Criança: Passagem R$ {valor_total},00"
        else:
            # Regra 1: Inscrição base R$ 163
            valor_total = 163
            
            # Se pegou bloco, o valor é baseado nos cupons (substitui os 163)
            if "100" in bloco:
                valor_total = 200 # 100 * 2
            elif "150" in bloco:
                valor_total = 300 # 150 * 2
            
            info_msg = f"👤 Adulto: Total R$ {valor_total},00 (Inscrição + Logística)"

        st.info(f"💰 {info_msg} | 🚗 Transporte: {transp}")

        if st.form_submit_button("🚀 Finalizar Inscrição"):
            if nome and cpf:
                dados = {
                    "nome": nome, 
                    "cpf": cpf, 
                    "unidade": unidade, 
                    "is_crianca": is_crianca,
                    "transporte": transp, 
                    "alojamento": aloj, 
                    "bloco": bloco, 
                    "valor_total": valor_total,
                    "pago": pago, 
                    "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                salvar_participante(dados)
                st.success(f"✅ {nome} cadastrado com sucesso!")
                st.balloons()
            else:
                st.warning("⚠️ Por favor, preencha o Nome e o CPF.")


# --- MÓDULO GESTÃO ---
elif choice == "📋 Gestão de Registros":
    st.title("📋 Gestão e Relatórios")
    df = buscar_participantes()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Geramos o PDF primeiro (isso é rápido)
        pdf_bytes = gerar_pdf_filtrado(df)
        
        # O botão de download fica sempre visível e funcional
        st.download_button(
            label="📄 Baixar Relatório PDF",
            data=pdf_bytes,
            file_name="Relatorio_SCCUADP.pdf",
            mime="application/pdf"
        )
        
        st.divider() # Uma linha para separar
        
        st.subheader("🗑️ Excluir Registro")
        cpf_del = st.text_input("Digite o CPF para excluir")
        if st.button("❌ Confirmar Exclusão"):
            if cpf_del:
                excluir_participante(cpf_del)
                st.warning(f"Registro {cpf_del} removido.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Por favor, digite um CPF.")
    else:
        st.info("O banco de dados está vazio.")
