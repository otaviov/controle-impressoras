from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.models.base import utcnow
from db import safe_commit
from sqlalchemy.orm import Session

from app.models import Part
from app.utils.cache import cached, invalidate
from app.utils.sanitize import sanitizar

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.part_movement import PartMovement
    from app.models.part_reservation import PartReservation
    from app.models.purchase_requisition import PurchaseRequisition
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class PartService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    @cached(ttl=15, namespace="part")
    def listar_todas(self, filtro: Optional[str] = None, limite: Optional[int] = None, offset: Optional[int] = None) -> list[Part]:
        query = self.session.query(Part).filter(Part.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Part.nome.like(f) | Part.codigo.like(f) | Part.modelo_compativel.like(f)
                | Part.marca.like(f) | Part.categoria.like(f) | Part.fornecedor.like(f)
            )
        query = query.order_by(Part.nome)
        if limite is not None:
            query = query.limit(limite)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def buscar_por_codigo(self, codigo: str) -> Optional[Part]:
        return self.session.query(Part).filter(Part.codigo == codigo).first()

    def buscar_por_nome(self, nome: str) -> Optional[Part]:
        return self.session.query(Part).filter(Part.nome == nome, Part.deleted_at == None).first()

    @cached(ttl=15, namespace="part")
    def buscar_por_id(self, part_id: int) -> Optional[Part]:
        return self.session.query(Part).filter(Part.deleted_at == None, Part.id == part_id).first()

    def criar(self, codigo: str, nome: str, descricao: str = "", modelo_compativel: str = "", quantidade: int = 0, estoque_minimo: int = 1, marca: str = "", categoria: str = "", fornecedor: str = "") -> Part:
        from app.utils.importer import normalizar_modelos
        peca = Part(
            codigo=sanitizar(codigo, "Part", "codigo"),
            nome=sanitizar(nome, "Part", "nome"),
            descricao=sanitizar(descricao),
            modelo_compativel=sanitizar(normalizar_modelos(modelo_compativel), "Part", "modelo_compativel"),
            quantidade_estoque=quantidade,
            estoque_minimo=estoque_minimo,
            preco_unitario=0.0,
            marca=sanitizar(marca, "Part", "marca"),
            categoria=sanitizar(categoria, "Part", "categoria"),
            fornecedor=sanitizar(fornecedor, "Part", "fornecedor"),
        )
        self.session.add(peca)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="parts", registro_id=peca.id, dados_depois=peca)
        invalidate("part")
        if quantidade > 0:
            self._log_movimento(peca, "entrada", quantidade, observacao="Estoque inicial")
        return peca

    def atualizar(self, peca: Part, **kwargs: Any) -> None:
        from app.utils.importer import normalizar_modelos
        quantidade_antiga = peca.quantidade_estoque
        if self.audit_service:
            dados_antes = {chave: getattr(peca, chave, None) for chave in kwargs}
        if "modelo_compativel" in kwargs and isinstance(kwargs["modelo_compativel"], str):
            kwargs["modelo_compativel"] = normalizar_modelos(kwargs["modelo_compativel"])
        for chave, valor in kwargs.items():
            if hasattr(peca, chave):
                if isinstance(valor, str):
                    valor = sanitizar(valor, "Part", chave)
                setattr(peca, chave, valor)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "atualizar", tabela_alvo="parts", registro_id=peca.id, dados_antes=dados_antes, dados_depois=peca)
        invalidate("part")
        if "quantidade_estoque" in kwargs:
            diff = peca.quantidade_estoque - quantidade_antiga
            if diff != 0:
                tipo = "entrada" if diff > 0 else "saida"
                self._log_movimento(peca, tipo, abs(diff), observacao="Ajuste manual")
                if peca.quantidade_estoque < peca.estoque_minimo:
                    self._criar_requisicao_auto(peca)

    def excluir(self, peca: Part) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="parts", registro_id=peca.id, dados_antes=peca)
        peca.deleted_at = utcnow()
        safe_commit(self.session)
        invalidate("part")

    @cached(ttl=15, namespace="part")
    def contar(self, filtro: Optional[str] = None) -> int:
        query = self.session.query(Part).filter(Part.deleted_at == None)
        if filtro:
            f = f"%{filtro}%"
            query = query.filter(
                Part.nome.like(f) | Part.codigo.like(f) | Part.modelo_compativel.like(f)
                | Part.marca.like(f) | Part.categoria.like(f) | Part.fornecedor.like(f)
            )
        return query.count()

    def gerar_codigo(self) -> str:
        count = self.contar()
        return f"PEC{count + 1:04d}"

    def listar_excluidos(self, limite: int = 50) -> list[Part]:
        return self.session.query(Part).filter(
            Part.deleted_at != None
        ).order_by(Part.deleted_at.desc()).limit(limite).all()

    def restaurar(self, obj: Part) -> None:
        obj.deleted_at = None
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "restaurar", tabela_alvo="parts", registro_id=obj.id)
        invalidate("part")

    # ── Movimentações ──────────────────────────────────────────

    def _log_movimento(self, part: Part, tipo: str, quantidade: int, activity_id: Optional[int] = None, observacao: str = "") -> PartMovement:
        from app.models.part_movement import PartMovement
        if part is None:
            log.warning("_log_movimento chamado com part=None, ignorando")
            part_id = 0
            saldo_anterior = 0
            saldo_posterior = 0
        else:
            part_id = part.id
            saldo_anterior = part.quantidade_estoque
            if tipo == "entrada":
                saldo_posterior = saldo_anterior + quantidade
            elif tipo == "saida":
                saldo_posterior = saldo_anterior - quantidade
            else:
                saldo_posterior = saldo_anterior
        mov = PartMovement(
            part_id=part_id,
            activity_id=activity_id,
            tipo=tipo,
            quantidade=quantidade,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            observacao=observacao,
        )
        self.session.add(mov)
        safe_commit(self.session)
        return mov

    def receber_estoque(self, part: Part, quantidade: int, observacao: str = "") -> PartMovement:
        part.quantidade_estoque += quantidade
        safe_commit(self.session)
        return self._log_movimento(part, "entrada", quantidade, observacao=observacao)

    def retirar_estoque_por_nome(self, nomes: str, activity_id: Optional[int] = None) -> None:
        for nome_peca in nomes.split(","):
            nome_peca = nome_peca.strip()
            if not nome_peca:
                continue
            part = self.buscar_por_nome(nome_peca)
            if part and part.quantidade_estoque > 0:
                self.retirar_estoque(part, activity_id=activity_id)

    def retirar_estoque(self, part: Part, quantidade: int = 1, activity_id: Optional[int] = None, observacao: str = "") -> PartMovement:
        if part.quantidade_estoque < quantidade:
            quantidade = part.quantidade_estoque
        part.quantidade_estoque -= quantidade
        safe_commit(self.session)
        mov = self._log_movimento(part, "saida", quantidade, activity_id=activity_id, observacao=observacao)
        if part.quantidade_estoque < part.estoque_minimo:
            self._criar_requisicao_auto(part)
        return mov

    def movimentacoes(self, part_id: int, limite: int = 100) -> list[PartMovement]:
        from app.models.part_movement import PartMovement
        return self.session.query(PartMovement).filter(
            PartMovement.part_id == part_id,
            PartMovement.deleted_at == None,
        ).order_by(PartMovement.created_at.desc()).limit(limite).all()

    def listar_movimentacoes_por_os(self, activity_id: int) -> list[PartMovement]:
        from app.models.part_movement import PartMovement
        return self.session.query(PartMovement).filter(
            PartMovement.activity_id == activity_id,
            PartMovement.deleted_at == None,
        ).order_by(PartMovement.created_at.asc()).all()

    def movimentacoes_geral(self, limite: int = 200) -> list[PartMovement]:
        from app.models.part_movement import PartMovement
        return self.session.query(PartMovement).filter(
            PartMovement.deleted_at == None,
        ).order_by(PartMovement.created_at.desc()).limit(limite).all()

    def estornar_movimento(self, movimento_id: int) -> None:
        from app.models.part_movement import PartMovement
        mov = self.session.query(PartMovement).filter(
            PartMovement.id == movimento_id,
            PartMovement.deleted_at == None,
        ).first()
        if not mov:
            log.warning("estornar_movimento #%s: não encontrado ou já estornado", movimento_id)
            return
        part = self.session.query(Part).filter(Part.id == mov.part_id).first()
        if part is None:
            log.warning("estornar_movimento #%s: peça não encontrada", movimento_id)
            return
        if mov.tipo == "entrada":
            part.quantidade_estoque -= mov.quantidade
        elif mov.tipo in ("saida", "reserva", "cancelamento_reserva"):
            part.quantidade_estoque += mov.quantidade
        mov.deleted_at = utcnow()
        safe_commit(self.session)
        log.info("Movimento #%s estornado (tipo=%s, qtd=%s)", movimento_id, mov.tipo, mov.quantidade)

    # ── Reservas ───────────────────────────────────────────────

    def criar_reserva(self, part_id: int, activity_id: int, quantidade: int = 1) -> Optional[PartReservation]:
        from app.models.part_reservation import PartReservation
        part = self.buscar_por_id(part_id)
        if not part or part.quantidade_estoque < quantidade:
            return None
        part.quantidade_estoque -= quantidade
        self._log_movimento(part, "reserva", quantidade, activity_id=activity_id)
        res = PartReservation(part_id=part_id, activity_id=activity_id, quantidade=quantidade)
        self.session.add(res)
        safe_commit(self.session)
        return res

    def reservas_por_os(self, activity_id: int) -> list[PartReservation]:
        from app.models.part_reservation import PartReservation
        return self.session.query(PartReservation).filter(
            PartReservation.activity_id == activity_id
        ).order_by(PartReservation.created_at.asc()).all()

    def usar_reserva(self, reservation_id: int) -> None:
        from app.models.part_movement import PartMovement
        from app.models.part_reservation import PartReservation
        res = self.session.query(PartReservation).filter(PartReservation.id == reservation_id).first()
        if not res or res.status != "reservada":
            return
        res.status = "usada"
        res.updated_at = utcnow()
        part = res.part
        if part is None:
            log.warning("usar_reserva #%s: part not found", reservation_id)
            safe_commit(self.session)
            return
        self._log_movimento(part, "saida", res.quantidade, activity_id=res.activity_id, observacao="Reserva consumida")
        safe_commit(self.session)
        if part.quantidade_estoque < part.estoque_minimo:
            self._criar_requisicao_auto(part)

    def cancelar_reserva(self, reservation_id: int) -> None:
        from app.models.part_reservation import PartReservation
        res = self.session.query(PartReservation).filter(PartReservation.id == reservation_id).first()
        if not res or res.status != "reservada":
            return
        res.status = "cancelada"
        res.updated_at = utcnow()
        part = res.part
        if part is None:
            log.warning("cancelar_reserva #%s: part not found", reservation_id)
            safe_commit(self.session)
            return
        part.quantidade_estoque += res.quantidade
        self._log_movimento(part, "cancelamento_reserva", res.quantidade, activity_id=res.activity_id, observacao="Reserva cancelada")
        safe_commit(self.session)

    def listar_reservas_pendentes(self) -> list[PartReservation]:
        from app.models.part_reservation import PartReservation
        return self.session.query(PartReservation).filter(
            PartReservation.status == "reservada"
        ).order_by(PartReservation.created_at.asc()).all()

    # ── Requisições de Compra ──────────────────────────────────

    def _criar_requisicao_auto(self, part: Part) -> None:
        from app.models.purchase_requisition import PurchaseRequisition
        existente = self.session.query(PurchaseRequisition).filter(
            PurchaseRequisition.part_id == part.id,
            PurchaseRequisition.status == "pendente",
        ).first()
        if existente:
            return
        qtd = max(part.estoque_minimo * 2 - part.quantidade_estoque, 1)
        req = PurchaseRequisition(
            part_id=part.id,
            quantidade_sugerida=qtd,
            observacao=f"Estoque abaixo do mínimo ({part.quantidade_estoque} < {part.estoque_minimo})",
        )
        self.session.add(req)
        safe_commit(self.session)

    def criar_requisicao(self, part_id: int, quantidade: int = 1, observacao: str = "") -> PurchaseRequisition:
        from app.models.purchase_requisition import PurchaseRequisition
        req = PurchaseRequisition(
            part_id=part_id,
            quantidade_sugerida=quantidade,
            observacao=observacao,
        )
        self.session.add(req)
        safe_commit(self.session)
        return req

    def listar_requisicoes(self, status: Optional[str] = None, limite: int = 100) -> list[PurchaseRequisition]:
        from app.models.purchase_requisition import PurchaseRequisition
        query = self.session.query(PurchaseRequisition).order_by(PurchaseRequisition.created_at.desc())
        if status:
            query = query.filter(PurchaseRequisition.status == status)
        return query.limit(limite).all()

    def aprovar_requisicao(self, req_id: int) -> None:
        from app.models.purchase_requisition import PurchaseRequisition
        req = self.session.query(PurchaseRequisition).filter(PurchaseRequisition.id == req_id).first()
        if req and req.status == "pendente":
            req.status = "aprovada"
            req.updated_at = datetime.utcnow()
            safe_commit(self.session)

    def receber_requisicao(self, req_id: int) -> None:
        from app.models.purchase_requisition import PurchaseRequisition
        req = self.session.query(PurchaseRequisition).filter(PurchaseRequisition.id == req_id).first()
        if req and req.status in ("pendente", "aprovada"):
            part = self.buscar_por_id(req.part_id)
            if part:
                self.receber_estoque(part, req.quantidade_sugerida, observacao=f"Requisição #{req.id}")
            req.status = "recebida"
            req.updated_at = datetime.utcnow()
            safe_commit(self.session)

    def cancelar_requisicao(self, req_id: int) -> None:
        from app.models.purchase_requisition import PurchaseRequisition
        req = self.session.query(PurchaseRequisition).filter(PurchaseRequisition.id == req_id).first()
        if req and req.status != "recebida":
            req.status = "cancelada"
            req.updated_at = datetime.utcnow()
            safe_commit(self.session)
