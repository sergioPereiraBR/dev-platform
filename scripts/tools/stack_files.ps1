# .\scripts\tools\stack_files.ps1 ".\src" "py"
param(
    [Parameter(Mandatory=$true)]
    [string]$TargetPath,
    
    [Parameter(Mandatory=$true)]
    [string]$FileExtension
)

# Verifica se a extensão começa com ponto, caso contrário adiciona
if (-not $FileExtension.StartsWith(".")) {
    $FileExtension = "." + $FileExtension
}

# Converte o caminho para absoluto caso seja o caminho atual (.)
if ($TargetPath -eq ".") {
    $TargetPath = Get-Location
}

# Cria o caminho completo para a pasta stake_file
$StakeFolderPath = Join-Path -Path $TargetPath -ChildPath "stake_file"

# Verifica se a pasta stake_file existe, se não, cria
if (-not (Test-Path -Path $StakeFolderPath -PathType Container)) {
    New-Item -Path $StakeFolderPath -ItemType Directory | Out-Null
    Write-Host "Pasta stake_file criada em: $StakeFolderPath"
}
else {
    Write-Host "Pasta stake_file já existe em: $StakeFolderPath"
}

# Função para obter um nome de arquivo único caso já exista
function Get-UniqueFileName {
    param (
        [string]$FilePath,
        [string]$BaseName,
        [string]$Extension
    )

    $Counter = 1
    $NewFileName = $BaseName + $Extension
    $NewFilePath = Join-Path -Path $FilePath -ChildPath $NewFileName

    # Enquanto o arquivo existir, adiciona um número sequencial ao nome
    while (Test-Path -Path $NewFilePath -PathType Leaf) {
        $NewFileName = "${BaseName}_${Counter}${Extension}"
        $NewFilePath = Join-Path -Path $FilePath -ChildPath $NewFileName
        $Counter++
    }

    return $NewFilePath
}

# Conta quantos arquivos foram copiados
$CopiedFiles = 0

# Primeiro, obter a lista de arquivos existentes na pasta stake_file para comparar por nome
$ExistingFiles = @{}
if (Test-Path -Path $StakeFolderPath) {
    Get-ChildItem -Path $StakeFolderPath -File | ForEach-Object {
        $ExistingFiles[$_.Name] = $true
    }
}

# Obter todos os arquivos recursivamente (exceto os da pasta stake_file)
$FilesToCopy = Get-ChildItem -Path $TargetPath -Recurse -File -Filter "*$FileExtension" | Where-Object {
    -not $_.FullName.StartsWith($StakeFolderPath)
}

# Processar cada arquivo encontrado
foreach ($File in $FilesToCopy) {
    $FileName = $File.Name
    $BaseName = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    
    # Determinar o caminho de destino baseado na existência prévia ou não
    $DestinationFilePath = Join-Path -Path $StakeFolderPath -ChildPath $FileName
    
    # Verifica se já existe um arquivo com este nome (seja da operação atual ou anterior)
    if ($ExistingFiles.ContainsKey($FileName) -or (Test-Path -Path $DestinationFilePath)) {
        # Se existe arquivo com mesmo nome, cria um nome único
        $DestinationFilePath = Get-UniqueFileName -FilePath $StakeFolderPath -BaseName $BaseName -Extension $FileExtension
        # Adiciona o novo nome ao registro de arquivos existentes
        $ExistingFiles[[System.IO.Path]::GetFileName($DestinationFilePath)] = $true
    }
    else {
        # Marca este nome de arquivo como "usado"
        $ExistingFiles[$FileName] = $true
    }
    
    # Copia o arquivo para o destino
    Copy-Item -Path $File.FullName -Destination $DestinationFilePath
    
    # Incrementa o contador e exibe mensagem
    $CopiedFiles++
    Write-Host "Arquivo copiado: $($File.FullName) -> $DestinationFilePath"
}

Write-Host "Processo concluído. Total de $CopiedFiles arquivos copiados para $StakeFolderPath"
