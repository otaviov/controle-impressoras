from datetime import datetime

from app.utils.helpers import encurtar, formatar_data, formatar_data_hora, limpar_local, parse_data
from app.utils.sanitize import sanitizar, truncar


# ── sanitizar ─────────────────────────────────────────────────

def test_sanitizar_none():
    assert sanitizar(None) is None


def test_sanitizar_nao_string():
    assert sanitizar(42) == 42
    assert sanitizar(0) == 0
    assert sanitizar(True) is True


def test_sanitizar_strip():
    assert sanitizar("  texto  ") == "texto"


def test_sanitizar_truncate_by_model():
    v = sanitizar("a" * 200, model_class="User", field="nome")
    assert len(v) <= 120


def test_sanitizar_truncate_by_max_len():
    v = sanitizar("abcdefghij", max_len=5)
    assert v == "abcde"


def test_sanitizar_with_all_params_none():
    assert sanitizar("texto") == "texto"


# ── truncar ───────────────────────────────────────────────────

def test_truncar_empty():
    assert truncar("", 10) == ""


def test_truncar_none():
    assert truncar(None, 10) == ""


def test_truncar_whitespace():
    assert truncar("   ", 10) == ""


def test_truncar_shorter_than_max():
    assert truncar("abc", 10) == "abc"


def test_truncar_exact_match():
    assert truncar("12345", 5) == "12345"


def test_truncar_longer():
    assert truncar("abcdefghij", 5) == "abcde"


# ── limpar_local ──────────────────────────────────────────────

def test_limpar_local_none():
    assert limpar_local(None) == ""


def test_limpar_local_empty():
    assert limpar_local("") == ""


def test_limpar_local_no_prefix():
    assert limpar_local("Matriz") == "Matriz"


def test_limpar_local_com_prefixo_predio():
    assert limpar_local("\U0001f3e2 Filial A") == "Filial A"


def test_limpar_local_com_prefixo_pino():
    assert limpar_local("\U0001f4cd Sala 3") == "Sala 3"


def test_limpar_local_apenas_prefixo():
    assert limpar_local("\U0001f3e2 ") == ""


# ── formatar_data ─────────────────────────────────────────────

def test_formatar_data_none():
    assert formatar_data(None) == "-"


def test_formatar_data_valida():
    d = datetime(2025, 12, 25)
    assert formatar_data(d) == "25/12/2025"


def test_formatar_data_formato_personalizado():
    d = datetime(2025, 1, 1)
    assert formatar_data(d, "%Y-%m-%d") == "2025-01-01"


# ── formatar_data_hora ────────────────────────────────────────

def test_formatar_data_hora_none():
    assert formatar_data_hora(None) == "-"


def test_formatar_data_hora_valida():
    d = datetime(2025, 6, 15, 14, 30, 0)
    assert formatar_data_hora(d) == "15/06/2025 14:30"


# ── parse_data ────────────────────────────────────────────────

def test_parse_data_none():
    assert parse_data(None) is None


def test_parse_data_empty():
    assert parse_data("") is None


def test_parse_data_formato_completo():
    r = parse_data("25/12/2025 14:30")
    assert r is not None
    assert r.hour == 14
    assert r.minute == 30


def test_parse_data_formato_curto():
    r = parse_data("01/01/2026")
    assert r is not None
    assert r.day == 1
    assert r.month == 1
    assert r.year == 2026
    assert r.hour == 0


def test_parse_data_invalida():
    assert parse_data("31/02/2025") is None


def test_parse_data_formato_errado():
    assert parse_data("2025-01-01") is None


def test_parse_data_texto_puro():
    assert parse_data("abc") is None


def test_parse_data_com_espacos():
    assert parse_data("  25/12/2025  ") is not None


# ── encurtar ──────────────────────────────────────────────────

def test_encurtar_none():
    assert encurtar(None) == "-"


def test_encurtar_empty():
    assert encurtar("") == "-"


def test_encurtar_short():
    assert encurtar("abc") == "abc"


def test_encurtar_exact():
    assert encurtar("a" * 40) == "a" * 40


def test_encurtar_long():
    result = encurtar("a" * 100)
    assert len(result) == 40
    assert result.endswith("...")


def test_encurtar_custom_max():
    result = encurtar("abcdefghij", max_len=6)
    assert result == "abc..."
