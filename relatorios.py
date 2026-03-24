from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # Logo ou Nome da Instituição
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 31, 63) # Azul Marinho
        self.cell(0, 10, 'AD PARAÍSO - SCCUADP 2026', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Relatório Oficial de Inscritos e Logística', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_pdf_filtrado(df, titulo_filtro="Geral"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    df = df.sort_values(by=['unidade', 'departamento', 'nome'])
    unidades = df['unidade'].unique()

    # --- LISTAGEM ---
    for unidade in unidades:
        pdf.add_page()
        pdf.set_fill_color(0, 31, 63)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f" REGIONAL: {unidade.upper()}", 0, 1, 'L', True)
        pdf.ln(2)

        df_unidade = df[df['unidade'] == unidade]
        for dept in ["AGE", "JGE", "Outro"]:
            df_dept = df_unidade[df_unidade['departamento'] == dept]
            if not df_dept.empty:
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(0, 31, 63)
                pdf.set_fill_color(230, 245, 255) # Azul clarinho
                pdf.cell(0, 7, f" > Departamento: {dept}", 0, 1, 'L', True)
                
                # Cabeçalho da Tabela
                pdf.set_font('Arial', 'B', 8)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(80, 80, 80)
                
                # Ajuste de larguras: Nome (75), CPF (35), Transporte (30), Status (25), Qtd (25)
                cols = [75, 35, 30, 25, 25]
                headers = ['Nome Completo', 'CPF', 'Transporte', 'Pagamento', 'Cupons']
                for i in range(len(headers)):
                    pdf.cell(cols[i], 7, headers[i], 1, 0, 'C', True)
                pdf.ln()

                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(0, 0, 0)
                for _, row in df_dept.iterrows():
                    # Colorir status de pagamento
                    pago_status = str(row['pago'])
                    pdf.cell(cols[0], 6, str(row['nome'])[:40], 1, 0, 'L')
                    pdf.cell(cols[1], 6, str(row['cpf']), 1, 0, 'C')
                    pdf.cell(cols[2], 6, str(row['transporte']), 1, 0, 'C')
                    
                    # Destaque visual para "Pago" ou "Pendente"
                    if pago_status == 'Pago':
                        pdf.set_text_color(0, 100, 0) # Verde Escuro
                    else:
                        pdf.set_text_color(150, 0, 0) # Vermelho
                        
                    pdf.cell(cols[3], 6, pago_status, 1, 0, 'C')
                    pdf.set_text_color(0, 0, 0) # Reset cor
                    pdf.cell(cols[4], 6, str(row['qtd_cupons']), 1, 1, 'C')
                pdf.ln(5)

    # --- RESUMO ESTATÍSTICO ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "CONSOLIDADO LOGÍSTICO E FINANCEIRO", 0, 1, 'C')
    pdf.ln(5)

    resumo = [
        ("Total de Inscritos", len(df), ""),
        ("Vagas de Ônibus Ocupadas", len(df[df['transporte'] == 'Ônibus']), ""),
        ("Vagas de Alojamento", len(df[df['alojamento'] == 'Sim']), ""),
        ("Arrecadação Total Estimada", f"R$ {df['qtd_cupons'].sum() * 2},00", "AZUL"),
        ("Total Já Recebido (Confirmado)", f"R$ {df[df['pago'] == 'Pago']['qtd_cupons'].sum() * 2},00", "VERDE"),
        ("Total Pendente", f"R$ {(df[df['pago'] == 'Pendente']['qtd_cupons'].sum() * 2)},00", "VERMELHO")
    ]

    for label, valor, cor in resumo:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(100, 10, f" {label}", 1, 0, 'L', True)
        
        # Cores no resumo financeiro
        if cor == "VERDE": pdf.set_text_color(0, 128, 0)
        elif cor == "VERMELHO": pdf.set_text_color(200, 0, 0)
        elif cor == "AZUL": pdf.set_text_color(0, 31, 63)
        
        pdf.cell(90, 10, str(valor), 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    # Assinaturas
    pdf.ln(30)
    y_pos = pdf.get_y()
    pdf.line(20, y_pos, 90, y_pos)
    pdf.line(110, y_pos, 180, y_pos)
    pdf.set_font('Arial', '', 8)
    pdf.set_xy(20, y_pos)
    pdf.cell(70, 5, "Responsável Local / Regional", 0, 0, 'C')
    pdf.set_xy(110, y_pos)
    pdf.cell(70, 5, "Tesouraria Geral SCCUADP", 0, 0, 'C')

    
    return bytes(pdf.output())