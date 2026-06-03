import logging

from db import safe_commit

log = logging.getLogger(__name__)
from datetime import datetime, timedelta

from app.models import Alert, Printer
from app.utils.sanitize import sanitizar
from sqlalchemy.orm import selectinload


class AlertService:
    def __init__(self, session, audit_service=None, user_id=None, notificador=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id
        self.notificador = notificador

    def listar_todos(self, apenas_pendentes=False, filtro_busca=None, limite=None, offset=None):
        query = self.session.query(Alert).filter(Alert.deleted_at == None).options(
            selectinload(Alert.printer)
        ).order_by(Alert.created_at.desc())
        if apenas_pendentes:
            query = query.filter(Alert.resolvido == False)
        if filtro_busca:
            f = f"%{filtro_busca}%"
            query = query.filter(
                Alert.titulo.like(f) | Alert.tipo.like(f) | Alert.descricao.like(f)
            )
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_impressora(self, printer_id, limite=None, offset=None):
        query = self.session.query(Alert).filter(Alert.deleted_at == None).filter(
            Alert.printer_id == printer_id
        ).order_by(Alert.created_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, alert_id):
        return self.session.query(Alert).filter(Alert.deleted_at == None, Alert.id == alert_id).first()

    def criar(self, printer_id, tipo, titulo, descricao="", data_alerta=None):
        alerta = Alert(
            printer_id=printer_id,
            tipo=sanitizar(tipo, "Alert", "tipo"),
            titulo=sanitizar(titulo, "Alert", "titulo"),
            descricao=sanitizar(descricao),
            data_alerta=data_alerta or datetime.now(),
        )
        self.session.add(alerta)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="alerts", registro_id=alerta.id, dados_depois=alerta)

        if self.notificador and not alerta.notificado:
            try:
                self.notificador.notificar_alerta(alerta)
                alerta.notificado = True
                alerta.notificado_em = datetime.now()
                safe_commit(self.session)
            except Exception as e:
                log.warning("Erro ao notificar alerta %s: %s", alerta.id, e)

        return alerta

    def resolver(self, alerta, user_id=None):
        if self.audit_service:
            self.audit_service.log(user_id or self.user_id, "resolver", tabela_alvo="alerts", registro_id=alerta.id, dados_antes=alerta)
        alerta.resolvido = True
        alerta.resolvido_em = datetime.now()
        alerta.resolvido_por = user_id
        safe_commit(self.session)

    def excluir(self, alerta):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="alerts", registro_id=alerta.id, dados_antes=alerta)
        alerta.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_todos(self, apenas_pendentes=False, filtro_busca=None):
        query = self.session.query(Alert).filter(Alert.deleted_at == None)
        if apenas_pendentes:
            query = query.filter(Alert.resolvido == False)
        if filtro_busca:
            f = f"%{filtro_busca}%"
            query = query.filter(
                Alert.titulo.like(f) | Alert.tipo.like(f) | Alert.descricao.like(f)
            )
        return query.count()

    def contar_pendentes(self):
        return self.session.query(Alert).filter(Alert.resolvido == False).count()

    def gerar_alertas_revisao(self, dias_limite=30):
        hoje = datetime.now()
        limite = hoje + timedelta(days=dias_limite)
        printers = self.session.query(Printer).filter(
            Printer.proxima_revisao <= limite
        ).all()
        criados = 0
        for p in printers:
            if not p.proxima_revisao:
                continue
            existente = self.session.query(Alert).filter(
                Alert.printer_id == p.id,
                Alert.tipo == "revisao",
                Alert.resolvido == False
            ).first()
            if existente:
                continue
            self.criar(
                printer_id=p.id,
                tipo="revisao",
                titulo=f"Revisão próxima: {p.patrimonio}",
                descricao=f"Impressora {p.modelo} ({p.patrimonio}) precisa de revisão até {p.proxima_revisao.strftime('%d/%m/%Y')}",
                data_alerta=p.proxima_revisao,
            )
            criados += 1
        return criados

    def listar_excluidos(self, limite=50):
        return self.session.query(Alert).filter(
            Alert.deleted_at != None
        ).order_by(Alert.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="alerts", registro_id=obj.id)

    def verificar_estoque_baixo(self):
        from app.models import Part
        from sqlalchemy import or_
        partes = self.session.query(Part).filter(
            or_(
                Part.quantidade_estoque <= 0,
                Part.quantidade_estoque <= Part.estoque_minimo,
            )
        ).all()
        criados = 0
        for peca in partes:
            existente = self.session.query(Alert).filter(
                Alert.tipo == "estoque",
                Alert.resolvido == False,
                Alert.titulo.like(f"%{peca.nome}%"),
            ).first()
            if existente:
                continue
            printer = self.session.query(Printer).filter(
                Printer.modelo.ilike(f"%{peca.modelo_compativel}%")
            ).first()
            printer_id = printer.id if printer else "unknown"
            self.criar(
                printer_id=printer_id,
                tipo="estoque",
                titulo=f"Estoque baixo: {peca.nome}",
                descricao=f"Peça {peca.nome} (cód. {peca.codigo}) tem apenas {peca.quantidade_estoque} unidade(s) — mínimo é {peca.estoque_minimo}.",
            )
            criados += 1
        return criados

