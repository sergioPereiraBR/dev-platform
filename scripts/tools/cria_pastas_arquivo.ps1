param($estrutura)

# Função para determinar se um caminho é um arquivo ou pasta
function Test-IsFile {
    param([string]$path)
    
    # Verificar casos explícitos primeiro
    if ($path.EndsWith('\') -or $path.EndsWith('/')) {
        return $false  # É explicitamente uma pasta
    }
    
    # Extrair o nome do arquivo/pasta do caminho
    $itemName = Split-Path -Path $path -Leaf
    
    # Casos comuns de arquivos ocultos no estilo Unix/Linux/Git
    $commonHiddenFiles = @(
        '.gitignore', '.gitattributes', '.env', '.editorconfig', 
        '.htaccess', '.bashrc', '.bash_profile', '.vimrc', 
        '.npmrc', '.dockerignore', '.python-version'
    )
    
    if ($commonHiddenFiles -contains $itemName) {
        return $true  # É um arquivo oculto conhecido
    }
    
    # Verificar se parece um arquivo por ter uma extensão
    # Mas não confundir com uma pasta que começa com ponto (como .git)
    if ($itemName -match "^[^\.]+\.[^\.\\\/]+$") {
        return $true  # Formato normal: nome.extensão
    }
    
    if ($itemName -match "^\..*\.[^\.\\\/]+$") {
        return $true  # Formato .algo.extensão (arquivo oculto com extensão)
    }
    
    # Se não foi identificado como arquivo, assume que é uma pasta
    return $false
}

# Verificar se o arquivo de estrutura existe, se não, criá-lo
if (-not (Test-Path -Path $estrutura)) {
    New-Item -ItemType File -Path $estrutura -Force | Out-Null
    Write-Host "Arquivo de estrutura criado: $estrutura"
} else {
    Write-Host "Arquivo de estrutura já existe: $estrutura"
}

# Ler o conteúdo do arquivo
$paths = Get-Content -Path $estrutura

# Processar cada caminho
foreach ($path in $paths) {
    # Determinar se é arquivo ou pasta
    $isFile = Test-IsFile -path $path
    
    # Obter o diretório pai para criar a estrutura de pastas primeiro
    if ($isFile) {
        $parentDir = Split-Path -Path $path -Parent
        
        # Criar diretórios pai se não existirem
        if (-not [string]::IsNullOrEmpty($parentDir) -and -not (Test-Path -Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            Write-Host "Pasta criada: $parentDir"
        }
        
        # Criar o arquivo
        if (-not (Test-Path -Path $path)) {
            New-Item -ItemType File -Path $path -Force | Out-Null
            Write-Host "Arquivo criado: $path"
        } else {
            Write-Host "Arquivo já existe: $path"
        }
    } else {
        # É uma pasta
        if (-not (Test-Path -Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Host "Pasta criada: $path"
        } else {
            Write-Host "Pasta já existe: $path"
        }
    }
}

Write-Host "Estrutura de pastas e arquivos criada com sucesso!"