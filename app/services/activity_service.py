from __future__ import annotations

import logging

from db import safe_commit

log = logging.getLogger(__name__)
import calendar
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import Activity, Printer
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.services.audit_service import AuditService


class ActivityService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def buscar_por_id(self, activity_id: int) -> Optional[Activity]:
        return self.session.query(Activity).options(
            selectinload(Activity.printer)
        ).filter(Activity.deleted_at == None, Activity.id == activity_id).first()

    def listar(self, filtro_tipo: Optional[str] = None, limite: int = 200, offset: Optional[int] = None) -> list[Activity]:
        query = self.session.query(Activity).filter(Activity.deleted_at == None).options(
            selectinload(Activity.printer)
        ).order_by(Activity.event_at.desc())
        if filtro_tipo and filtro_tipo != "TODAS":
            query = query.filter(Activity.kind == filtro_tipo)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_status(self, status: str, limite: int = 200, offset: Optional[int] = None) -> list[Activity]:
        query = self.session.query(Activity).filter(Activity.deleted_at == None).options(
            selectinload(Activity.printer)
        ).order_by(Activity.event_at.desc())
        query = query.filter(Activity.status_atividade.in_([status, status.lower(), status.capitalize()]))
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_movimentacoes(self, limite: int = 100, offset: Optional[int] = None) -> list[Activity]:
        query = self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.kind == "MOVIMENTACAO"
        ).order_by(Activity.event_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_impressora(self, printer_id: str, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Activity]:
        query = self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id
        ).order_by(Activity.event_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_ultima_manutencao(self, printer_id: str) -> Optional[Activity]:
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id,
            Activity.kind == "MANUTENCAO"
        ).order_by(Activity.event_at.desc()).first()

    def buscar_por_descricao(self, printer_id: str, descricao: str) -> Optional[Activity]:
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id,
            Activity.notes == descricao
        ).order_by(Activity.event_at.desc()).first()

    def criar(self, printer_id: str, kind: str, notes: str = "",
              parts_used: str = "", from_location: str = "", to_location: str = "",
              numero_recibo: str = "", status_atividade: str = "Aberta",
              event_at: Optional[datetime] = None, tecnico_id: Optional[int] = None,
              procedimentos: str = "", sintoma_relatado: str = "",
              diagnostico_tecnico: str = "", solucao_aplicada: str = "",
              inicio_atendimento: Optional[datetime] = None,
              fim_atendimento: Optional[datetime] = None,
              urgencia: str = "Normal",
              os_vinculada_id: Optional[int] = None) -> Activity:
        atividade = Activity(
            printer_id=printer_id,
            kind=sanitizar(kind, "Activity", "kind"),
            event_at=event_at or datetime.now(),
            notes=sanitizar(notes),
            parts_used=sanitizar(parts_used),
            from_location=sanitizar(from_location, "Activity", "from_location"),
            to_location=sanitizar(to_location, "Activity", "to_location"),
            numero_recibo=sanitizar(numero_recibo, "Activity", "numero_recibo"),
            status_atividade=sanitizar(status_atividade, "Activity", "status_atividade"),
            tecnico_id=tecnico_id,
            procedimentos=procedimentos,
            urgencia=sanitizar(urgencia, "Activity", "urgencia") if isinstance(urgencia, str) else urgencia,
            sintoma_relatado=sanitizar(sintoma_relatado),
            diagnostico_tecnico=sanitizar(diagnostico_tecnico),
            solucao_aplicada=sanitizar(solucao_aplicada),
            inicio_atendimento=inicio_atendimento,
            fim_atendimento=fim_atendimento,
            os_vinculada_id=os_vinculada_id,
        )
        self.session.add(atividade)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="activities", registro_id=atividade.id, dados_depois=atividade)
        return atividade

    def listar_vinculadas(self, activity_id: int, limite: int = 20) -> list[Activity]:
        """Retorna OSs que estão vinculadas à activity_id (filhas + pai)."""
        activity = self.buscar_por_id(activity_id)
        if not activity:
            return []
        resultado: list[Activity] = []
        if activity.os_vinculada_id:
            pai = self.buscar_por_id(activity.os_vinculada_id)
            if pai:
                resultado.append(pai)
        filhas = (
            self.session.query(Activity)
            .filter(Activity.os_vinculada_id == activity_id, Activity.deleted_at == None)
            .limit(limite)
            .all()
        )
        resultado.extend(filhas)
        return resultado

    def listar_candidatas_vinculo(self, printer_id: str, excluir_id: Optional[int] = None, limite: int = 30) -> list[Activity]:
        """Retorna OSs recentes da mesma impressora para vínculo."""
        q = self.session.query(Activity).filter(
            Activity.printer_id == printer_id, Activity.deleted_at == None
        )
        if excluir_id:
            q = q.filter(Activity.id != excluir_id)
        q = q.order_by(Activity.event_at.desc()).limit(limite)
        return q.all()

    def atualizar(self, atividade: Activity, **kwargs: Any) -> None:
        if self.audit_service:
            dados_antes = {chave: getattr(atividade, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(atividade, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Activity", chave)
                setattr(atividade, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="activities", registro_id=atividade.id, dados_antes=dados_antes, dados_depois=atividade)

    def excluir(self, atividade: Activity) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="activities", registro_id=atividade.id, dados_antes=atividade)
        atividade.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_total(self) -> int:
        return self.session.query(Activity).filter(Activity.deleted_at == None).count()

    def contar_por_status(self, status: str) -> int:
        return self.session.query(Activity).filter(
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).count()

    def contar_por_mes(self, ano: int, mes: int, kind: Optional[str] = None) -> int:
        inicio = datetime(ano, mes, 1)
        fim = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)
        query = self.session.query(Activity).filter(
            Activity.event_at >= inicio, Activity.event_at < fim
        )
        if kind:
            query = query.filter(Activity.kind == kind)
        return query.count()

    def contar_ultimos_6_meses(self) -> dict[str, list]:
        hoje = datetime.now()
        resultado: dict[str, list] = {"manut": [], "mov": [], "labels": []}
        for i in range(5, -1, -1):
            mes_n = hoje.month - i
            ano_n = hoje.year
            while mes_n <= 0:
                mes_n += 12
                ano_n -= 1
            resultado["labels"].append(calendar.month_abbr[mes_n])
            resultado["manut"].append(self.contar_por_mes(ano_n, mes_n, "MANUTENCAO"))
            resultado["mov"].append(self.contar_por_mes(ano_n, mes_n, "MOVIMENTACAO"))
        return resultado

    def buscar_por_filtro_busca(self, texto: str, limite: int = 200, offset: Optional[int] = None) -> list[Activity]:
        query = self.session.query(Activity).filter(Activity.deleted_at == None).order_by(Activity.event_at.desc())
        printers = self.session.query(Printer).filter(
            Printer.patrimonio.like(f"%{texto}%")
        ).all()
        printer_ids = [p.id for p in printers]
        if printer_ids:
            query = query.filter(Activity.printer_id.in_(printer_ids))
        else:
            query = query.filter(Activity.printer_id == "NENHUM")
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_movimentacoes_por_filtro(self, texto: str, limite: int = 100, offset: Optional[int] = None) -> list[Activity]:
        filtro = f"%{texto}%"
        query = self.session.query(Activity).filter(Activity.kind == "MOVIMENTACAO")
        printers = self.session.query(Printer).filter(
            Printer.patrimonio.like(filtro)
        ).all()
        printer_ids = [p.id for p in printers]
        if printer_ids:
            query = query.filter(
                Activity.printer_id.in_(printer_ids) |
                Activity.from_location.like(filtro) |
                Activity.to_location.like(filtro) |
                Activity.parts_used.like(filtro) |
                Activity.notes.like(filtro) |
                Activity.numero_recibo.like(filtro)
            )
        else:
            query = query.filter(
                Activity.from_location.like(filtro) |
                Activity.to_location.like(filtro) |
                Activity.parts_used.like(filtro) |
                Activity.notes.like(filtro) |
                Activity.numero_recibo.like(filtro)
            )
        query = query.order_by(Activity.event_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_origem_destino(self, origem: str, destino: str) -> Optional[Activity]:
        return self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO",
            Activity.from_location == origem,
            Activity.to_location == destino
        ).order_by(Activity.event_at.desc()).first()

    def listar_por_tecnico(self, tecnico_id: int, limite: int = 200) -> list[Activity]:
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.tecnico_id == tecnico_id
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def listar_por_tecnico_e_status(self, tecnico_id: int, status: str, limite: int = 200) -> list[Activity]:
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def listar_por_tecnico_e_tipo(self, tecnico_id: int, kind: str, limite: int = 200) -> list[Activity]:
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.kind == kind
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def contar_por_tecnico(self, tecnico_id: int) -> int:
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id
        ).count()

    def contar_por_tecnico_por_status(self, tecnico_id: int, status: str) -> int:
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).count()

    def listar_por_tecnico_e_data(self, tecnico_id: int, data: datetime, limite: int = 200) -> list[Activity]:
        inicio = datetime(data.year, data.month, data.day, 0, 0, 0)
        fim = datetime(data.year, data.month, data.day, 23, 59, 59)
        return self.session.query(Activity).filter(
            Activity.deleted_at == None,
            Activity.tecnico_id == tecnico_id,
            Activity.event_at >= inicio,
            Activity.event_at <= fim,
        ).order_by(Activity.from_location, Activity.event_at).limit(limite).all()

    def contar_por_tecnico_por_data(self, tecnico_id: int, data: datetime) -> int:
        inicio = datetime(data.year, data.month, data.day, 0, 0, 0)
        fim = datetime(data.year, data.month, data.day, 23, 59, 59)
        return self.session.query(Activity).filter(
            Activity.deleted_at == None,
            Activity.tecnico_id == tecnico_id,
            Activity.event_at >= inicio,
            Activity.event_at <= fim,
        ).count()

    def listar_concluidas_por_tecnico_no_periodo(
        self, tecnico_id: int, inicio: datetime, fim: datetime, limite: int = 500
    ) -> list[Activity]:
        return self.session.query(Activity).filter(
            Activity.deleted_at == None,
            Activity.tecnico_id == tecnico_id,
            Activity.kind == "MANUTENCAO",
            Activity.status_atividade.in_(["Concluido", "Concluído", "Verificada"]),
            Activity.fim_atendimento >= inicio,
            Activity.fim_atendimento <= fim,
        ).order_by(Activity.fim_atendimento.desc()).limit(limite).all()

    def listar_pecas_por_tecnico(self, tecnico_id: int, limite: int = 20) -> list[tuple[str, int]]:
        from collections import Counter
        pecas = Counter()
        atividades = self.session.query(Activity).filter(
            Activity.deleted_at == None,
            Activity.tecnico_id == tecnico_id,
            Activity.parts_used != "",
        ).all()
        for a in atividades:
            if a.parts_used:
                for p in a.parts_used.split(","):
                    p = p.strip()
                    if p:
                        pecas[p] += 1
        return pecas.most_common(limite)

    def listar_tecnicos_por_peca(self, nome_peca: str, limite: int = 50) -> list[Activity]:
        filtro = f"%{nome_peca}%"
        resultados = self.session.query(Activity).options(
            selectinload(Activity.technician)
        ).filter(
            Activity.deleted_at == None,
            Activity.parts_used.like(filtro),
        ).order_by(Activity.event_at.desc()).limit(limite * 5).all()
        nome_peca_lower = nome_peca.strip().lower()
        return [
            a for a in resultados
            if a.technician and any(p.strip().lower() == nome_peca_lower for p in (a.parts_used or "").split(","))
        ][:limite]

    def listar_os_abertas_por_tecnico(self, tecnico_id: int, limite: int = 100) -> list[Activity]:
        excluidos = ["Concluido", "Concluído", "Verificada"]
        return self.session.query(Activity).options(
            selectinload(Activity.printer)
        ).filter(
            Activity.deleted_at == None,
            Activity.tecnico_id == tecnico_id,
            ~Activity.status_atividade.in_(excluidos),
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def contar_por_impressora_e_kind(self, printer_id: str, kind: str) -> int:
        return self.session.query(Activity).filter(
            Activity.printer_id == printer_id,
            Activity.kind == kind
        ).count()

    def listar_por_peca(self, nome_peca: str, limite: int = 100) -> list[Activity]:
        filtro = f"%{nome_peca}%"
        resultados = self.session.query(Activity).options(
            selectinload(Activity.printer)
        ).filter(
            Activity.deleted_at == None, Activity.parts_used.like(filtro)
        ).order_by(Activity.event_at.desc()).limit(limite * 5).all()
        nome_peca_lower = nome_peca.strip().lower()
        filtrados = [
            a for a in resultados
            if any(p.strip().lower() == nome_peca_lower for p in (a.parts_used or "").split(","))
        ]
        return filtrados[:limite]

    def listar_por_peca_com_relacionadas(self, nome_peca: str, limite: int = 100) -> tuple[list[Activity], list[Activity]]:
        diretas = self.listar_por_peca(nome_peca, limite=limite)
        printer_ids = list({a.printer_id for a in diretas if a.printer_id})
        if not printer_ids:
            return diretas, []
        diretas_ids = {a.id for a in diretas}
        query = self.session.query(Activity).options(
            selectinload(Activity.printer)
        ).filter(Activity.deleted_at == None, Activity.printer_id.in_(printer_ids))
        if diretas_ids:
            query = query.filter(~Activity.id.in_(diretas_ids))
        relacionadas = query.order_by(Activity.event_at.desc()).limit(limite).all()
        return diretas, relacionadas

    def top_pecas_trocadas(self, limite: int = 8) -> list[tuple[str, int]]:
        from collections import Counter
        pecas_count = Counter()
        atividades = self.session.query(Activity).filter(
            Activity.deleted_at == None, Activity.parts_used != ""
        ).all()
        for a in atividades:
            if a.parts_used:
                for peca in a.parts_used.split(','):
                    peca = peca.strip()
                    if peca:
                        pecas_count[peca] += 1
        return pecas_count.most_common(limite)

    def listar_excluidos(self, limite: int = 50) -> list[Activity]:
        return self.session.query(Activity).filter(
            Activity.deleted_at != None
        ).order_by(Activity.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Activity) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="activities", registro_id=obj.id)

