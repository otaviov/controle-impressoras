from datetime import datetime


def limpar_local(texto):
    """Remove prefixos de local (🏢, 📍)"""
    if not texto:
        return ""
    for prefixo in ["🏢 ", "📍 "]:
        if texto.startswith(prefixo):
            return texto[len(prefixo):].strip()
    return texto.strip()


def formatar_data(data, formato="%d/%m/%Y"):
    return data.strftime(formato) if data else "-"


def formatar_data_hora(data, formato="%d/%m/%Y %H:%M"):
    return data.strftime(formato) if data else "-"


def parse_data(texto):
    """Tenta parsear data nos formatos dd/mm/aaaa HH:MM e dd/mm/aaaa"""
    if not texto:
        return None
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try:
            return datetime.strptime(texto.strip(), fmt)
        except ValueError:
            continue
    return None


def encurtar(texto, max_len=40):
    if not texto:
        return "-"
    if len(texto) > max_len:
        return texto[:max_len-3] + "..."
    return texto
