#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de Markdown para Word (.docx) - Versão Corrigida
Converte arquivos .md para .docx usando pypandoc com melhor suporte a Mermaid
CORREÇÃO: Resolve problemas de timeout, permissões e paths de Chrome
"""

import os
import sys
import argparse
import re
import tempfile
import subprocess
import shutil
import json
from pathlib import Path
import pypandoc
import time


def verificar_dependencias():
    """Verifica se o Pandoc e Mermaid CLI estão instalados"""
    pandoc_ok = True
    mermaid_ok = False
    pandoc_version = None
    mermaid_cmd = None
    chrome_ok = False
    chrome_path = None

    # Verificar Pandoc
    try:
        pandoc_version = pypandoc.get_pandoc_version()
        print(f"✅ Pandoc encontrado (versão {pandoc_version})")
    except OSError:
        print("❌ Pandoc não encontrado!")
        print("Por favor, instale o Pandoc:")
        print("- Windows: choco install pandoc")
        print("- macOS: brew install pandoc")
        print("- Ubuntu/Debian: sudo apt-get install pandoc")
        print("- Ou baixe de: https://pandoc.org/installing.html")
        pandoc_ok = False

    # Verificar Chrome/Chromium no sistema
    chrome_commands = [
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome",
    ]

    print("🔍 Verificando Chrome/Chromium no sistema...")
    for cmd in chrome_commands:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Chrome/Chromium encontrado: {cmd}")
                print(f"   Versão: {result.stdout.strip()}")
                chrome_ok = True
                # Obter caminho completo do executável
                chrome_path_result = subprocess.run(
                    ["which", cmd], capture_output=True, text=True
                )
                if chrome_path_result.returncode == 0:
                    chrome_path = chrome_path_result.stdout.strip()
                    print(f"   Caminho: {chrome_path}")
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    # Verificar Chrome do Puppeteer - buscar versões mais recentes primeiro
    puppeteer_paths = obter_caminhos_chrome_puppeteer()
    
    if puppeteer_paths and not chrome_ok:
        print(f"✅ Chrome do Puppeteer encontrado: {puppeteer_paths[0]}")
        chrome_ok = True
        chrome_path = puppeteer_paths[0]

    if not chrome_ok:
        print("❌ Chrome/Chromium não encontrado!")

    # Verificar Mermaid CLI
    comandos_mermaid = ["mmdc", "mermaid", "mermaid-cli"]

    print("🔍 Verificando Mermaid CLI...")

    for cmd in comandos_mermaid:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                print(f"✅ Mermaid CLI encontrado: {cmd}")
                print(f"   Versão: {result.stdout.strip()}")
                mermaid_ok = True
                mermaid_cmd = cmd
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    if not mermaid_ok:
        print("❌ Mermaid CLI não encontrado!")
        print_mermaid_install_instructions()

    return (
        pandoc_ok,
        mermaid_ok,
        pandoc_version,
        mermaid_cmd,
        chrome_ok,
        chrome_path,
        puppeteer_paths,
    )


def print_mermaid_install_instructions():
    """Imprime instruções de instalação do Mermaid"""
    print("\n📋 Para instalar o Mermaid CLI:")
    print("1. Certifique-se que Node.js está instalado:")
    print("   - Download: https://nodejs.org/")
    print("   - Versão recomendada: LTS")
    print("\n2. Instale o Mermaid CLI globalmente:")
    print("   npm install -g @mermaid-js/mermaid-cli")
    print("\n3. Instale o Chrome headless para Puppeteer:")
    print("   npx puppeteer browsers install chrome")


def obter_estilo_highlight_compativel(pandoc_version):
    """Retorna um estilo de highlight compatível com a versão do Pandoc"""
    estilos_preferidos = ["pygments", "kate", "espresso", "haddock", "tango"]

    if pandoc_version and pandoc_version.startswith("1."):
        return "pygments"

    return "pygments"


def extrair_diagramas_mermaid(conteudo_md):
    """Extrai diagramas Mermaid do conteúdo Markdown"""
    diagramas = []
    linhas = conteudo_md.split("\n")

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if linha.startswith("```mermaid"):
            inicio = i
            codigo_mermaid = []
            i += 1

            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                codigo_mermaid.append(linhas[i])
                i += 1

            if i < len(linhas):
                fim = i
                codigo_completo = "\n".join(codigo_mermaid).strip()
                if codigo_completo:
                    diagramas.append((codigo_completo, inicio, fim))

        i += 1

    return diagramas


def obter_caminhos_chrome_puppeteer():
    """Obtém todos os caminhos possíveis do Chrome do Puppeteer"""
    import glob

    # Padrões para buscar Chrome do Puppeteer
    puppeteer_chrome_patterns = [
        os.path.expanduser("~/.cache/puppeteer/chrome/linux-*/chrome-linux*/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser("~/.local/share/ms-playwright/chromium-*/chrome-linux/chrome"),
        "/root/.cache/puppeteer/chrome/linux-*/chrome-linux*/chrome",
    ]

    all_chrome_paths = []

    for pattern in puppeteer_chrome_patterns:
        try:
            paths = glob.glob(pattern)
            all_chrome_paths.extend(paths)
        except Exception:
            continue

    if all_chrome_paths:
        # Ordenar por data de modificação (mais recente primeiro)
        try:
            all_chrome_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        except:
            pass

    return all_chrome_paths


def testar_chrome_funcional(chrome_path):
    """Testa se um caminho do Chrome é funcional"""
    if not chrome_path or not os.path.exists(chrome_path):
        return False
    
    try:
        # Teste básico - verificar se o Chrome executa
        result = subprocess.run(
            [chrome_path, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def instalar_chrome_puppeteer():
    """Tenta instalar o Chrome para Puppeteer com timeout reduzido"""
    print("🔧 Instalando Chrome para Puppeteer...")
    try:
        # Comandos com timeout reduzido
        comandos = [
            ["npx", "puppeteer", "browsers", "install", "chrome"],
            ["npx", "@puppeteer/browsers", "install", "chrome@stable"],
        ]

        for cmd in comandos:
            print(f"   Executando: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120  # Reduzido para 2 min
                )
                if result.returncode == 0:
                    print("✅ Chrome instalado com sucesso!")
                    time.sleep(2)  # Aguardar instalação finalizar
                    return True
                else:
                    if result.stderr and "already installed" in result.stderr.lower():
                        print("✅ Chrome já estava instalado!")
                        return True
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  Timeout - comando levou mais de 2 minutos")
                continue
            except Exception as e:
                print(f"   Erro: {e}")
                continue

        return False
    except Exception as e:
        print(f"❌ Erro ao instalar Chrome: {e}")
        return False


def gerar_imagem_mermaid(
    codigo_mermaid,
    arquivo_saida,
    mermaid_cmd="mmdc",
    chrome_path=None,
    puppeteer_paths=None,
    pasta_temp=None,
):
    """Gera imagem PNG a partir de código Mermaid com melhor tratamento de erros"""
    temp_mermaid = None

    try:
        # Criar arquivo temporário com o código Mermaid
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(codigo_mermaid)
            temp_mermaid = temp_file.name

        print(f"   📄 Arquivo Mermaid temporário: {temp_mermaid}")
        print(f"   🎯 Arquivo de saída: {arquivo_saida}")

        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)

        # Obter todos os caminhos do Chrome disponíveis
        chrome_paths = obter_caminhos_chrome_puppeteer()
        
        # Adicionar chrome_path se fornecido
        if chrome_path and chrome_path not in chrome_paths:
            chrome_paths.insert(0, chrome_path)

        # Tentar usar Chrome existente primeiro
        for chrome_atual in chrome_paths:
            if not testar_chrome_funcional(chrome_atual):
                continue
                
            print(f"   🌟 Testando Chrome: {chrome_atual}")

            env = os.environ.copy()
            env["PUPPETEER_EXECUTABLE_PATH"] = chrome_atual

            try:
                result = subprocess.run(
                    [
                        mermaid_cmd,
                        "-i",
                        temp_mermaid,
                        "-o",
                        arquivo_saida,
                        "-b",
                        "white",
                        "-s",
                        "2",
                        "--theme",
                        "default",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,  # Timeout reduzido
                    env=env,
                )

                if result.returncode == 0 and os.path.exists(arquivo_saida):
                    file_size = os.path.getsize(arquivo_saida)
                    if file_size > 0:  # Verificar se arquivo não está vazio
                        print(f"   ✅ Diagrama gerado! Tamanho: {file_size} bytes")
                        return True
                    else:
                        print(f"   ⚠️  Arquivo gerado está vazio")
                        os.remove(arquivo_saida)
                else:
                    if result.stderr:
                        print(f"   ⚠️  Erro: {result.stderr[:100]}")
                        
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  Timeout com Chrome atual")
                continue
            except Exception as e:
                print(f"   ⚠️  Erro: {e}")
                continue

        # Se chegou até aqui, não conseguiu gerar com Chrome existente
        print("   🔧 Tentando instalar Chrome novo...")
        
        # Tentar instalar apenas se não tiver nenhum Chrome funcional
        if not any(testar_chrome_funcional(p) for p in chrome_paths):
            if instalar_chrome_puppeteer():
                # Buscar Chrome recém-instalado
                novos_paths = obter_caminhos_chrome_puppeteer()
                for chrome_novo in novos_paths:
                    if not testar_chrome_funcional(chrome_novo):
                        continue
                        
                    print(f"   🌟 Testando Chrome novo: {chrome_novo}")

                    env = os.environ.copy()
                    env["PUPPETEER_EXECUTABLE_PATH"] = chrome_novo

                    try:
                        result = subprocess.run(
                            [
                                mermaid_cmd,
                                "-i",
                                temp_mermaid,
                                "-o",
                                arquivo_saida,
                                "-b",
                                "white",
                                "-s",
                                "2",
                                "--theme",
                                "default",
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            env=env,
                        )

                        if result.returncode == 0 and os.path.exists(arquivo_saida):
                            file_size = os.path.getsize(arquivo_saida)
                            if file_size > 0:
                                print(f"   ✅ Diagrama gerado após instalação! Tamanho: {file_size} bytes")
                                return True
                            else:
                                print(f"   ⚠️  Arquivo gerado está vazio")
                                os.remove(arquivo_saida)
                    except Exception as e:
                        print(f"   ❌ Erro: {e}")
                        continue

        print(f"   ❌ Falha ao gerar diagrama")
        return False

    except Exception as e:
        print(f"   ❌ Erro inesperado: {str(e)}")
        return False
    finally:
        # Limpar arquivo temporário
        if temp_mermaid and os.path.exists(temp_mermaid):
            try:
                os.unlink(temp_mermaid)
                print(f"   🧹 Arquivo temporário removido")
            except Exception:
                pass


def criar_pasta_imagens_temp(arquivo_base):
    """Cria uma pasta temporária para armazenar as imagens durante a conversão"""
    # Criar pasta temporária com nome simples
    pasta_temp = tempfile.mkdtemp(prefix="mermaid_temp_")
    print(f"📁 Pasta temporária de imagens criada: {pasta_temp}")
    return pasta_temp


def processar_mermaid_no_markdown(
    arquivo_md, mermaid_cmd="mmdc", chrome_path=None, puppeteer_paths=None
):
    """Processa diagramas Mermaid e substitui por imagens no Markdown"""
    # Ler conteúdo do arquivo
    with open(arquivo_md, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Extrair diagramas Mermaid
    diagramas = extrair_diagramas_mermaid(conteudo)

    if not diagramas:
        print("   ℹ️  Nenhum diagrama Mermaid encontrado")
        return arquivo_md, None

    print(f"🔍 Encontrados {len(diagramas)} diagramas Mermaid")

    # Criar pasta temporária para imagens
    pasta_temp = criar_pasta_imagens_temp(arquivo_md)

    # Processar cada diagrama
    linhas = conteudo.split("\n")
    offset = 0
    diagramas_processados = 0

    for i, (codigo, inicio, fim) in enumerate(diagramas):
        print(f"\n📊 Processando diagrama {i+1}/{len(diagramas)}...")

        # Ajustar índices pelo offset
        inicio_adj = inicio - offset
        fim_adj = fim - offset

        # Gerar imagem na pasta temporária com nome simples
        nome_imagem = f"diagram_{i+1}.png"
        caminho_imagem = os.path.join(pasta_temp, nome_imagem)

        if gerar_imagem_mermaid(
            codigo, caminho_imagem, mermaid_cmd, chrome_path, puppeteer_paths
        ):
            # Substituir bloco Mermaid por referência à imagem usando caminho absoluto
            substituicao = f"![Diagrama Mermaid {i+1}]({caminho_imagem})"

            # Remover linhas do diagrama e inserir referência à imagem
            linhas = linhas[:inicio_adj] + [substituicao] + linhas[fim_adj + 1 :]

            # Atualizar offset
            offset += (fim - inicio + 1) - 1
            diagramas_processados += 1

            print(f"   ✅ Diagrama {i+1} processado com sucesso")
        else:
            print(f"   ⚠️  Mantendo código Mermaid original para diagrama {i+1}")

    # Salvar arquivo Markdown processado temporariamente
    arquivo_processado = os.path.join(pasta_temp, "processed.md")
    with open(arquivo_processado, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"📝 Arquivo processado salvo: {arquivo_processado}")
    print(f"🎯 Diagramas convertidos: {diagramas_processados}/{len(diagramas)}")

    return arquivo_processado, pasta_temp


def converter_arquivo(
    arquivo_md,
    arquivo_saida=None,
    formato_saida="docx",
    processar_mermaid=True,
    pandoc_version=None,
    mermaid_cmd="mmdc",
    chrome_path=None,
    puppeteer_paths=None,
):
    """Converte um arquivo Markdown para Word com melhor tratamento de permissões"""
    pasta_temp_imagens = None

    try:
        # Verificar se arquivo existe
        if not os.path.exists(arquivo_md):
            print(f"❌ Arquivo não encontrado: {arquivo_md}")
            return False

        # Definir arquivo de saída se não especificado
        if arquivo_saida is None:
            caminho_base = Path(arquivo_md).stem
            # Usar pasta atual em vez do diretório do arquivo MD
            arquivo_saida = os.path.join(os.getcwd(), f"{caminho_base}.docx")

        # Verificar permissões de escrita no diretório de saída
        diretorio_saida = os.path.dirname(os.path.abspath(arquivo_saida))
        if not os.access(diretorio_saida, os.W_OK):
            print(f"❌ Sem permissão de escrita em: {diretorio_saida}")
            # Tentar usar diretório temporário
            arquivo_saida = os.path.join(tempfile.gettempdir(), os.path.basename(arquivo_saida))
            print(f"🔄 Usando arquivo temporário: {arquivo_saida}")

        print(f"\n📝 Convertendo: {arquivo_md} → {arquivo_saida}")

        arquivo_para_converter = arquivo_md

        try:
            # Processar diagramas Mermaid se solicitado
            if processar_mermaid:
                print("🎨 Processando diagramas Mermaid...")
                (
                    arquivo_para_converter,
                    pasta_temp_imagens,
                ) = processar_mermaid_no_markdown(
                    arquivo_md, mermaid_cmd, chrome_path, puppeteer_paths
                )

            # Configurar argumentos do Pandoc
            args_extra = [
                "--standalone",
                "--toc",
                "--toc-depth=3",
            ]

            # Adicionar highlight style compatível
            estilo_highlight = obter_estilo_highlight_compativel(pandoc_version)
            args_extra.append(f"--highlight-style={estilo_highlight}")

            # Adicionar template se existir
            if os.path.exists("template.docx"):
                args_extra.append("--reference-doc=template.docx")
                print("📋 Usando template personalizado: template.docx")

            print("🔧 Executando conversão Pandoc...")

            # Realizar conversão
            pypandoc.convert_file(
                arquivo_para_converter,
                formato_saida,
                outputfile=arquivo_saida,
                extra_args=args_extra,
            )

            # Verificar se arquivo foi criado
            if os.path.exists(arquivo_saida):
                file_size = os.path.getsize(arquivo_saida)
                print(f"✅ Conversão concluída: {arquivo_saida} ({file_size} bytes)")
                return True
            else:
                print("❌ Arquivo de saída não foi criado")
                return False

        except Exception as e:
            print(f"❌ Erro na conversão: {str(e)}")

            # Tentar conversão mais simples em caso de erro
            try:
                print("🔄 Tentando conversão simplificada...")

                args_simples = ["--standalone"]

                pypandoc.convert_file(
                    arquivo_md,
                    formato_saida,
                    outputfile=arquivo_saida,
                    extra_args=args_simples,
                )

                if os.path.exists(arquivo_saida):
                    print(f"✅ Conversão simplificada concluída: {arquivo_saida}")
                    return True
                else:
                    print("❌ Conversão simplificada também falhou")
                    return False

            except Exception as e2:
                print(f"❌ Erro na conversão simplificada: {str(e2)}")
                return False

    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return False
    finally:
        # Limpar pasta temporária de imagens
        if pasta_temp_imagens and os.path.exists(pasta_temp_imagens):
            try:
                shutil.rmtree(pasta_temp_imagens)
                print("🧹 Pasta temporária de imagens removida")
            except Exception as e:
                print(f"⚠️  Não foi possível remover pasta temporária: {e}")


def converter_pasta(
    pasta_origem,
    pasta_destino=None,
    processar_mermaid=True,
    pandoc_version=None,
    mermaid_cmd="mmdc",
    chrome_path=None,
    puppeteer_paths=None,
):
    """Converte todos os arquivos .md de uma pasta"""
    if not os.path.exists(pasta_origem):
        print(f"❌ Pasta não encontrada: {pasta_origem}")
        return

    # Criar pasta de destino se não existir
    if pasta_destino and not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta criada: {pasta_destino}")

    # Encontrar todos os arquivos .md
    arquivos_md = list(Path(pasta_origem).glob("*.md"))

    if not arquivos_md:
        print(f"📝 Nenhum arquivo .md encontrado em: {pasta_origem}")
        return

    print(f"📚 Encontrados {len(arquivos_md)} arquivos .md")

    sucessos = 0
    for arquivo in arquivos_md:
        arquivo_saida = None
        if pasta_destino:
            arquivo_saida = os.path.join(pasta_destino, f"{arquivo.stem}.docx")

        if converter_arquivo(
            str(arquivo),
            arquivo_saida,
            "docx",
            processar_mermaid,
            pandoc_version,
            mermaid_cmd,
            chrome_path,
            puppeteer_paths,
        ):
            sucessos += 1

    print(
        f"\n🎉 Conversão concluída: {sucessos}/{len(arquivos_md)} arquivos convertidos"
    )

def resolver_problema_chrome():
    """Função para resolver automaticamente o problema do Chrome"""
    print("🔧 Iniciando resolução automática do problema do Chrome...")

    # Verificar configuração atual
    _, _, _, _, chrome_ok, chrome_path, puppeteer_paths = verificar_dependencias()

    if chrome_ok:
        print(f"✅ Chrome já está disponível: {chrome_path}")

    # Tentar instalar Chrome via Puppeteer
    print("1. Instalando Chrome via Puppeteer...")
    if instalar_chrome_puppeteer():
        print("✅ Problema do Chrome resolvido!")
        return True

    # Sugerir instalação manual
    print("2. Instalação manual do Chrome/Chromium...")
    print("\nPara resolver permanentemente, instale o Chrome ou Chromium:")
    print("\nUbuntu/Debian:")
    print("  sudo apt update")
    print("  sudo apt install chromium-browser")
    print("\nOu para Google Chrome:")
    print(
        "  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
    )
    print(
        "  echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list"
    )
    print("  sudo apt update && sudo apt install google-chrome-stable")

    return False


def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Conversor de Markdown para Word com suporte melhorado a diagramas Mermaid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python md_to_word.py arquivo.md
  python md_to_word.py arquivo.md -o documento.docx
  python md_to_word.py arquivo.md --sem-mermaid
  python md_to_word.py -d pasta_markdown/
  python md_to_word.py -d origem/ -o destino/
  python md_to_word.py --verificar
  python md_to_word.py --resolver-chrome

Dependências necessárias:
  pip install pypandoc
  npm install -g @mermaid-js/mermaid-cli
  npx puppeteer browsers install chrome
        """,
    )

    parser.add_argument("arquivo", nargs="?", help="Arquivo .md para converter")
    parser.add_argument("-o", "--output", help="Arquivo ou pasta de saída")
    parser.add_argument("-d", "--diretorio", help="Converter todos .md de uma pasta")
    parser.add_argument(
        "--sem-mermaid", action="store_true", help="Desabilitar processamento Mermaid"
    )
    parser.add_argument(
        "--verificar", action="store_true", help="Verificar dependências e sair"
    )
    parser.add_argument(
        "--resolver-chrome",
        action="store_true",
        help="Tentar resolver problema do Chrome automaticamente",
    )
    parser.add_argument(
        "--versao",
        action="version",
        version="%(prog)s 2.5 - Versão corrigida para caminhos de imagens",
    )

    args = parser.parse_args()

    # Resolver problema do Chrome se solicitado
    if args.resolver_chrome:
        resolver_problema_chrome()
        return

    # Verificar dependências
    (
        pandoc_ok,
        mermaid_ok,
        pandoc_version,
        mermaid_cmd,
        chrome_ok,
        chrome_path,
        puppeteer_paths,
    ) = verificar_dependencias()

    if args.verificar:
        print("\n" + "=" * 50)
        print("RESUMO DA VERIFICAÇÃO:")
        print(f"Pandoc: {'✅ OK' if pandoc_ok else '❌ ERRO'}")
        print(f"Mermaid CLI: {'✅ OK' if mermaid_ok else '❌ ERRO'}")
        print(f"Chrome/Chromium: {'✅ OK' if chrome_ok else '❌ ERRO'}")
        if mermaid_cmd:
            print(f"Comando Mermaid: {mermaid_cmd}")
        if chrome_path:
            print(f"Caminho Chrome: {chrome_path}")
        print("=" * 50)

        if mermaid_ok and not chrome_ok:
            print("\n💡 SOLUÇÃO RECOMENDADA:")
            print("Execute: python md_to_word.py --resolver-chrome")

        return

    if not pandoc_ok:
        print("\n❌ Pandoc é obrigatório para a conversão!")
        sys.exit(1)

    # Avisar se Mermaid não estiver disponível
    processar_mermaid = mermaid_ok and not args.sem_mermaid

    if not mermaid_ok and not args.sem_mermaid:
        print("\n⚠️  AVISO: Diagramas Mermaid serão mantidos como código")
        print(
            "   Para converter diagramas Mermaid em imagens, instale o Mermaid CLI e o Chrome/Chromium, ou use a opção --sem-mermaid para desabilitar o processamento de diagramas."
        )
        print("   Use --verificar para ver instruções detalhadas")
        processar_mermaid = False

    # Converter pasta
    if args.diretorio:
        converter_pasta(
            args.diretorio, args.output, processar_mermaid, pandoc_version, mermaid_cmd
        )
        return

    # Converter arquivo único
    if args.arquivo:
        converter_arquivo(
            args.arquivo,
            args.output,
            "docx",
            processar_mermaid,
            pandoc_version,
            mermaid_cmd,
        )
        return

    # Se nenhum argumento foi fornecido, mostrar ajuda
    parser.print_help()


if __name__ == "__main__":
    main()
