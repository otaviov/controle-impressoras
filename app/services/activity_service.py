from datetime import datetime
from sqlalchemy import func
from app.models import Activity, Printer
import calendar


class ActivityService:
    def __init__(self, session):
        self.session = session

    def listar(self, filtro_tipo=None, limite=200):
        query = self.session.query(Activity).order_by(Activity.event_at.desc())
        if filtro_tipo and filtro_tipo != "TODAS":
            query = query.filter(Activity.kind == filtro_tipo)
        return query.limit(limite).all()

    def listar_por_status(self, status, limite=200):
        query = self.session.query(Activity).order_by(Activity.event_at.desc())
        query = query.filter(Activity.status_atividade.in_([status, status.lower(), status.capitalize()]))
        return query.limit(limite).all()

    def listar_movimentacoes(self, limite=100):
        return self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO"
        ).order_by(Activity.event_at.desc()).limit(limite).all()

    def listar_por_impressora(self, printer_id, limite=None):
        query = self.session.query(Activity).filter(
            Activity.printer_id == printer_id
        ).order_by(Activity.event_at.desc())
        if limite:
            query = query.limit(limite)
        return query.all()

    def buscar_ultima_manutencao(self, printer_id):
        return self.session.query(Activity).filter(
            Activity.printer_id == printer_id,
            Activity.kind == "MANUTENCAO"
        ).order_by(Activity.event_at.desc()).first()

    def buscar_por_descricao(self, printer_id, descricao):
        return self.session.query(Activity).filter(
            Activity.printer_id == printer_id,
            Activity.notes == descricao
        ).order_by(Activity.event_at.desc()).first()

    def criar(self, printer_id, kind, notes="", parts_used="",
              from_location="", to_location="", numero_recibo="",
              status_atividade="Concluida", event_at=None):
        atividade = Activity(
            printer_id=printer_id,
            kind=kind,
            event_at=event_at or datetime.now(),
            notes=notes,
            parts_used=parts_used,
            from_location=from_location,
            to_location=to_location,
            numero_recibo=numero_recibo,
            status_atividade=status_atividade
        )
        self.session.add(atividade)
        self.session.commit()
        return atividade

    def atualizar(self, atividade, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(atividade, chave):
                setattr(atividade, chave, valor)
        self.session.commit()

    def excluir(self, atividade):
        self.session.delete(atividade)
        self.session.commit()

    def contar_total(self):
        return self.session.query(Activity).count()

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

    def buscar_por_filtro_busca(self, texto, limite=200):
        query = self.session.query(Activity).order_by(Activity.event_at.desc())
        printers = self.session.query(Printer).filter(
            Printer.patrimonio.like(f"%{texto}%")
        ).all()
        printer_ids = [p.id for p in printers]
        if printer_ids:
            query = query.filter(Activity.printer_id.in_(printer_ids))
        else:
            query = query.filter(Activity.printer_id == "NENHUM")
        return query.limit(limite).all()

    def buscar_movimentacoes_por_filtro(self, texto, limite=100):
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
        return query.order_by(Activity.event_at.desc()).limit(limite).all()

    def buscar_por_origem_destino(self, origem, destino):
        return self.session.query(Activity).filter(
            Activity.kind == "MOVIMENTACAO",
            Activity.from_location == origem,
            Activity.to_location == destino
        ).order_by(Activity.event_at.desc()).first()

    def top_pecas_trocadas(self, limite=8):
        from collections import Counter
        pecas_count = Counter()
        atividades = self.session.query(Activity).filter(
            Activity.parts_used != ""
        ).all()
        for a in atividades:
            if a.parts_used:
                for peca in a.parts_used.split(','):
                    peca = peca.strip()
                    if peca:
                        pecas_count[peca] += 1
        return pecas_count.most_common(limite)
