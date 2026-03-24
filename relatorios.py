from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 31, 63) # Azul Marinho
        self.cell(0, 10, 'SCCUADP 2026 - RELATÓRIO OFICIAL', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_pdf_filtrado(df, titulo_filtro="Geral"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Ordenação para o agrupamento
    df = df.sort_values(by=['unidade', 'departamento', 'nome'])
    unidades = df['unidade'].unique()

    # --- PARTE 1: LISTAGEM DETALHADA ---
    for unidade in unidades:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(0, 31, 63)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 12, f"UNIDADE: {unidade.upper()}", 1, 1, 'L', True)
        pdf.ln(2)

        df_unidade = df[df['unidade'] == unidade]
        for dept in ["AGE", "JGE", "Outro"]:
            df_dept = df_unidade[df_unidade['departamento'] == dept]
            if not df_dept.empty:
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(0, 31, 63)
                pdf.set_fill_color(135, 206, 235)
                pdf.cell(0, 8, f" Departamento: {dept}", 0, 1, 'L', True)
                
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(50, 50, 50)
                col_widths = [80, 35, 25, 25, 25]
                headers = ['Nome', 'CPF', 'Transp.', 'Status', 'Qtd']
                for i in range(len(headers)):
                    pdf.cell(col_widths[i], 8, headers[i], 1, 0, 'C', True)
                pdf.ln()

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
                pdf.ln(2)

    # --- PARTE 2: MINI-DASHBOARD FINAL (Resumo Estatístico) ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 31, 63)
    pdf.cell(0, 15, "RESUMO ESTATÍSTICO DO RELATÓRIO", 0, 1, 'C')
    pdf.ln(5)

    # Cálculos baseados nos filtros aplicados
    total_inscritos = len(df)
    total_onibus = len(df[df['transporte'] == 'Ônibus'])
    total_alojamento = len(df[df['alojamento'] == 'Sim'])
    valor_total = df['qtd_cupons'].sum() * 2
    valor_pago = df[df['pago'] == 'Pago']['qtd_cupons'].sum() * 2
    valor_pendente = valor_total - valor_pago

    # Tabela de Totais Gerais
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(95, 10, "Indicador", 1, 0, 'C', True)
    pdf.cell(95, 10, "Quantidade / Valor", 1, 1, 'C', True)

    pdf.set_font('Arial', '', 11)
    resumo_dados = [
        ("Total de Inscritos", f"{total_inscritos}"),
        ("Passageiros de Ônibus", f"{total_onibus}"),
        ("Vagas de Alojamento", f"{total_alojamento}"),
        ("Valor Total Estimado", f"R$ {valor_total},00"),
        ("Valor Já Recebido", f"R$ {valor_pago},00"),
        ("Valor Pendente", f"R$ {valor_pendente},00")
    ]

    for label, value in resumo_dados:
        pdf.cell(95, 10, label, 1, 0, 'L')
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(95, 10, value, 1, 1, 'R')
        pdf.set_font('Arial', '', 11)

    pdf.ln(10)
    # Espaço para Assinatura do Responsável
    pdf.ln(20)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Assinatura do Responsável SCCUADP", 0, 1, 'C')

    return bytes(pdf.output())