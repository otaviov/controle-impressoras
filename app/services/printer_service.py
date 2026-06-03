import logging
from datetime import datetime

from sqlalchemy import func

from app.models import Activity, Printer
from app.utils.sanitize import sanitizar
from db import safe_commit

log = logging.getLogger(__name__)


class PrinterService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todos(self, filtro=None, limite=None, offset=None):
        query = self.session.query(Printer).filter(Printer.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Printer.patrimonio.like(f) | Printer.modelo.like(f) |
                Printer.serial.like(f) | Printer.local_atual.like(f) |
                Printer.marca.like(f)
            )
        query = query.order_by(Printer.patrimonio)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_patrimonio(self, patrimonio):
        return self.session.query(Printer).filter(Printer.deleted_at == None, Printer.patrimonio == patrimonio).first()

    def buscar_por_id(self, printer_id):
        return self.session.query(Printer).filter(Printer.deleted_at == None, Printer.id == printer_id).first()

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
            .filter(Printer.deleted_at == None, Printer.id.in_(ids)).all()
        }

    def buscar_por_status(self, status_list):
        return self.session.query(Printer).filter(
            Printer.status.in_(status_list)
        ).order_by(Printer.patrimonio).all()

    def verificar_patrimonio_existe(self, patrimonio):
        return self.session.query(Printer).filter(Printer.patrimonio == patrimonio).first()

    def criar(self, patrimonio, modelo="", marca="", serial="", tipo="",
              local_atual="", status="Operacional", ip_rede="",
              mac_address="", tecnico="", observacao=""):
        printer = Printer(
            patrimonio=sanitizar(patrimonio, "Printer", "patrimonio"),
            modelo=sanitizar(modelo, "Printer", "modelo"),
            marca=sanitizar(marca, "Printer", "marca"),
            serial=sanitizar(serial, "Printer", "serial"),
            tipo=sanitizar(tipo, "Printer", "tipo"),
            local_atual=sanitizar(local_atual, "Printer", "local_atual"),
            status=sanitizar(status, "Printer", "status"),
            ip_rede=sanitizar(ip_rede, "Printer", "ip_rede"),
            mac_address=sanitizar(mac_address, "Printer", "mac_address"),
            tecnico=sanitizar(tecnico, "Printer", "tecnico"),
            observacao=sanitizar(observacao, "Printer", "observacao")
        )
        self.session.add(printer)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="printers", registro_id=printer.id, dados_depois=printer)
        return printer

    def atualizar(self, printer, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(printer, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(printer, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Printer", chave)
                setattr(printer, chave, valor)
        printer.updated_at = func.now()
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="printers", registro_id=printer.id, dados_antes=dados_antes, dados_depois=printer)

    def excluir(self, printer):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="printers", registro_id=printer.id, dados_antes=printer)
        printer.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_todos(self, filtro=None):
        query = self.session.query(Printer).filter(Printer.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Printer.patrimonio.like(f) | Printer.modelo.like(f) |
                Printer.serial.like(f) | Printer.local_atual.like(f) |
                Printer.marca.like(f)
            )
        return query.count()

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
            m[0] for m in self.session.query(Printer.modelo).filter(Printer.deleted_at == None)
            .filter(Printer.modelo != "").distinct().order_by(Printer.modelo).all()
            if m[0]
        ]

    def locais_distintos(self):
        return [
            l[0] for l in self.session.query(Printer.local_atual).filter(Printer.deleted_at == None)
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

    def listar_patrimonios(self, status=None):
        query = self.session.query(Printer.patrimonio)
        if status and status != "Todos":
            query = query.filter(Printer.status == status)
        return [p[0] for p in query.order_by(Printer.patrimonio).all()]

    def listar_patrimonios_por_busca(self, texto, status=None):
        query = self.session.query(Printer.patrimonio)
        if status and status != "Todos":
            query = query.filter(Printer.status == status)
        if texto.strip():
            query = query.filter(Printer.patrimonio.like(f"%{texto.strip()}%"))
        return [p[0] for p in query.order_by(Printer.patrimonio).all()]

    def listar_por_local(self, local):
        return self.session.query(Printer).filter(
            Printer.local_atual == local
        ).order_by(Printer.patrimonio).all()

    def atualizar_local_por_nome_antigo(self, nome_antigo, nome_novo):
        impressoraS = self.session.query(Printer).filter(
            Printer.local_atual == nome_antigo
        ).all()
        for p in impressoraS:
            p.local_atual = nome_novo
        safe_commit(self.session)

    def listar_por_filtros(self, status=None, patrimonio=None, modelo=None, local=None):
        query = self.session.query(Printer).filter(Printer.deleted_at == None)
        if status and status != "Todos":
            query = query.filter(Printer.status == status)
        if patrimonio:
            query = query.filter(Printer.patrimonio.like(f"%{patrimonio}%"))
        if modelo and modelo != "Todos":
            query = query.filter(Printer.modelo == modelo)
        if local and local != "Todos":
            query = query.filter(Printer.local_atual.like(f"%{local}%"))
        return query.order_by(Printer.patrimonio).all()

    def listar_excluidos(self, limite=50):
        return self.session.query(Printer).filter(
            Printer.deleted_at != None
        ).order_by(Printer.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="printers", registro_id=obj.id)
