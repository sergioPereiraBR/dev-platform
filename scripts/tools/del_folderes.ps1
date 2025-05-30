# .\scripts\tools\del_folderes.ps1 ".\src" "__pycache__"
param(
    [Parameter(Mandatory=$true)]
    [string]$PastaRaiz,
    
    [Parameter(Mandatory=$true)]
    [string]$NomePasta
)

Write-Host "Executando del_folderes.ps1 na pasta '$PastaRaiz' para apagar pastas e subpastas com nome '$NomePasta'." -ForegroundColor Blue

# Verifica se a pasta raiz existe
if (-not (Test-Path -Path $PastaRaiz -PathType Container)) {
    Write-Error "A pasta raiz '$PastaRaiz' não existe ou não é uma pasta válida."
    exit 1
}

# Converte para caminho absoluto
$PastaRaiz = (Get-Item -Path $PastaRaiz).FullName

Write-Host "Procurando pastas com nome '$NomePasta' em '$PastaRaiz'..." -ForegroundColor Yellow

try {
    # Busca todas as pastas com o nome especificado recursivamente
    $pastasEncontradas = Get-ChildItem -Path $PastaRaiz -Filter $NomePasta -Directory -Recurse -ErrorAction SilentlyContinue
    
    if ($pastasEncontradas.Count -eq 0) {
        Write-Host "Nenhuma pasta com nome '$NomePasta' foi encontrada." -ForegroundColor Green
        exit 0
    }
    
    Write-Host "Encontradas $($pastasEncontradas.Count) pasta(s) com nome '$NomePasta':" -ForegroundColor Cyan
    
    # Lista as pastas encontradas
    foreach ($pasta in $pastasEncontradas) {
        Write-Host "  - $($pasta.FullName)" -ForegroundColor Gray
    }
    
    # Confirma a exclusão
    $confirmacao = Read-Host "`nDeseja realmente deletar todas essas pastas? (S/N)"
    
    if ($confirmacao -match "^[Ss]$") {
        $contadorSucesso = 0
        $contadorErro = 0
        
        foreach ($pasta in $pastasEncontradas) {
            try {
                Remove-Item -Path $pasta.FullName -Recurse -Force -ErrorAction Stop
                Write-Host "✓ Deletada: $($pasta.FullName)" -ForegroundColor Green
                $contadorSucesso++
            }
            catch {
                Write-Host "✗ Erro ao deletar: $($pasta.FullName)" -ForegroundColor Red
                Write-Host "  Motivo: $($_.Exception.Message)" -ForegroundColor Red
                $contadorErro++
            }
        }
        
        Write-Host "`nResumo da operação:" -ForegroundColor Yellow
        Write-Host "  Pastas deletadas com sucesso: $contadorSucesso" -ForegroundColor Green
        Write-Host "  Pastas com erro na exclusão: $contadorErro" -ForegroundColor Red
    }
    else {
        Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
    }
}
catch {
    Write-Error "Erro durante a busca: $($_.Exception.Message)"
    exit 1
}
