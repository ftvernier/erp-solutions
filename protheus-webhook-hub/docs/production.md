# 🚀 Deploy em Produção - Protheus Webhook Hub

## 📋 Checklist Pré-Deploy

- [ ] Servidor Linux configurado (Ubuntu/Debian recomendado)
- [ ] Docker e Docker Compose instalados
- [ ] Domínio configurado (ex: webhooks.suaempresa.com.br)
- [ ] Certificado SSL/TLS válido
- [ ] Firewall configurado
- [ ] Backup strategy definida

---

## 🔒 Configuração de Segurança

### 1. Alterar Senhas Padrão

Edite o arquivo `.env`:

```bash
# NÃO USE AS SENHAS PADRÃO EM PRODUÇÃO!
POSTGRES_USER=webhook_prod_user
POSTGRES_PASSWORD=SuaSenhaSuperSegura123!@#
POSTGRES_DB=webhook_hub_prod
DATABASE_URL=postgresql://webhook_prod_user:SuaSenhaSuperSegura123!@#@db:5432/webhook_hub_prod

# Secret key para JWT (gere uma nova)
SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Configurar Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Certifique-se que portas internas NÃO estejam expostas
# 5432 (PostgreSQL), 6379 (Redis), 8000 (API) devem estar bloqueadas externamente
```

---

## 🌐 Configuração de HTTPS com Nginx

### 1. Instalar Nginx

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### 2. Configurar Reverse Proxy

Crie `/etc/nginx/sites-available/webhook-hub`:

```nginx
# API Backend
server {
    listen 80;
    server_name api.webhooks.suaempresa.com.br;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}

# Frontend
server {
    listen 80;
    server_name webhooks.suaempresa.com.br;
    
    location / {
        proxy_pass http://localhost:4200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Ativar e Configurar SSL

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/webhook-hub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obter certificado SSL (Let's Encrypt)
sudo certbot --nginx -d webhooks.suaempresa.com.br
sudo certbot --nginx -d api.webhooks.suaempresa.com.br
```

---

## 🐳 Deploy com Docker

### 1. Clonar Repositório

```bash
cd /opt
sudo git clone https://github.com/SEU_USUARIO/protheus-webhook-hub.git
cd protheus-webhook-hub
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar e editar .env
cp .env.example .env
nano .env
```

### 3. Ajustar docker-compose para Produção

Crie `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build: ./api
    container_name: webhook-hub-api-prod
    restart: always
    ports:
      - "127.0.0.1:8000:8000"  # Apenas localhost
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - db
    volumes:
      - ./api:/app
    networks:
      - webhook-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  worker:
    build: ./api
    container_name: webhook-hub-worker-prod
    restart: always
    command: python worker.py
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - db
    volumes:
      - ./api:/app
    networks:
      - webhook-network
    deploy:
      replicas: 3  # 3 workers para alta disponibilidade
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: webhook-hub-redis-prod
    restart: always
    ports:
      - "127.0.0.1:6379:6379"  # Apenas localhost
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    networks:
      - webhook-network

  db:
    image: postgres:15-alpine
    container_name: webhook-hub-db-prod
    restart: always
    ports:
      - "127.0.0.1:5432:5432"  # Apenas localhost
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups  # Para backups
    networks:
      - webhook-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  frontend:
    build: ./frontend
    container_name: webhook-hub-frontend-prod
    restart: always
    ports:
      - "127.0.0.1:4200:80"  # Apenas localhost
    depends_on:
      - api
    networks:
      - webhook-network

volumes:
  redis-data:
  postgres-data:

networks:
  webhook-network:
    driver: bridge
```

### 4. Iniciar em Produção

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 💾 Backup Automático

### Script de Backup PostgreSQL

Crie `/opt/webhook-hub-backup.sh`:

```bash
#!/bin/bash

# Configurações
BACKUP_DIR="/opt/protheus-webhook-hub/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="webhook-hub-db-prod"
DB_NAME="webhook_hub_prod"

# Criar diretório se não existir
mkdir -p $BACKUP_DIR

# Fazer backup
docker exec $CONTAINER_NAME pg_dump -U webhook_prod_user $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup realizado: backup_$DATE.sql.gz"
```

### Agendar Backup Diário

