from fpdf import FPDF
import sqlite3
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 31, 63) # Azul Marinho
        self.cell(0, 10, 'SCCUADP 2026 - RELATÓRIO DE PARTICIPANTES', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf_filtrado(df, titulo_filtro="Geral"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Cabeçalho do Relatório
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, f"Filtro Aplicado: {titulo_filtro}", 0, 1, 'L')
    pdf.cell(0, 10, f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'L')
    pdf.ln(5)

    # Cabeçalho da Tabela
    pdf.set_fill_color(0, 31, 63) # Azul Marinho
    pdf.set_text_color(255, 255, 255) # Branco
    col_widths = [60, 30, 30, 30, 20, 25] # Nome, Regional, Dept, Transp, Pago, Cupons
    headers = ['Nome', 'Regional', 'Dept', 'Transp', 'Pago', 'Cupons']
    
    
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 10, headers[i], 1, 0, 'C', True)
    pdf.ln()

    # Dados
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', size=8)
    
    for index, row in df.iterrows():
        # Ajuste de cores alternadas para leitura fácil
        fill = index % 2 == 0
        pdf.set_fill_color(230, 240, 250)
        
        pdf.cell(col_widths[0], 8, str(row['nome'])[:30], 1, 0, 'L', fill)
        pdf.cell(col_widths[1], 8, str(row['unidade']), 1, 0, 'C', fill)
        pdf.cell(col_widths[2], 8, str(row['departamento']), 1, 0, 'C', fill)
        pdf.cell(col_widths[3], 8, str(row['transporte']), 1, 0, 'C', fill)
        pdf.cell(col_widths[4], 8, str(row['pago']), 1, 0, 'C', fill)
        pdf.cell(col_widths[5], 8, str(row['qtd_cupons']), 1, 1, 'C', fill)

    return bytes(pdf.output())