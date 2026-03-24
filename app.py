import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA E IDENTIDADE VISUAL (RNF 001) ---
st.set_page_config(page_title="SCCUADP 2026", layout="wide")

st.markdown(f"""
    <style>
    .main {{ background-color: #FFFFFF; }}
    .stSidebar {{ background-color: #001F3F; color: white; }}
    div.stButton > button:first-child {{
        background-color: #87CEEB;
        color: #001F3F;
        font-weight: bold;
        border-radius: 5px;
    }}
    h1, h2, h3 {{ color: #001F3F; }}
    </style>
    """, unsafe_allow_stdio=True)

# --- FUNÇÕES DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('sccuadp_2026.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT UNIQUE NOT NULL,
                    unidade TEXT,
                    departamento TEXT,
                    transporte TEXT,
                    alojamento TEXT,
                    retirou_bloco TEXT,
                    qtd_cupons INTEGER,
                    pago TEXT,
                    data_registro TIMESTAMP)''')
    conn.commit()
    conn.close()

def salvar_participante(dados):
    try:
        conn = sqlite3.connect('sccuadp_2026.db')
        c = conn.cursor()
        c.execute('''INSERT INTO participantes 
                  (nome, cpf, unidade, departamento, transporte, alojamento, retirou_bloco, qtd_cupons, pago, data_registro) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

init_db()

# --- INTERFACE ---
st.title("🎫 SCCUADP 2026 - Controle de Cupons")
st.subheader("Assembleia de Deus Nação Madureira (Paraíso - TO)")

menu = ["Cadastrar", "Visualizar Registros", "Dashboard"]
choice = st.sidebar.selectbox("Menu de Navegação", menu)

if choice == "Cadastrar":
    st.markdown("### 📝 Novo Cadastro de Participante")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF (Somente números)")
            unidade = st.selectbox("Origem", ["Matriz", "Regional 1", "Regional 2", "Regional 3", "Regional 4", "Regional 5", "Regional 6"])
            departamento = st.selectbox("Departamento", ["JGE", "AGE", "Outro"])
        
        with col2:
            transporte = st.radio("Transporte", ["Ônibus", "Carro"])
            alojamento = st.radio("Necessita Alojamento?", ["Sim", "Não"])
            retirou_bloco = st.selectbox("Retirou Bloco?", ["Sim", "Não"])
            qtd_cupons = st.number_input("Quantidade de Cupons", min_value=0, step=50, value=100)
            pago = st.selectbox("Status de Pagamento", ["Pendente", "Pago"])

        submit = st.form_submit_button("Finalizar Cadastro")

    if submit:
        if nome and cpf:
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            dados = (nome.upper(), cpf, unidade, departamento, transporte, alojamento, retirou_bloco, qtd_cupons, pago, agora)
            
            sucesso = salvar_participante(dados)
            if sucesso:
                st.success(f"✅ {nome} cadastrado com sucesso!")
            else:
                st.error("❌ Erro: Este CPF já está cadastrado no sistema.")
        else:
            st.warning("⚠️ Por favor, preencha Nome e CPF.")

elif choice == "Visualizar Registros":
    st.markdown("### 📋 Participantes Cadastrados")
    conn = sqlite3.connect('sccuadp_2026.db')
    df = pd.read_sql_query("SELECT * FROM participantes", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
