# 🚀 Protheus Webhook Hub

Sistema de integração moderno para o ERP Protheus, permitindo envio de eventos para aplicações externas via webhooks.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Integrações Disponíveis](#integrações-disponíveis)
- [API Reference](#api-reference)
- [Exemplos](#exemplos)
- [Contribuindo](#contribuindo)

## 🎯 Sobre o Projeto

O **Protheus Webhook Hub** é uma solução completa que permite ao ERP Protheus enviar eventos em tempo real para aplicações modernas como Slack, Microsoft Teams, WhatsApp Business, e qualquer webhook customizado.

### Por que usar?

- ✅ **Notificações em tempo real** - Receba alertas instantâneos no Slack/Teams
- ✅ **Integração facilitada** - Conecte o Protheus com 1000+ apps via Zapier/Make
- ✅ **Confiável** - Sistema de fila garante entrega dos eventos
- ✅ **Escalável** - Arquitetura containerizada com Docker
- ✅ **Rastreável** - Logs completos de todos os eventos
- ✅ **Fácil de usar** - Painel web intuitivo

## ⚡ Funcionalidades

### Core
- 📤 **Envio de webhooks** do Protheus para sistemas externos
- 🔄 **Fila de processamento** com Redis para garantir entrega
- 📊 **Dashboard web** para gerenciar integrações
- 📝 **Logs detalhados** de todos os eventos
- 🎯 **Suporte a múltiplos destinos** para o mesmo evento
- 🔒 **Sistema robusto** com retry e tratamento de erros

### Integrações Nativas
- 💬 **Slack** - Mensagens formatadas com blocks
- 👥 **Microsoft Teams** - Cards adaptativos
- 📱 **WhatsApp Business** - Via API oficial
- 🔗 **Webhooks Customizados** - Para qualquer sistema
- ⚡ **Zapier/Make.com** - Conecte com 1000+ apps

## 🏗️ Arquitetura

```
┌─────────────┐
│  Protheus   │
│   (ADVPL)   │
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────────┐
│   API (FastAPI) │ ◄─── Painel Web (Frontend)
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Redis  │ (Fila)
    └────┬───┘
         │
         ▼
    ┌────────┐
    │ Worker │ ────► Slack / Teams / WhatsApp / Custom
    └────────┘
         │
         ▼
   ┌──────────┐
   │PostgreSQL│ (Logs e Configs)
   └──────────┘
```

## 🔧 Pré-requisitos

- Docker e Docker Compose instalados
- Protheus com acesso HTTP (porta 8000)
- (Opcional) Webhook URL do Slack ou Teams

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/ftvernier/protheus-webhook-hub.git
cd protheus-webhook-hub
```

### 2. Inicie os containers

```bash
docker-compose up -d
```

### 3. Verifique se está rodando

```bash
docker-compose ps
```

Você deverá ver 5 containers rodando:
- `webhook-hub-api` (porta 8000)
- `webhook-hub-worker`
- `webhook-hub-frontend` (porta 4200)
- `webhook-hub-redis` (porta 6379)
- `webhook-hub-db` (porta 5432)

### 4. Acesse o painel

Abra no navegador: `http://localhost:4200`

## ⚙️ Configuração

### No Protheus

1. Compile o fonte `advpl/WEBHUBLIB.prw` no seu repositório

2. Configure o parâmetro no Configurador:

```
Parâmetro: MV_WEBHURL
Tipo: Caracter
Conteúdo: http://SEU_IP:8000
```

**Importante:** Substitua `SEU_IP` pelo IP da máquina onde o Docker está rodando.

3. Teste a conexão:

```advpl
U_WHTestConnection()
```

### No Painel Web

1. Acesse `http://localhost:4200`

2. Clique em "Nova Configuração"

3. Preencha:
   - **Nome**: Exemplo: "Notificação Slack - Pedidos"
   - **Tipo de Evento**: `pedido.criado`
   - **Tipo de Destino**: Selecione (Slack, Teams, Custom)
   - **URL de Destino**: Cole a URL do webhook

4. Clique em "Salvar"

## 🎮 Uso

### Enviando Eventos do Protheus

#### Exemplo 1: Pedido Criado

```advpl
User Function MeuPE001()
    Local oData := JsonObject():new()
    
    oData["numero_pedido"] := SC5->C5_NUM
    oData["cliente"] := SC5->C5_CLIENTE
    oData["valor_total"] := SC5->C5_TOTAL
    
    WHSendEvent("pedido.criado", oData)
    
Return
```

#### Exemplo 2: NF-e Emitida

```advpl
User Function AposNFe()
    Local oData := JsonObject():new()
    
    oData["numero_nfe"] := SF2->F2_DOC
    oData["serie"] := SF2->F2_SERIE
    oData["chave_nfe"] := SF2->F2_CHVNFE
    oData["valor"] := SF2->F2_VALBRUT
    
    WHSendEvent("nfe.emitida", oData)
    
Return
```

#### Exemplo 3: Estoque Baixo

```advpl
User Function JOBEST001()
    DbSelectArea("SB2")
    SB2->(DbGoTop())
    
    While !SB2->(Eof())
        If SaldoSB2() < SB1->B1_EMIN
            Local oData := JsonObject():new()
            oData["produto"] := SB2->B2_COD
            oData["saldo"] := SaldoSB2()
            
            WHSendEvent("estoque.baixo", oData)
        EndIf
        
        SB2->(DbSkip())
    End
    
Return
```

### Testando via Painel Web

1. Acesse a aba "Testar Webhook"
2. Informe o tipo de evento
3. Coloque um JSON de teste
4. Clique em "Enviar Teste"

## 🔗 Integrações Disponíveis

### Slack

1. Crie um Incoming Webhook no Slack:
   - Vá em https://api.slack.com/apps
   - Crie um app
   - Ative "Incoming Webhooks"
   - Copie a URL

2. Configure no painel:
   - Tipo de Destino: **Slack**
   - URL: Cole a URL copiada

### Microsoft Teams

1. No seu canal do Teams:
   - Clique nos "..." do canal
   - Connectors → Incoming Webhook
   - Configure e copie a URL

2. Configure no painel:
   - Tipo de Destino: **Teams**
   - URL: Cole a URL copiada

### Webhook Customizado

Para qualquer sistema que aceite POST:

```json
{
  "event_type": "pedido.criado",
  "data": {
    "numero_pedido": "123456",
    "cliente": "000001"
  },
  "source": "protheus",
  "timestamp": "2025-10-27T10:30:00Z"
}
```

## 📚 API Reference

### POST /webhook

Recebe um evento do Protheus

**Request:**
```json
{
  "event_type": "pedido.criado",
  "data": {
    "numero_pedido": "123456"
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "log_id": 1,
  "message": "Evento recebido e enfileirado"
}
```

### GET /configs

Lista todas as configurações

### POST /configs

Cria nova configuração

### GET /logs

Lista logs de eventos

### GET /stats

Retorna estatísticas do sistema

### GET /health

Health check da API

## 💡 Exemplos de Uso

### Notificar Vendas no Slack

```advpl
User Function NotificaVenda()
    Local oData := JsonObject():new()
    
    oData["vendedor"] := SA3->A3_NOME
    oData["cliente"] := SA1->A1_NOME
    oData["valor"] := SC5->C5_TOTAL
    oData["produto"] := SC6->C6_PRODUTO
    
    WHSendEvent("venda.realizada", oData)
Return
```

### Alertas de Inadimplência

```advpl
User Function JobInadimpl()
    // Busca títulos vencidos
    Local oData := JsonObject():new()
    
    oData["cliente"] := SE1->E1_NOMCLI
    oData["titulo"] := SE1->E1_NUM
    oData["vencimento"] := SE1->E1_VENCTO
    oData["valor"] := SE1->E1_VALOR
    oData["dias_atraso"] := Date() - SE1->E1_VENCTO
    
    WHSendEvent("inadimplencia.detectada", oData)
Return
```

### Integração com WhatsApp via Zapier

1. Configure webhook customizado no painel
2. No Zapier:
   - Trigger: Webhook (Catch Hook)
   - Action: WhatsApp (Send Message)
3. Use a URL do Zapier no painel

## 🐳 Docker

### Comandos Úteis

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Ver logs
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f api
docker-compose logs -f worker

# Reiniciar um serviço
docker-compose restart api

# Reconstruir imagens
docker-compose up -d --build
```

### Variáveis de Ambiente

Edite o `docker-compose.yml` para customizar:

```yaml
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - DATABASE_URL=postgresql://user:pass@db:5432/webhook_hub
```

## 🔒 Segurança

- ✅ Use HTTPS em produção
- ✅ Configure firewall para portas específicas
- ✅ Altere senhas padrão do banco
- ✅ Implemente autenticação se necessário
- ✅ Monitore logs de acesso

## 🚀 Produção

Para ambiente de produção:

1. **Use HTTPS**: Configure reverse proxy (nginx/traefik)
2. **Backups**: Configure backup do PostgreSQL
3. **Monitoramento**: Use Prometheus + Grafana
4. **Escalabilidade**: Aumente workers conforme necessidade
5. **Segurança**: Adicione autenticação na API

## 🤝 Contribuindo

Contribuições são bem-vindas!

1. Fork o projeto
2. Crie sua branch: `git checkout -b feature/NovaFuncionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/NovaFuncionalidade`
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Fernando Vernier**

- LinkedIn: [Fernando Vernier](https://www.linkedin.com/in/fernando-v-10758522/)
- GitHub: [@ftvernier](https://github.com/ftvernier)
- Email: fernando.vernier@hotmail.com


## 📞 Suporte

- Abra uma [Issue](https://github.com/ftvernier/protheus-webhook-hub/issues)
- Envie um email: fernando.vernier@hotmail.com

---

⭐ **Se este projeto foi útil, deixe uma estrela no GitHub!**

🚀 **Desenvolvido com ❤️ para a comunidade Protheus**
