import os
import re
import json
import pandas as pd
import numpy as np # Importar numpy para a linha de tendência
from datetime import datetime, timedelta
import pytz # Para manipulação de timezone

# Importações para Matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# Configuração de Logs - Usando loguru como exemplo
from loguru import logger

# Configurar o logger para salvar em um arquivo e exibir no console
logger.remove()
logger.add("app.log", rotation="10 MB", level="INFO")
logger.add(lambda msg: print(msg.strip()), format="{message}", level="INFO")


def parse_log_entry(log_line):
    """
    Parses a single log line into a dictionary.
    Assumes loguru's default JSON format for structured logs.
    """
    try:
        # Tenta carregar a linha como um JSON.
        # Isso é ideal para logs estruturados (como os do Loguru com serialize=True)
        log_entry = json.loads(log_line)

        # Se for um loguru.record (serialize=True), extrai o 'record' e 'text'
        if "record" in log_entry and "text" in log_entry:
            record = log_entry["record"]
            message = log_entry["text"].strip() # A mensagem em si

            # Re-parsear a mensagem para extrair o nível de log e o timestamp
            # Este regex é robusto para o formato "YYYY-MM-DD HH:MM:SS.ms | LEVEL | Message"
            match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3,6}) \| (\w+) \| (.*)", message)
            if match:
                timestamp_str, level, msg_content = match.groups()
                # Converter para datetime com timezone (se a string contiver info de timezone)
                # O loguru serializa o 'time' com 'repr' que inclui o offset, ex: "2025-06-09 15:59:31.450567-03:00"
                # Record time é mais preciso.
                parsed_time = record["time"]["repr"]
                # A mensagem real deve ser a do 'record'
                log_message = record["message"]
                function_name = record["function"]
                file_name = record["file"]["name"]
                line_number = record["line"]
                elapsed_seconds = record["elapsed"]["seconds"]
                extra_data = record["extra"]

                return {
                    "timestamp": parsed_time,
                    "level": level,
                    "message": log_message,
                    "function": function_name,
                    "file": file_name,
                    "line": line_number,
                    "elapsed": elapsed_seconds,
                    "extra": extra_data,
                    "full_line": log_line.strip()
                }
            else:
                # Fallback para logs que não seguem o formato esperado, mas são JSON
                logger.warning(f"Linha JSON não corresponde ao padrão Loguru: {log_line.strip()}")
                return None # Ou retorne um dicionário parcial se houver dados úteis

        # Se for um JSON simples sem 'record'/'text' (outros formatos de log estruturado)
        # Você precisaria adaptar a extração aqui com base na estrutura do seu JSON
        logger.warning(f"Linha JSON não é do formato Loguru serializado: {log_line.strip()}")
        return None # Ou retorne o dicionário completo se for utilizável

    except json.JSONDecodeError:
        # Se a linha não for um JSON, tente parsear como log não estruturado.
        # Regex mais genérico para logs não estruturados (ex: "YYYY-MM-DD HH:MM:SS | LEVEL | Message")
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3,6})?) \| (\w+) \| (.*)", log_line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                # Tentativa de parsear o timestamp com ou sem microssegundos e offset
                # Remove o offset para parsear primeiro, depois adiciona se necessário
                ts_no_offset = re.sub(r'([+-]\d{2}:\d{2})$', '', timestamp_str)
                dt_obj = datetime.fromisoformat(ts_no_offset) # Handle microseconds automatically
                if timestamp_str.endswith("Z"): # UTC
                    dt_obj = dt_obj.replace(tzinfo=pytz.utc)
                elif re.search(r'[+-]\d{2}:\d{2}$', timestamp_str): # Has offset
                    offset_str = re.search(r'([+-]\d{2}:\d{2})$', timestamp_str).group(1)
                    sign = 1 if offset_str[0] == '+' else -1
                    hours = int(offset_str[1:3])
                    minutes = int(offset_str[4:6])
                    offset = timedelta(hours=sign * hours, minutes=sign * minutes)
                    dt_obj = dt_obj.replace(tzinfo=pytz.FixedOffset(offset.total_seconds() / 60))
                else: # Assume local timezone if no info
                    # dt_obj = pytz.timezone('America/Sao_Paulo').localize(dt_obj) # Example, use your local timezone
                    pass # Keep as naive for now or add specific localizing logic

            except ValueError:
                dt_obj = None # Could not parse timestamp

            return {
                "timestamp": dt_obj,
                "level": level,
                "message": message.strip(),
                "function": "N/A", # Não disponível em logs não estruturados
                "file": "N/A",
                "line": "N/A",
                "elapsed": None,
                "extra": {},
                "full_line": log_line.strip()
            }
        else:
            logger.warning(f"Linha de log não reconhecida: {log_line.strip()}")
            return None
    except Exception as e:
        logger.error(f"Erro inesperado ao processar linha de log '{log_line.strip()}': {e}")
        return None

