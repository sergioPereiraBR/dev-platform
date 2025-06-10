#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de Markdown para Word (.docx) - Versão Corrigida
Converte arquivos .md para .docx usando pypandoc com melhor suporte a Mermaid
CORREÇÃO: Resolve problemas de caminhos e codificação para imagens Mermaid
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
    puppeteer_chrome_patterns = [
        os.path.expanduser("~/.cache/puppeteer/chrome/linux-*/chrome-linux*/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser(
            "~/.local/share/ms-playwright/chromium-*/chrome-linux/chrome"
        ),
    ]

    puppeteer_paths = []

    try:
        import glob

        for pattern in puppeteer_chrome_patterns:
            paths = glob.glob(pattern)
            puppeteer_paths.extend(paths)

        # Ordenar por data de modificação (mais recente primeiro)
        if puppeteer_paths:
            puppeteer_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            print(f"✅ Chrome do Puppeteer encontrado: {puppeteer_paths[0]}")
            if not chrome_ok:
                chrome_ok = True
                chrome_path = puppeteer_paths[0]
    except Exception:
        pass

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


def obter_chrome_mais_recente():
    """Obtém o caminho do Chrome mais recente do Puppeteer"""
    import glob

    # Padrões para buscar Chrome do Puppeteer
    puppeteer_chrome_patterns = [
        os.path.expanduser("~/.cache/puppeteer/chrome/linux-*/chrome-linux*/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser(
            "~/.local/share/ms-playwright/chromium-*/chrome-linux/chrome"
        ),
    ]

    all_chrome_paths = []

    for pattern in puppeteer_chrome_patterns:
        paths = glob.glob(pattern)
        all_chrome_paths.extend(paths)

    if all_chrome_paths:
        # Ordenar por data de modificação (mais recente primeiro)
        all_chrome_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return all_chrome_paths[0]

    return None


def gerar_imagem_mermaid(
    codigo_mermaid,
    arquivo_saida,
    mermaid_cmd="mmdc",
    chrome_path=None,
    puppeteer_paths=None,
    pasta_temp=None,
):
    """Gera imagem PNG a partir de código Mermaid"""
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

        # Obter Chrome mais recente automaticamente
        chrome_atual = obter_chrome_mais_recente()

        if chrome_atual and os.path.exists(chrome_atual):
            print(f"   🌟 Usando Chrome mais recente: {chrome_atual}")

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
                    timeout=60,
                    env=env,
                )

                if result.returncode == 0 and os.path.exists(arquivo_saida):
                    file_size = os.path.getsize(arquivo_saida)
                    print(
                        f"   ✅ Diagrama gerado com sucesso! Tamanho: {file_size} bytes"
                    )
                    return True
                else:
                    print(f"   ⚠️  Falha com Chrome atual, tentando instalação...")
            except Exception as e:
                print(f"   ⚠️  Erro com Chrome atual: {e}")

        # Se falhou, tentar instalar Chrome novo
        print("   🔧 Instalando Chrome atualizado...")
        if instalar_chrome_puppeteer():
            # Buscar Chrome recém-instalado
            chrome_novo = obter_chrome_mais_recente()
            if chrome_novo and os.path.exists(chrome_novo):
                print(f"   🌟 Usando Chrome recém-instalado: {chrome_novo}")

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
                        timeout=60,
                        env=env,
                    )

                    if result.returncode == 0 and os.path.exists(arquivo_saida):
                        file_size = os.path.getsize(arquivo_saida)
                        print(
                            f"   ✅ Diagrama gerado após instalação! Tamanho: {file_size} bytes"
                        )
                        return True
                except Exception as e:
                    print(f"   ❌ Erro após instalação: {e}")

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


def instalar_chrome_puppeteer():
    """Tenta instalar o Chrome para Puppeteer"""
    print("🔧 Instalando Chrome para Puppeteer...")
    try:
        # Tentar diferentes comandos de instalação
        comandos = [
            ["npx", "puppeteer", "browsers", "install", "chrome"],
            ["npx", "@puppeteer/browsers", "install", "chrome@stable"],
            ["npx", "puppeteer", "browsers", "install", "chrome@stable"],
        ]

        for cmd in comandos:
            print(f"   Executando: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=180
                )
                if result.returncode == 0:
                    print("✅ Chrome instalado com sucesso!")
                    return True
                else:
                    if result.stderr and "already installed" in result.stderr.lower():
                        print("✅ Chrome já estava instalado!")
                        return True
                    if result.stderr:
                        print(f"   Falhou: {result.stderr[:100]}")
            except Exception as e:
                print(f"   Erro: {e}")
                continue

        return False
    except Exception as e:
        print(f"❌ Erro ao instalar Chrome: {e}")
        return False


