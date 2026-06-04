from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.orm import Session

from app.models import Printer, PrinterLocation
from app.utils.sanitize import sanitizar
from db import safe_commit

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

log = logging.getLogger(__name__)


class PrinterLocationService:
    def __init__(self, session: Session, audit_service: Optional[AuditService] = None, user_id: Optional[int] = None) -> None:
        self.session: Session = session
        self.audit_service: Optional[AuditService] = audit_service
        self.user_id: Optional[int] = user_id

    def listar_por_impressora(self, printer_id: str, limite: int = 200) -> list[PrinterLocation]:
        return self.session.query(PrinterLocation).filter(
            PrinterLocation.printer_id == printer_id
        ).order_by(PrinterLocation.data.desc().nullslast(), PrinterLocation.created_at.desc()).limit(limite).all()

    def adicionar(self, printer_id: str, local: str, data: Optional[datetime] = None, observacao: str = "") -> PrinterLocation:
        reg = PrinterLocation(
            printer_id=printer_id,
            local=sanitizar(local, "PrinterLocation", "local"),
            data=data,
            observacao=sanitizar(observacao, "PrinterLocation", "observacao")
        )
        self.session.add(reg)
        safe_commit(self.session)
        if self.audit_service:
            self.audit_service.log(self.user_id, "criar", tabela_alvo="printer_locations", registro_id=str(reg.id), dados_depois=reg)
        return reg

    def excluir(self, reg: PrinterLocation) -> None:
        if self.audit_service:
            self.audit_service.log(self.user_id, "excluir", tabela_alvo="printer_locations", registro_id=str(reg.id), dados_antes=reg)
        self.session.delete(reg)
        safe_commit(self.session)

    def importar(self, printer_id: str, registros: list[dict[str, Any]]) -> int:
        importados = 0
        for r in registros:
            local = r.get("local") or r.get("Local") or ""
            data = r.get("data") or r.get("Data") or None
            obs = r.get("observacao") or r.get("Observacao") or r.get("Observação") or ""
            if data:
                try:
                    data = datetime.strptime(str(data).strip(), "%d/%m/%Y")
                except ValueError:
                    try:
                        data = datetime.strptime(str(data).strip(), "%Y-%m-%d")
                    except ValueError:
                        data = None
            self.adicionar(printer_id, local, data, obs)
            importados += 1
        return importados