def read_logs_from_folder(log_folder_path):
    """Reads all log files from a given folder and parses them."""
    all_parsed_logs = []
    logger.info(f"Iniciando leitura de logs da pasta: {log_folder_path}")

    if not os.path.exists(log_folder_path):
        logger.error(f"A pasta de logs '{log_folder_path}' não existe.")
        return []

    for filename in os.listdir(log_folder_path):
        if filename.endswith(".log") or filename.endswith(".txt"):
            filepath = os.path.join(log_folder_path, filename)
            logger.info(f"Processando arquivo: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        parsed_log = parse_log_entry(line)
                        if parsed_log:
                            all_parsed_logs.append(parsed_log)
            except Exception as e:
                logger.error(f"Não foi possível ler o arquivo {filepath}: {e}")
    
    logger.info(f"Total de logs parseados: {len(all_parsed_logs)}")
    return all_parsed_logs

def analyze_logs(parsed_logs):
    """Performs various analyses on the parsed log data."""
    if not parsed_logs:
        return {"summary": "Nenhum log para analisar."}

    df = pd.DataFrame(parsed_logs)

    # Convertendo timestamps para datetime objects para manipulação
    # Tratar entradas None ou inválidas no timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)

    # Análise de Erros
    errors_df = df[df['level'] == 'ERROR']
    total_errors = len(errors_df)
    
    error_summary = {
        "total_errors": total_errors,
        "percentage_errors": (total_errors / len(df) * 100) if len(df) > 0 else 0,
        "top_errors_by_frequency": []
    }

    if total_errors > 0:
        top_errors = errors_df['message'].value_counts().head(5)
        for message, count in top_errors.items():
            last_occurrence = errors_df[errors_df['message'] == message]['timestamp'].max()
            error_summary["top_errors_by_frequency"].append({
                "message": message,
                "occurrences": int(count),
                "last_occurrence": last_occurrence.isoformat() if last_occurrence else "N/A"
            })
    
    # Análise de Desempenho (se 'elapsed' estiver disponível e for numérico)
    performance_summary = {
        "fastest_operations": [],
        "slowest_operations": []
    }
    
    if 'elapsed' in df.columns and pd.api.types.is_numeric_dtype(df['elapsed']):
        # Filtrar logs com 'elapsed' válido e diferente de None
        df_perf = df[df['elapsed'].notna()]
        if not df_perf.empty:
            # Operações mais rápidas
            fastest_ops = df_perf.nsmallest(5, 'elapsed')[['message', 'function', 'elapsed', 'timestamp']]
            for _, row in fastest_ops.iterrows():
                performance_summary["fastest_operations"].append({
                    "message": row['message'],
                    "function": row['function'],
                    "time": float(row['elapsed']),
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else "N/A"
                })

            # Operações mais lentas
            slowest_ops = df_perf.nlargest(5, 'elapsed')[['message', 'function', 'elapsed', 'timestamp']]
            for _, row in slowest_ops.iterrows():
                performance_summary["slowest_operations"].append({
                    "message": row['message'],
                    "function": row['function'],
                    "time": float(row['elapsed']),
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else "N/A"
                })

    # Análise de Carga
    load_summary = {
        "total_logs_processed": len(df),
        "log_level_distribution": {},
        "logs_per_hour": {} # Adicionar aqui para ser preenchido por outra função
    }

    log_level_distribution = df['level'].value_counts(normalize=True) * 100
    for level, percentage in log_level_distribution.items():
        load_summary["log_level_distribution"][level] = f"{percentage:.2f}%"

    # Período de logs
    min_timestamp = df['timestamp'].min()
    max_timestamp = df['timestamp'].max()
    period_covered = {
        "start": min_timestamp.isoformat() if pd.notna(min_timestamp) else "N/A",
        "end": max_timestamp.isoformat() if pd.notna(max_timestamp) else "N/A"
    }

    return {
        "error_analysis": error_summary,
        "performance_analysis": performance_summary,
        "load_analysis": load_summary,
        "period_covered": period_covered,
        "raw_data": parsed_logs # Manter os dados brutos para outras análises/gráficos
    }

def generate_logs_per_hour_chart_image(log_data):
    """
    Generates a Matplotlib chart of logs per hour with a trend line,
    and returns it as a PNG image byte string.
    """
    if not log_data:
        logger.warning("Dados de log vazios para gerar o gráfico.")
        return None

    df = pd.DataFrame(log_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True) # Remover linhas com timestamp inválido
    
    if df.empty:
        logger.warning("DataFrame vazio após limpeza de timestamps inválidos, não é possível gerar o gráfico.")
        return None

    df['hour'] = df['timestamp'].dt.floor('h') # Usar 'h' conforme o FutureWarning
    logs_per_hour = df.groupby('hour').size().reset_index(name='count')
    logs_per_hour = logs_per_hour.sort_values('hour')

    try:
        # Criar o gráfico com Matplotlib
        fig, ax = plt.subplots(figsize=(10, 6)) # Define o tamanho da figura
        
        ax.bar(logs_per_hour['hour'], logs_per_hour['count'], color='skyblue', label='Logs por Hora')
        
        # Adicionar linha de tendência
        # Converter as datas para números para o cálculo da regressão linear
        x_numeric = mdates.date2num(logs_per_hour['hour'])
        y_values = logs_per_hour['count']
        
        # Calcular a regressão linear (polinômio de grau 1)
        z = np.polyfit(x_numeric, y_values, 1)
        p = np.poly1d(z)
        
        # Criar valores x para a linha de tendência que cubram todo o gráfico
        x_trend = np.linspace(x_numeric.min(), x_numeric.max(), 100)
        
        ax.plot(x_trend, p(x_trend), color='red', linestyle='--', label='Linha de Tendência')
        
        ax.set_title('Volume de Logs por Hora', fontsize=16)
        ax.set_xlabel('Hora', fontsize=12)
        ax.set_ylabel('Número de Logs', fontsize=12)
        
        # Formatar o eixo X para exibir as horas
        formatter = mdates.DateFormatter('%Y-%m-%d %H:%M')
        ax.xaxis.set_major_formatter(formatter)
        fig.autofmt_xdate() # Rotaciona as datas para melhor legibilidade
        
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend() # Exibe a legenda para a linha de tendência
        plt.tight_layout() # Ajusta o layout para evitar sobreposição
        
        # Salvar o gráfico em um buffer de bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300) # Salva como PNG de alta resolução
        buffer.seek(0) # Retorna ao início do buffer
        plt.close(fig) # Fecha a figura para liberar memória

        logger.info("Gráfico Matplotlib gerado com sucesso.")
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Erro ao gerar o gráfico Matplotlib: {e}")
        return None # Retorna None se a geração da imagem falhar


def generate_pdf_report(analysis_results, chart_image_bytes=None, output_dir="."):
    """Generates a PDF report from analysis results."""
    report_filename = f"relatorio_log_{datetime.now().strftime('%Y%m%d-%H-%M-%S')}.pdf"
    filepath = os.path.join(output_dir, report_filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()

    # Modificar estilos padrão existentes
    if 'Title' in styles:
        styles['Title'].fontSize = 24
        styles['Title'].leading = 28
        styles['Title'].alignment = TA_CENTER
        styles['Title'].spaceAfter = 20
        styles['Title'].fontName = 'Helvetica-Bold'
    else:
        # Fallback, though 'Title' should always be there
        styles.add(ParagraphStyle(name='Title', fontSize=24, leading=28, alignment=TA_CENTER, spaceAfter=20, fontName='Helvetica-Bold'))

    if 'h1' in styles:
        styles['h1'].fontSize = 18
        styles['h1'].leading = 22
        styles['h1'].spaceAfter = 14
        styles['h1'].fontName = 'Helvetica-Bold'
    else:
        styles.add(ParagraphStyle(name='h1', fontSize=18, leading=22, spaceAfter=14, fontName='Helvetica-Bold'))

    if 'h2' in styles:
        styles['h2'].fontSize = 14
        styles['h2'].leading = 18
        styles['h2'].spaceAfter = 10
        styles['h2'].fontName = 'Helvetica-Bold'
    else:
        styles.add(ParagraphStyle(name='h2', fontSize=14, leading=18, spaceAfter=10, fontName='Helvetica-Bold'))

    # Adicionar estilos personalizados se não existirem
    if 'BodyText' not in styles:
        styles.add(ParagraphStyle(name='BodyText', fontSize=10, leading=12, spaceAfter=6))
    if 'ListItem' not in styles:
        styles.add(ParagraphStyle(name='ListItem', fontSize=10, leading=12, spaceAfter=3, leftIndent=20))
    if 'Code' not in styles:
        styles.add(ParagraphStyle(name='Code', fontSize=9, leading=11, spaceAfter=3, fontName='Courier', backColor=colors.lightgrey))


    story = []

    # Título
    story.append(Paragraph("Relatório de Análise de Logs", styles['Title']))
    story.append(Paragraph(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['BodyText']))
    story.append(Paragraph(f"Logs Analisados: {analysis_results['load_analysis']['total_logs_processed']} logs", styles['BodyText']))
    story.append(Paragraph(f"Período Coberto: De {analysis_results['period_covered']['start']} a {analysis_results['period_covered']['end']}", styles['BodyText']))
    story.append(Spacer(1, 0.2 * inch))

    # Gráfico (se disponível)
    if chart_image_bytes:
        try:
            image = Image(BytesIO(chart_image_bytes))
            # Ajustar tamanho da imagem para caber na página (exemplo: largura 6 polegadas)
            img_width = 6 * inch
            img_height = image.drawHeight * img_width / image.drawWidth
            image.drawWidth = img_width
            image.drawHeight = img_height
            story.append(Paragraph("Volume de Logs por Hora", styles['h1']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(image)
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            logger.error(f"Erro ao adicionar imagem do gráfico ao PDF: {e}")
            story.append(Paragraph("<i>(Gráfico não disponível devido a um erro na geração)</i>", styles['BodyText']))
            story.append(Spacer(1, 0.2 * inch))
    else:
        story.append(Paragraph("<i>(Gráfico de Volume de Logs por Hora não disponível)</i>", styles['BodyText']))
        story.append(Spacer(1, 0.2 * inch))


    # Análise de Erros
    story.append(PageBreak()) # Nova página para Análise de Erros
    story.append(Paragraph("1. Análise de Erros", styles['h1']))
    story.append(Paragraph(f"Total de Erros Encontrados: {analysis_results['error_analysis']['total_errors']}", styles['BodyText']))
    story.append(Paragraph(f"Porcentagem de Erros (do total de logs): {analysis_results['error_analysis']['percentage_errors']:.2f}%", styles['BodyText']))
    story.append(Spacer(1, 0.1 * inch))

    if analysis_results['error_analysis']['top_errors_by_frequency']:
        story.append(Paragraph("Top 5 Erros por Frequência:", styles['h2']))
        for error in analysis_results['error_analysis']['top_errors_by_frequency']:
            story.append(Paragraph(f"- Mensagem: {error['message']}", styles['ListItem']))
            story.append(Paragraph(f"  Ocorrências: {error['occurrences']}", styles['ListItem']))
            story.append(Paragraph(f"  Última Ocorrência: {error['last_occurrence']}", styles['ListItem']))
            story.append(Spacer(1, 0.05 * inch))
    else:
        story.append(Paragraph("Nenhum erro encontrado.", styles['BodyText']))
    story.append(Spacer(1, 0.2 * inch))

    # Análise de Desempenho
    story.append(Paragraph("2. Análise de Desempenho", styles['h1']))
    if analysis_results['performance_analysis']['slowest_operations']:
        story.append(Paragraph("Top 5 Operações Mais Lentas:", styles['h2']))
        for op in analysis_results['performance_analysis']['slowest_operations']:
            story.append(Paragraph(f"- Mensagem: {op['message']}", styles['ListItem']))
            story.append(Paragraph(f"  Função: {op['function']}", styles['ListItem']))
            story.append(Paragraph(f"  Tempo: {op['time']:.4f} segundos", styles['ListItem']))
            story.append(Paragraph(f"  Timestamp: {op['timestamp']}", styles['ListItem']))
            story.append(Spacer(1, 0.05 * inch))
    else:
        story.append(Paragraph("Dados de desempenho não disponíveis ou insuficientes.", styles['BodyText']))
    story.append(Spacer(1, 0.2 * inch))

    # Análise de Carga
    story.append(Paragraph("3. Análise de Carga", styles['h1']))
    story.append(Paragraph(f"Total de Logs Processados: {analysis_results['load_analysis']['total_logs_processed']}", styles['BodyText']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Distribuição de Logs por Nível:", styles['h2']))
    for level, percentage in analysis_results['load_analysis']['log_level_distribution'].items():
        story.append(Paragraph(f"- <b>{level}:</b> {percentage}", styles['ListItem']))
    story.append(Spacer(1, 0.2 * inch))

    # Tabela de logs por hora (se houver dados)
    if 'raw_data' in analysis_results and analysis_results['raw_data']:
        df_raw = pd.DataFrame(analysis_results['raw_data'])
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], errors='coerce')
        df_raw.dropna(subset=['timestamp'], inplace=True)
        if not df_raw.empty:
            logs_per_hour_table = df_raw.groupby(df_raw['timestamp'].dt.floor('h')).size().reset_index(name='Contagem') # 'h' aqui também
            logs_per_hour_table.columns = ['Hora (UTC)', 'Contagem']
            logs_per_hour_table['Hora (UTC)'] = logs_per_hour_table['Hora (UTC)'].dt.strftime('%Y-%m-%d %H:%M')

            story.append(Paragraph("Logs por Hora (Tabela):", styles['h2']))
            # Formatação da tabela
            data = [logs_per_hour_table.columns.tolist()] + logs_per_hour_table.values.tolist()
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

    logger.info(f"Relatório PDF gerado com sucesso em: {filepath}")
    doc.build(story)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analisa logs e gera um relatório PDF.")
    parser.add_argument("--log_folder_path", type=str, required=True,
                        help="Caminho para a pasta contendo os arquivos de log.")
    parser.add_argument("--output_dir", type=str, default=".",
                        help="Diretório onde o relatório PDF será salvo (padrão: diretório atual).")

    args = parser.parse_args()

    logger.info("Iniciando análise de logs...")
    parsed_logs = read_logs_from_folder(args.log_folder_path)
    analysis_results = analyze_logs(parsed_logs)

    chart_image_bytes = None
    # Gerar o gráfico somente se houver dados para evitar erro no Matplotlib
    if parsed_logs:
        chart_image_bytes = generate_logs_per_hour_chart_image(analysis_results['raw_data'])
    
    generate_pdf_report(analysis_results, chart_image_bytes, args.output_dir)
    logger.info("Análise de logs concluída e relatório gerado.")

if __name__ == "__main__":
    # Adicione este import aqui para que Table e TableStyle estejam disponíveis
    # antes de serem usados na função generate_pdf_report
    from reportlab.platypus import Table, TableStyle
    main()