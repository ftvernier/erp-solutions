# 📁 Estrutura do Projeto

```
protheus-webhook-hub/
│
├── 📄 README.md                    # Documentação principal
├── 📄 QUICKSTART.md                # Guia de início rápido
├── 📄 LICENSE                      # Licença MIT
├── 📄 .env.example                 # Exemplo de variáveis de ambiente
├── 🔧 install.sh                   # Script de instalação automática
├── 🐳 docker-compose.yml           # Orquestração dos containers
│
├── 📂 api/                         # Backend (FastAPI)
│   ├── Dockerfile                  # Container da API
│   ├── requirements.txt            # Dependências Python
│   ├── main.py                     # API principal (FastAPI)
│   └── worker.py                   # Worker que processa webhooks
│
├── 📂 frontend/                    # Frontend (HTML/CSS/JS)
│   ├── Dockerfile                  # Container do frontend
│   ├── index.html                  # Painel de controle
│   ├── style.css                   # Estilos do painel
│   └── app.js                      # JavaScript do painel
│
├── 📂 advpl/                       # Integração Protheus
│   └── WEBHUBLIB.prw               # Biblioteca ADVPL completa
│
└── 📂 docs/                        # Documentação adicional
    ├── EXAMPLES.md                 # Exemplos práticos de uso
    └── PRODUCTION.md               # Guia de deploy em produção
```

## 🎯 Componentes Principais

### Backend (API)
- **FastAPI**: Framework web moderno e rápido
- **PostgreSQL**: Banco de dados para logs e configurações
- **Redis**: Fila de mensagens para processamento assíncrono
- **Worker**: Processa eventos e envia webhooks

### Frontend
- **HTML5/CSS3/JavaScript**: Interface web responsiva
- **Nginx**: Servidor web estático

### Integração Protheus
- **ADVPL**: Biblioteca completa para envio de eventos
- **Funções prontas**: Pedidos, NF-e, Estoque, Clientes

### Infraestrutura
- **Docker**: Containerização de todos os serviços
- **Docker Compose**: Orquestração facilitada

## 📊 Fluxo de Dados

```
┌─────────────────┐
│   Protheus      │
│   (ADVPL)       │
└────────┬────────┘
         │
         │ HTTP POST /webhook
         ▼
┌─────────────────┐
│  API (FastAPI)  │ ◄──── Frontend (Configurações)
│  Port 8000      │
└────────┬────────┘
         │
         │ Enfileira evento
         ▼
┌─────────────────┐
│  Redis (Queue)  │
│  Port 6379      │
└────────┬────────┘
         │
         │ Consome fila
         ▼
┌─────────────────┐
│  Worker         │
│  (Python)       │
└────────┬────────┘
         │
         │ Envia para destinos
         ▼
┌─────────────────────────────────┐
│  Slack / Teams / WhatsApp /     │
│  Custom Webhooks / Zapier       │
└─────────────────────────────────┘
         │
         │ Salva resultado
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  (Logs & Configs)│
│  Port 5432      │
└─────────────────┘
```

## 🔌 Portas Utilizadas

| Serviço    | Porta | Descrição                    |
|------------|-------|------------------------------|
| API        | 8000  | API REST (FastAPI)           |
| Frontend   | 4200  | Painel Web                   |
| PostgreSQL | 5432  | Banco de dados               |
| Redis      | 6379  | Fila de mensagens            |

## 📦 Containers Docker

1. **webhook-hub-api**: API REST principal
2. **webhook-hub-worker**: Processa eventos da fila
3. **webhook-hub-frontend**: Interface web
4. **webhook-hub-db**: PostgreSQL
5. **webhook-hub-redis**: Redis

## 🚀 Como Funciona

1. **Protheus envia evento** via HTTP POST para a API
2. **API valida e armazena** no banco de dados
3. **Evento é enfileirado** no Redis
4. **Worker processa** a fila
5. **Worker busca configurações** ativas para aquele tipo de evento
6. **Worker envia** para todos os destinos configurados
7. **Resultado é registrado** nos logs

## 📝 Arquivos de Configuração

- `.env`: Variáveis de ambiente (senhas, URLs, etc)
- `docker-compose.yml`: Define todos os serviços
- Painel Web: Configurações de webhooks via interface

## 🎨 Customização

### Adicionar novo tipo de destino

1. Edite `api/worker.py`
2. Adicione função `format_TIPO_message()`
3. Atualize `send_webhook()` para incluir novo tipo

### Adicionar novos eventos

1. No Protheus: Use `WHSendEvent("novo.evento", oData)`
2. No Painel: Configure destino para "novo.evento"
3. Pronto! Não precisa alterar código

### Personalizar Frontend

1. Edite `frontend/index.html`, `style.css`, `app.js`
2. Rebuild container: `docker-compose up -d --build frontend`

## 📚 Documentação Completa

- **README.md**: Visão geral e instalação
- **QUICKSTART.md**: Começar em 5 minutos
- **EXAMPLES.md**: Casos de uso práticos
- **PRODUCTION.md**: Deploy em produção
- **WEBHUBLIB.prw**: Documentação inline do código ADVPL

## 🔐 Segurança

- Senhas em variáveis de ambiente
- Portas internas não expostas
- HTTPS recomendado em produção
- Validação de dados na API
- Logs completos de auditoria

## 🎯 Tecnologias Utilizadas

| Camada      | Tecnologia           | Versão  |
|-------------|---------------------|---------|
| Backend     | Python              | 3.11    |
| Framework   | FastAPI             | 0.104   |
| Database    | PostgreSQL          | 15      |
| Cache/Queue | Redis               | 7       |
| Frontend    | HTML5/CSS3/JS       | -       |
| Server      | Nginx               | Alpine  |
| ERP         | Protheus            | 12.1.33+|
| Language    | ADVPL               | -       |
| Container   | Docker              | 20+     |
| Orchestration| Docker Compose     | 2.0+    |

---

**Desenvolvido com ❤️ por [Fernando Vernier](https://github.com/ftvernier)**
