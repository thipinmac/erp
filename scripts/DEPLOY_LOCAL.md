# Deploy Local — Ubuntu Server no HyperV

## Pré-requisitos
- Ubuntu Server 22.04 ou 24.04 rodando no HyperV
- SSH habilitado no Ubuntu (`sudo systemctl enable ssh --now`)
- Saber o IP da VM: `ip a` no terminal do Ubuntu

---

## Passo 1 — Descobrir o IP do servidor Ubuntu

No terminal do Ubuntu Server:
```bash
ip a | grep "inet " | grep -v 127
# Anote o IP, ex: 192.168.1.105
```

---

## Passo 2 — Transferir o projeto (do Windows para o Ubuntu)

No **Git Bash** ou **PowerShell** dentro da pasta do projeto:

```bash
# Opção A: usando o script (precisa de rsync — funciona no Git Bash)
bash scripts/transferir.sh 192.168.1.105 ubuntu

# Opção B: usando scp (PowerShell ou CMD)
scp -r . ubuntu@192.168.1.105:/var/www/moveis_erp
```

> **Nota:** Se não tiver rsync no Windows, use o `scp` da opção B.
> O `.env` e o `db.sqlite3` NÃO são transferidos (correto — o servidor terá o seu próprio .env).

---

## Passo 3 — Rodar o deploy no servidor

```bash
# Conecta no servidor
ssh ubuntu@192.168.1.105

# Roda o deploy completo
sudo bash /var/www/moveis_erp/scripts/deploy.sh
```

O script faz automaticamente:
- Instala Python, PostgreSQL, Redis, Nginx
- Cria banco de dados e usuário PostgreSQL
- Cria o virtualenv e instala dependências
- Gera um `.env` com SECRET_KEY aleatória
- Roda `migrate` e `collectstatic`
- Cria e inicia os serviços systemd (Gunicorn, Celery, CeleryBeat)
- Configura o Nginx

---

## Passo 4 — Criar o superusuário Django

```bash
# Ainda no servidor:
sudo -u erp /var/www/moveis_erp/venv/bin/python /var/www/moveis_erp/manage.py createsuperuser
```

---

## Passo 5 — Acessar o sistema

Abra no navegador do seu PC Windows:
```
http://192.168.1.105/
```

Login em:
```
http://192.168.1.105/entrar/
```

Admin Django:
```
http://192.168.1.105/admin/
```

---

## Comandos úteis no servidor

```bash
# Ver logs ao vivo
journalctl -u gunicorn_erp -f

# Ver erros do Gunicorn
tail -f /var/www/moveis_erp/logs/gunicorn_error.log

# Status de todos os serviços
make -C /var/www/moveis_erp status

# Reiniciar tudo
make -C /var/www/moveis_erp restart

# Após copiar código novo
sudo bash /var/www/moveis_erp/scripts/update.sh
```

---

## Solução de problemas

### "502 Bad Gateway"
```bash
systemctl status gunicorn_erp
journalctl -u gunicorn_erp -n 50
```

### "Static files não aparecem (CSS quebrado)"
```bash
sudo -u erp /var/www/moveis_erp/venv/bin/python \
    /var/www/moveis_erp/manage.py collectstatic --noinput
sudo systemctl reload nginx
```

### "Erro de banco de dados"
```bash
systemctl status postgresql
sudo -u postgres psql -c "\l"  # lista bancos
```

### "Celery não processa tarefas"
```bash
systemctl status celery_erp
journalctl -u celery_erp -n 50
```

---

## Estrutura dos serviços instalados

| Serviço           | Porta/Socket              | Descrição                  |
|-------------------|---------------------------|----------------------------|
| Nginx             | :80                       | Proxy reverso              |
| Gunicorn          | unix:/run/gunicorn_erp/gunicorn.sock | App Django        |
| PostgreSQL        | :5432 (local)             | Banco de dados             |
| Redis             | :6379 (local)             | Cache / Broker Celery      |
| Celery Worker     | —                         | Tarefas assíncronas        |
| Celery Beat       | —                         | Agendamento de tarefas     |
