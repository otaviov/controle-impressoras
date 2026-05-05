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
        
        # Título
        titulo = QLabel("📊 Configurações do Relatório")
        titulo.setStyleSheet("color: #e94560; font-size: 18px; font-weight: bold; background: transparent;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #533483; max-height: 2px;")
        layout.addWidget(sep)
        layout.addSpacing(5)
        
        # ====== TIPO DE RELATÓRIO ======
        grupo_tipo = QGroupBox("Tipo de Relatório")
        tipo_layout = QVBoxLayout(grupo_tipo)
        tipo_layout.setSpacing(6)
        
        self.rb_impressoras = QRadioButton("🖨️  Impressoras")
        self.rb_atividades = QRadioButton("📋  Atividades / Ordens de Serviço")
        self.rb_impressoras.setChecked(True)
        tipo_layout.addWidget(self.rb_impressoras)
        tipo_layout.addWidget(self.rb_atividades)
        layout.addWidget(grupo_tipo)
        
        # ====== FILTROS ======
        grupo_filtro = QGroupBox("🔍 Filtros")
        filtro_layout = QVBoxLayout(grupo_filtro)
        filtro_layout.setSpacing(8)
        
        # Status
        filtro_layout.addWidget(QLabel("Status da Impressora:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Operacional", "Em uso", "Em manutenção", "Manutenção", "Parada", "Aguardando peça", "Sucata"])
        self.status_combo.currentTextChanged.connect(self._atualizar_patrimonios)
        filtro_layout.addWidget(self.status_combo)
        
        # Patrimônio
        filtro_layout.addWidget(QLabel("Patrimônio Específico:"))
        self.pat_input = QLineEdit()
        self.pat_input.setPlaceholderText("Deixe em branco ou digite para buscar...")
        self.pat_input.textChanged.connect(self._ao_selecionar_patrimonio)
        filtro_layout.addWidget(self.pat_input)
        
        # Modelo
        filtro_layout.addWidget(QLabel("Modelo:"))
        self.modelo_combo = QComboBox()
        self.modelo_combo.addItem("Todos")
        from models import Printer
        modelos = self.session.query(Printer.modelo).filter(Printer.modelo != "").distinct().order_by(Printer.modelo).all()
        for m in modelos:
            if m[0]:
                self.modelo_combo.addItem(m[0])
        filtro_layout.addWidget(self.modelo_combo)
        
        # Local
        filtro_layout.addWidget(QLabel("Local / Empresa:"))
        self.local_combo = QComboBox()
        self.local_combo.addItem("Todos")
        from models import Company
        empresas = self.session.query(Company).order_by(Company.nome).all()
        for emp in empresas:
            self.local_combo.addItem(emp.nome)
        filtro_layout.addWidget(self.local_combo)
        
        layout.addWidget(grupo_filtro)
        
        # ====== FORMATO ======
        grupo_saida = QGroupBox("📁 Formato de Saída")
        saida_layout = QVBoxLayout(grupo_saida)
        saida_layout.setSpacing(6)
        
        self.rb_pdf = QRadioButton("📄  PDF - Relatório formatado")
        self.rb_excel = QRadioButton("📊  Excel - Planilha editável")
        self.rb_pdf.setChecked(True)
        saida_layout.addWidget(self.rb_pdf)
        saida_layout.addWidget(self.rb_excel)
        layout.addWidget(grupo_saida)
        
        # ====== OPÇÕES ======
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
        
        # ====== BOTÕES ======
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
        
        # Carrega autocomplete inicial
        self._atualizar_patrimonios()
    
    def _atualizar_patrimonios(self):
        """Atualiza o autocomplete baseado no status selecionado"""
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
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", nome_padrao,
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return
        
        try:
            if tipo_rel == 'impressoras':
                query = self.session.query(Printer)
                if status_filtro != "Todos":
                    query = query.filter(Printer.status == status_filtro)
                if patrimonio:
                    query = query.filter(Printer.patrimonio.like(f"%{patrimonio}%"))
                if modelo != "Todos":
                    query = query.filter(Printer.modelo == modelo)
                if local != "Todos":
                    query = query.filter(Printer.local_atual.like(f"%{local}%"))
                
                printers = query.order_by(Printer.patrimonio).all()
                
                if not printers:
                    QMessageBox.warning(self, "Aviso", "Nenhuma impressora encontrada!")
                    return
                
                if formato == 'pdf' and detalhado:
                    self._gerar_pdf_detalhado(printers, filepath)
                elif formato == 'pdf':
                    RelatorioService.exportar_impressoras_pdf(printers, filepath)
                else:
                    RelatorioService.exportar_impressoras_excel(printers, filepath)
            else:
                query = self.session.query(Activity)
                if patrimonio:
                    ids = [p.id for p in self.session.query(Printer).filter(Printer.patrimonio.like(f"%{patrimonio}%")).all()]
                    if ids:
                        query = query.filter(Activity.printer_id.in_(ids))
                
                atividades = query.order_by(Activity.event_at.desc()).limit(500).all()
                if not atividades:
                    QMessageBox.warning(self, "Aviso", "Nenhuma atividade encontrada!")
                    return
                
                if formato == 'pdf':
                    RelatorioService.exportar_atividades_pdf(atividades, filepath)
                else:
                    RelatorioService.exportar_atividades_excel(atividades, filepath)
            
            if abrir:
                os.startfile(filepath)
            
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
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=14, textColor=colors.HexColor('#e94560'), spaceAfter=8)
        
        for printer in printers:
            elements.append(Paragraph(f"Relatório - Patrimônio: {printer.patrimonio} - {printer.modelo}", title_style))
            elements.append(Spacer(1, 6))
            
            dados = [
                ["Patrimônio", printer.patrimonio, "Modelo", printer.modelo],
                ["Serial", printer.serial or '-', "Marca", printer.marca or '-'],
                ["Status", printer.status, "Local", printer.local_atual or '-'],
                ["IP Rede", printer.ip_rede or '-', "Técnico", printer.tecnico or '-'],
            ]
            t = Table(dados, colWidths=[90, 200, 90, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#533483')),
                ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#533483')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#533483')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#533483')),
            ]))
            elements.append(t)
            
            if printer.observacao:
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>Obs:</b> {printer.observacao}", styles['Normal']))
            
            if printer.pecas_faltantes:
                elements.append(Paragraph(f"<b>⚠️ Peças Faltantes:</b> {printer.pecas_faltantes}", styles['Normal']))
            
            atividades = self.session.query(Activity).filter(
                Activity.printer_id == printer.id
            ).order_by(Activity.event_at.desc()).limit(10).all()
            
            if atividades:
                elements.append(Spacer(1, 6))
                elements.append(Paragraph("<b>Últimas Atividades:</b>", styles['Heading4']))
                
                hist_data = [['Data', 'Tipo', 'Descrição', 'Peças']]
                for a in atividades:
                    hist_data.append([
                        a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else '-',
                        'Manut.' if a.kind == 'MANUTENCAO' else 'Movim.',
                        (a.notes or '-')[:80],
                        a.parts_used or '-'
                    ])
                
                th = Table(hist_data, colWidths=[70, 50, 320, 100])
                th.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('PADDING', (0, 0), (-1, -1), 3),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#533483')),
                ]))
                elements.append(th)
            
            elements.append(PageBreak())
        
        doc.build(elements)

    def _ao_selecionar_patrimonio(self, texto):
        """Quando digita um patrimônio, filtra o autocomplete e preenche modelo/local"""
        # Atualiza o completer para filtrar enquanto digita
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
        
        # Se digitou exatamente um patrimônio, preenche modelo e local
        if texto.strip():
            printer = self.session.query(Printer).filter(Printer.patrimonio == texto.strip()).first()
            if printer:
                if printer.modelo:
                    idx = self.modelo_combo.findText(printer.modelo)
                    if idx >= 0:
                        self.modelo_combo.setCurrentIndex(idx)
                
                if printer.local_atual:
                    idx = self.local_combo.findText(printer.local_atual)
                    if idx >= 0:
                        self.local_combo.setCurrentIndex(idx)
                
                # Atualiza o status para o status real da impressora
                if printer.status:
                    idx = self.status_combo.findText(printer.status)
                    if idx >= 0:
                        self.status_combo.setCurrentIndex(idx)
    
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
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", nome_padrao,
            f"{'PDF' if formato == 'pdf' else 'Excel'} (*.{formato})"
        )
        if not filepath:
            return
        
        try:
            if tipo_rel == 'impressoras':
                query = self.session.query(Printer)
                if status_filtro != "Todos":
                    query = query.filter(Printer.status == status_filtro)
                if patrimonio:
                    query = query.filter(Printer.patrimonio.like(f"%{patrimonio}%"))
                if modelo != "Todos":
                    query = query.filter(Printer.modelo == modelo)
                if local != "Todos":
                    query = query.filter(Printer.local_atual.like(f"%{local}%"))
                
                printers = query.order_by(Printer.patrimonio).all()
                
                if not printers:
                    QMessageBox.warning(self, "Aviso", "Nenhuma impressora encontrada!")
                    return
                
                if formato == 'pdf' and detalhado:
                    self._gerar_pdf_detalhado(printers, filepath)
                elif formato == 'pdf':
                    RelatorioService.exportar_impressoras_pdf(printers, filepath)
                else:
                    RelatorioService.exportar_impressoras_excel(printers, filepath)
            else:
                query = self.session.query(Activity)
                if patrimonio:
                    ids = [p.id for p in self.session.query(Printer).filter(Printer.patrimonio.like(f"%{patrimonio}%")).all()]
                    if ids:
                        query = query.filter(Activity.printer_id.in_(ids))
                
                atividades = query.order_by(Activity.event_at.desc()).limit(500).all()
                if not atividades: 
                    QMessageBox.warning(self, "Aviso", "Nenhuma atividade encontrada!")
                    return
                
                if formato == 'pdf':
                    RelatorioService.exportar_atividades_pdf(atividades, filepath)
                else:
                    RelatorioService.exportar_atividades_excel(atividades, filepath)
            
            if abrir:
                os.startfile(filepath)
            
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
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        elements = []
        
        title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=14, textColor=colors.HexColor('#e94560'), spaceAfter=8)
        
        for printer in printers:
            elements.append(Paragraph(f"Relatório - Patrimônio: {printer.patrimonio} - {printer.modelo}", title_style))
            elements.append(Spacer(1, 6))
            
            dados = [
                ["Patrimônio", printer.patrimonio, "Modelo", printer.modelo],
                ["Serial", printer.serial or '-', "Marca", printer.marca or '-'],
                ["Status", printer.status, "Local", printer.local_atual or '-'],
                ["IP Rede", printer.ip_rede or '-', "Técnico", printer.tecnico or '-'],
            ]
            t = Table(dados, colWidths=[90, 200, 90, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#533483')),
                ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#533483')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#533483')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#533483')),
            ]))
            elements.append(t)
            
            if printer.observacao:
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>Obs:</b> {printer.observacao}", styles['Normal']))
            
            if printer.pecas_faltantes:
                elements.append(Paragraph(f"<b>⚠️ Peças Faltantes:</b> {printer.pecas_faltantes}", styles['Normal']))
            
            atividades = self.session.query(Activity).filter(
                Activity.printer_id == printer.id
            ).order_by(Activity.event_at.desc()).limit(10).all()
            
            if atividades:
                elements.append(Spacer(1, 6))
                elements.append(Paragraph("<b>Últimas Atividades:</b>", styles['Heading4']))
                
                hist_data = [['Data', 'Tipo', 'Descrição', 'Peças']]
                for a in atividades:
                    hist_data.append([
                        a.event_at.strftime("%d/%m/%Y %H:%M") if a.event_at else '-',
                        'Manut.' if a.kind == 'MANUTENCAO' else 'Movim.',
                        (a.notes or '-')[:80],
                        a.parts_used or '-'
                    ])
                
                th = Table(hist_data, colWidths=[70, 50, 320, 100])
                th.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('PADDING', (0, 0), (-1, -1), 3),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#533483')),
                ]))
                elements.append(th)
            
            elements.append(PageBreak())
        
        doc.build(elements)