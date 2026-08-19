from __future__ import annotations

import csv
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

from app.models.activity import Activity
from app.models.printer import Printer


class ReportService:

    @staticmethod
    def export_history_csv(path: str, printer: Printer, activities: list[Activity]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Patrimônio", "Modelo", "Serial", "Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"])
            for a in activities:
                w.writerow([
                    printer.patrimonio, printer.modelo, printer.serial,
                    a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "",
                    "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                    a.notes or "",
                    a.parts_used or "",
                    a.from_location or "",
                    a.to_location or ""
                ])

    @staticmethod
    def export_pdf(path: str, printer: Printer, activities: list[Activity], maintenance_count: int) -> None:
        # Usar página em paisagem para mais espaço
        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(A4),
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        # --- Estilos Personalizados ---
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=22,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=6,
            alignment=1  # Centralizado
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#546e7a'),
            alignment=1,
            spaceAfter=16
        )

        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=8,
            spaceBefore=12,
            borderPadding=4,
            borderWidth=0
        )

        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#37474f'),
            fontName='Helvetica-Bold'
        )

        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a237e')
        )

        # --- 1. Cabeçalho com Logo e Título ---
        # Título principal
        elements.append(Paragraph("RELATÓRIO COMPLETO DA IMPRESSORA", title_style))
        elements.append(Paragraph(f"Patrimônio: <b>{printer.patrimonio}</b>", subtitle_style))
        elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 0.3*cm))

        # Linha separadora
        elements.append(Spacer(1, 0.2*cm))

        # --- 2. SEÇÃO: DADOS GERAIS DA IMPRESSORA ---
        elements.append(Paragraph("DADOS GERAIS DA IMPRESSORA", section_title_style))
        
        # Dados em formato de grade (3 colunas para aproveitar a página paisagem)
        printer_data = [
            ["Patrimônio:", printer.patrimonio or "-", 
             "Modelo:", printer.modelo or "-",
             "Serial:", printer.serial or "-"],
            ["Marca:", printer.marca or "-", 
             "Tipo:", printer.tipo or "-",
             "Status:", printer.status or "-"],
            ["Local Atual:", printer.local_atual or "-", 
             "IP de Rede:", printer.ip_rede or "-",
             "MAC Address:", printer.mac_address or "-"],
            ["Técnico Responsável:", printer.tecnico or "-", 
             "Última Revisão:", printer.ultima_revisao.strftime("%d/%m/%Y") if printer.ultima_revisao else "-",
             "Próxima Revisão:", printer.proxima_revisao.strftime("%d/%m/%Y") if printer.proxima_revisao else "-"],
            ["Urgência:", getattr(printer, 'urgencia_prox_manutencao', 'Normal'), 
             "Total Manutenções:", str(maintenance_count),
             "Peças Faltantes:", "Sim" if printer.pecas_faltantes else "Não"],
        ]

        # Estilo da tabela de dados
        t_data = Table(printer_data, colWidths=[2.5*cm, 3.5*cm, 2.5*cm, 3.5*cm, 2.5*cm, 3.5*cm])
        t_data.setStyle(TableStyle([
            # Rótulos em cinza claro
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eceff1')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#eceff1')),
            ('BACKGROUND', (4, 0), (4, -1), colors.HexColor('#eceff1')),
            # Valores em branco
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#fafafa')),
            ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#fafafa')),
            ('BACKGROUND', (5, 0), (5, -1), colors.HexColor('#fafafa')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cfd8dc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#78909c')),
        ]))
        elements.append(t_data)
        elements.append(Spacer(1, 0.3*cm))

        # --- Observação Geral (em destaque) ---
        if printer.observacao:
            elements.append(Paragraph("OBSERVAÇÃO GERAL", section_title_style))
            # Fundo amarelo claro para destacar
            obs_text = printer.observacao.replace("\n", "<br/>")
            obs_style = ParagraphStyle(
                'ObsStyle',
                parent=value_style,
                fontSize=10,
                textColor=colors.HexColor('#1a237e'),
                backColor=colors.HexColor('#fff8e1'),
                borderPadding=8,
                borderWidth=1,
                borderColor=colors.HexColor('#ffd54f'),
                borderRadius=4
            )
            elements.append(Paragraph(obs_text, obs_style))
            elements.append(Spacer(1, 0.3*cm))

        # --- Peças Faltantes (em destaque) ---
        if printer.pecas_faltantes:
            elements.append(Paragraph("PEÇAS FALTANTES", section_title_style))
            pf_style = ParagraphStyle(
                'PFStyle',
                parent=value_style,
                fontSize=10,
                textColor=colors.HexColor('#b71c1c'),
                backColor=colors.HexColor('#ffebee'),
                borderPadding=8,
                borderWidth=1,
                borderColor=colors.HexColor('#ef5350'),
                borderRadius=4
            )
            pf_text = printer.pecas_faltantes.replace("\n", "<br/>")
            elements.append(Paragraph(pf_text, pf_style))
            elements.append(Spacer(1, 0.3*cm))

        # --- 3. SEÇÃO: HISTÓRICO DE ATIVIDADES ---
        elements.append(PageBreak())
        elements.append(Paragraph("HISTÓRICO DE ATIVIDADES", section_title_style))

        if activities:
            # Cabeçalho da tabela de atividades
            table_header = ['Data/Hora', 'Tipo', 'Descrição', 'Peças', 'De', 'Para', 'Status']
            data = [table_header]

            for a in activities:
                data.append([
                    a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-",
                    "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                    (a.notes or "")[:100],
                    (a.parts_used or "")[:80],
                    a.from_location or "-",
                    a.to_location or "-",
                    a.status_atividade or "-",
                ])

            # Estilo da tabela de histórico (mais compacta)
            t_hist = Table(data, colWidths=[3*cm, 2.5*cm, 4.5*cm, 4*cm, 2.5*cm, 2.5*cm, 2.5*cm])
            t_hist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fafafa')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fafafa'), colors.HexColor('#f5f5f5')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cfd8dc')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#78909c')),
            ]))
            elements.append(t_hist)
            
            # Rodapé com total de atividades
            elements.append(Spacer(1, 0.3*cm))
            total_style = ParagraphStyle(
                'TotalStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#546e7a'),
                alignment=2  # Direita
            )
            elements.append(Paragraph(f"Total de atividades: {len(activities)}", total_style))
        else:
            elements.append(Paragraph("Nenhuma atividade registrada para esta impressora.", value_style))

        # --- Rodapé (Função para adicionar em cada página) ---
        def add_footer(canvas_obj, doc_obj):
            canvas_obj.saveState()
            
            # Linha separadora do rodapé
            canvas_obj.setStrokeColor(colors.HexColor('#b0bec5'))
            canvas_obj.setLineWidth(0.5)
            canvas_obj.line(doc_obj.leftMargin, 1.8*cm, landscape(A4)[0] - doc_obj.rightMargin, 1.8*cm)
            
            # Textos do rodapé
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.setFillColor(colors.HexColor('#78909c'))
            
            # Número da página (direita)
            page_num = canvas_obj.getPageNumber()
            canvas_obj.drawRightString(landscape(A4)[0] - doc_obj.rightMargin, 1.2*cm, f"Página {page_num}")
            
            # Nome da empresa (esquerda)
            canvas_obj.drawString(doc_obj.leftMargin, 1.2*cm, "Brasil Toner - Recife PE")
            
            # Patrimônio no centro
            canvas_obj.drawCentredString(landscape(A4)[0] / 2, 1.2*cm, f"Patrimônio: {printer.patrimonio}")
            
            # Data de geração (abaixo)
            canvas_obj.setFont('Helvetica', 7)
            canvas_obj.setFillColor(colors.HexColor('#b0bec5'))
            canvas_obj.drawString(doc_obj.leftMargin, 0.8*cm, f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            canvas_obj.restoreState()

        # --- Build do documento ---
        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)