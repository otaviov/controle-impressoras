class PrinterController:
    def __init__(self, printer_service, company_service, activity_service):
        self.printer_service = printer_service
        self.company_service = company_service
        self.activity_service = activity_service

    def listar_todas(self, filtro=None):
        return self.printer_service.listar_todos(filtro)

    def buscar_por_patrimonio(self, patrimonio):
        return self.printer_service.buscar_por_patrimonio(patrimonio)

    def criar(self, **kwargs):
        return self.printer_service.criar(**kwargs)

    def atualizar(self, printer, **kwargs):
        return self.printer_service.atualizar(printer, **kwargs)
