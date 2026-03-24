from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 31, 63) # Azul Marinho
        self.cell(0, 10, 'SCCUADP 2026 - RELATÓRIO AGRUPADO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_pdf_filtrado(df, titulo_filtro="Geral"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Ordenar os dados para o agrupamento funcionar visualmente
    # Primeiro por Unidade, depois por Departamento, depois por Nome
    df = df.sort_values(by=['unidade', 'departamento', 'nome'])

    unidades = df['unidade'].unique()

    for unidade in unidades:
        pdf.add_page()
        
        # Título da Regional (Agrupamento Principal)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(0, 31, 63) # Azul Marinho
        pdf.set_text_color(255, 255, 255) # Branco
        pdf.cell(0, 12, f"UNIDADE: {unidade.upper()}", 1, 1, 'L', True)
        pdf.ln(2)

        df_unidade = df[df['unidade'] == unidade]
        departamentos = ["AGE", "JGE", "Outro"] # Segue a ordem de importância

        for dept in departamentos:
            df_dept = df_unidade[df_unidade['departamento'] == dept]
            
            if not df_dept.empty:
                # Sub-título do Departamento
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(0, 31, 63)
                pdf.set_fill_color(135, 206, 235) # Azul Bebê
                pdf.cell(0, 8, f" Departamento: {dept}", 0, 1, 'L', True)
                
                # Cabeçalho da Tabela
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(50, 50, 50) # Cinza escuro
                
                col_widths = [80, 35, 25, 25, 25] # Nome, CPF, Transp, Pago, Cupons
                headers = ['Nome', 'CPF', 'Transp.', 'Status', 'Qtd']
                
                for i in range(len(headers)):
                    pdf.cell(col_widths[i], 8, headers[i], 1, 0, 'C', True)
                pdf.ln()

                # Dados dos Participantes
                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(0, 0, 0)
                
                for index, row in df_dept.iterrows():
                    fill = index % 2 == 0
                    pdf.set_fill_color(245, 245, 245)
                    
                    pdf.cell(col_widths[0], 7, str(row['nome'])[:40], 1, 0, 'L', fill)
                    pdf.cell(col_widths[1], 7, str(row['cpf']), 1, 0, 'C', fill)
                    pdf.cell(col_widths[2], 7, str(row['transporte']), 1, 0, 'C', fill)
                    pdf.cell(col_widths[3], 7, str(row['pago']), 1, 0, 'C', fill)
                    pdf.cell(col_widths[4], 7, str(row['qtd_cupons']), 1, 1, 'C', fill)
                
                # Resumo do Departamento
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(0, 6, f"Total em {dept}: {len(df_dept)} pessoas", 0, 1, 'R')
                pdf.ln(3)

    return bytes(pdf.output())