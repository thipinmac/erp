# =============================================================================
# MóveisERP — Transferência de arquivos para Ubuntu Server via PowerShell
# Usa OpenSSH nativo do Windows 10/11 (scp + ssh)
#
# Uso:
#   .\scripts\Enviar-ParaServidor.ps1
#   .\scripts\Enviar-ParaServidor.ps1 -IP 192.168.1.105 -Usuario ubuntu
# =============================================================================
param(
    [string]$IP       = "192.168.1.105",
    [string]$Usuario  = "ubuntu",
    [string]$Origem   = "D:\Projetos IA\Claude\moveis_erp",
    [string]$Destino  = "/var/www/moveis_erp"
)

# ── Verificações iniciais ──────────────────────────────────────────────────────

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  MóveisERP — Envio para o servidor"  -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Origem : $Origem"
Write-Host "  Destino: $Usuario@${IP}:$Destino"
Write-Host ""

# Verifica se scp existe
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: 'scp' não encontrado." -ForegroundColor Red
    Write-Host "Instale o OpenSSH Client:" -ForegroundColor Yellow
    Write-Host "  Configurações > Apps > Recursos Opcionais > Cliente OpenSSH" -ForegroundColor Yellow
    exit 1
}

# Verifica se a pasta de origem existe
if (-not (Test-Path $Origem)) {
    Write-Host "ERRO: Pasta '$Origem' não encontrada." -ForegroundColor Red
    exit 1
}

# ── Cria cópia temporária limpa (sem arquivos desnecessários) ─────────────────

$TempDir = Join-Path $env:TEMP "moveis_erp_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Write-Host "[1/4] Preparando arquivos (excluindo venv, cache, db)..." -ForegroundColor Yellow

# robocopy copia excluindo pastas/arquivos desnecessários
$ExcluirPastas = @("venv", "__pycache__", ".git", "staticfiles", "node_modules", ".mypy_cache", ".pytest_cache")
$ExcluirArquivos = @("*.pyc", "*.pyo", "db.sqlite3", "*.sqlite3", ".env", "*.log")

$RoboArgs = @(
    $Origem,
    $TempDir,
    "/E",                          # copia subpastas inclusive vazias
    "/NFL", "/NDL", "/NJH", "/NJS" # silencioso
)

# Adiciona exclusões de pastas
foreach ($pasta in $ExcluirPastas) {
    $RoboArgs += "/XD"
    $RoboArgs += $pasta
}

# Adiciona exclusões de arquivos
foreach ($arq in $ExcluirArquivos) {
    $RoboArgs += "/XF"
    $RoboArgs += $arq
}

& robocopy @RoboArgs | Out-Null

# Robocopy retorna 1 quando copia com sucesso (não é erro)
if ($LASTEXITCODE -ge 8) {
    Write-Host "ERRO ao copiar arquivos localmente (código $LASTEXITCODE)." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}

# Conta arquivos copiados
$TotalArquivos = (Get-ChildItem -Recurse $TempDir -File).Count
Write-Host "  OK: $TotalArquivos arquivos preparados em pasta temporária" -ForegroundColor Green

# ── Cria o diretório remoto ────────────────────────────────────────────────────

Write-Host ""
Write-Host "[2/4] Criando diretório remoto no servidor..." -ForegroundColor Yellow
Write-Host "  (pode pedir senha SSH)"

# -t aloca pseudo-terminal para o sudo conseguir pedir senha interativamente
# -o StrictHostKeyChecking=no evita o prompt de confirmação de host na primeira conexão
ssh -t -o StrictHostKeyChecking=no "${Usuario}@${IP}" `
    "sudo mkdir -p $Destino && sudo chown ${Usuario}:${Usuario} $Destino && echo OK_DIR"

if ($LASTEXITCODE -ne 0) {
    Write-Host "" -ForegroundColor Red
    Write-Host "ERRO: Falha ao criar diretório remoto." -ForegroundColor Red
    Write-Host ""
    Write-Host "Solução rápida: no Ubuntu Server execute uma vez:" -ForegroundColor Yellow
    Write-Host "  echo '$Usuario ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/$Usuario" -ForegroundColor White
    Write-Host ""
    Write-Host "Depois rode este script novamente." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "  OK: Diretório $Destino pronto no servidor" -ForegroundColor Green

# ── Transfere os arquivos via SCP ─────────────────────────────────────────────

Write-Host ""
Write-Host "[3/4] Transferindo arquivos via SCP..." -ForegroundColor Yellow
Write-Host "  Isso pode demorar alguns minutos..."

# scp -r copia a pasta toda para dentro do destino remoto
# Para garantir que o CONTEÚDO vá para $Destino (não uma subpasta),
# copiamos para /tmp e depois movemos no servidor
$NomePastaTemp = Split-Path $TempDir -Leaf
Write-Host "  Enviando $TotalArquivos arquivos..."

scp -r -o StrictHostKeyChecking=no "$TempDir" "${Usuario}@${IP}:/tmp/${NomePastaTemp}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha na transferência SCP." -ForegroundColor Red
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    exit 1
}

# Move o conteúdo da pasta temp para o destino correto no servidor
Write-Host "  Movendo arquivos para $Destino..."
ssh -t -o StrictHostKeyChecking=no "${Usuario}@${IP}" `
    "cp -r /tmp/${NomePastaTemp}/. $Destino/ && rm -rf /tmp/${NomePastaTemp} && echo OK_MOVE"

if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: Erro ao mover arquivos no servidor. Verifique manualmente em /tmp/${NomePastaTemp}" -ForegroundColor Yellow
}

Write-Host "  OK: Arquivos transferidos com sucesso" -ForegroundColor Green

# ── Limpeza da pasta temporária ────────────────────────────────────────────────

Write-Host ""
Write-Host "[4/4] Limpando arquivos temporários..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
Write-Host "  OK: Pasta temporária removida" -ForegroundColor Green

# ── Resumo e próximos passos ───────────────────────────────────────────────────

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Transferência concluída!"            -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos no servidor Ubuntu:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Conectar:" -ForegroundColor White
Write-Host "     ssh $Usuario@$IP" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Rodar o deploy:" -ForegroundColor White
Write-Host "     sudo bash $Destino/scripts/deploy.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Criar superusuário:" -ForegroundColor White
Write-Host "     sudo -u erp $Destino/venv/bin/python $Destino/manage.py createsuperuser" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Acessar no navegador:" -ForegroundColor White
Write-Host "     http://$IP/" -ForegroundColor Gray
Write-Host ""

# Pergunta se quer conectar via SSH agora
$Resposta = Read-Host "Conectar ao servidor agora via SSH? (s/n)"
if ($Resposta -eq "s" -or $Resposta -eq "S") {
    Write-Host ""
    Write-Host "Conectando..." -ForegroundColor Cyan
    ssh "${Usuario}@${IP}"
}
