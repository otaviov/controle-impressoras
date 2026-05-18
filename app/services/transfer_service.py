from datetime import datetime
from sqlalchemy import func
from app.models import Transfer


class TransferService:
    def __init__(self, session):
        self.session = session

    def listar_todas(self, limite=200):
        return self.session.query(Transfer).order_by(Transfer.created_at.desc()).limit(limite).all()

    def listar_por_impressora(self, printer_id):
        return self.session.query(Transfer).filter(
            Transfer.printer_id == printer_id
        ).order_by(Transfer.created_at.desc()).all()

    def listar_por_tipo(self, tipo, limite=100):
        return self.session.query(Transfer).filter(
            Transfer.tipo == tipo
        ).order_by(Transfer.created_at.desc()).limit(limite).all()

    def buscar_por_id(self, transfer_id):
        return self.session.query(Transfer).filter(Transfer.id == transfer_id).first()

    def buscar_por_numero_os(self, numero_os):
        return self.session.query(Transfer).filter(
            Transfer.numero_os == numero_os
        ).order_by(Transfer.created_at.desc()).all()

    def criar(self, printer_id, numero_os="", tipo="saida",
              from_company_id=None, to_company_id=None,
              responsavel_entrega="", responsavel_recebimento="",
              data_saida=None, data_retorno_prev=None, observacao=""):
        t = Transfer(
            printer_id=printer_id,
            numero_os=numero_os,
            tipo=tipo,
            from_company_id=from_company_id,
            to_company_id=to_company_id,
            responsavel_entrega=responsavel_entrega,
            responsavel_recebimento=responsavel_recebimento,
            data_saida=data_saida or datetime.now(),
            data_retorno_prev=data_retorno_prev,
            observacao=observacao,
        )
        self.session.add(t)
        self.session.commit()
        return t

    def atualizar(self, transferencia, **kwargs):
        for chave, valor in kwargs.items():
            if hasattr(transferencia, chave):
                setattr(transferencia, chave, valor)
        self.session.commit()

    def registrar_retorno(self, transferencia):
        transferencia.data_retorno_real = datetime.now()
        self.session.commit()

    def excluir(self, transferencia):
        self.session.delete(transferencia)
        self.session.commit()

    def contar_pendentes(self):
        return self.session.query(Transfer).filter(
            Transfer.data_retorno_real == None
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
