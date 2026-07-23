"""
Organiza a planilha de peças para importação no sistema.
Separa descrição em nome + modelo, limpa dados e gera xlsx pronto.
"""
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side


# ── Palavras que indicam modelo/spec (não são nome da peça) ──
_MODELPattern = re.compile(
    r"(?:^|\s)"
    r"("
    r"[A-Z]{1,3}\s?\d{2,5}(?:[/\-]\s?[A-Z]{0,3}\d{1,5})*"  # HP P1102/M1132, SCX 4833/SCX 5637
    r"|P\d{3,5}(?:[/\-]\d{1,5})*"                             # P2035, P1102
    r"|\d{3,5}[A-Z]?"                                          # 1010, 2035, 8157
    r"|[A-Z]\d{3,5}(?:[/\-]\d{1,5})*"                         # M1132, L4150, T650
    r"|SCX\s?\d{3,5}(?:[/\-]?\s?[A-Z]{0,3}\d{1,5})*"         # SCX 4833/SCX 5637/M4070
    r"|ML\s?\d{3,5}"                                           # ML 2851
    r"|FS\s?\d{3,5}"                                           # FS1035
    r"|X\d{3,5}"                                               # X203
    r")"
    r"(?:\s*\([^)]*\))?"                                       # (PAR), (CONJUNTO)
    r"(?:\s+(?:METALICO|RESERVA|CONJUNTO))?"                   # sufixos descritivos
)


def _limpar_descricao(desc: str, marca: str) -> tuple[str, str]:
    """Separa 'ROLO DE PRESSAO HP P1102/M1132' → ('ROLO DE PRESSAO', 'HP P1102/M1132')"""
    desc = desc.strip()

    # Remove marca do início se presente
    if desc.upper().startswith(marca.upper()):
        desc = desc[len(marca):].strip()

    # Tenta extrair modelo do final
    modelos_encontrados = list(_MODELPattern.finditer(desc))

    if modelos_encontrados:
        ultimo = modelos_encontrados[-1]
        nome = desc[:ultimo.start()].strip()
        modelo = desc[ultimo.start():].strip()

        # Limpa nome: remove marca se sobrou
        nome = re.sub(rf"\b{re.escape(marca)}\b", "", nome, flags=re.IGNORECASE).strip()
        # Remove espaços duplos
        nome = re.sub(r"\s+", " ", nome).strip()
        modelo = re.sub(r"\s+", " ", modelo).strip()

        # Remove marca duplicada do modelo (ex: "HP HP 4014" → "HP 4014")
        modelo = re.sub(rf"^{re.escape(marca)}\s+{re.escape(marca)}\b", marca, modelo, flags=re.IGNORECASE)

        # Se nome ficou vazio, usa a descrição toda como nome
        if not nome:
            nome = desc.strip()

        return nome, modelo

    # Sem modelo encontrado: tudo é nome
    nome = re.sub(rf"\b{re.escape(marca)}\b", "", desc, flags=re.IGNORECASE).strip()
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome or desc, ""


