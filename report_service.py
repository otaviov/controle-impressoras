from __future__ import annotations

from datetime import datetime
import csv

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


class ReportService:
    @staticmethod
    def export_history_csv(path: str, printer, activities):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Patrimônio", "Modelo", "Serial", "Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"])
            for a in activities:
                w.writerow([
                    printer.patrimonio, printer.modelo, printer.serial,
                    a.event_at.strftime("%d/%m/%Y %H:%M"),
                    "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                    a.notes or "",
                    a.parts_used or "",
                    a.from_location or "",
                    a.to_location or ""
                ])

    @staticmethod
    def export_pdf(path: str, printer, activities, maintenance_count: int):
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
        elems = []

        elems.append(Paragraph("Relatório de Impressora", styles["Title"]))
        elems.append(Spacer(1, 12))

        header = [
            ["Patrimônio", printer.patrimonio or "-"],
            ["Modelo", printer.modelo or "-"],
            ["Serial", printer.serial or "-"],
            ["Status", printer.status or "-"],
            ["Local atual", printer.local_atual or "-"],
            ["Manutenções (contador)", str(maintenance_count)],
        ]
        t_header = Table(header, colWidths=[130, 360])
        t_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elems.append(t_header)
        elems.append(Spacer(1, 14))

        if (printer.observacao or "").strip():
            elems.append(Paragraph("Observação geral:", styles["Heading3"]))
            elems.append(Paragraph((printer.observacao or "").replace("\n", "<br/>"), styles["BodyText"]))
            elems.append(Spacer(1, 10))

        elems.append(Paragraph("Histórico de atividades:", styles["Heading3"]))
        elems.append(Spacer(1, 6))

        data = [["Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"]]
        for a in activities:
            data.append([
                a.event_at.strftime("%d/%m/%Y %H:%M"),
                "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                (a.notes or "")[:1200],
                (a.parts_used or "")[:400],
                a.from_location or "",
                a.to_location or "",
            ])

        t = Table(data, colWidths=[75, 70, 170, 90, 55, 55])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elems.append(t)

        elems.append(Spacer(1, 10))
        elems.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))

        doc.build(elems)
