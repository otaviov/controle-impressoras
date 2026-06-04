from datetime import datetime
from typing import Optional


def limpar_local(texto: Optional[str]) -> str:
    if not texto:
        return ""
    for prefixo in ["🏢 ", "📍 "]:
        if texto.startswith(prefixo):
            return texto[len(prefixo):].strip()
    return texto.strip()


def formatar_data(data: Optional[datetime], formato: str = "%d/%m/%Y") -> str:
    return data.strftime(formato) if data else "-"


def formatar_data_hora(data: Optional[datetime], formato: str = "%d/%m/%Y %H:%M") -> str:
    return data.strftime(formato) if data else "-"


def parse_data(texto: Optional[str]) -> Optional[datetime]:
    if not texto:
        return None
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try:
            return datetime.strptime(texto.strip(), fmt)
        except ValueError:
            continue
    return None


def encurtar(texto: Optional[str], max_len: int = 40) -> str:
    if not texto:
        return "-"
    if len(texto) > max_len:
        return texto[:max_len-3] + "..."
    return texto
