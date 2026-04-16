#!/bin/bash
# =============================================================================
# MóveisERP — Verifica se o servidor está pronto para o deploy
# Uso: bash check_server.sh
# =============================================================================

OK=0
FAIL=0

check() {
    local DESC="$1"
    local CMD="$2"
    if eval "$CMD" &>/dev/null; then
        echo "  ✓ $DESC"
        OK=$((OK+1))
    else
        echo "  ✗ $DESC"
        FAIL=$((FAIL+1))
    fi
}

echo ""
echo "=============================="
echo " Verificação pré-deploy"
echo "=============================="
echo ""

echo "Sistema:"
check "Ubuntu 22.04+" "lsb_release -d | grep -i ubuntu"
check "Acesso à internet" "curl -s --max-time 5 https://pypi.org > /dev/null"
check "Python 3.10+" "python3 --version | grep -E '3\.(10|11|12|13)'"

echo ""
echo "Portas livres:"
check "Porta 80 livre" "! ss -tlnp | grep ':80 '"
check "Porta 5432 livre ou PostgreSQL rodando" "ss -tlnp | grep ':5432' || ! dpkg -l postgresql* 2>/dev/null | grep ii"

echo ""
echo "Permissões:"
check "Rodando como root/sudo" "[ $(id -u) -eq 0 ]"
check "/var/www/ acessível" "[ -d /var/www ] || mkdir -p /var/www"

echo ""
echo "Informações do servidor:"
echo "  IP local:    $(hostname -I | awk '{print $1}')"
echo "  Hostname:    $(hostname)"
echo "  OS:          $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  RAM:         $(free -h | grep Mem | awk '{print $2}') total, $(free -h | grep Mem | awk '{print $7}') disponível"
echo "  Disco /var:  $(df -h /var | tail -1 | awk '{print $4}') livre"

echo ""
if [ $FAIL -eq 0 ]; then
    echo "✅ Tudo OK! Execute: sudo bash deploy.sh"
else
    echo "⚠  $FAIL verificação(ões) falharam. Revise antes de prosseguir."
fi
echo ""
