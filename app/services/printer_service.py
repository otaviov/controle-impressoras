from sqlalchemy import func
from app.models import Printer, Activity, simple_uid


class PrinterService:
    def __init__(self, session):
        self.session = session

    def listar_todos(self, filtro=None):
        query = self.session.query(Printer)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Printer.patrimonio.like(f) | Printer.modelo.like(f) |
                Printer.serial.like(f) | Printer.local_atual.like(f) |
                Printer.marca.like(f)
            )
        return query.order_by(Printer.patrimonio).all()

    def buscar_por_patrimonio(self, patrimonio):
        return self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()

    def buscar_por_id(self, printer_id):
        return self.session.query(Printer).filter(Printer.id == printer_id).first()

    def buscar_por_ids(self, ids):
        if not ids:
            return {}
        return {
            p.id: p
            for p in self.session.query(Printer).filter(Printer.id.in_(ids)).all()
        }

    def mapa_patrimonio(self, ids):
        if not ids:
            return {}
        return {
            p.id: p.patrimonio
            for p in self.session.query(Printer.id, Printer.patrimonio)
            .filter(Printer.id.in_(ids)).all()
        }

    def buscar_por_status(self, status_list):
        return self.session.query(Printer).filter(
            Printer.status.in_(status_list)
        ).order_by(Printer.patrimonio).all()

    def verificar_patrimonio_existe(self, patrimonio):
        return self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()

    def criar(self, patrimonio, modelo="", marca="", serial="", tipo="",
              local_atual="", status="Operacional", ip_rede="",
              tecnico="", observacao=""):
        printer = Printer(
            id=simple_uid(),
            patrimonio=patrimonio,
            modelo=modelo,
            marca=marca,
            serial=serial,
            tipo=tipo,
            local_atual=local_atual,
            status=status,
            ip_rede=ip_rede,
            tecnico=tecnico,
            observacao=observacao
        )
        self.session.add(printer)
        self.session.commit()
        return printer

    def atualizar(self, printer, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(printer, chave):
                setattr(printer, chave, valor)
        printer.updated_at = func.now()
        self.session.commit()

    def excluir(self, printer):
        self.session.delete(printer)
        self.session.commit()

    def contar_atividades(self, printer_ids):
        if not printer_ids:
            return {}
        return {
            pid: cnt
            for pid, cnt in (
                self.session.query(Activity.printer_id, func.count(Activity.id))
                .filter(Activity.printer_id.in_(printer_ids))
                .group_by(Activity.printer_id)
                .all()
            )
        }

    def total_por_status(self):
        dados = (
            self.session.query(Printer.status, func.count(Printer.id))
            .group_by(Printer.status).all()
        )
        return {s: c for s, c in dados}

    def modelos_distintos(self):
        return [
            m[0] for m in self.session.query(Printer.modelo)
            .filter(Printer.modelo != "").distinct().order_by(Printer.modelo).all()
            if m[0]
        ]

    def locais_distintos(self):
        return [
            l[0] for l in self.session.query(Printer.local_atual)
            .filter(Printer.local_atual != "").distinct().order_by(Printer.local_atual).all()
        ]

    def agrupar_por_status(self):
        dados = self.session.query(Printer.status, func.count(Printer.status)).group_by(Printer.status).all()
        return [(s[0], s[1]) for s in dados]

    def top_modelos(self, limite=5):
        dados = (
            self.session.query(Printer.modelo, func.count(Printer.modelo))
            .group_by(Printer.modelo)
            .order_by(func.count(Printer.modelo).desc())
            .limit(limite).all()
        )
        return [(m[0], m[1]) for m in dados]

    def contar_por_local(self, nome_local):
        return self.session.query(Printer).filter(
            Printer.local_atual.like(f"%{nome_local}%")
        ).count()
