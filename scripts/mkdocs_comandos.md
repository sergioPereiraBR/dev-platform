# Comandos para gerenciar a documentação MkDocs

## Iniciando o servidor de desenvolvimento

Para iniciar o servidor de desenvolvimento e visualizar a documentação enquanto você edita:

```bash
# Usando o comando direto do MkDocs
poetry run mkdocs serve

# OU usando o script definido no pyproject.toml
poetry run docs-serve
```

Acesse `http://127.0.0.1:8000` no navegador para ver a documentação.

## Gerando a documentação estática

Para gerar os arquivos HTML estáticos da documentação:

```bash
# Usando o comando direto do MkDocs
poetry run mkdocs build

# OU usando o script definido no pyproject.toml
poetry run docs-build
```

Os arquivos gerados estarão na pasta `site/` na raiz do projeto.

## Publicando a documentação

Se quiser publicar a documentação no GitHub Pages:

```bash
poetry run mkdocs gh-deploy
```

Isso construirá a documentação e a enviará para a branch `gh-pages` do seu repositório.

## Verificando erros na documentação

Para verificar se há links quebrados ou outros problemas:

```bash
poetry run mkdocs build --strict
```

## Criando nova página de documentação

Para criar uma nova página, adicione um arquivo .md no local apropriado sob o diretório `docs/` e atualize o `nav` no arquivo `mkdocs.yml`.