def processar_arquivo(caminho: str) -> list[dict]:
    """Lê todas as abas e retorna lista de dicts organizados."""
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    pecas = []

    for sheet_name in wb.sheetnames:
        if sheet_name.upper() == "INDICE":
            continue

        marca = sheet_name.strip()
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))

        # Encontra a linha do cabeçalho (contém "N", "QTD", etc.)
        header_idx = None
        for i, row in enumerate(rows):
            if row and any(c and str(c).upper().strip() in ("N", "NUM", "Nº") for c in row if c):
                header_idx = i
                break

        if header_idx is None:
            continue

        header = [str(c or "").upper().strip() for c in rows[header_idx]]

        # Mapeia índices das colunas
        col_map = {}
        for i, h in enumerate(header):
            if h in ("N", "NUM", "Nº"):
                col_map["n"] = i
            elif h in ("QTD", "QTDE", "QUANTIDADE"):
                col_map["qtd"] = i
            elif "COD" in h or "REFERENC" in h or "REF" in h:
                col_map["codigo"] = i
            elif "DESCR" in h:
                col_map["descricao"] = i
            elif "CATEG" in h:
                col_map["categoria"] = i
            elif "STATUS" in h:
                col_map["status"] = i
            elif "FORNEC" in h:
                col_map["fornecedor"] = i
            elif "NOTA" in h:
                col_map["nota"] = i
            elif "DATA" in h:
                col_map["data"] = i

        # Processa linhas de dados
        for row in rows[header_idx + 1:]:
            if not row:
                continue

            # Pula linhas de resumo/rodapé
            n_val = row[col_map.get("n", 0)] if col_map.get("n") is not None else None
            if n_val is None or not str(n_val).strip().isdigit():
                continue

            qtd_val = row[col_map.get("qtd", 1)] if col_map.get("qtd") is not None else 0
            try:
                qtd = int(float(str(qtd_val or 0)))
            except (ValueError, TypeError):
                qtd = 0

            cod_val = row[col_map.get("codigo", 3)] if col_map.get("codigo") is not None else ""
            codigo = str(cod_val or "").strip()

            desc_val = row[col_map.get("descricao", 4)] if col_map.get("descricao") is not None else ""
            descricao = str(desc_val or "").strip()

            cat_val = row[col_map.get("categoria", 5)] if col_map.get("categoria") is not None else ""
            categoria = str(cat_val or "").strip()

            status_val = row[col_map.get("status", 6)] if col_map.get("status") is not None else ""
            status_planilha = str(status_val or "").strip()

            fornec_val = row[col_map.get("fornecedor", 7)] if col_map.get("fornecedor") is not None else ""
            fornecedor = str(fornec_val or "").strip()

            if not descricao or descricao.upper() == "DESCRICAO":
                continue

            nome, modelo = _limpar_descricao(descricao, marca)

            # Modelo compativel: marca + modelo, mas evita marca duplicada
            if modelo:
                if modelo.upper().startswith(marca.upper()):
                    modelo_compat = modelo
                else:
                    modelo_compat = f"{marca} {modelo}".strip()
            else:
                modelo_compat = marca

            # Status do sistema baseado no estoque
            if qtd <= 0:
                status_sistema = "Sem Estoque"
            elif status_planilha.upper() == "BAIXO":
                status_sistema = "Baixo"
            else:
                status_sistema = "Normal"

            pecas.append({
                "marca": marca,
                "codigo": codigo if codigo and codigo.upper() != "DESCONHECIDO" else "",
                "nome": nome,
                "descricao": descricao,
                "modelo": modelo,
                "modelo_compativel": modelo_compat,
                "quantidade_estoque": qtd,
                "categoria": categoria,
                "status_original": status_planilha,
                "status_sistema": status_sistema,
                "fornecedor": fornecedor if fornecedor != "-" else "",
            })

    wb.close()
    return pecas


def gerar_xlsx(pecas: list[dict], saida: str) -> None:
    """Gera planilha limpa para importação."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Peças Importação"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    # Cabeçalho
    colunas = ["Código", "Nome", "Descrição", "Modelo Compatível", "Quantidade",
               "Estoque Mínimo", "Categoria", "Marca", "Fornecedor"]
    for c, titulo in enumerate(colunas, 1):
        cell = ws.cell(row=1, column=c, value=titulo)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # Dados
    for i, p in enumerate(pecas, 2):
        dados = [
            p["codigo"],
            p["nome"],
            p["descricao"],
            p["modelo_compativel"],
            p["quantidade_estoque"],
            1,  # estoque mínimo padrão
            p["categoria"],
            p["marca"],
            p["fornecedor"],
        ]
        for c, val in enumerate(dados, 1):
            cell = ws.cell(row=i, column=c, value=val)
            cell.border = thin_border
            if c in (5, 6):
                cell.alignment = Alignment(horizontal="center")

    # Larguras das colunas
    larguras = [15, 40, 50, 30, 12, 15, 25, 15, 25]
    for c, larg in enumerate(larguras, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(c)].width = larg

    # Congela primeira linha
    ws.freeze_panes = "A2"

    # Auto-filtro
    ws.auto_filter.ref = ws.dimensions

    wb.save(saida)
    print(f"Planilha salva em: {saida}")
    print(f"Total de peças: {len(pecas)}")


if __name__ == "__main__":
    entrada = r"C:\Users\Suporte Tecnico\Downloads\Planilha atualizada de pecas\PECAS_IMPRESSORAS_RECIFE_v2.xlsx"
    saida = r"C:\Users\Suporte Tecnico\Downloads\Planilha atualizada de pecas\PECAS_IMPORTACAO_v2.xlsx"

    if len(sys.argv) > 1:
        entrada = sys.argv[1]
    if len(sys.argv) > 2:
        saida = sys.argv[2]

    print(f"Lendo: {entrada}")
    pecas = processar_arquivo(entrada)
    print(f"Peças encontradas: {len(pecas)}")

    # Mostra preview
    print("\n=== Preview (10 primeiras) ===")
    for p in pecas[:10]:
        print(f"  Nome: {p['nome']:35s} | Modelo: {p['modelo_compativel']:25s} | Qtd: {p['quantidade_estoque']}")

    print(f"\nGerando planilha de importação...")
    gerar_xlsx(pecas, saida)
