from db import safe_commit


def test_printer_service_criar(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="SVC001", modelo="HP Test", status="Operacional")
    assert p.patrimonio == "SVC001"
    assert p.status == "Operacional"
    assert p.id is not None


def test_printer_service_listar(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="LST001", modelo="Epson")
    svc.criar(patrimonio="LST002", modelo="Brother")
    todos = svc.listar_todos()
    assert len(todos) >= 2


def test_printer_service_buscar_por_patrimonio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="BUSCA01", modelo="Kyocera")
    p = svc.buscar_por_patrimonio("BUSCA01")
    assert p is not None
    assert p.modelo == "Kyocera"


def test_printer_service_atualizar(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="UPD001", modelo="Xerox")
    svc.atualizar(p, modelo="Xerox Altalink", local_atual="Filial B")
    assert p.modelo == "Xerox Altalink"
    assert p.local_atual == "Filial B"


def test_printer_service_excluir(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="DEL001", modelo="Samsung")
    svc.excluir(p)
    assert svc.buscar_por_patrimonio("DEL001") is None


def test_printer_service_filtro(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="FILTRO01", modelo="HP")
    svc.criar(patrimonio="FILTRO02", modelo="Epson")
    resultados = svc.listar_todos(filtro="FILTRO")
    assert len(resultados) == 2
    resultados = svc.listar_todos(filtro="XPTO")
    assert len(resultados) == 0


def test_company_service_criar(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    c = svc.criar(nome="Empresa Teste", cnpj="12.345.678/0001-00", tipo="matriz")
    assert c.id is not None
    assert c.nome == "Empresa Teste"


def test_company_service_listar(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    svc.criar(nome="Empresa A")
    svc.criar(nome="Empresa B")
    assert len(svc.listar_todas()) >= 2


def test_user_service_criar(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    u = svc.criar(nome="Usuário Teste", username="teste", email="teste@email.com", senha="123456", perfil="admin")
    assert u.id is not None
    assert u.perfil == "admin"
    assert u.ativo is True


def test_user_service_buscar(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    svc.criar(nome="Busca User", username="buscador", email="busca@email.com", senha="abc", perfil="tecnico")
    u = svc.buscar_por_username_ou_email("buscador")
    assert u is not None
    assert u.nome == "Busca User"


def test_part_service_criar(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    peca = svc.criar(codigo="TON001", nome="Toner HP 12A", quantidade=5)
    assert peca.id is not None
    assert peca.quantidade_estoque == 5


def test_technician_service_criar(db_session):
    from app.services.technician_service import TechnicianService
    svc = TechnicianService(db_session)
    t = svc.criar(nome_completo="João Técnico", telefone="81999999999")
    assert t.id is not None
    assert t.ativo is True


def test_technician_service_listar_ativos(db_session):
    from app.services.technician_service import TechnicianService
    svc = TechnicianService(db_session)
    svc.criar(nome_completo="Técnico Ativo")
    t_inativo = svc.criar(nome_completo="Técnico Inativo")
    t_inativo.ativo = False
    safe_commit(db_session)
    ativos = svc.listar_ativos()
    assert all(t.ativo for t in ativos)


def test_activity_service_criar(db_session):
    from app.services.activity_service import ActivityService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ACT001", modelo="HP")
    svc = ActivityService(db_session)
    a = svc.criar(printer_id=p.id, kind="MANUTENCAO", notes="Troca de toner")
    assert a.id is not None
    assert a.kind == "MANUTENCAO"


def test_activity_service_listar_por_impressora(db_session):
    from app.services.activity_service import ActivityService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ACTLST", modelo="Epson")
    svc = ActivityService(db_session)
    svc.criar(printer_id=p.id, kind="MANUTENCAO")
    svc.criar(printer_id=p.id, kind="MOVIMENTACAO")
    atividades = svc.listar_por_impressora(p.id)
    assert len(atividades) == 2


def test_transfer_service_criar(db_session):
    from app.services.printer_service import PrinterService
    from app.services.transfer_service import TransferService
    p = PrinterService(db_session).criar(patrimonio="TRANSF001", modelo="Brother")
    svc = TransferService(db_session)
    t = svc.criar(printer_id=p.id, tipo="saida", responsavel_entrega="João")
    assert t.id is not None
    assert t.tipo == "saida"


def test_dashboard_service_resumo(db_session):
    from app.services.dashboard_service import DashboardService
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="DASH01", modelo="HP", status="Operacional")
    svc.criar(patrimonio="DASH02", modelo="Epson", status="Em manutenção")
    dash = DashboardService(db_session)
    r = dash.resumo()
    assert r["total_impressoras"] >= 2
    assert r["em_manutencao"] >= 1
    assert r["operacionais"] >= 1


def test_alert_service_criar(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ALERT01", modelo="HP")
    svc = AlertService(db_session)
    a = svc.criar(printer_id=p.id, tipo="revisao", titulo="Teste alerta")
    assert a.id is not None
    assert a.tipo == "revisao"
    assert a.resolvido is False


def test_alert_service_resolver(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    from app.services.user_service import UserService
    p = PrinterService(db_session).criar(patrimonio="ALERT02", modelo="Epson")
    usr = UserService(db_session).criar(nome="User", username="resolver", email="r@t.com", senha="123")
    svc = AlertService(db_session)
    a = svc.criar(printer_id=p.id, tipo="critico", titulo="Resolver")
    svc.resolver(a, user_id=usr.id)
    assert a.resolvido is True
    assert a.resolvido_por == usr.id


def test_alert_service_contar_pendentes(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ALERT03", modelo="Brother")
    svc = AlertService(db_session)
    svc.criar(printer_id=p.id, tipo="info", titulo="Pendente 1")
    svc.criar(printer_id=p.id, tipo="info", titulo="Pendente 2")
    a3 = svc.criar(printer_id=p.id, tipo="info", titulo="Resolvido 1")
    svc.resolver(a3)
    assert svc.contar_pendentes() == 2


def test_alert_service_excluir(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ALERT04", modelo="Xerox")
    svc = AlertService(db_session)
    a = svc.criar(printer_id=p.id, tipo="info", titulo="Excluir")
    svc.excluir(a)
    assert svc.buscar_por_id(a.id) is None


def test_audit_service_log(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    log = svc.log(user_id=1, acao="CRIAR", tabela_alvo="printers", registro_id="abc-123")
    assert log.id is not None
    assert log.acao == "CRIAR"
    assert log.tabela_alvo == "printers"


def test_audit_service_log_com_dados(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    antes = {"status": "Operacional"}
    depois = {"status": "Em manutenção"}
    log = svc.log(user_id=1, acao="ATUALIZAR", tabela_alvo="printers",
                  registro_id="abc", dados_antes=antes, dados_depois=depois)
    assert log.dados_antes is not None
    assert log.dados_depois is not None
    import json
    parsed = json.loads(log.dados_depois)
    assert parsed["status"] == "Em manutenção"


def test_audit_service_listar(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    svc.log(user_id=1, acao="CRIAR", tabela_alvo="companies")
    svc.log(user_id=1, acao="CRIAR", tabela_alvo="printers")
    svc.log(user_id=2, acao="ATUALIZAR", tabela_alvo="printers")
    assert len(svc.listar()) >= 3
    assert len(svc.listar_por_tabela("printers")) >= 2
    assert len(svc.listar_por_usuario(1)) >= 2
