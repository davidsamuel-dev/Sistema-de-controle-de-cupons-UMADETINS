import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SCCUADP 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stSidebar { background-color: #001F3F; color: white; }
    div.stButton > button:first-child {
        background-color: #87CEEB; color: #001F3F; font-weight: bold; border-radius: 5px;
    }
    h1, h2, h3 { color: #001F3F; }
    .metric-card {
        background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #001F3F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DO BANCO ---
def get_connection():
    return sqlite3.connect('sccuadp_2026.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL, cpf TEXT UNIQUE NOT NULL,
                    unidade TEXT, departamento TEXT, transporte TEXT,
                    alojamento TEXT, retirou_bloco TEXT, qtd_cupons INTEGER,
                    pago TEXT, data_registro TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- SIDEBAR MENU ---
st.sidebar.title("📌 SCCUADP 2026")
menu = ["📊 Dashboard", "📝 Cadastrar", "📋 Lista de Registros"]
choice = st.sidebar.selectbox("Navegação", menu)

# --- LÓGICA DO DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Painel de Indicadores")
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM participantes", conn)
    conn.close()

    if not df.empty:
        # Métricas Rápidas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Inscritos", len(df))
        col2.metric("Total Cupons", df['qtd_cupons'].sum())
        col3.metric("Pagos", len(df[df['pago'] == 'Pago']))
        col4.metric("Pendentes", len(df[df['pago'] == 'Pendente']))

        st.markdown("---")

        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Pagamentos")
            fig_pago = px.pie(df, names='pago', color='pago', 
                             color_discrete_map={'Pago':'#87CEEB', 'Pendente':'#001F3F'})
            st.plotly_chart(fig_pago, use_container_width=True)

        with col_graf2:
            st.subheader("Inscritos por Unidade")
            fig_unidade = px.bar(df['unidade'].value_counts().reset_index(), 
                                x='unidade', y='count', color_discrete_sequence=['#001F3F'])
            st.plotly_chart(fig_unidade, use_container_width=True)
            
        st.subheader("Distribuição por Departamento")
        fig_dept = px.funnel(df['departamento'].value_counts().reset_index(), x='count', y='departamento')
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("Nenhum dado cadastrado para exibir no Dashboard.")

# --- LÓGICA DE CADASTRO ---
elif choice == "📝 Cadastrar":
    st.title("📝 Novo Cadastro")
    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo").upper()
            cpf = st.text_input("CPF (Somente números)")
            unidade = st.selectbox("Unidade/Regional", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            dept = st.selectbox("Departamento", ["JGE", "AGE", "Outro"])
        with c2:
            transp = st.radio("Transporte", ["Ônibus", "Carro"])
            aloj = st.radio("Alojamento?", ["Sim", "Não"])
            bloco = st.selectbox("Retirou Bloco?", ["Sim", "Não"])
            qtd = st.number_input("Qtd Cupons", value=100, step=50)
            pago = st.selectbox("Status", ["Pendente", "Pago"])
        
        if st.form_submit_button("Salvar Registro"):
            if nome and cpf:
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO participantes (nome, cpf, unidade, departamento, transporte, alojamento, retirou_bloco, qtd_cupons, pago, data_registro) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (nome, cpf, unidade, dept, transp, aloj, bloco, qtd, pago, datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    st.success("Cadastrado com sucesso!")
                except:
                    st.error("Erro: CPF já existe!")
                finally: conn.close()
            else: st.warning("Preencha os campos obrigatórios.")

# --- LÓGICA DE LISTAGEM E EDIÇÃO ---
elif choice == "📋 Lista de Registros":
    st.title("📋 Gestão de Inscritos")
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM participantes", conn)
    
    if not df.empty:
        # Filtro rápido
        busca = st.text_input("🔍 Pesquisar por Nome ou CPF")
        if busca:
            df = df[df['nome'].str.contains(busca) | df['cpf'].str.contains(busca)]
        
        st.dataframe(df, use_container_width=True)
        
        # Botão para excluir (simples)
        id_deletar = st.number_input("Digite o ID para excluir", min_value=0, step=1)
        if st.button("❌ Excluir Registro"):
            c = conn.cursor()
            c.execute(f"DELETE FROM participantes WHERE id={id_deletar}")
            conn.commit()
            st.rerun()
    conn.close()