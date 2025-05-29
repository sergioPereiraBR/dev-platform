# Definir a estrutura de pastas
param($estrutura)
$Computers = Get-Content -Path .\$estrutura
$folderStructure = @(
    $Computers
)

# Criar as pastas
foreach ($folder in $folderStructure) {
    if (-not (Test-Path -Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "Pasta criada: $folder"
    } else {
        Write-Host "Pasta já existe: $folder"
    }
}

Write-Host "Estrutura de pastas criada com sucesso!"
