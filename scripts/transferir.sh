#!/bin/bash
# =============================================================================
# MóveisERP — Transfere o projeto do Windows para o Ubuntu Server
# Execute este script NO WINDOWS (Git Bash, WSL, ou PowerShell com scp)
#
# Uso:
#   bash scripts/transferir.sh IP_DO_SERVIDOR USUARIO_SSH
# Exemplo:
#   bash scripts/transferir.sh 192.168.1.100 ubuntu
# =============================================================================

SERVER_IP="${1:-192.168.1.100}"
SSH_USER="${2:-ubuntu}"
REMOTE_DIR="/var/www/moveis_erp"

echo "Transferindo projeto para $SSH_USER@$SERVER_IP:$REMOTE_DIR"
echo ""

# Cria o diretório remoto
ssh "$SSH_USER@$SERVER_IP" "sudo mkdir -p $REMOTE_DIR && sudo chown $SSH_USER:$SSH_USER $REMOTE_DIR"

# Transfere excluindo arquivos desnecessários
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    --exclude='staticfiles' \
    --exclude='media' \
    --exclude='db.sqlite3' \
    --exclude='*.sqlite3' \
    --exclude='.DS_Store' \
    ./ "$SSH_USER@$SERVER_IP:$REMOTE_DIR/"

echo ""
echo "✅ Transferência concluída!"
echo ""
echo "Próximo passo — no servidor:"
echo "  ssh $SSH_USER@$SERVER_IP"
echo "  sudo bash $REMOTE_DIR/scripts/deploy.sh"
