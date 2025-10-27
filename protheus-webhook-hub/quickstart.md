# 🚀 Início Rápido - Protheus Webhook Hub

## ⚡ Em 5 Minutos

### 1. Iniciar o Sistema (2 min)

```bash
# Clone o repositório
git clone https://github.com/ftvernier/protheus-webhook-hub.git
cd protheus-webhook-hub

# Inicie os containers
docker-compose up -d

# Aguarde ~30 segundos para tudo iniciar
```

### 2. Verificar se está Online (30 seg)

Abra no navegador:
- **Painel Web**: http://localhost:4200
- **API**: http://localhost:8000

### 3. Configurar Integração Slack (2 min)

**No Slack:**
1. Acesse: https://api.slack.com/apps
2. Clique em "Create New App" → "From scratch"
3. Dê um nome (ex: "Protheus Notifier")
4. Escolha seu workspace
5. No menu lateral: "Incoming Webhooks" → Ative
6. Clique em "Add New Webhook to Workspace"
7. Escolha um canal e autorize
8. **Copie a URL** (ex: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX)

**No Painel Web (localhost:4200):**
1. Clique em "Nova Configuração"
2. Preencha:
   - Nome: `Notificações Protheus`
   - Tipo de Evento: `pedido.criado`
   - Tipo de Destino: `Slack`
   - URL: *cole a URL copiada*
3. Salvar

### 4. Testar (30 seg)

**No Painel Web:**
1. Vá na aba "Testar Webhook"
2. Clique em "Enviar Teste"
3. Verifique se chegou no Slack! 🎉

---

## 🔧 Configurar Protheus

### Passo 1: Compilar o Fonte

1. Copie o arquivo `advpl/WEBHUBLIB.prw` para seu repositório
2. Compile no Protheus

### Passo 2: Configurar Parâmetro

No **Configurador do Protheus**:

```
Código: MV_WEBHURL
Tipo: C (Caracter)
Conteúdo: http://192.168.1.100:8000
```

⚠️ **Importante**: Troque `192.168.1.100` pelo IP da máquina onde o Docker está rodando.

**Como descobrir meu IP:**

Windows:
```cmd
ipconfig
```

Linux/Mac:
```bash
ifconfig
```

### Passo 3: Testar Conexão

No Protheus (Smartclient):

```advpl
U_WHTestConnection()
```

Se aparecer "Conexão bem sucedida" no console, está pronto! ✅

---

## 📤 Primeiro Envio Real

### Exemplo: Notificar quando criar pedido

**Crie um fonte de teste:**

```advpl
#Include "Protheus.ch"

User Function TESTWH01()
    Local oData := JsonObject():new()
    
    // Simula dados de um pedido
    oData["numero_pedido"] := "123456"
    oData["cliente"] := "CLIENTE TESTE LTDA"
    oData["valor_total"] := 1500.00
    oData["vendedor"] := "João Silva"
    
    // Envia o webhook
    If WHSendEvent("pedido.criado", oData)
        MsgInfo("Webhook enviado! Verifique o Slack")
    Else
        MsgStop("Erro ao enviar webhook")
    EndIf
    
Return
```

Execute: `U_TESTWH01()`

Verifique o Slack - deve aparecer uma mensagem! 🎊

---

## 🎯 Próximos Passos

### 1. Adicionar mais eventos

Configure outros tipos de eventos no painel:
- `nfe.emitida`
- `estoque.baixo`
- `inadimplencia.detectada`
- `cliente.cadastrado`

### 2. Integrar com Microsoft Teams

Mesmo processo do Slack:
1. No Teams: Canal → ⋯ → Connectors → Incoming Webhook
2. Configure e copie a URL
3. Adicione no painel como "Teams"

### 3. Integrar nos Pontos de Entrada

Adicione nos seus pontos de entrada existentes:

**Após inclusão de pedido (MTA410I):**
```advpl
User Function MTA410I()
    WHPedidoCriado()
Return
```

**Após emissão de NF-e:**
```advpl
User Function MT100AGR()
    WHNFeEmitida()
Return
```

---

## 🆘 Problemas Comuns

### "Erro ao conectar" no Protheus

**Causa**: Protheus não consegue acessar a API

**Solução**:
1. Verifique se o parâmetro `MV_WEBHURL` está correto
2. Teste ping do servidor Protheus para a máquina com Docker
3. Verifique firewall (porta 8000 deve estar aberta)

### "Webhook não chega no Slack"

**Causa**: URL do Slack incorreta ou configuração não ativa

**Solução**:
1. Verifique se a configuração está "Ativa" no painel
2. Teste a URL do Slack diretamente com curl:
```bash
curl -X POST -H 'Content-Type: application/json' \
-d '{"text":"Teste"}' \
SUA_URL_DO_SLACK
```

### "Containers não sobem"

**Causa**: Portas já em uso

**Solução**:
```bash
# Pare outros serviços ou mude as portas no docker-compose.yml
docker-compose down
docker-compose up -d
```

---

## 📊 Monitoramento

### Ver logs em tempo real:

```bash
# API
docker-compose logs -f api

# Worker (processa os webhooks)
docker-compose logs -f worker

# Todos
docker-compose logs -f
```

### Verificar saúde do sistema:

Abra: http://localhost:8000/health

Deve retornar:
```json
{
  "status": "healthy",
  "redis": "healthy",
  "database": "healthy"
}
```

---

## 🎉 Pronto!

Agora você tem um sistema de webhooks completo rodando!

**O que você consegue fazer:**
- ✅ Receber notificações do Protheus no Slack/Teams
- ✅ Integrar com qualquer sistema via webhooks
- ✅ Monitorar todos os eventos através do painel
- ✅ Escalar conforme necessidade

**Próximos passos sugeridos:**
1. Configure mais integrações
2. Adicione eventos customizados
3. Explore a integração com Zapier/Make.com
4. Implemente em produção com HTTPS

---

## 💬 Precisa de Ajuda?

- 📧 Email: fernando.vernier@hotmail.com
- 💼 LinkedIn: [Fernando Vernier](https://www.linkedin.com/in/fernando-v-10758522/)
- 🐛 Issues: [GitHub Issues](https://github.com/ftvernier/protheus-webhook-hub/issues)

---

**Feito com ❤️ para a comunidade Protheus**