```bash
# Tornar executável
chmod +x /opt/webhook-hub-backup.sh

# Adicionar ao crontab (todo dia às 2h da manhã)
crontab -e

# Adicione:
0 2 * * * /opt/webhook-hub-backup.sh >> /var/log/webhook-backup.log 2>&1
```

---

## 📊 Monitoramento

### 1. Configurar Logs

```bash
# Rotação de logs do Docker
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

### 2. Healthcheck Script

Crie `/opt/webhook-healthcheck.sh`:

```bash
#!/bin/bash

# Verifica se a API está respondendo
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "$(date): API OK"
else
    echo "$(date): API DOWN - Reiniciando..."
    cd /opt/protheus-webhook-hub
    docker-compose -f docker-compose.prod.yml restart api worker
fi
```

Agende a cada 5 minutos:
```bash
*/5 * * * * /opt/webhook-healthcheck.sh >> /var/log/webhook-health.log 2>&1
```

### 3. Alertas via Telegram (Opcional)

```bash
#!/bin/bash
TOKEN="SEU_BOT_TOKEN"
CHAT_ID="SEU_CHAT_ID"

send_telegram() {
    MESSAGE=$1
    curl -s -X POST https://api.telegram.org/bot$TOKEN/sendMessage \
         -d chat_id=$CHAT_ID \
         -d text="$MESSAGE"
}

# No healthcheck, adicione:
send_telegram "⚠️ Webhook Hub API está fora do ar!"
```

---

## 🔄 Atualização em Produção

### Processo de Atualização

```bash
cd /opt/protheus-webhook-hub

# 1. Backup antes da atualização
./webhook-hub-backup.sh

# 2. Baixar nova versão
git pull origin main

# 3. Rebuild com zero downtime
docker-compose -f docker-compose.prod.yml build

# 4. Atualizar serviços um por um
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api
sleep 10
docker-compose -f docker-compose.prod.yml up -d --no-deps --build worker
docker-compose -f docker-compose.prod.yml up -d --no-deps --build frontend

# 5. Verificar logs
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

---

## 📈 Performance e Escalabilidade

### 1. Aumentar Workers

No `docker-compose.prod.yml`:

```yaml
worker:
  deploy:
    replicas: 5  # Aumentar conforme carga
```

### 2. Otimizar PostgreSQL

Edite as configurações do container:

```yaml
db:
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=512MB"
    - "-c"
    - "effective_cache_size=2GB"
```

### 3. Cache Redis

O Redis já está configurado com persistência. Monitore:

```bash
docker exec webhook-hub-redis-prod redis-cli INFO stats
```

---

## 🚨 Troubleshooting Produção

### API não responde

```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs api

# Reiniciar
docker-compose -f docker-compose.prod.yml restart api
```

### Workers travados

```bash
# Ver quantos jobs na fila
docker exec webhook-hub-redis-prod redis-cli LLEN webhook_queue

# Limpar fila (CUIDADO!)
docker exec webhook-hub-redis-prod redis-cli DEL webhook_queue

# Reiniciar workers
docker-compose -f docker-compose.prod.yml restart worker
```

### Banco de dados corrompido

```bash
# Restaurar do backup
gunzip < /opt/protheus-webhook-hub/backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
docker exec -i webhook-hub-db-prod psql -U webhook_prod_user webhook_hub_prod
```

---

## 📞 Suporte

Em caso de problemas em produção:

1. Verifique logs: `docker-compose logs -f`
2. Execute healthcheck: `/opt/webhook-healthcheck.sh`
3. Consulte documentação: [GitHub](https://github.com/ftvernier/protheus-webhook-hub)
4. Contato: fernando.vernier@hotmail.com

---

## ✅ Checklist Pós-Deploy

- [ ] SSL configurado e funcionando
- [ ] Backups automáticos rodando
- [ ] Healthcheck configurado
- [ ] Monitoramento ativo
- [ ] Firewall configurado corretamente
- [ ] Logs sendo rotacionados
- [ ] Documentação atualizada com URLs de produção
- [ ] Equipe treinada
- [ ] Plano de rollback testado

---

**🎉 Parabéns! Seu Protheus Webhook Hub está em produção!**

Desenvolvido por [Fernando Vernier](https://github.com/ftvernier)
