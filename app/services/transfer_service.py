import logging

from db import safe_commit

log = logging.getLogger(__name__)
from datetime import datetime

from sqlalchemy import func

from app.models import Transfer
from app.utils.sanitize import sanitizar


class TransferService:
    def __init__(self, session, audit_service=None, user_id=None):
        self.session = session
        self.audit_service = audit_service
        self.user_id = user_id

    def listar_todas(self, limite=200, offset=None):
        query = self.session.query(Transfer).filter(Transfer.deleted_at == None).order_by(Transfer.created_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_impressora(self, printer_id, limite=None, offset=None):
        query = self.session.query(Transfer).filter(Transfer.deleted_at == None).filter(
            Transfer.printer_id == printer_id
        ).order_by(Transfer.created_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def listar_por_tipo(self, tipo, limite=100, offset=None):
        query = self.session.query(Transfer).filter(Transfer.deleted_at == None).filter(
            Transfer.tipo == tipo
        ).order_by(Transfer.created_at.desc())
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_id(self, transfer_id):
        return self.session.query(Transfer).filter(Transfer.deleted_at == None, Transfer.id == transfer_id).first()

    def buscar_por_numero_os(self, numero_os):
        return self.session.query(Transfer).filter(
            Transfer.deleted_at == None, Transfer.numero_os == numero_os
        ).order_by(Transfer.created_at.desc()).all()

    def criar(self, printer_id, numero_os="", tipo="saida",
              from_company_id=None, to_company_id=None,
              responsavel_entrega="", responsavel_recebimento="",
              data_saida=None, data_retorno_prev=None, observacao=""):
        t = Transfer(
            printer_id=printer_id,
            numero_os=sanitizar(numero_os, "Transfer", "numero_os"),
            tipo=sanitizar(tipo, "Transfer", "tipo"),
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            responsavel_entrega=sanitizar(responsavel_entrega, "Transfer", "responsavel_entrega"),
            responsavel_recebimento=sanitizar(responsavel_recebimento, "Transfer", "responsavel_recebimento"),
            data_saida=data_saida or datetime.now(),
            data_retorno_prev=data_retorno_prev,
            observacao=observacao,
        )
        self.session.add(t)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="transfers", registro_id=t.id, dados_depois=t)
        return t

    def atualizar(self, transferencia, **kwargs):
        if self.audit_service:
            dados_antes = {chave: getattr(transferencia, chave, None) for chave in kwargs}
        for chave, valor in kwargs.items():
            if hasattr(transferencia, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Transfer", chave)
                setattr(transferencia, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="transfers", registro_id=transferencia.id, dados_antes=dados_antes, dados_depois=transferencia)

    def registrar_retorno(self, transferencia):
        if self.audit_service:
            self.audit_service.log(self.user_id, "registrar_retorno", tabela_alvo="transfers", registro_id=transferencia.id, dados_antes=transferencia)
        transferencia.data_retorno_real = datetime.now()
        safe_commit(self.session)

    def excluir(self, transferencia):
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="transfers", registro_id=transferencia.id, dados_antes=transferencia)
        transferencia.deleted_at = datetime.utcnow()
        safe_commit(self.session)

    def contar_pendentes(self):
        return self.session.query(Transfer).filter(
            Transfer.deleted_at == None, Transfer.data_retorno_real == None
        ).count()

    def contar_por_tipo(self):
        dados = self.session.query(Transfer.tipo, func.count(Transfer.id)).group_by(Transfer.tipo).all()
        return {t: c for t, c in dados}

    def contar_por_mes(self, ano, mes):
        inicio = datetime(ano, mes, 1)
        fim = datetime(ano + 1, 1, 1) if mes == 12 else datetime(ano, mes + 1, 1)
        return self.session.query(Transfer).filter(
            Transfer.created_at >= inicio, Transfer.created_at < fim
        ).count()

    def listar_excluidos(self, limite=50):
        return self.session.query(Transfer).filter(
            Transfer.deleted_at != None
        ).order_by(Transfer.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj):
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="transfers", registro_id=obj.id)

