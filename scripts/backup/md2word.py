#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de Markdown para Word (.docx) - Versão Corrigida
Converte arquivos .md para .docx usando pypandoc com melhor suporte a Mermaid
"""

import os
import sys
import argparse
import re
import tempfile
import subprocess
import shutil
from pathlib import Path
import pypandoc

def verificar_dependencias():
    """Verifica se o Pandoc e Mermaid CLI estão instalados"""
    pandoc_ok = True
    mermaid_ok = False
    pandoc_version = None
    mermaid_cmd = None
    
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
    
    # Verificar Mermaid CLI - múltiplas tentativas
    comandos_mermaid = ['mmdc', 'mermaid', 'mermaid-cli']
    
    print("🔍 Verificando Mermaid CLI...")
    
    for cmd in comandos_mermaid:
        try:
            # Tentar --version primeiro
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print(f"✅ Mermaid CLI encontrado: {cmd}")
                print(f"   Versão: {result.stdout.strip()}")
                mermaid_ok = True
                mermaid_cmd = cmd
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"   Tentativa {cmd}: {type(e).__name__}")
            continue
        
        # Se --version falhou, tentar --help
        try:
            result = subprocess.run([cmd, '--help'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and 'mermaid' in result.stdout.lower():
                print(f"✅ Mermaid CLI encontrado: {cmd}")
                mermaid_ok = True
                mermaid_cmd = cmd
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    
    if not mermaid_ok:
        print("❌ Mermaid CLI não encontrado!")
        print("\n📋 Para instalar o Mermaid CLI:")
        print("1. Certifique-se que Node.js está instalado:")
        print("   - Download: https://nodejs.org/")
        print("   - Versão recomendada: LTS")
        print("\n2. Instale o Mermaid CLI globalmente:")
        print("   npm install -g @mermaid-js/mermaid-cli")
        print("\n3. Alternativamente, tente:")
        print("   npm install -g mermaid.cli")
        print("\n4. Reinicie o terminal após a instalação")
        
        print("\n🔍 Diagnóstico do ambiente:")
        
        # Verificar se Node.js está instalado
        try:
            node_result = subprocess.run(['node', '--version'], 
                                       capture_output=True, text=True, timeout=10)
            if node_result.returncode == 0:
                print(f"   ✅ Node.js: {node_result.stdout.strip()}")
            else:
                print("   ❌ Node.js não encontrado")
        except Exception:
            print("   ❌ Node.js não encontrado")
        
        # Verificar se npm está instalado
        try:
            npm_result = subprocess.run(['npm', '--version'], 
                                      capture_output=True, text=True, timeout=10)
            if npm_result.returncode == 0:
                print(f"   ✅ npm: {npm_result.stdout.strip()}")
                
                # Verificar pacotes globais do npm
                try:
                    npm_list = subprocess.run(['npm', 'list', '-g', '--depth=0'], 
                                            capture_output=True, text=True, timeout=15)
                    if 'mermaid' in npm_list.stdout.lower():
                        print("   ℹ️  Mermaid encontrado nos pacotes npm, mas comando não acessível")
                        print("   💡 Tente adicionar o diretório npm global ao PATH")
                except Exception:
                    pass
            else:
                print("   ❌ npm não encontrado")
        except Exception:
            print("   ❌ npm não encontrado")
    
    return pandoc_ok, mermaid_ok, pandoc_version, mermaid_cmd

def obter_estilo_highlight_compativel(pandoc_version):
    """
    Retorna um estilo de highlight compatível com a versão do Pandoc
    """
    # Estilos mais seguros e amplamente suportados
    estilos_preferidos = ['pygments', 'kate', 'espresso', 'haddock', 'tango']
    
    # Para versões mais antigas, usar pygments como padrão
    if pandoc_version and pandoc_version.startswith('1.'):
        return 'pygments'
    
    # Para versões mais novas, tentar pygments primeiro
    return 'pygments'

def extrair_diagramas_mermaid(conteudo_md):
    """
    Extrai diagramas Mermaid do conteúdo Markdown
    """
    diagramas = []
    linhas = conteudo_md.split('\n')
    
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        
        # Detectar início de bloco Mermaid
        if linha.startswith('```mermaid'):
            inicio = i
            codigo_mermaid = []
            i += 1
            
            # Coletar conteúdo do diagrama
            while i < len(linhas) and not linhas[i].strip().startswith('```'):
                codigo_mermaid.append(linhas[i])
                i += 1
            
            if i < len(linhas):  # Encontrou o fim do bloco
                fim = i
                codigo_completo = '\n'.join(codigo_mermaid).strip()
                if codigo_completo:  # Só adicionar se tem conteúdo
                    diagramas.append((codigo_completo, inicio, fim))
        
        i += 1
    
    return diagramas

def gerar_imagem_mermaid(codigo_mermaid, arquivo_saida, mermaid_cmd='mmdc'):
    """
    Gera imagem PNG a partir de código Mermaid
    """
    temp_mermaid = None
    try:
        # Criar arquivo temporário com o código Mermaid
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(codigo_mermaid)
            temp_mermaid = temp_file.name
        
        print(f"   📄 Arquivo Mermaid temporário: {temp_mermaid}")
        print(f"   🎯 Arquivo de saída: {arquivo_saida}")
        
        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
        
        # Executar mermaid CLI para gerar imagem
        cmd = [
            mermaid_cmd, 
            '-i', temp_mermaid, 
            '-o', arquivo_saida,
            '-b', 'white',  # Background branco
            '-s', '2',      # Scale 2x para melhor qualidade
            '--theme', 'default'  # Tema padrão
        ]
        
        print(f"   🔧 Executando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"   📤 Return code: {result.returncode}")
        if result.stdout:
            print(f"   📝 STDOUT: {result.stdout}")
        if result.stderr:
            print(f"   ⚠️  STDERR: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(arquivo_saida):
            file_size = os.path.getsize(arquivo_saida)
            print(f"   ✅ Diagrama gerado com sucesso! Tamanho: {file_size} bytes")
            return True
        else:
            print(f"   ❌ Falha na geração do diagrama")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout ao gerar diagrama Mermaid")
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
                print(f"   ⚠️  Não foi possível remover arquivo temporário: {temp_mermaid}")

def processar_mermaid_no_markdown(arquivo_md, pasta_temp, mermaid_cmd='mmdc'):
    """
    Processa diagramas Mermaid e substitui por imagens no Markdown
    """
    # Ler conteúdo do arquivo
    with open(arquivo_md, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Extrair diagramas Mermaid
    diagramas = extrair_diagramas_mermaid(conteudo)
    
    if not diagramas:
        print("   ℹ️  Nenhum diagrama Mermaid encontrado")
        return arquivo_md  # Sem diagramas, retorna arquivo original
    
    print(f"🔍 Encontrados {len(diagramas)} diagramas Mermaid")
    
    # Processar cada diagrama
    linhas = conteudo.split('\n')
    offset = 0  # Para ajustar índices após modificações
    
    for i, (codigo, inicio, fim) in enumerate(diagramas):
        print(f"\n📊 Processando diagrama {i+1}/{len(diagramas)}...")
        
        # Ajustar índices pelo offset
        inicio_adj = inicio - offset
        fim_adj = fim - offset
        
        # Gerar imagem
        nome_imagem = f"mermaid_diagram_{i+1}.png"
        caminho_imagem = os.path.join(pasta_temp, nome_imagem)
        
        if gerar_imagem_mermaid(codigo, caminho_imagem, mermaid_cmd):
            # Substituir bloco Mermaid por referência à imagem
            substituicao = f"![Diagrama Mermaid {i+1}]({caminho_imagem})"
            
            # Remover linhas do diagrama e inserir referência à imagem
            linhas = linhas[:inicio_adj] + [substituicao] + linhas[fim_adj+1:]
            
            # Atualizar offset (removemos fim-inicio+1 linhas e adicionamos 1)
            offset += (fim - inicio + 1) - 1
            
            print(f"   ✅ Diagrama {i+1} processado com sucesso")
        else:
            print(f"   ⚠️  Mantendo código Mermaid original para diagrama {i+1}")
    
    # Salvar arquivo Markdown processado
    arquivo_processado = os.path.join(pasta_temp, f"processed_{os.path.basename(arquivo_md)}")
    with open(arquivo_processado, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))
    
    print(f"📝 Arquivo processado salvo: {arquivo_processado}")
    return arquivo_processado

def converter_arquivo(arquivo_md, arquivo_saida=None, formato_saida='docx', processar_mermaid=True, pandoc_version=None, mermaid_cmd='mmdc'):
    """
    Converte um arquivo Markdown para Word
    """
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
        
        # Criar pasta temporária para processamento
        pasta_temp = tempfile.mkdtemp(prefix='md_to_word_')
        print(f"📁 Pasta temporária: {pasta_temp}")
        
        arquivo_para_converter = arquivo_md
        
        try:
            # Processar diagramas Mermaid se solicitado
            if processar_mermaid:
                print("🎨 Processando diagramas Mermaid...")
                arquivo_para_converter = processar_mermaid_no_markdown(arquivo_md, pasta_temp, mermaid_cmd)
            
            # Configurar argumentos do Pandoc
            args_extra = [
                '--standalone',  # Documento completo
                '--toc',         # Índice automático
                '--toc-depth=3', # Profundidade do índice
            ]
            
            # Adicionar highlight style compatível
            estilo_highlight = obter_estilo_highlight_compativel(pandoc_version)
            args_extra.append(f'--highlight-style={estilo_highlight}')
            
            # Adicionar template se existir
            if os.path.exists('template.docx'):
                args_extra.append('--reference-doc=template.docx')
                print("📋 Usando template personalizado: template.docx")
            
            print("🔧 Executando conversão Pandoc...")
            
            # Realizar conversão
            pypandoc.convert_file(
                arquivo_para_converter,
                formato_saida,
                outputfile=arquivo_saida,
                extra_args=args_extra
            )
            
            # Verificar se arquivo foi criado
            if os.path.exists(arquivo_saida):
                file_size = os.path.getsize(arquivo_saida)
                print(f"✅ Conversão concluída: {arquivo_saida} ({file_size} bytes)")
                return True
            else:
                print("❌ Arquivo de saída não foi criado")
                return False
            
        finally:
            # Limpar pasta temporária
            try:
                shutil.rmtree(pasta_temp)
                print("🧹 Pasta temporária removida")
            except Exception as e:
                print(f"⚠️  Erro ao remover pasta temporária: {e}")
        
    except Exception as e:
        print(f"❌ Erro na conversão: {str(e)}")
        
        # Tentar conversão mais simples em caso de erro
        try:
            print("🔄 Tentando conversão simplificada...")
            
            args_simples = ['--standalone']
            
            pypandoc.convert_file(
                arquivo_md,
                formato_saida,
                outputfile=arquivo_saida,
                extra_args=args_simples
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

def converter_pasta(pasta_origem, pasta_destino=None, processar_mermaid=True, pandoc_version=None, mermaid_cmd='mmdc'):
    """
    Converte todos os arquivos .md de uma pasta
    """
    if not os.path.exists(pasta_origem):
        print(f"❌ Pasta não encontrada: {pasta_origem}")
        return
    
    # Criar pasta de destino se não existir
    if pasta_destino and not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta criada: {pasta_destino}")
    
    # Encontrar todos os arquivos .md
    arquivos_md = list(Path(pasta_origem).glob('*.md'))
    
    if not arquivos_md:
        print(f"📝 Nenhum arquivo .md encontrado em: {pasta_origem}")
        return
    
    print(f"📚 Encontrados {len(arquivos_md)} arquivos .md")
    
    sucessos = 0
    for arquivo in arquivos_md:
        arquivo_saida = None
        if pasta_destino:
            arquivo_saida = os.path.join(pasta_destino, f"{arquivo.stem}.docx")
        
        if converter_arquivo(str(arquivo), arquivo_saida, 'docx', processar_mermaid, pandoc_version, mermaid_cmd):
            sucessos += 1
    
    print(f"\n🎉 Conversão concluída: {sucessos}/{len(arquivos_md)} arquivos convertidos")

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
    
    with open('exemplo.md', 'w', encoding='utf-8') as f:
        f.write(exemplo)
    
    print("📄 Arquivo de exemplo criado: exemplo.md")
    print("💡 O exemplo inclui diagramas Mermaid que serão convertidos em imagens!")
    print("🔧 Execute: python md_to_word.py exemplo.md")

def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description='Conversor de Markdown para Word com suporte melhorado a diagramas Mermaid',
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

Dependências necessárias:
  pip install pypandoc
  npm install -g @mermaid-js/mermaid-cli

Para resolver problemas:
  1. Certifique-se que Node.js está instalado
  2. Instale o Mermaid CLI globalmente
  3. Reinicie o terminal após a instalação
  4. Use --verificar para diagnosticar problemas
        """
    )
    
    parser.add_argument('arquivo', nargs='?', help='Arquivo .md para converter')
    parser.add_argument('-o', '--output', help='Arquivo ou pasta de saída')
    parser.add_argument('-d', '--diretorio', help='Converter todos .md de uma pasta')
    parser.add_argument('--sem-mermaid', action='store_true', help='Desabilitar processamento Mermaid')
    parser.add_argument('--exemplo', action='store_true', help='Criar arquivo de exemplo')
    parser.add_argument('--verificar', action='store_true', help='Verificar dependências e sair')
    parser.add_argument('--versao', action='version', version='%(prog)s 2.1 - Versão Corrigida')
    
    args = parser.parse_args()
    
    # Verificar dependências
    pandoc_ok, mermaid_ok, pandoc_version, mermaid_cmd = verificar_dependencias()
    
    if args.verificar:
        print("\n" + "="*50)
        print("RESUMO DA VERIFICAÇÃO:")
        print("="*50)
        print(f"Pandoc: {'✅ OK' if pandoc_ok else '❌ ERRO'}")
        print(f"Mermaid CLI: {'✅ OK' if mermaid_ok else '❌ ERRO'}")
        if mermaid_cmd:
            print(f"Comando Mermaid: {mermaid_cmd}")
        print("="*50)
        return
    
    if not pandoc_ok:
        print("\n❌ Pandoc é obrigatório para a conversão!")
        sys.exit(1)
    
    # Avisar se Mermaid não estiver disponível
    processar_mermaid = mermaid_ok and not args.sem_mermaid
    
    if not mermaid_ok and not args.sem_mermaid:
        print("\n⚠️  AVISO: Diagramas Mermaid serão mantidos como código")
        print("   Para converter diagramas em imagens, instale o Mermaid CLI")
        print("   Use --verificar para ver instruções detalhadas")
        processar_mermaid = False
    
    # Criar exemplo se solicitado
    if args.exemplo:
        criar_template_exemplo()
        return
    
    # Converter pasta
    if args.diretorio:
        converter_pasta(args.diretorio, args.output, processar_mermaid, pandoc_version, mermaid_cmd)
        return
    
    # Converter arquivo único
    if args.arquivo:
        converter_arquivo(args.arquivo, args.output, 'docx', processar_mermaid, pandoc_version, mermaid_cmd)
        return
    
    # Se nenhum argumento foi fornecido, mostrar ajuda
    parser.print_help()

if __name__ == "__main__":
    main()
