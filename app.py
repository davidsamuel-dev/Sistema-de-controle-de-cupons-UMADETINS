import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from relatorios import gerar_pdf_filtrado
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SCCUADP 2026", layout="wide", page_icon="🎫")

# CSS Refinado para Contraste Total (Independente de Tema Claro/Escuro)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #001F3F !important;
        border-right: 1px solid #87CEEB;
    }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        background-color: rgba(135, 206, 235, 0.1);
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        transition: 0.3s;
        border: 1px solid transparent;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background-color: rgba(135, 206, 235, 0.3);
        border: 1px solid #87CEEB;
    }
    .sidebar-title {
        color: #87CEEB !important;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 0px;
    }
    .sidebar-sub {
        color: #FFFFFF !important;
        text-align: center;
        font-size: 14px;
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        background-color: #87CEEB !important;
        color: #001F3F !important;
        font-weight: bold;
    }
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
with st.sidebar:
    st.markdown('<p class="sidebar-title">⛪ AD PARAÍSO</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-sub">SCCUADP 2026</p>', unsafe_allow_html=True)
    
    col_img1, col_img2, col_img3 = st.columns([1,2,1])
    with col_img2:
        st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=80)
    
    st.markdown("---")
    
    # IMPORTANTE: O nome aqui deve ser igual ao usado nos IFs abaixo
    choice = st.radio(
        "NAVEGAÇÃO PRINCIPAL",
        ["📊 Dashboard", "📝 Novo Cadastro", "📋 Gestão de Registros"]
    )
    
    st.markdown("---")
    st.caption("📍 Paraíso do Tocantins - TO")
    
# --- MÓDULO DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📊 Painel de Indicadores - SCCUADP 2026")
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM participantes", conn)
    conn.close()

    if not df.empty:
        valor_pago = df[df['pago'] == 'Pago']['qtd_cupons'].sum() * 2
        valor_pendente = (df[df['pago'] == 'Pendente']['qtd_cupons'].sum() * 2)
        total_onibus = len(df[df['transporte'] == 'Ônibus'])
        vagas_alojamento = len(df[df['alojamento'] == 'Sim'])
        blocos_100 = len(df[df['qtd_cupons'] == 100])
        blocos_150 = len(df[df['qtd_cupons'] == 150])
        sem_bloco = len(df[df['qtd_cupons'] == 0])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Financeiro Recebido", f"R$ {valor_pago},00")
            st.caption(f"Pendente: R$ {valor_pendente},00")
        with col2:
            st.metric("Passageiros (Ônibus)", f"{total_onibus} pessoas")
        with col3:
            st.metric("Vagas Alojamento", f"{vagas_alojamento} vagas")
        with col4:
            st.metric("Total Inscritos", len(df))

        st.markdown("---")
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            st.subheader("Distribuição de Blocos")
            dados_blocos = pd.DataFrame({
                'Tipo de Bloco': ['100 Cupons', '150 Cupons', 'Sem Bloco'],
                'Quantidade': [blocos_100, blocos_150, sem_bloco]
            })
            fig_blocos = px.bar(dados_blocos, x='Tipo de Bloco', y='Quantidade', color='Tipo de Bloco',
                               color_discrete_map={'100 Cupons':'#87CEEB', '150 Cupons':'#001F3F', 'Sem Bloco':'#C0C0C0'})
            st.plotly_chart(fig_blocos, use_container_width=True)
        with c_g2:
            st.subheader("Inscritos por Regional")
            fig_un = px.pie(df, names='unidade', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_un, use_container_width=True)
    else:
        st.info("Ainda não há dados cadastrados para exibir os indicadores.")

# --- MÓDULO CADASTRO ---
elif choice == "📝 Novo Cadastro":
    st.title("📝 Novo Cadastro de Participante")
    with st.form("cadastro_form"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo").upper()
            cpf = st.text_input("CPF (Apenas números)")
            unidade = st.selectbox("Unidade/Regional", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            dept = st.selectbox("Departamento", ["JGE", "AGE", "Outro"])
        with col2:
            qtd = st.selectbox("Quantidade de Cupons", [100, 150, 0], help="100 (Carro) / 150 (Ônibus)")
            transp = "Ônibus" if qtd == 150 else "Carro"
            valor_total = qtd * 2
            aloj = st.radio("Necessita Alojamento?", ["Sim", "Não"])
            bloco = st.selectbox("Retirou Bloco?", ["Sim", "Não"])
            pago = st.selectbox("Status Pagamento", ["Pendente", "Pago"])

        if st.form_submit_button("Confirmar Registro"):
            if nome and cpf:
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""INSERT INTO participantes 
                              (nome, cpf, unidade, departamento, transporte, alojamento, retirou_bloco, qtd_cupons, pago, data_registro) 
                              VALUES (?,?,?,?,?,?,?,?,?,?)""",
                              (nome, cpf, unidade, dept, transp, aloj, bloco, qtd, pago, datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {nome} registrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Este CPF já existe!")
            else:
                st.warning("Preencha Nome e CPF.")

# --- MÓDULO GESTÃO (LISTA E EDIÇÃO) ---
elif choice == "📋 Gestão de Registros":
    st.title("📋 Gestão e Relatórios")
    conn = get_connection()
    df_original = pd.read_sql_query("SELECT * FROM participantes", conn)
    
    if not df_original.empty:
        st.subheader("🔍 Filtros para PDF")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1: f_unidade = st.multiselect("Regional", df_original['unidade'].unique())
        with f_col2: f_dept = st.multiselect("Departamento", df_original['departamento'].unique())
        with f_col3: f_transp = st.multiselect("Transporte", df_original['transporte'].unique())
        with f_col4: f_pago = st.multiselect("Pagamento", df_original['pago'].unique())

        df_filtrado = df_original.copy()
        if f_unidade: df_filtrado = df_filtrado[df_filtrado['unidade'].isin(f_unidade)]
        if f_dept: df_filtrado = df_filtrado[df_filtrado['departamento'].isin(f_dept)]
        if f_transp: df_filtrado = df_filtrado[df_filtrado['transporte'].isin(f_transp)]
        if f_pago: df_filtrado = df_filtrado[df_filtrado['pago'].isin(f_pago)]

        st.dataframe(df_filtrado, use_container_width=True)

        pdf_output = gerar_pdf_filtrado(df_filtrado, "Relatório Filtrado")
        st.download_button(label="📄 Baixar Lista em PDF", data=pdf_output, 
                           file_name=f"Relatorio_SCCUADP.pdf", mime="application/pdf")
        
        st.markdown("---")
        id_del = st.number_input("ID para excluir", min_value=0, step=1)
        if st.button("❌ Excluir"):
            c = conn.cursor()
            c.execute("DELETE FROM participantes WHERE id=?", (id_del,))
            conn.commit()
            conn.close()
            st.rerun()
    else:
        st.info("Banco de dados vazio.")
    conn.close()