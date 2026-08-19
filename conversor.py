import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Preformatted, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def converter_para_pdf():
    pdf_nome = "todos_os_codigos.pdf"
    doc = SimpleDocTemplate(pdf_nome, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'TituloCodigo',
        parent=styles['Heading2'],
        textColor='#0066CC',
        spaceBefore=15,
        spaceAfter=5
    )
    
    estilo_codigo = ParagraphStyle(
        'TextoCodigo',
        fontName='Courier',
        fontSize=8.5,
        leading=11
    )

    elementos = []
    arquivos_encontrados = False
    
    for raiz, diretorios, arquivos in os.walk('.'):
        # CORRIGIDO: Mudado de 'em' para 'in'
        if any(p in raiz.split(os.sep) for p in ['.venv', 'venv', '__pycache__', '.git', '.idea', '.vscode']):
            continue
            
        for arquivo in arquivos:
            if arquivo.endswith('.py') and arquivo != 'conversor.py':
                arquivos_encontrados = True
                caminho_completo = os.path.join(raiz, arquivo)
                
                elementos.append(Paragraph(f"=== ARQUIVO: {caminho_completo} ===", estilo_titulo))
                elementos.append(Spacer(1, 5))
                
                texto_do_arquivo = []
                
                with open(caminho_completo, "r", encoding="utf-8", errors="replace") as f:
                    for num_linha, linha in enumerate(f, 1):
                        linha_limpa = linha.rstrip('\n')
                        texto_do_arquivo.append(f"{num_linha:03d} | {linha_limpa}")
                
                bloco_codigo = "\n".join(texto_do_arquivo)
                elementos.append(Preformatted(bloco_codigo, estilo_codigo))
                elementos.append(Spacer(1, 15))

    if not arquivos_encontrados:
        print("Nenhum arquivo .py foi encontrado na pasta raiz ou nas subpastas.")
        return

    print("Gerando o PDF... Isso pode levar alguns segundos dependendo do volume de código.")
    doc.build(elementos)
    print(f"Sucesso! Todos os arquivos foram unificados em '{pdf_nome}'.")

if __name__ == "__main__":
    converter_para_pdf()
