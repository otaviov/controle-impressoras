import pytest
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


# ═══════════════════════════════════════════════════════════════
# Edge cases – PrinterService
# ═══════════════════════════════════════════════════════════════

def test_printer_criar_duplicate_patrimonio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="DUP001", modelo="HP")
    with pytest.raises(Exception):
        svc.criar(patrimonio="DUP001", modelo="Epson")


def test_printer_criar_sem_patrimonio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="", modelo="HP")
    assert p.id is not None


def test_printer_criar_whitespace_patrimonio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="  ESPACO  ", modelo="HP")
    assert svc.buscar_por_patrimonio("ESPACO") is not None


def test_printer_buscar_por_patrimonio_inexistente(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    assert svc.buscar_por_patrimonio("NAO_EXISTE") is None


def test_printer_buscar_por_patrimonio_vazio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    assert svc.buscar_por_patrimonio("") is None


def test_printer_atualizar_com_none(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="NONE001", modelo="HP")
    svc.atualizar(p, proxima_revisao=None)
    assert p.proxima_revisao is None


def test_printer_excluir_duas_vezes(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="DEL2X", modelo="HP")
    svc.excluir(p)
    assert svc.buscar_por_patrimonio("DEL2X") is None
    svc.excluir(p)
    assert svc.buscar_por_patrimonio("DEL2X") is None


def test_printer_restaurar(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="REST001", modelo="HP")
    svc.excluir(p)
    assert svc.buscar_por_patrimonio("REST001") is None
    svc.restaurar(p)
    assert svc.buscar_por_patrimonio("REST001") is not None


def test_printer_restaurar_duas_vezes(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p = svc.criar(patrimonio="REST2X", modelo="HP")
    svc.restaurar(p)
    assert svc.buscar_por_patrimonio("REST2X") is not None
    svc.restaurar(p)
    assert svc.buscar_por_patrimonio("REST2X") is not None


def test_printer_listar_com_filtro_vazio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="VZ01", modelo="HP")
    todos = svc.listar_todos(filtro="")
    assert len(todos) >= 1


def test_printer_listar_com_filtro_muito_longo(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="LGFLT", modelo="HP")
    resultados = svc.listar_todos(filtro="a" * 500)
    assert len(resultados) == 0


def test_printer_listar_excluidos_vazio(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    excluidos = svc.listar_excluidos()
    assert isinstance(excluidos, list)


def test_printer_listar_excluidos_com_restaurados(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    p1 = svc.criar(patrimonio="EXCLST1", modelo="HP")
    p2 = svc.criar(patrimonio="EXCLST2", modelo="Epson")
    svc.excluir(p1)
    svc.excluir(p2)
    svc.restaurar(p1)
    excluidos = svc.listar_excluidos()
    pats = [e.patrimonio for e in excluidos]
    assert "EXCLST2" in pats
    assert "EXCLST1" not in pats


def test_printer_contar_todos_sem_filtro(db_session):
    from app.services.printer_service import PrinterService
    svc = PrinterService(db_session)
    svc.criar(patrimonio="CNT01", modelo="HP")
    total = svc.contar_todos()
    assert total >= 1


# ═══════════════════════════════════════════════════════════════
# Edge cases – CompanyService
# ═══════════════════════════════════════════════════════════════

def test_company_criar_sem_nome(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    c = svc.criar(nome="", cnpj="")
    assert c.id is not None


def test_company_criar_duplicate_nome(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    c1 = svc.criar(nome="Empresa Unica")
    c2 = svc.criar(nome="Empresa Unica")
    assert c1.id != c2.id


def test_company_buscar_por_nome_inexistente(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    assert svc.buscar_por_nome("NAO_EXISTE") is None


def test_company_listar_nomes_sem_empresas(db_session):
    from app.services.company_service import CompanyService
    svc = CompanyService(db_session)
    nomes = svc.listar_nomes()
    assert isinstance(nomes, list)


# ═══════════════════════════════════════════════════════════════
# Edge cases – UserService
# ═══════════════════════════════════════════════════════════════

def test_user_criar_username_repetido(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    u1 = svc.criar(nome="User1", username="repetido", email="u1@t.com", senha="123", perfil="tecnico")
    u2 = svc.criar(nome="User2", username="repetido", email="u2@t.com", senha="456", perfil="admin")
    assert u1.id != u2.id


def test_user_criar_email_repetido(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    svc.criar(nome="User1", username="user1", email="dup@t.com", senha="123", perfil="tecnico")
    with pytest.raises(Exception):
        svc.criar(nome="User2", username="user2", email="dup@t.com", senha="456", perfil="admin")


def test_user_criar_sem_senha(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    u = svc.criar(nome="Sem Senha", username="sem_senha", email="ss@t.com", senha="", perfil="tecnico")
    assert u.id is not None


def test_user_buscar_por_username_inexistente(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    assert svc.buscar_por_username_ou_email("nao_existe") is None


def test_user_verificar_existente_username(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    svc.criar(nome="Existente", username="existe", email="ex@t.com", senha="123", perfil="tecnico")
    resultado = svc.verificar_existente(email="ex@t.com", username="existe")
    assert resultado is not None
    assert resultado.username == "existe"


def test_user_verificar_existente_nonexistent(db_session):
    from app.services.user_service import UserService
    svc = UserService(db_session)
    resultado = svc.verificar_existente(email="nao@t.com", username="nao_existe")
    assert resultado is None


# ═══════════════════════════════════════════════════════════════
# Edge cases – PartService
# ═══════════════════════════════════════════════════════════════

def test_part_criar_com_estoque_negativo(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    p = svc.criar(codigo="NEG001", nome="Peça Negativa", quantidade=-5)
    assert p.quantidade_estoque == -5


def test_part_criar_sem_codigo(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    p = svc.criar(codigo="", nome="Sem Codigo", quantidade=0)
    assert p.id is not None


def test_part_buscar_por_nome_inexistente(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    assert svc.buscar_por_nome("NAO_EXISTE") is None


def test_part_decrementar_estoque(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    p = svc.criar(codigo="DEC01", nome="Decremento", quantidade=2)
    p.quantidade_estoque -= 5
    svc.atualizar(p, quantidade_estoque=p.quantidade_estoque)
    assert p.quantidade_estoque == -3


def test_part_listar_todas_sem_pecas(db_session):
    from app.services.part_service import PartService
    svc = PartService(db_session)
    todas = svc.listar_todas()
    assert isinstance(todas, list)
    assert len(todas) == 0


# ═══════════════════════════════════════════════════════════════
# Edge cases – TechnicianService
# ═══════════════════════════════════════════════════════════════

def test_technician_criar_nome_completo_vazio(db_session):
    from app.services.technician_service import TechnicianService
    from app.utils.sanitize import truncar
    svc = TechnicianService(db_session)
    with pytest.raises(IndexError):
        svc.criar(nome_completo="", telefone="")


def test_technician_listar_ativos_sem_tecnicos(db_session):
    from app.services.technician_service import TechnicianService
    svc = TechnicianService(db_session)
    assert svc.listar_ativos() == []


def test_technician_excluir_e_restaurar(db_session):
    from app.services.technician_service import TechnicianService
    svc = TechnicianService(db_session)
    t = svc.criar(nome_completo="Tec Rest", telefone="81")
    svc.excluir(t)
    assert svc.buscar_por_id(t.id) is None
    svc.restaurar(t)
    assert svc.buscar_por_id(t.id) is not None


# ═══════════════════════════════════════════════════════════════
# Edge cases – ActivityService
# ═══════════════════════════════════════════════════════════════

def test_activity_listar_por_impressora_inexistente(db_session):
    from app.services.activity_service import ActivityService
    svc = ActivityService(db_session)
    assert svc.listar_por_impressora(99999) == []


def test_activity_criar_com_kind_vazio(db_session):
    from app.services.activity_service import ActivityService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ACTKIND", modelo="HP")
    svc = ActivityService(db_session)
    a = svc.criar(printer_id=p.id, kind="", notes="")
    assert a.id is not None


def test_activity_excluir_e_restaurar(db_session):
    from app.services.activity_service import ActivityService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ACTRST", modelo="HP")
    svc = ActivityService(db_session)
    a = svc.criar(printer_id=p.id, kind="MANUTENCAO")
    svc.excluir(a)
    assert svc.buscar_por_id(a.id) is None
    svc.restaurar(a)
    assert svc.buscar_por_id(a.id) is not None


# ═══════════════════════════════════════════════════════════════
# Edge cases – TransferService
# ═══════════════════════════════════════════════════════════════

def test_transfer_criar_com_tipo_invalido(db_session):
    from app.services.printer_service import PrinterService
    from app.services.transfer_service import TransferService
    p = PrinterService(db_session).criar(patrimonio="TRFTP", modelo="HP")
    svc = TransferService(db_session)
    t = svc.criar(printer_id=p.id, tipo="invalido", responsavel_entrega="João")
    assert t.id is not None
    assert t.tipo == "invalido"


def test_transfer_buscar_por_numero_os_inexistente(db_session):
    from app.services.transfer_service import TransferService
    svc = TransferService(db_session)
    resultado = svc.buscar_por_numero_os("NAO_EXISTE")
    assert resultado == []


def test_transfer_excluir_e_restaurar(db_session):
    from app.services.printer_service import PrinterService
    from app.services.transfer_service import TransferService
    p = PrinterService(db_session).criar(patrimonio="TRFRST", modelo="HP")
    svc = TransferService(db_session)
    t = svc.criar(printer_id=p.id, tipo="saida")
    svc.excluir(t)
    assert svc.buscar_por_id(t.id) is None
    svc.restaurar(t)
    assert svc.buscar_por_id(t.id) is not None


# ═══════════════════════════════════════════════════════════════
# Edge cases – AlertService
# ═══════════════════════════════════════════════════════════════

def test_alert_criar_sem_titulo(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ALTTL", modelo="HP")
    svc = AlertService(db_session)
    a = svc.criar(printer_id=p.id, tipo="info", titulo="")
    assert a.id is not None


def test_alert_criar_sem_printer(db_session):
    from app.services.alert_service import AlertService
    svc = AlertService(db_session)
    a = svc.criar(printer_id=None, tipo="info", titulo="Sem impressora")
    assert a.id is not None
    assert a.printer_id is None


def test_alert_resolver_ja_resolvido(db_session):
    from app.services.alert_service import AlertService
    from app.services.printer_service import PrinterService
    p = PrinterService(db_session).criar(patrimonio="ALRST", modelo="HP")
    svc = AlertService(db_session)
    a = svc.criar(printer_id=p.id, tipo="info", titulo="Ja resolvido")
    svc.resolver(a)
    svc.resolver(a)
    assert a.resolvido is True
    assert a.resolvido_em is not None


# ═══════════════════════════════════════════════════════════════
# Edge cases – AuditService
# ═══════════════════════════════════════════════════════════════

def test_audit_log_sem_usuario(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    log = svc.log(user_id=None, acao="TESTE", tabela_alvo="printers")
    assert log.id is not None


def test_audit_listar_por_usuario_sem_logs(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    assert svc.listar_por_usuario(99999) == []


def test_audit_listar_por_tabela_sem_logs(db_session):
    from app.services.audit_service import AuditService
    svc = AuditService(db_session)
    assert svc.listar_por_tabela("inexistente") == []


# ═══════════════════════════════════════════════════════════════
# Edge cases – DashboardService
# ═══════════════════════════════════════════════════════════════

def test_dashboard_resumo_sem_impressoras(db_session):
    from app.services.dashboard_service import DashboardService
    svc = DashboardService(db_session)
    r = svc.resumo()
    assert r["total_impressoras"] == 0
    assert r["em_manutencao"] == 0
    assert r["operacionais"] == 0


def test_dashboard_grafico_pizza_sem_dados(db_session):
    from app.services.dashboard_service import DashboardService
    svc = DashboardService(db_session)
    labels, valores = svc.dados_grafico_pizza()
    assert isinstance(labels, list)
    assert isinstance(valores, list)


def test_dashboard_grafico_atividades_sem_dados(db_session):
    from app.services.dashboard_service import DashboardService
    svc = DashboardService(db_session)
    meses, valores = svc.dados_grafico_atividades()
    assert isinstance(meses, list)
    assert isinstance(valores, list)


def test_dashboard_grafico_alertas_sem_dados(db_session):
    from app.services.dashboard_service import DashboardService
    svc = DashboardService(db_session)
    dias, criados = svc.dados_grafico_alertas()
    assert isinstance(dias, list)
    assert isinstance(criados, list)
