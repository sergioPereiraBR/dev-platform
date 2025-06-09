#!/usr/bin/env python3
"""
PDF Generator CLI - Converte arquivos de uma pasta em um PDF estruturado
Autor: Script gerado para converter arquivos em PDF com índice e formatação
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
import logging
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class PDFGenerator:
    """Classe principal para geração de PDF a partir de arquivos"""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        self.story: list = []
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Configura os estilos personalizados para o documento"""
        # Estilo para títulos de seção
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading1"],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue,
                alignment=TA_LEFT,
            )
        )

        # Estilo para o índice
        self.styles.add(
            ParagraphStyle(
                name="TOCTitle",
                parent=self.styles["Heading1"],
                fontSize=16,
                spaceAfter=18,
                alignment=TA_CENTER,
                textColor=colors.black,
            )
        )

        # Estilo para itens do índice
        self.styles.add(
            ParagraphStyle(
                name="TOCItem",
                parent=self.styles["Normal"],
                fontSize=11,
                leftIndent=20,
                spaceAfter=6,
            )
        )

        # Estilo para conteúdo de arquivo (monoespaçado)
        self.styles.add(
            ParagraphStyle(
                name="FileContent",
                parent=self.styles["Code"],
                fontName="Courier",
                fontSize=9,
                leftIndent=10,
                rightIndent=10,
                spaceAfter=3,
                spaceBefore=3,
                leading=11,  # Espaçamento entre linhas um pouco maior que o tamanho da fonte
                preserveLineBreaks=True,
                alignment=TA_LEFT,
                wordWrap="LTR",  # Quebra de linha da esquerda para direita
            )
        )

        # Estilo para cabeçalho de arquivo
        self.styles.add(
            ParagraphStyle(
                name="FileHeader",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.grey,
                spaceAfter=6,
                leftIndent=10,
            )
        )

    def add_title_page(self, title: str, folder_path: str):
        """Adiciona página de título ao PDF"""
        title_style = ParagraphStyle(
            name="Title",
            parent=self.styles["Title"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        subtitle_style = ParagraphStyle(
            name="Subtitle",
            parent=self.styles["Normal"],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )

        self.story.append(Spacer(1, 2 * inch))
        self.story.append(Paragraph(title, title_style))
        self.story.append(Spacer(1, 0.5 * inch))
        self.story.append(
            Paragraph(f"Conteúdo da pasta: {folder_path}", subtitle_style)
        )
        self.story.append(Spacer(1, 0.3 * inch))
        self.story.append(
            Paragraph(f"Gerado em: {self._get_current_date()}", subtitle_style)
        )
        self.story.append(PageBreak())

    def add_table_of_contents(self, file_list: List[str]):
        """Adiciona índice ao PDF"""
        self.story.append(Paragraph("Índice", self.styles["TOCTitle"]))
        self.story.append(Spacer(1, 20))

        for i, filename in enumerate(file_list, 1):
            toc_item = f"{i}. Arquivo: {filename}"
            self.story.append(Paragraph(toc_item, self.styles["TOCItem"]))

        self.story.append(PageBreak())

    def add_file_section(self, count: int, filename: str, content: str, file_path: str):
        """Adiciona uma seção para um arquivo específico"""
        # Título da seção
        section_title = f"{count}. Arquivo: {filename}"
        self.story.append(Paragraph(section_title, self.styles["SectionTitle"]))

        # Informações do arquivo
        # file_info = f"Caminho: {file_path} | Tamanho: {self._get_file_size(file_path)}"
        # self.story.append(Paragraph(file_info, self.styles['FileHeader']))
        self.story.append(Spacer(1, 8))

        # Linha separadora
        # line_data = [['─' * 100]]
        # line_table = Table(line_data, colWidths=[7*inch])
        # line_table.setStyle(TableStyle([
        #     ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
        #     ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
        #     ('FONTSIZE', (0, 0), (-1, -1), 8),
        #     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        # ]))
        # self.story.append(line_table)
        # self.story.append(Spacer(1, 8))

        # Conteúdo do arquivo
        if content.strip():
            # Para arquivos muito grandes, processa em chunks menores
            if len(content) > 50000:  # Se arquivo > 50KB
                chunks = self._split_content_into_chunks(content, 40000)
                for i, chunk in enumerate(chunks):
                    if i > 0:
                        self.story.append(Spacer(1, 10))
                        continuation_note = (
                            f"... continuação do arquivo {filename} (parte {i+1}) ..."
                        )
                        self.story.append(
                            Paragraph(continuation_note, self.styles["FileHeader"])
                        )
                        self.story.append(Spacer(1, 5))

                    processed_chunk = self._process_content(chunk)
                    self.story.append(
                        Paragraph(processed_chunk, self.styles["FileContent"])
                    )
            else:
                processed_content = self._process_content(content)
                self.story.append(
                    Paragraph(processed_content, self.styles["FileContent"])
                )
        else:
            empty_msg = "&lt;Arquivo vazio ou sem conteúdo legível&gt;"
            self.story.append(Paragraph(empty_msg, self.styles["FileContent"]))

        # Quebra de página após cada seção
        self.story.append(PageBreak())

    def _process_content(self, content: str) -> str:
        """Processa o conteúdo preservando formatação exata e escapando caracteres especiais"""
        # Escapa caracteres especiais do HTML/XML
        content = content.replace("&", "&amp;")
        content = content.replace("<", "&lt;")
        content = content.replace(">", "&gt;")

        # Preserva quebras de linha e todos os espaços/tabs exatamente como estão
        lines = content.split("\n")
        processed_lines = []

        for line in lines:
            # Preserva exatamente todos os espaços e tabs
            processed_line = ""
            for char in line:
                if char == " ":
                    processed_line += "&nbsp;"
                elif char == "\t":
                    processed_line += "&nbsp;&nbsp;&nbsp;&nbsp;"  # Tab = 4 espaços
                else:
                    processed_line += char
            processed_lines.append(processed_line)

        return "<br/>".join(processed_lines)

    def _split_content_into_chunks(self, content: str, chunk_size: int) -> List[str]:
        """Divide conteúdo grande em chunks menores para melhor processamento"""
        chunks = []
        lines = content.split("\n")
        current_chunk: list = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 para a quebra de linha
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _get_file_size(self, file_path: str) -> str:
        """Retorna o tamanho do arquivo formatado"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        except OSError:
            return "Tamanho desconhecido"

    def _get_current_date(self) -> str:
        """Retorna a data atual formatada"""
        from datetime import datetime

        return datetime.now().strftime("%d/%m/%Y às %H:%M")

    def build(self):
        """Constrói e salva o PDF"""
        try:
            self.doc.build(self.story)
            logger.info(f"PDF gerado com sucesso: {self.output_file}")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            raise


class FileProcessor:
    """Classe para processar arquivos de uma pasta"""

    def __init__(
        self,
        folder_path: str,
        include_extensions: Optional[Set[str]] = None,
        exclude_extensions: Optional[Set[str]] = None,
    ):
        self.folder_path = Path(folder_path)
        self.include_extensions = include_extensions or set()
        self.exclude_extensions = exclude_extensions or set()

    def get_files(self) -> List[Path]:
        """Retorna lista de arquivos filtrados"""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {self.folder_path}")

        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Caminho não é uma pasta: {self.folder_path}")

        files = []
        for file_path in self.folder_path.iterdir():
            if file_path.is_file() and self._should_include_file(file_path):
                files.append(file_path)

        # Ordena arquivos por nome
        files.sort(key=lambda x: x.name.lower())
        return files

    def _should_include_file(self, file_path: Path) -> bool:
        """Verifica se o arquivo deve ser incluído baseado nos filtros"""
        extension = file_path.suffix.lower()

        # Se há extensões para incluir, só inclui se estiver na lista
        if self.include_extensions:
            return extension in self.include_extensions

        # Se há extensões para excluir, não inclui se estiver na lista
        if self.exclude_extensions:
            return extension not in self.exclude_extensions

        return True

    def read_file_content(self, file_path: Path) -> str:
        """Lê o conteúdo de um arquivo com encoding UTF-8"""
        try:
            # Primeiro tenta UTF-8
            with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                return f.read()
        except UnicodeDecodeError:
            logger.warning(f"Erro UTF-8 em {file_path}. Tentando UTF-8 com ignore...")
            try:
                # Tenta UTF-8 ignorando caracteres problemáticos
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    logger.warning(
                        f"Arquivo {file_path} lido com UTF-8 (alguns caracteres ignorados)"
                    )
                    return content
            except Exception:
                # Como último recurso, tenta latin-1
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                        logger.warning(f"Arquivo {file_path} lido com encoding latin-1")
                        return content
                except Exception as e:
                    logger.error(f"Não foi possível ler o arquivo {file_path}: {e}")
                    return f"[ERRO: Não foi possível ler o conteúdo do arquivo]\n[Erro específico: {e}]"
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {file_path}")
            return "[ERRO: Arquivo não encontrado]"
        except PermissionError:
            logger.error(f"Sem permissão para ler: {file_path}")
            return "[ERRO: Sem permissão para ler o arquivo]"
        except Exception as e:
            logger.error(f"Erro inesperado ao ler arquivo {file_path}: {e}")
            return f"[ERRO: {e}]"


def parse_extensions(extensions_str: str) -> Set[str]:
    """Converte string de extensões em conjunto"""
    if not extensions_str:
        return set()

    extensions = set()
    for ext in extensions_str.split(","):
        ext = ext.strip()
        if not ext.startswith("."):
            ext = "." + ext
        extensions.add(ext.lower())

    return extensions


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Gera PDF estruturado com conteúdo de arquivos de uma pasta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s /caminho/para/pasta
  %(prog)s /caminho/para/pasta -o meu_documento.pdf
  %(prog)s /caminho/para/pasta --include txt,py,js
  %(prog)s /caminho/para/pasta --exclude pdf,exe,zip
  %(prog)s /caminho/para/pasta --title "Meu Projeto"
        """,
    )

    data_hoje = datetime.now().strftime("%Y%m%d")

    parser.add_argument("folder", help="Caminho para a pasta contendo os arquivos")

    parser.add_argument(
        "-o",
        "--output",
        default=f"arquivos_compilados_{data_hoje}.pdf",
        help="Nome do arquivo PDF de saída (padrão: arquivos_compilados.pdf)",
    )

    parser.add_argument(
        "--title",
        default="Compilação de Arquivos",
        help='Título do documento PDF (padrão: "Compilação de Arquivos")',
    )

    parser.add_argument(
        "--include",
        help="Extensões de arquivo para incluir (separadas por vírgula, ex: txt,py,js)",
    )

    parser.add_argument(
        "--exclude",
        help="Extensões de arquivo para excluir (separadas por vírgula, ex: pdf,exe,zip)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Modo verboso (mais informações de log)",
    )

    args = parser.parse_args()

    # Configura nível de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Processa extensões
        include_extensions = parse_extensions(args.include) if args.include else None
        exclude_extensions = parse_extensions(args.exclude) if args.exclude else None

        # Valida argumentos conflitantes
        if include_extensions and exclude_extensions:
            logger.error("Não é possível usar --include e --exclude ao mesmo tempo")
            sys.exit(1)

        logger.info(f"Processando pasta: {args.folder}")
        logger.info(f"Arquivo de saída: {args.output}")

        if include_extensions:
            logger.info(f"Incluindo extensões: {', '.join(include_extensions)}")
        elif exclude_extensions:
            logger.info(f"Excluindo extensões: {', '.join(exclude_extensions)}")

        # Processa arquivos
        processor = FileProcessor(args.folder, include_extensions, exclude_extensions)
        files = processor.get_files()

        if not files:
            logger.warning("Nenhum arquivo encontrado na pasta especificada")
            sys.exit(1)

        logger.info(f"Encontrados {len(files)} arquivo(s) para processar")

        # Gera PDF
        pdf_generator = PDFGenerator(args.output)

        # Adiciona página de título
        pdf_generator.add_title_page(args.title, args.folder)

        # Adiciona índice
        file_names = [f.name for f in files]
        pdf_generator.add_table_of_contents(file_names)

        # Processa cada arquivo
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processando ({i}/{len(files)}): {file_path.name}")
            content = processor.read_file_content(file_path)
            pdf_generator.add_file_section(i, file_path.name, content, str(file_path))

        # Gera o PDF final
        pdf_generator.build()

        logger.info("Processo concluído com sucesso!")

    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
