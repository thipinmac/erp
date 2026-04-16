# =============================================================================
# MóveisERP — Envio via ZIP (método alternativo mais robusto)
# Compacta o projeto, envia 1 arquivo zip, extrai no servidor
#
# Uso:
#   .\scripts\Enviar-ZIP.ps1
#   .\scripts\Enviar-ZIP.ps1 -IP 192.168.1.105 -Usuario ubuntu
# =============================================================================
param(
    [string]$IP      = "192.168.1.105",
    [string]$Usuario = "ubuntu",
    [string]$Origem  = "D:\Projetos IA\Claude\moveis_erp",
    [string]$Destino = "/var/www/moveis_erp"
)

$ZipLocal  = "$env:TEMP\moveis_erp_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
$ZipRemoto = "/tmp/moveis_erp_deploy.zip"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  MóveisERP — Envio via ZIP"           -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Servidor: $Usuario@$IP"
Write-Host "  Destino : $Destino"
Write-Host ""

# ── Verificações ──────────────────────────────────────────────────────────────
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: OpenSSH não instalado. Vá em:" -ForegroundColor Red
    Write-Host "  Configurações > Apps > Recursos Opcionais > Cliente OpenSSH" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $Origem)) {
    Write-Host "ERRO: Pasta '$Origem' não encontrada." -ForegroundColor Red
    exit 1
}

# ── Coleta os arquivos a enviar ────────────────────────────────────────────────
Write-Host "[1/4] Coletando arquivos..." -ForegroundColor Yellow

# Pastas e arquivos a IGNORAR
$Ignorar = @(
    "venv", "__pycache__", ".git", "staticfiles", "node_modules",
    ".mypy_cache", ".pytest_cache", "*.pyc", "*.pyo",
    "db.sqlite3", "*.sqlite3", ".env", "*.log", "media"
)

# Coleta todos os arquivos, excluindo os indesejados
$Arquivos = Get-ChildItem -Path $Origem -Recurse -File | Where-Object {
    $caminho = $_.FullName
    $incluir = $true

    foreach ($padrao in $Ignorar) {
        # Verifica se o arquivo ou alguma pasta pai bate com o padrão
        if ($caminho -like "*\$padrao\*" -or $caminho -like "*\$padrao" -or $_.Name -like $padrao) {
            $incluir = $false
            break
        }
    }
    $incluir
}

Write-Host "  $($Arquivos.Count) arquivos selecionados" -ForegroundColor Green

# ── Compacta em ZIP ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Compactando..." -ForegroundColor Yellow

# Remove zip antigo se existir
if (Test-Path $ZipLocal) { Remove-Item $ZipLocal -Force }

# Cria o zip mantendo a estrutura de pastas relativa
$Arquivos | ForEach-Object {
    $relativo = $_.FullName.Substring($Origem.Length).TrimStart('\')
    $_ | Select-Object @{N='FullName'; E={$_.FullName}}, @{N='Relativo'; E={$relativo}}
} | ForEach-Object {
    # Adiciona ao zip com caminho relativo
    [System.IO.Compression.ZipFile]::Open($ZipLocal, 'Update') | ForEach-Object {
        $zip = $_
        $entry = $zip.CreateEntry($_.Relativo.Replace('\', '/'))
        $stream = $entry.Open()
        $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Dispose()
        $zip.Dispose()
    }
}

# Método mais simples e rápido — usa Compress-Archive com lista de arquivos
Remove-Item $ZipLocal -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ZipStream = [System.IO.Compression.ZipFile]::Open($ZipLocal, 'Create')
foreach ($arquivo in $Arquivos) {
    $relativo = $arquivo.FullName.Substring($Origem.Length).TrimStart('\').Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $ZipStream, $arquivo.FullName, $relativo
    ) | Out-Null
}
$ZipStream.Dispose()

$ZipTamanho = [math]::Round((Get-Item $ZipLocal).Length / 1MB, 2)
Write-Host "  ZIP criado: $ZipTamanho MB" -ForegroundColor Green

# ── Envia o ZIP via SCP ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Enviando ZIP para o servidor..." -ForegroundColor Yellow
Write-Host "  (pode pedir senha SSH)"

scp "$ZipLocal" "${Usuario}@${IP}:$ZipRemoto"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha no envio via SCP." -ForegroundColor Red
    Write-Host "Verifique: IP correto? SSH habilitado no Ubuntu? Usuário correto?" -ForegroundColor Yellow
    Remove-Item $ZipLocal -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "  ZIP enviado com sucesso" -ForegroundColor Green

# ── Extrai no servidor ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Extraindo no servidor..." -ForegroundColor Yellow

$ComandoRemoto = @"
sudo mkdir -p $Destino
sudo chown ${Usuario}:${Usuario} $Destino
sudo apt-get install -y -qq unzip
unzip -o $ZipRemoto -d $Destino
rm -f $ZipRemoto
echo "EXTRAIDO_OK"
"@

$Resultado = ssh "${Usuario}@${IP}" $ComandoRemoto

if ($Resultado -match "EXTRAIDO_OK") {
    Write-Host "  Arquivos extraídos em $Destino" -ForegroundColor Green
} else {
    Write-Host "  Aviso: verifique se a extração foi bem-sucedida no servidor" -ForegroundColor Yellow
}

# Limpeza local
Remove-Item $ZipLocal -ErrorAction SilentlyContinue

# ── Resumo ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Pronto! Arquivo enviado e extraído." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Agora no servidor Ubuntu, execute:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ssh $Usuario@$IP" -ForegroundColor White
Write-Host "  sudo bash $Destino/scripts/deploy.sh" -ForegroundColor White
Write-Host ""

$Resposta = Read-Host "Conectar ao servidor agora? (s/n)"
if ($Resposta -match "^[sS]$") {
    ssh "${Usuario}@${IP}"
}
