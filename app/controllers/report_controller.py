class ReportController:
    def __init__(self, printer_service, activity_service):
        self.printer_service = printer_service
        self.activity_service = activity_service

    def gerar_relatorio_impressoras(self, formato, filepath):
        from app.services.relatorio_service import RelatorioService
        printers = self.printer_service.listar_todos()
        if formato == 'pdf':
            RelatorioService.exportar_impressoras_pdf(printers, filepath)
        else:
            RelatorioService.exportar_impressoras_excel(printers, filepath)

    def gerar_relatorio_atividades(self, formato, filepath):
        from app.services.relatorio_service import RelatorioService
        atividades = self.activity_service.listar(limite=500)
        if formato == 'pdf':
            RelatorioService.exportar_atividades_pdf(atividades, filepath)
        else:
            RelatorioService.exportar_atividades_excel(atividades, filepath)
