import logging

from db import safe_commit

log = logging.getLogger(__name__)
import calendar
from datetime import datetime

from app.models import Activity, Printer
from app.utils.sanitize import sanitizar
from sqlalchemy.orm import selectinload


class ActivityService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def buscar_por_id(self, activity_id):
        return self.session.query(Activity).options(
            selectinload(Activity.printer)
        ).filter(Activity.deleted_at == None, Activity.id == activity_id).first()

    def listar(self, filtro_tipo=None, limite=200, offset=None):
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

    def listar_por_status(self, status, limite=200, offset=None):
        query = self.session.query(Activity).filter(Activity.deleted_at == None).options(
            selectinload(Activity.printer)
        ).order_by(Activity.event_at.desc())
        query = query.filter(Activity.status_atividade.in_([status, status.lower(), status.capitalize()]))
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_movimentacoes(self, limite=100, offset=None):
        query = self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.kind == "MOVIMENTACAO"
        ).order_by(Activity.event_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_impressora(self, printer_id, limite=None, offset=None):
        query = self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id
        ).order_by(Activity.event_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_ultima_manutencao(self, printer_id):
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id,
            Activity.kind == "MANUTENCAO"
        ).order_by(Activity.event_at.desc()).first()

    def buscar_por_descricao(self, printer_id, descricao):
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.printer_id == printer_id,
            Activity.notes == descricao
        ).order_by(Activity.event_at.desc()).first()

    def criar(self, printer_id, kind, notes="", parts_used="",
              from_location="", to_location="", numero_recibo="",
              status_atividade="Concluida", event_at=None, tecnico_id=None):
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
        )
        self.session.add(atividade)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="activities", registro_id=atividade.id, dados_depois=atividade)
        return atividade

    def atualizar(self, atividade, **kwargs):
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

    def excluir(self, atividade):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="activities", registro_id=atividade.id, dados_antes=atividade)
        atividade.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_total(self):
        return self.session.query(Activity).filter(Activity.deleted_at == None).count()

    def contar_por_status(self, status):
        return self.session.query(Activity).filter(
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).count()

    def contar_por_mes(self, ano, mes, kind=None):
        inicio = datetime(ano, mes, 1)
        fim = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)
        query = self.session.query(Activity).filter(
            Activity.event_at >= inicio, Activity.event_at < fim
        )
        if kind:
            query = query.filter(Activity.kind == kind)
        return query.count()

    def contar_ultimos_6_meses(self):
        hoje = datetime.now()
        resultado = {"manut": [], "mov": [], "labels": []}
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

    def buscar_por_filtro_busca(self, texto, limite=200, offset=None):
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

    def buscar_movimentacoes_por_filtro(self, texto, limite=100, offset=None):
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

    def buscar_por_origem_destino(self, origem, destino):
        return self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO",
            Activity.from_location == origem,
            Activity.to_location == destino
        ).order_by(Activity.event_at.desc()).first()

    def listar_por_tecnico(self, tecnico_id, limite=200):
        return self.session.query(Activity).filter(Activity.deleted_at == None).filter(
            Activity.tecnico_id == tecnico_id
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def listar_por_tecnico_e_status(self, tecnico_id, status, limite=200):
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def listar_por_tecnico_e_tipo(self, tecnico_id, kind, limite=200):
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.kind == kind
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def contar_por_tecnico(self, tecnico_id):
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id
        ).count()

    def contar_por_tecnico_por_status(self, tecnico_id, status):
        return self.session.query(Activity).filter(
            Activity.tecnico_id == tecnico_id,
            Activity.status_atividade.in_([status, status.lower(), status.capitalize()])
        ).count()

    def contar_por_impressora_e_kind(self, printer_id, kind):
        return self.session.query(Activity).filter(
            Activity.printer_id == printer_id,
            Activity.kind == kind
        ).count()

    def listar_por_peca(self, nome_peca, limite=100):
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

    def listar_por_peca_com_relacionadas(self, nome_peca, limite=100):
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

    def top_pecas_trocadas(self, limite=8):
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

    def listar_excluidos(self, limite=50):
        return self.session.query(Activity).filter(
            Activity.deleted_at != None
        ).order_by(Activity.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="activities", registro_id=obj.id)

