import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from relatorios import gerar_pdf_filtrado
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SCCUADP 2026", layout="wide", page_icon="🎫")

# CSS Personalizado (RNF 001)
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stSidebar { background-color: #001F3F; color: white; }
    div.stButton > button:first-child {
        background-color: #87CEEB; color: #001F3F; font-weight: bold; border-radius: 5px;
    }
    h1, h2, h3 { color: #001F3F; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
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

# --- SIDEBAR ---
st.sidebar.title("🎫 SCCUADP 2026")
st.sidebar.markdown("---")
menu = ["📊 Dashboard", "📝 Cadastrar", "📋 Lista e Edição"]
choice = st.sidebar.radio("Selecione uma opção:", menu)

# --- MÓDULO: DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Painel de Controlo - SCCUADP")
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM participantes", conn)
    conn.close()

    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Inscritos", len(df))
        c2.metric("Cupons Totais", int(df['qtd_cupons'].sum()))
        c3.metric("Pagos", len(df[df['pago'] == 'Pago']))
        c4.metric("Pendentes", len(df[df['pago'] == 'Pendente']))

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Situação Financeira")
            fig_pago = px.pie(df, names='pago', color='pago', 
                             color_discrete_map={'Pago':'#87CEEB', 'Pendente':'#001F3F'})
            st.plotly_chart(fig_pago, use_container_width=True)

        with col_g2:
            st.subheader("Inscritos por Unidade")
            fig_un = px.bar(df['unidade'].value_counts().reset_index(), x='unidade', y='count',
                           color_discrete_sequence=['#001F3F'])
            st.plotly_chart(fig_un, use_container_width=True)
    else:
        st.info("Aguardando dados para gerar o Dashboard...")

# --- MÓDULO: CADASTRO ---
elif choice == "📝 Cadastrar":
    st.title("📝 Registo de Participante")
    with st.form("cadastro_form"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo").upper()
            cpf = st.text_input("CPF (Apenas números)")
            unidade = st.selectbox("Unidade/Regional", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            dept = st.selectbox("Departamento", ["JGE", "AGE", "Outro"])
        with col2:
            transp = st.radio("Transporte", ["Ônibus", "Carro"])
            aloj = st.radio("Necessita Alojamento?", ["Sim", "Não"])
            bloco = st.selectbox("Retirou Bloco?", ["Sim", "Não"])
            qtd = st.number_input("Quantidade de Cupons", value=100, step=50)
            pago = st.selectbox("Status Pagamento", ["Pendente", "Pago"])
        
        if st.form_submit_button("Confirmar Registo"):
            if nome and cpf:
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO participantes (nome, cpf, unidade, departamento, transporte, alojamento, retirou_bloco, qtd_cupons, pago, data_registro) VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (nome, cpf, unidade, dept, transp, aloj, bloco, qtd, pago, datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    st.success(f"Sucesso! {nome} foi registado.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Este CPF já existe no sistema!")
                finally: conn.close()
            else: st.warning("Por favor, preencha o Nome e o CPF.")

# --- MÓDULO: LISTA, EDIÇÃO E EXPORTAÇÃO ---
# --- DENTRO DO MÓDULO: LISTA E EDIÇÃO NO app.py ---
elif choice == "📋 Lista e Edição":
    st.title("📋 Gestão e Relatórios")
    conn = get_connection()
    df_original = pd.read_sql_query("SELECT * FROM participantes", conn)
    
    if not df_original.empty:
        st.subheader("🔍 Filtros Avançados para PDF/Lista")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        with f_col1:
            f_unidade = st.multiselect("Regional", df_original['unidade'].unique())
        with f_col2:
            f_dept = st.multiselect("Departamento", df_original['departamento'].unique())
        with f_col3:
            f_transp = st.multiselect("Transporte", df_original['transporte'].unique())
        with f_col4:
            f_pago = st.multiselect("Pagamento", df_original['pago'].unique())

        # Aplicação dos filtros no DataFrame
        df_filtrado = df_original.copy()
        if f_unidade: df_filtrado = df_filtrado[df_filtrado['unidade'].isin(f_unidade)]
        if f_dept: df_filtrado = df_filtrado[df_filtrado['departamento'].isin(f_dept)]
        if f_transp: df_filtrado = df_filtrado[df_filtrado['transporte'].isin(f_transp)]
        if f_pago: df_filtrado = df_filtrado[df_filtrado['pago'].isin(f_pago)]

        st.dataframe(df_filtrado, use_container_width=True)

        # Botão para Gerar PDF
        pdf_bytes = gerar_pdf_filtrado(df_filtrado, "Filtro Personalizado")
        st.download_button(
            label="📄 Baixar Lista em PDF",
            data=pdf_bytes,
            file_name="Relatorio_SCCUADP.pdf",
            mime="application/pdf"
        )
        
        # ... (resto do código de edição/exclusão permanece o mesmo)