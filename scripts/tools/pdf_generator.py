#!/usr/bin/env python3
"""
Script CLI para gerar PDF com conteúdo de arquivos de uma pasta.
Cada arquivo vira uma seção no PDF com título sendo o nome do arquivo.
"""

import argparse
import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def is_text_file(file_path):
    """
    Verifica se o arquivo é de texto (pode ser lido como texto).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Tenta ler os primeiros 1024 caracteres
        return True
    except (UnicodeDecodeError, IOError):
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                f.read(1024)
            return True
        except (UnicodeDecodeError, IOError):
            return False


def read_file_content(file_path):
    """
    Lê o conteúdo de um arquivo, tentando diferentes codificações.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Se nenhuma codificação funcionar, retorna uma mensagem de erro
    return f"[ERRO: Não foi possível ler o arquivo {file_path} - formato não suportado]"


def get_files_from_directory(directory_path, include_extensions=None, exclude_extensions=None):
    """
    Obtém lista de arquivos de um diretório, com filtros opcionais.
    """
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Diretório não encontrado: {directory_path}")
    
    files = []
    for file_path in directory.iterdir():
        if file_path.is_file():
            # Filtrar por extensões incluídas
            if include_extensions:
                if file_path.suffix.lower() not in include_extensions:
                    continue
            
            # Filtrar por extensões excluídas
            if exclude_extensions:
                if file_path.suffix.lower() in exclude_extensions:
                    continue
            
            # Verificar se é arquivo de texto
            if is_text_file(file_path):
                files.append(file_path)
    
    return sorted(files)


def create_pdf(files, output_path, title="Compilação de Arquivos"):
    """
    Cria o PDF com o conteúdo dos arquivos.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='#2E86AB'
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#A23B72'
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=10,
        fontName='Courier'  # Fonte monoespaçada para código
    )
    
    story = []
    
    # Título principal
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # Índice
    story.append(Paragraph("Índice", styles['Heading2']))
    for i, file_path in enumerate(files, 1):
        index_line = f"{i}. {file_path.name}"
        story.append(Paragraph(index_line, styles['Normal']))
    
    story.append(PageBreak())
    
    # Conteúdo dos arquivos
    for i, file_path in enumerate(files, 1):
        # Título da seção
        section_title = f"{i}. {file_path.name}"
        story.append(Paragraph(section_title, section_title_style))
        
        # Informações do arquivo
        file_info = f"<i>Caminho: {file_path}<br/>Tamanho: {file_path.stat().st_size} bytes</i>"
        story.append(Paragraph(file_info, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Conteúdo do arquivo
        content = read_file_content(file_path)
        
        # Dividir conteúdo em linhas e processar para PDF
        lines = content.split('\n')
        for line in lines:
            # Escapar caracteres especiais do HTML
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if line.strip():  # Ignorar linhas vazias
                story.append(Paragraph(line, content_style))
            else:
                story.append(Spacer(1, 6))
        
        # Quebra de página entre arquivos (exceto no último)
        if i < len(files):
            story.append(PageBreak())
    
    # Gerar PDF
    doc.build(story)


def main():
    parser = argparse.ArgumentParser(
        description='Gera um PDF com o conteúdo de arquivos de uma pasta',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python pdf_generator.py /caminho/para/pasta
  python pdf_generator.py ./meus_arquivos -o meu_pdf.pdf
  python pdf_generator.py ./src --include .py .js .html
  python pdf_generator.py ./docs --exclude .log .tmp --title "Documentação"
        """
    )
    
    parser.add_argument(
        'pasta',
        help='Caminho para a pasta contendo os arquivos'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='arquivos_compilados.pdf',
        help='Nome do arquivo PDF de saída (padrão: arquivos_compilados.pdf)'
    )
    
    parser.add_argument(
        '--title',
        default='Compilação de Arquivos',
        help='Título do documento PDF'
    )
    
    parser.add_argument(
        '--include',
        nargs='+',
        help='Incluir apenas arquivos com essas extensões (ex: .py .txt .md)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Excluir arquivos com essas extensões (ex: .log .tmp .cache)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostrar informações detalhadas durante o processamento'
    )
    
    args = parser.parse_args()
    
    try:
        # Verificar se reportlab está instalado
        try:
            import reportlab
        except ImportError:
            print("ERRO: A biblioteca 'reportlab' não está instalada.")
            print("Instale com: pip install reportlab")
            sys.exit(1)
        
        # Obter lista de arquivos
        if args.verbose:
            print(f"Processando pasta: {args.pasta}")
        
        files = get_files_from_directory(
            args.pasta,
            include_extensions=args.include,
            exclude_extensions=args.exclude
        )
        
        if not files:
            print("AVISO: Nenhum arquivo de texto encontrado na pasta especificada.")
            sys.exit(0)
        
        if args.verbose:
            print(f"Arquivos encontrados: {len(files)}")
            for file_path in files:
                print(f"  - {file_path.name}")
        
        # Criar PDF
        output_path = Path(args.output)
        if args.verbose:
            print(f"Gerando PDF: {output_path}")
        
        create_pdf(files, str(output_path), args.title)
        
        print(f"PDF gerado com sucesso: {output_path}")
        print(f"Arquivos incluídos: {len(files)}")
        
    except ValueError as e:
        print(f"ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()