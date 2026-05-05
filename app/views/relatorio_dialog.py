from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QRadioButton, QCheckBox, QGroupBox,
    QLineEdit, QScrollArea, QWidget, QFrame, QCompleter
)
from PySide6.QtCore import Qt
from datetime import datetime as dt
import os

class RelatorioDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("📊 Gerar Relatório")
        self.setMinimumSize(480, 580)
        self.setMaximumSize(480, 750)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel { color: #c0c0d0; font-size: 12px; background: transparent; }
            QGroupBox { 
                color: #89b4fa; font-weight: bold; 
                border: 2px solid #533483; border-radius: 10px; 
                margin-top: 12px; padding: 18px 12px 12px 12px; 
                font-size: 14px; background-color: #1a1a2e;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; left: 12px; padding: 0 8px; 
                background-color: #1a1a2e; color: #89b4fa;
            }
            QRadioButton, QCheckBox { 
                color: #e0e0e0; font-size: 13px; spacing: 8px; 
                padding: 4px 2px; background: transparent;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 16px; height: 16px; 
                border: 2px solid #89b4fa; 
                background-color: #0f3460;
            }
            QRadioButton::indicator { border-radius: 8px; }
            QCheckBox::indicator { border-radius: 3px; }
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                background-color: #e94560; border-color: #e94560;
            }
            QComboBox { 
                background-color: #0f3460; color: white; 
                border: 2px solid #533483; border-radius: 6px; 
                padding: 7px 12px; font-size: 13px; min-height: 20px;
            }
            QComboBox:hover { border-color: #89b4fa; }
            QComboBox QAbstractItemView {
                background-color: #0f3460; color: white;
                selection-background-color: #533483;
                border: 1px solid #533483; outline: none;
            }
            QComboBox QAbstractItemView::item { padding: 6px 12px; }
            QComboBox QAbstractItemView::item:hover { background-color: #e94560; }
            QLineEdit { 
                background-color: #0f3460; color: white; 
                border: 2px solid #533483; border-radius: 6px; 
                padding: 7px 12px; font-size: 13px;
            }
            QLineEdit:hover { border-color: #89b4fa; }
            QLineEdit:focus { border-color: #e94560; }
            QPushButton { border: none; border-radius: 6px; padding: 10px 22px; font-size: 14px; font-weight: bold; }
            QScrollArea { border: none; background-color: #1a1a2e; }
            QScrollBar:vertical { background: #0f3460; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #533483; border-radius: 4px; min-height: 25px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.init_ui()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #1a1a2e; border: none; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: #1a1a2e;")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)
        
        titulo = QLabel("📊 Configurações do Relatório")
        titulo.setStyleSheet("color: #e94560; font-size: 18px; font-weight: bold; background: transparent;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #533483; max-height: 2px;")
        layout.addWidget(sep)
        layout.addSpacing(5)
        
        # TIPO DE RELATÓRIO
        grupo_tipo = QGroupBox("Tipo de Relatório")
        tipo_layout = QVBoxLayout(grupo_tipo)
        tipo_layout.setSpacing(6)
        self.rb_impressoras = QRadioButton("🖨️  Impressoras")
        self.rb_atividades = QRadioButton("📋  Atividades / Ordens de Serviço")
        self.rb_impressoras.setChecked(True)
        tipo_layout.addWidget(self.rb_impressoras)
        tipo_layout.addWidget(self.rb_atividades)
        layout.addWidget(grupo_tipo)
        
        # FILTROS
        grupo_filtro = QGroupBox("🔍 Filtros")
        filtro_layout = QVBoxLayout(grupo_filtro)
        filtro_layout.setSpacing(8)
        
        filtro_layout.addWidget(QLabel("Status da Impressora:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Operacional", "Em uso", "Em manutenção", "Manutenção", "Parada", "Aguardando peça", "Sucata"])
        self.status_combo.currentTextChanged.connect(self._atualizar_patrimonios)
        filtro_layout.addWidget(self.status_combo)
        
        filtro_layout.addWidget(QLabel("Patrimônio Específico:"))
        self.pat_input = QLineEdit()
        self.pat_input.setPlaceholderText("Deixe em branco ou digite para buscar...")
        self.pat_input.textChanged.connect(self._ao_selecionar_patrimonio)
        filtro_layout.addWidget(self.pat_input)
        
        filtro_layout.addWidget(QLabel("Modelo:"))
        self.modelo_combo = QComboBox()
        self.modelo_combo.addItem("Todos")
        from models import Printer
        modelos = self.session.query(Printer.modelo).filter(Printer.modelo != "").distinct().order_by(Printer.modelo).all()
        for m in modelos:
            if m[0]:
                self.modelo_combo.addItem(m[0])
        filtro_layout.addWidget(self.modelo_combo)
        
        filtro_layout.addWidget(QLabel("Local / Empresa:"))
        self.local_combo = QComboBox()
        self.local_combo.addItem("Todos")
        from models import Company
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            self.local_combo.addItem(emp.nome)
        filtro_layout.addWidget(self.local_combo)
        
        layout.addWidget(grupo_filtro)
        
        # FORMATO
        grupo_saida = QGroupBox("📁 Formato de Saída")
        saida_layout = QVBoxLayout(grupo_saida)
        saida_layout.setSpacing(6)
        self.rb_pdf = QRadioButton("📄  PDF - Relatório formatado")
        self.rb_excel = QRadioButton("📊  Excel - Planilha editável")
        self.rb_pdf.setChecked(True)
        saida_layout.addWidget(self.rb_pdf)
        saida_layout.addWidget(self.rb_excel)
        layout.addWidget(grupo_saida)
        
        # OPÇÕES
        grupo_extra = QGroupBox("⚙️ Opções Adicionais")
        extra_layout = QVBoxLayout(grupo_extra)
        extra_layout.setSpacing(6)
        self.cb_detalhado = QCheckBox("📋 Incluir histórico completo (apenas PDF)")
        extra_layout.addWidget(self.cb_detalhado)
        self.cb_abrir = QCheckBox("📂 Abrir arquivo ao gerar")
        self.cb_abrir.setChecked(True)
        extra_layout.addWidget(self.cb_abrir)
        layout.addWidget(grupo_extra)
        layout.addSpacing(10)
        
        # BOTÕES
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_gerar = QPushButton("🚀 Gerar Relatório")
        btn_gerar.setCursor(Qt.PointingHandCursor)
        btn_gerar.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #1a1a2e; } QPushButton:hover { background-color: #94d89f; }")
        btn_gerar.clicked.connect(self.gerar_relatorio)
        btn_layout.addWidget(btn_gerar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #e94560; color: white; } QPushButton:hover { background-color: #d63850; }")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        layout.addSpacing(10)
        
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        self._atualizar_patrimonios()

    def _atualizar_patrimonios(self):
        from models import Printer
        status = self.status_combo.currentText()
        query = self.session.query(Printer)
        if status != "Todos":
            query = query.filter(Printer.status == status)
        patrimonios = [p.patrimonio for p in query.order_by(Printer.patrimonio).all()]
        completer = QCompleter(patrimonios)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.pat_input.setCompleter(completer)
    
    def _ao_selecionar_patrimonio(self, texto):
        from models import Printer
        status = self.status_combo.currentText()
        query = self.session.query(Printer)
        if status != "Todos":
            query = query.filter(Printer.status == status)
        if texto.strip():
            query = query.filter(Printer.patrimonio.like(f"%{texto.strip()}%"))
        patrimonios = [p.patrimonio for p in query.order_by(Printer.patrimonio).all()]
        completer = QCompleter(patrimonios)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.pat_input.setCompleter(completer)
        
        if texto.strip():
            printer = self.session.query(Printer).filter(Printer.patrimonio == texto.strip()).first()
            if printer:
                if printer.modelo:
                    idx = self.modelo_combo.findText(printer.modelo)
                    if idx >= 0: self.modelo_combo.setCurrentIndex(idx)
                if printer.local_atual:
                    idx = self.local_combo.findText(printer.local_atual)
                    if idx >= 0: self.local_combo.setCurrentIndex(idx)
                if printer.status:
                    idx = self.status_combo.findText(printer.status)
                    if idx >= 0: self.status_combo.setCurrentIndex(idx)
    
    def gerar_relatorio(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from app.services.relatorio_service import RelatorioService
        from models import Printer, Activity
        
        status_filtro = self.status_combo.currentText()
        patrimonio = self.pat_input.text().strip()
        modelo = self.modelo_combo.currentText()
        local = self.local_combo.currentText()
        formato = 'pdf' if self.rb_pdf.isChecked() else 'xlsx'
        detalhado = self.cb_detalhado.isChecked()
        abrir = self.cb_abrir.isChecked()
        tipo_rel = 'impressoras' if self.rb_impressoras.isChecked() else 'atividades'
        
        sufixo = f"_{patrimonio}" if patrimonio else ""
        nome_padrao = f"relatorio_{tipo_rel}{sufixo}_{dt.now().strftime('%Y%m%d_%H%M%S')}.{formato}"
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório", nome_padrao, f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})")
        if not filepath: return
        
        try:
            if tipo_rel == 'impressoras':
                query = self.session.query(Printer)
                if status_filtro != "Todos": query = query.filter(Printer.status == status_filtro)
                if patrimonio: query = query.filter(Printer.patrimonio.like(f"%{patrimonio}%"))
                if modelo != "Todos": query = query.filter(Printer.modelo == modelo)
                if local != "Todos": query = query.filter(Printer.local_atual.like(f"%{local}%"))
                printers = query.order_by(Printer.patrimonio).all()
                if not printers: QMessageBox.warning(self, "Aviso", "Nenhuma impressora encontrada!"); return
                if formato == 'pdf' and detalhado: self._gerar_pdf_detalhado(printers, filepath)
                elif formato == 'pdf': RelatorioService.exportar_impressoras_pdf(printers, filepath)
                else: RelatorioService.exportar_impressoras_excel(printers, filepath)
            else:
                query = self.session.query(Activity)
                if patrimonio:
                    ids = [p.id for p in self.session.query(Printer).filter(Printer.patrimonio.like(f"%{patrimonio}%")).all()]
                    if ids: query = query.filter(Activity.printer_id.in_(ids))
                atividades = query.order_by(Activity.event_at.desc()).limit(500).all()
                if not atividades: QMessageBox.warning(self, "Aviso", "Nenhuma atividade encontrada!"); return
                if formato == 'pdf': RelatorioService.exportar_atividades_pdf(atividades, filepath)
                else: RelatorioService.exportar_atividades_excel(atividades, filepath)
            if abrir: os.startfile(filepath)
            QMessageBox.information(self, "Sucesso", f"Relatório gerado com sucesso!\n\n{filepath}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório:\n\n{str(e)}")

    def _gerar_pdf_detalhado(self, printers, filepath):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from models import Activity
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=45)
        styles = getSampleStyleSheet()
        cor_primaria = colors.HexColor("#1A3C6C")
        cor_fundo_zebra = colors.HexColor("#F8F9FA")
        elements = []
        
        for idx, p in enumerate(printers):
            elements.append(Spacer(1, 40))
            
            style_title = styles["Title"]
            style_title.textColor = cor_primaria
            style_title.fontSize = 18
            elements.append(Paragraph(f"Relatório de Impressora - Patrimônio: {p.patrimonio}", style_title))
            elements.append(Spacer(1, 20))
            
            maint_count = self.session.query(Activity).filter(Activity.printer_id == p.id, Activity.kind == "MANUTENCAO").count()
            
            header_data = [
                ["Patrimônio", p.patrimonio or "-"],
                ["Modelo", p.modelo or "-"],
                ["Serial", p.serial or "-"],
                ["Status", p.status or "-"],
                ["Peças Faltantes", p.pecas_faltantes or "-"],
                ["Local atual", p.local_atual or "-"],
                ["Contador de Manutenções", str(maint_count)],
                ["Última Revisão", p.proxima_revisao.strftime("%d/%m/%Y") if p.proxima_revisao else "-"],
                ["Técnico Revisor", p.tecnico or "-"]
            ]
            
            t_header = Table(header_data, colWidths=[140, 380])
            t_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), cor_fundo_zebra),
                ('TEXTCOLOR', (0, 0), (0, -1), cor_primaria),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(t_header)
            elements.append(Spacer(1, 20))
            
            if (p.observacao or "").strip():
                elements.append(Paragraph("<b>Observação geral:</b>", styles["Normal"]))
                elements.append(Paragraph((p.observacao or "").replace("\n", "<br/>"), styles["BodyText"]))
                elements.append(Spacer(1, 15))
            
            elements.append(Paragraph("<b>Histórico de atividades:</b>", styles["Normal"]))
            elements.append(Spacer(1, 8))
            
            atividades = self.session.query(Activity).filter(Activity.printer_id == p.id).order_by(Activity.event_at.desc()).limit(15).all()
            
            data_hist = [["Data/Hora", "Tipo", "Descrição", "Peças", "De", "Para"]]
            for a in atividades:
                desc = Paragraph((a.notes or "")[:1200], styles["BodyText"])
                pecas = Paragraph((a.parts_used or "")[:400], styles["BodyText"])
                data_hist.append([
                    a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else "-",
                    "Manutenção" if a.kind == "MANUTENCAO" else "Movimentação",
                    desc, pecas,
                    a.from_location or "-", a.to_location or "-",
                ])
            
            t_hist = Table(data_hist, colWidths=[75, 75, 170, 90, 55, 55], repeatRows=1)
            t_hist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cor_fundo_zebra]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t_hist)
            elements.append(Spacer(1, 20))
            
            from reportlab.platypus.flowables import HRFlowable
            from reportlab.lib.enums import TA_CENTER
            line = HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e94560'))
            elements.append(line)
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(
                f"Gerado em: {dt.now().strftime('%d/%m/%Y %H:%M')} | Controle de Impressoras Pro v2.0",
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.gray, alignment=TA_CENTER)
            ))
            
            if idx < len(printers) - 1:
                elements.append(PageBreak())
        
        doc.build(elements)