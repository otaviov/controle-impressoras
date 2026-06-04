from __future__ import annotations

import logging

from db import safe_commit

log = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import Alert, Printer
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.models.part import Part
    from app.models.user import User
    from app.services.audit_service import AuditService
    from app.services.notification_service import NotificadorService


class AlertService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None, notificador: Optional[NotificadorService] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id
        self.notificador: Optional[NotificadorService] = notificador

    def listar_todos(self, apenas_pendentes: bool = False, apenas_resolvidos: bool = False, filtro_busca: Optional[str] = None, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Alert]:
        query = self.session.query(Alert).filter(Alert.deleted_at == None).options(
            selectinload(Alert.printer), selectinload(Alert.part)
        ).order_by(Alert.created_at.desc())
        if apenas_pendentes:
            query = query.filter(Alert.resolvido == False)
        if apenas_resolvidos:
            query = query.filter(Alert.resolvido == True)
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

    def listar_por_impressora(self, printer_id: Optional[str], limite: Optional[int] = None, offset: Optional[int] = None) -> list[Alert]:
        query = self.session.query(Alert).filter(Alert.deleted_at == None).filter(
            Alert.printer_id == printer_id
        ).order_by(Alert.created_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, alert_id: int) -> Optional[Alert]:
        return self.session.query(Alert).filter(Alert.deleted_at == None, Alert.id == alert_id).first()

    def criar(self, tipo: str, titulo: str, descricao: str = "", printer_id: Optional[str] = None, part_id: Optional[int] = None, data_alerta: Optional[datetime] = None, data_agendada: Optional[datetime] = None) -> Alert:
        alerta = Alert(
            printer_id=printer_id,
            part_id=part_id,
            tipo=sanitizar(tipo, "Alert", "tipo"),
            titulo=sanitizar(titulo, "Alert", "titulo"),
            descricao=sanitizar(descricao),
            data_alerta=data_alerta or datetime.now(),
            data_agendada=data_agendada,
        )
        self.session.add(alerta)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="alerts", registro_id=alerta.id, dados_depois=alerta)

        if not data_agendada and self.notificador:
            try:
                self.notificador.notificar_alerta(alerta)
                alerta.notificado = True
                alerta.notificado_em = datetime.now()
                safe_commit(self.session)
            except Exception as e:
                log.warning("Erro ao notificar alerta %s: %s", alerta.id, e)

        return alerta

    def resolver(self, alerta: Alert, user_id: Optional[int] = None) -> None:
        if self.audit_service:
            self.audit_service.log(user_id or self.user_id, "resolver", tabela_alvo="alerts", registro_id=alerta.id, dados_antes=alerta)
        alerta.resolvido = True
        alerta.resolvido_em = datetime.now()
        alerta.resolvido_por = user_id
        safe_commit(self.session)

    def excluir(self, alerta: Alert) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="alerts", registro_id=alerta.id, dados_antes=alerta)
        alerta.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_todos(self, apenas_pendentes: bool = False, apenas_resolvidos: bool = False, filtro_busca: Optional[str] = None) -> int:
        query = self.session.query(Alert).filter(Alert.deleted_at == None)
        if apenas_pendentes:
            query = query.filter(Alert.resolvido == False)
        if apenas_resolvidos:
            query = query.filter(Alert.resolvido == True)
        if filtro_busca:
            f = f"%{filtro_busca}%"
            query = query.filter(
                Alert.titulo.like(f) | Alert.tipo.like(f) | Alert.descricao.like(f)
            )
        return query.count()

    def contar_pendentes(self) -> int:
        return self.session.query(Alert).filter(
            Alert.deleted_at == None, Alert.resolvido == False
        ).count()

    def gerar_alertas_revisao(self, dias_limite: int = 30) -> int:
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
                data_agendada=p.proxima_revisao,
            )
            criados += 1
        return criados

    def listar_excluidos(self, limite: int = 50) -> list[Alert]:
        return self.session.query(Alert).filter(
            Alert.deleted_at != None
        ).order_by(Alert.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Alert) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="alerts", registro_id=obj.id)

    def verificar_estoque_baixo(self) -> int:
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
            self.criar(
                part_id=peca.id,
                tipo="estoque",
                titulo=f"Estoque baixo: {peca.nome}",
                descricao=f"Peça {peca.nome} (cód. {peca.codigo}) tem apenas {peca.quantidade_estoque} unidade(s) — mínimo é {peca.estoque_minimo}.",
            )
            criados += 1
        return criados

    def verificar_agendados(self) -> list[Alert]:
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amanha = hoje + timedelta(days=1)
        alerts = self.session.query(Alert).filter(
            Alert.deleted_at == None,
            Alert.resolvido == False,
            Alert.notificado == False,
            Alert.data_agendada != None,
            Alert.data_agendada <= amanha,
        ).options(selectinload(Alert.printer), selectinload(Alert.part)).all()

        notificados = []
        for a in alerts:
            if self.notificador:
                try:
                    self.notificador.notificar_alerta(a)
                    a.notificado = True
                    a.notificado_em = datetime.now()
                    safe_commit(self.session)
                    notificados.append(a)
                except Exception as e:
                    log.warning("Erro ao notificar alerta agendado %s: %s", a.id, e)
        return notificados