def criar_pasta_imagens_temp(arquivo_base):
    """Cria uma pasta temporária para armazenar as imagens durante a conversão"""
    # Usar um nome simples sem caracteres especiais
    nome_base = Path(arquivo_base).stem
    # Normalizar nome removendo caracteres problemáticos
    nome_normalizado = re.sub(r"[^\w\-_.]", "_", nome_base)
    pasta_temp = tempfile.mkdtemp(prefix=f"mermaid_{nome_normalizado}_")

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
    """Converte um arquivo Markdown para Word"""
    pasta_temp_imagens = None

    try:
        # Verificar se arquivo existe
        if not os.path.exists(arquivo_md):
            print(f"❌ Arquivo não encontrado: {arquivo_md}")
            return False

        # Definir arquivo de saída se não especificado
        if arquivo_saida is None:
            caminho_base = Path(arquivo_md).stem
            arquivo_saida = f"{caminho_base}.{formato_saida}"

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


def criar_template_exemplo():
    """Cria um arquivo Markdown de exemplo para testes"""
    exemplo = """# Documento de Exemplo - Teste Mermaid

## Introdução

Este é um documento de **exemplo** para demonstrar a conversão de Markdown para Word com diagramas Mermaid.

### Características suportadas:

- **Texto em negrito**
- *Texto em itálico*
- `Código inline`
- [Links](https://www.example.com)

### Lista numerada:

1. Primeiro item
2. Segundo item
3. Terceiro item

### Bloco de código Python:

```python
def hello_world():
    print("Olá, mundo!")
    return True

# Exemplo de uso
if __name__ == "__main__":
    resultado = hello_world()
    print(f"Função executou: {resultado}")
```

### Diagrama Mermaid - Fluxograma Simples:

```mermaid
graph TD
    A[Início] --> B{Decisão}
    B -->|Sim| C[Ação 1]
    B -->|Não| D[Ação 2]
    C --> E[Fim]
    D --> E
```

### Diagrama Mermaid - Sequência:

```mermaid
sequenceDiagram
    participant U as Usuário
    participant S as Sistema
    participant D as Database
    
    U->>S: Solicita dados
    S->>D: Query SQL
    D-->>S: Retorna dados
    S-->>U: Exibe resultado
```

### Tabela de Exemplo:

| Nome | Idade | Cidade |
|------|-------|--------|
| Ana  | 25    | São Paulo |
| João | 30    | Rio de Janeiro |
| Maria | 28   | Belo Horizonte |

### Citação Inspiradora:

> "A vida é o que acontece enquanto você está ocupado fazendo outros planos."
> — John Lennon

### Lista de Tarefas:

- [x] Implementar conversão básica
- [x] Adicionar suporte a Mermaid
- [ ] Melhorar tratamento de erros
- [ ] Adicionar mais estilos

---

**Fim do documento de exemplo.**

*Este arquivo foi gerado automaticamente pelo conversor MD para Word.*
"""

    with open("exemplo.md", "w", encoding="utf-8") as f:
        f.write(exemplo)

    print("📄 Arquivo de exemplo criado: exemplo.md")
    print("💡 O exemplo inclui diagramas Mermaid que serão convertidos em imagens!")
    print("🔧 Execute: python md_to_word.py exemplo.md")


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
  python md_to_word.py --exemplo
  python md_to_word.py --verificar
  python md_to_word.py --resolver-chrome

Dependências necessárias:
  pip install pypandoc
  npm install -g @mermaid-js/mermaid-cli
  npx puppeteer browsers install chrome
        """,
    )

    parser.add_argument("erro", nargs="?", help="Verifique se as dependências estão corretamente instaladas no sistema operacional que estiver usando.")
    parser.add_argument("arquivo", nargs="?", help="Arquivo .md para converter")
    parser.add_argument("-o", "--output", help="Arquivo ou pasta de saída")
    parser.add_argument("-d", "--diretorio", help="Converter todos .md de uma pasta")
    parser.add_argument(
        "--sem-mermaid", action="store_true", help="Desabilitar processamento Mermaid"
    )
    parser.add_argument(
        "--exemplo", action="store_true", help="Criar arquivo de exemplo"
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

    # Criar exemplo se solicitado
    if args.exemplo:
        criar_template_exemplo()
        return

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
