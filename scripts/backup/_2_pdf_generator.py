#!/usr/bin/env python3
"""
PDF Generator CLI - Cria PDF com conteúdo de arquivos de texto de uma pasta
"""

import os
import sys
import argparse
import chardet
import re
from pathlib import Path
from typing import List, Tuple, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents

class PDFGenerator:
    def __init__(self, output_path: str = "arquivos_compilados.pdf"):
        self.output_path = output_path
        self.story = []
        self.toc_entries = []
        
        # Configurar estilos
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Configura estilos personalizados para o PDF"""
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Centralizado
            textColor=colors.darkblue
        ))
        
        # Estilo para títulos de seção
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=15,
            textColor=colors.darkgreen
        ))
        
        # Estilo para conteúdo de código com fonte monoespaçada
        self.styles.add(ParagraphStyle(
            name='CodeContent',
            fontName='Courier',
            fontSize=9,
            leftIndent=20,
            spaceBefore=10,
            spaceAfter=10,
            preserveLeadingSpaces=True,
            allowWidows=0,
            allowOrphans=0
        ))
        
        # Estilo para índice
        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            fontName='Helvetica',
            fontSize=12,
            leftIndent=20,
            spaceBefore=5
        ))

    def detect_encoding(self, file_path: str) -> str:
        """Detecta a codificação do arquivo"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'

    def FF(self, file_path: str, encodings: List[str] = None) -> Tuple[str, str]:
        """Lê o conteúdo do arquivo tentando diferentes codificações"""
        if encodings is None:
            encodings = ['utf-8'] # , 'latin-1', 'cp1252', 'iso-8859-1'
        
        # Primeiro tenta detectar automaticamente
        detected_encoding = self.detect_encoding(file_path)
        if detected_encoding and detected_encoding not in encodings:
            encodings.insert(0, detected_encoding)
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content, encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Erro ao ler arquivo {file_path}: {e}")
                continue
        
        # Se não conseguir ler, retorna erro
        return f"[ERRO: Não foi possível decodificar o arquivo {file_path}]", "error"

    def is_text_file(self, file_path: str) -> bool:
        """Verifica se o arquivo é um arquivo de texto"""
        text_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
            '.md', '.rst', '.cfg', '.ini', '.conf', '.log', '.sql', '.sh', '.bat',
            '.c', '.cpp', '.h', '.hpp', '.java', '.php', '.rb', '.go', '.rs',
            '.ts', '.jsx', '.tsx', '.vue', '.svelte', '.scss', '.sass', '.less',
            '.dockerfile', '.gitignore', '.env', '.properties', '.toml'
        }
        
        ext = Path(file_path).suffix.lower()
        if ext in text_extensions:
            return True
        
        # Tenta detectar se é arquivo de texto analisando o conteúdo
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Arquivo binário contém bytes nulos
                    return False
                
                # Tenta decodificar como texto
                try:
                    chunk.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    try:
                        chunk.decode('latin-1')
                        return True
                    except UnicodeDecodeError:
                        return False
        except Exception:
            return False

    def filter_files(self, files: List[str], include_extensions: List[str] = None, 
                    exclude_extensions: List[str] = None) -> List[str]:
        """Filtra arquivos baseado nas extensões"""
        filtered = []
        
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            
            # Aplicar filtro de exclusão
            if exclude_extensions and ext in exclude_extensions:
                continue
            
            # Aplicar filtro de inclusão
            if include_extensions and ext not in include_extensions:
                continue
            
            filtered.append(file_path)
        
        return filtered

    def escape_xml_chars(self, text: str) -> str:
        """Escapa caracteres especiais para XML/HTML preservando espaços"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        # Converter espaços múltiplos para espaços não-quebráveis para preservar indentação
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            if line.strip():  # Se a linha não está vazia
                # Contar espaços no início da linha
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    # Substituir espaços iniciais por espaços não-quebráveis
                    line = '&nbsp;' * leading_spaces + line.lstrip()
                
                # Substituir tabs por 4 espaços não-quebráveis
                line = line.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                
                # Substituir múltiplos espaços internos por espaços não-quebráveis
                import re
                line = re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group()), line)
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)

    def format_content_for_pdf(self, content: str) -> str:
        """Formata o conteúdo preservando espaçamento e quebras de linha exatamente como no original"""
        # Não modificar o conteúdo, apenas garantir que espaços sejam preservados
        return content

    def add_table_of_contents(self):
        """Adiciona índice ao PDF"""
        self.story.append(Paragraph("Índice", self.styles['CustomTitle']))
        self.story.append(Spacer(1, 20))
        
        for i, (title, page) in enumerate(self.toc_entries, 1):
            entry_text = f"{i}. {title}"
            self.story.append(Paragraph(entry_text, self.styles['TOCEntry']))
        
        self.story.append(PageBreak())

    def generate_pdf(self, source_folder: str, include_extensions: List[str] = None,
                    exclude_extensions: List[str] = None):
        """Gera o PDF com o conteúdo dos arquivos"""
        
        if not os.path.exists(source_folder):
            raise ValueError(f"Pasta não encontrada: {source_folder}")
        
        # Coletar todos os arquivos
        all_files = []
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if self.is_text_file(file_path):
                    all_files.append(file_path)
        
        # Aplicar filtros
        filtered_files = self.filter_files(all_files, include_extensions, exclude_extensions)
        filtered_files.sort()  # Ordenar alfabeticamente
        
        if not filtered_files:
            raise ValueError("Nenhum arquivo de texto encontrado na pasta especificada")
        
        print(f"Processando {len(filtered_files)} arquivos...")
        
        # Título principal
        title = f"Compilação de Arquivos - {os.path.basename(source_folder)}"
        self.story.append(Paragraph(title, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 30))
        
        # Processar cada arquivo
        for i, file_path in enumerate(filtered_files, 1):
            relative_path = os.path.relpath(file_path, source_folder)
            section_title = f"Arquivo: {relative_path}"
            
            print(f"Processando ({i}/{len(filtered_files)}): {relative_path}")
            
            # Adicionar entrada no índice
            self.toc_entries.append((relative_path, len(self.story)))
            
            # Título da seção
            self.story.append(Paragraph(section_title, self.styles['SectionTitle']))
            self.story.append(Spacer(1, 10))
            
            # Ler conteúdo do arquivo
            content, encoding = self.read_file_content(file_path)
            
            if encoding != "error":
                # Informações do arquivo
                file_size = os.path.getsize(file_path)
                info_text = f"<b>Caminho:</b> {relative_path}<br/>"
                info_text += f"<b>Tamanho:</b> {file_size} bytes<br/>"
                info_text += f"<b>Codificação:</b> {encoding}<br/>"
                
                self.story.append(Paragraph(info_text, self.styles['Normal']))
                self.story.append(Spacer(1, 10))
                
                # Conteúdo do arquivo
                if content.strip():
                    # Processar o conteúdo preservando formatação exata
                    formatted_content = self.format_content_for_pdf(content)
                    escaped_content = self.escape_xml_chars(formatted_content)
                    
                    # Dividir em chunks menores para evitar problemas com conteúdo muito longo
                    lines = escaped_content.split('\n')
                    chunk_size = 30  # Reduzido para melhor controle
                    
                    for i in range(0, len(lines), chunk_size):
                        chunk_lines = lines[i:i + chunk_size]
                        chunk_text = '<br/>'.join(chunk_lines)
                        
                        if chunk_text.strip() or any(line.strip() for line in chunk_lines):
                            self.story.append(Paragraph(chunk_text, self.styles['CodeContent']))
                else:
                    self.story.append(Paragraph("[Arquivo vazio]", self.styles['CodeContent']))
            else:
                self.story.append(Paragraph(content, self.styles['Normal']))
            
            # Quebra de página entre arquivos (exceto o último)
            if i < len(filtered_files):
                self.story.append(PageBreak())
        
        # Adicionar índice no início
        if self.toc_entries:
            toc_story = []
            toc_story.append(Paragraph("Índice", self.styles['CustomTitle']))
            toc_story.append(Spacer(1, 20))
            
            for i, (title, page) in enumerate(self.toc_entries, 1):
                entry_text = f"{i}. {title}"
                toc_story.append(Paragraph(entry_text, self.styles['TOCEntry']))
            
            toc_story.append(PageBreak())
            self.story = toc_story + self.story
        
        # Gerar PDF
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        doc.build(self.story)
        print(f"\nPDF gerado com sucesso: {self.output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Gera PDF com conteúdo de arquivos de texto de uma pasta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s /caminho/para/pasta
  %(prog)s /caminho/para/pasta -o meu_arquivo.pdf
  %(prog)s /caminho/para/pasta --include .py .js .html
  %(prog)s /caminho/para/pasta --exclude .log .tmp
  %(prog)s /caminho/para/pasta --include .py --exclude __pycache__
        """
    )
    
    parser.add_argument(
        'source_folder',
        help='Pasta contendo os arquivos para incluir no PDF'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='arquivos_compilados.pdf',
        help='Nome do arquivo PDF de saída (padrão: arquivos_compilados.pdf)'
    )
    
    parser.add_argument(
        '--include',
        nargs='+',
        help='Incluir apenas arquivos com estas extensões (ex: .py .js .html)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Excluir arquivos com estas extensões (ex: .log .tmp .cache)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Saída detalhada'
    )
    
    args = parser.parse_args()
    
    try:
        # Verificar se a pasta existe
        if not os.path.isdir(args.source_folder):
            print(f"Erro: '{args.source_folder}' não é uma pasta válida", file=sys.stderr)
            sys.exit(1)
        
        # Converter extensões para lowercase e adicionar ponto se necessário
        include_extensions = None
        if args.include:
            include_extensions = []
            for ext in args.include:
                if not ext.startswith('.'):
                    ext = '.' + ext
                include_extensions.append(ext.lower())
        
        exclude_extensions = None
        if args.exclude:
            exclude_extensions = []
            for ext in args.exclude:
                if not ext.startswith('.'):
                    ext = '.' + ext
                exclude_extensions.append(ext.lower())
        
        if args.verbose:
            print(f"Pasta de origem: {args.source_folder}")
            print(f"Arquivo de saída: {args.output}")
            if include_extensions:
                print(f"Incluir extensões: {include_extensions}")
            if exclude_extensions:
                print(f"Excluir extensões: {exclude_extensions}")
            print()
        
        # Gerar PDF
        generator = PDFGenerator(args.output)
        generator.generate_pdf(
            args.source_folder,
            include_extensions=include_extensions,
            exclude_extensions=exclude_extensions
        )
        
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()