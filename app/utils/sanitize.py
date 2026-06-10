from typing import Any, Optional

COLUMN_LENGTHS: dict[str, dict[str, int]] = {
    "Printer": {"patrimonio": 80, "modelo": 80, "serial": 80, "status": 30, "local_atual": 120, "marca": 80, "tipo": 20, "ip_rede": 45, "mac_address": 17, "tecnico": 120, "foto_path": 255, "urgencia_prox_manutencao": 20},
    "Activity": {"kind": 30, "numero_recibo": 50, "status_atividade": 30, "from_location": 120, "to_location": 120, "responsavel": 120, "urgencia": 20},
    "Company": {"nome": 150, "cnpj": 18, "endereco": 255, "cidade": 100, "uf": 2, "telefone": 20, "email": 120, "tipo": 20},
    "User": {"nome": 120, "email": 120, "username": 50, "perfil": 20},
    "Technician": {"nome_completo": 150, "nome_exibicao": 80, "telefone": 20, "email": 120},
    "Part": {"codigo": 50, "nome": 150, "modelo_compativel": 200},
    "Alert": {"tipo": 20, "titulo": 200},
    "PrinterLocation": {"local": 120, "observacao": 255},
    "Transfer": {"numero_os": 50, "tipo": 20, "responsavel_entrega": 120, "responsavel_recebimento": 120},
    "Attachment": {"entity_type": 50, "filename": 255, "original_name": 255, "mime_type": 100, "categoria": 50},
}


def truncar(valor: str, max_len: int) -> str:
    if not valor:
        return ""
    return valor.strip()[:max_len]


def sanitizar(valor: Any, model_class: Optional[str] = None, field: Optional[str] = None, max_len: Optional[int] = None) -> Any:
    if valor is None:
        return None
    if not isinstance(valor, str):
        return valor
    valor = valor.strip()
    if model_class and field:
        col_len = COLUMN_LENGTHS.get(model_class, {}).get(field)
        if col_len:
            valor = valor[:col_len]
    if max_len:
        valor = valor[:max_len]
    return valor
