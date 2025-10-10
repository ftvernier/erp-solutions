# 🚀 Protheus + Kafka: Event-Driven Architecture

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Protheus](https://img.shields.io/badge/Protheus-12.1.33+-green.svg)
![Node.js](https://img.shields.io/badge/Node.js-20+-brightgreen.svg)
![Kafka](https://img.shields.io/badge/Kafka-3.5+-orange.svg)

Solução completa para publicar eventos do **Protheus ERP** no **Apache Kafka**, permitindo arquitetura event-driven e integração moderna com outros sistemas.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Casos de Uso](#-casos-de-uso)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Monitoramento](#-monitoramento)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)

---

## 🎯 Visão Geral

Este projeto resolve o problema de **integração moderna** entre o Protheus ERP e sistemas externos, utilizando **Apache Kafka** como barramento de eventos.

### Por que usar?

- ✅ **Desacoplamento**: Sistemas externos não precisam acessar diretamente o Protheus
- ✅ **Escalabilidade**: Múltiplos consumidores podem processar o mesmo evento
- ✅ **Resiliência**: Eventos são persistidos mesmo se consumidores estiverem offline
- ✅ **Tempo Real**: Integração assíncrona e em tempo real
- ✅ **Auditoria**: Histórico completo de todos os eventos gerados
- ✅ **Modernização**: Ponte entre ERP legado e arquitetura moderna

### O que este projeto faz?

Captura eventos críticos do Protheus (como **Nota Fiscal emitida**) e publica no Kafka para consumo por outros sistemas:

- 📦 Sistemas de logística (WMS/TMS)
- 📊 Plataformas de analytics e BI
- 🛒 Marketplaces e e-commerce
- 📧 Sistemas de notificação
- 🤖 Automações e integrações

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│  PROTHEUS ERP   │
│   (ADVPL/TLPP)  │
│                 │
│  ┌───────────┐  │
│  │ M460FIM   │  │ ← Ponto de Entrada (NF emitida)
│  │ (P.E.)    │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │EventPubli-│  │ ← Classe de publicação
│  │   sher    │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ HTTP POST
         │ (JSON)
         ▼
┌─────────────────┐
│   MIDDLEWARE    │
│    (Node.js)    │ ← API REST + KafkaJS
│                 │
│  ┌───────────┐  │
│  │  Express  │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  KafkaJS  │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ Kafka Protocol
         ▼
┌─────────────────┐
│  KAFKA CLUSTER  │
│                 │
│  Topic:         │
│  protheus.      │
│  invoices.      │
│  issued         │
└────────┬────────┘
         │
         ├──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Consumer│ │Consumer│ │Consumer│ │Consumer│
    │   1    │ │   2    │ │   3    │ │   N    │
    └────────┘ └────────┘ └────────┘ └────────┘
    Logística   Analytics  Marketplace  Email
```

### Componentes

| Componente | Tecnologia | Função |
|------------|-----------|--------|
| **Ponto de Entrada** | ADVPL | Captura evento no Protheus |
| **EventPublisher** | ADVPL | Classe que serializa e envia eventos |
| **Middleware** | Node.js + Express + KafkaJS | Recebe HTTP e publica no Kafka |
| **Kafka** | Apache Kafka | Barramento de eventos |
| **Zookeeper** | Apache Zookeeper | Coordenação do cluster Kafka |
| **Kafka UI** | Provectus Kafka UI | Interface web para monitoramento |
| **Consumer Example** | Node.js + KafkaJS | Exemplo de consumidor |

---

## 💡 Casos de Uso

### 1. Nota Fiscal Emitida → Expedição Automática
Quando uma NF é faturada no Protheus, o evento é publicado e consumido pelo sistema de WMS que automaticamente:
- Separa os produtos
- Imprime etiquetas
- Notifica transportadora

### 2. Nota Fiscal Emitida → Analytics em Tempo Real
Dashboard atualizado em tempo real com:
- Faturamento do dia
- Performance por vendedor
- Análise de produtos mais vendidos

### 3. Nota Fiscal Emitida → Marketplace
Integração automática com marketplaces:
- Atualiza status do pedido
- Envia código de rastreio
- Notifica cliente

### 4. Multi-Sistema
Um único evento pode ser consumido por **vários sistemas simultaneamente**, cada um fazendo seu processamento específico.

---

## 📦 Pré-requisitos

### Protheus
- ✅ Protheus 12.1.33 ou superior
- ✅ REST habilitado
- ✅ Acesso para compilar fontes ADVPL

### Infraestrutura
- ✅ Docker e Docker Compose instalados
- ✅ Mínimo 4GB RAM disponível
- ✅ Portas disponíveis: 2181, 9092, 8080, 3000

### Conhecimentos
- 📚 ADVPL/TLPP básico
- 📚 Docker básico
- 📚 Conceitos de API REST

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/protheus-kafka-events.git
cd protheus-kafka-events
```

### 2. Suba o ambiente Kafka + Middleware

```bash
docker-compose up -d
```

Isso irá subir:
- ✅ Zookeeper (porta 2181)
- ✅ Kafka (porta 9092)
- ✅ Kafka UI (porta 8080)
- ✅ Middleware (porta 3000)
- ✅ Consumer Example

### 3. Verifique se está funcionando

```bash
# Health check do middleware
curl http://localhost:3000/health

# Acesse a interface do Kafka
open http://localhost:8080
```

### 4. Compile os fontes ADVPL no Protheus

Compile os seguintes arquivos:

```
advpl/classes/EventPublisher.prw
advpl/examples/M460FIM.prw
```

### 5. Configure os parâmetros

Crie os parâmetros no Protheus (SX6):

| Parâmetro | Tipo | Valor |
|-----------|------|-------|
| `MV_KFKURL` | C | `http://localhost:3000/events` |
| `MV_KFKENAB` | L | `.T.` |
| `MV_KFKTOUT` | N | `30` |

📖 [Veja instruções detalhadas de configuração](docs/PARAMETROS.md)

---

## ⚙️ Configuração

### Ajustando a URL do Middleware

Se o middleware não estiver rodando em `localhost`, ajuste o parâmetro:

```advpl
// No Configurador ou via código
PutMV("MV_KFKURL", "http://192.168.1.100:3000/events")
```

### Desabilitando temporariamente

```advpl
PutMV("MV_KFKENAB", .F.)
```

### Ambientes diferentes (Desenvolvimento, Homologação, Produção)

Crie parâmetros específicos por ambiente ou use includes condicionais:

```advpl
#IFDEF PRODUCTION
    ::cUrl := "http://kafka-prod.empresa.com:3000/events"
#ELSE
    ::cUrl := "http://kafka-dev.empresa.com:3000/events"
#ENDIF
```

---

## 🎮 Como Usar

### 1. Fature uma Nota Fiscal normalmente no Protheus

```
MATA460 → Faturamento → Gerar NF
```

### 2. O Ponto de Entrada M460FIM será executado automaticamente

```advpl
User Function M460FIM()
    // Coleta dados da NF
    // Publica no Kafka via middleware
    // Continua o processo normalmente
Return
```

### 3. Verifique os logs

**Console do Protheus:**
```
[EventPublisher] Evento publicado com sucesso - ID: 20251010-143025-123456
[M460FIM] Evento de NF publicado - 000123456/1
```

**Consumer Example (Docker logs):**
```bash
docker logs -f protheus-consumer-example
```

Você verá algo como:

```
================================================================================
📨 NOVO EVENTO RECEBIDO
================================================================================
🏷️  Tópico: protheus.invoices.issued
🔑 Event ID: 20251010-143025-123456
📋 Tipo: invoice_issued
⏰ Timestamp: 2025-10-10T14:30:25Z
🔗 Source: protheus_erp
--------------------------------------------------------------------------------

🧾 NOTA FISCAL EMITIDA
   Número: 000123456 | Série: 1
   Filial: 01
   Emissão: 10/10/2025

👤 CLIENTE
   000001/01 - Cliente Exemplo LTDA
   CNPJ: 12.345.678/0001-90
   São Paulo/SP

💰 VALORES
   Total Produtos: R$ 1500.00
   Total NF: R$ 1695.00
   ICMS: R$ 180.00
   IPI: R$ 15.00

📦 ITENS (1)
   1. PROD001 - Produto Exemplo
      Qtd: 10 | Unit: R$ 150.00 | Total: R$ 1500.00

✅ Evento processado com sucesso!
================================================================================
```

### 4. Visualize no Kafka UI

Acesse: http://localhost:8080

- Veja o tópico `protheus.invoices.issued`
- Inspecione as mensagens
- Monitore consumers

---

## 📊 Monitoramento

### Health Check do Middleware

```bash
curl http://localhost:3000/health
```

Resposta:
```json
{
  "status": "online",
  "kafka": "connected",
  "timestamp": "2025-10-10T14:30:00.000Z"
}
```

### Listar Tópicos

```bash
curl http://localhost:3000/topics
```

### Kafka UI

Interface completa em: http://localhost:8080

- 📊 Métricas de tópicos
- 📝 Mensagens em tempo real
- 👥 Consumers ativos
- ⚡ Performance do cluster

### Logs

```bash
# Middleware
docker logs -f protheus-middleware

# Consumer
docker logs -f protheus-consumer-example

# Kafka
docker logs -f protheus-kafka
```

---

## 🔧 Troubleshooting

### Erro: "Kafka não disponível"

```bash
# Verifique se o Kafka está rodando
docker ps | grep kafka

# Reinicie o Kafka
docker-compose restart kafka

# Aguarde uns 30 segundos para o Kafka inicializar completamente
```

### Erro: "URL do middleware não configurada"

Verifique se o parâmetro `MV_KFKURL` existe e está preenchido:

```advpl
ConOut(SuperGetMV("MV_KFKURL", .F., "VAZIO"))
```

### Eventos não aparecem no Kafka UI

1. ✅ Verifique se `MV_KFKENAB` está `.T.`
2. ✅ Veja os logs do console do Protheus
3. ✅ Teste o health do middleware
4. ✅ Verifique conectividade de rede

### Middleware não conecta no Kafka

```bash
# Entre no container do middleware
docker exec -it protheus-middleware sh

# Teste conectividade com o Kafka
ping kafka
nc -zv kafka 9092
```

---

## 🗺️ Roadmap

### Próximos Eventos

- [ ] Pedido de Venda criado (SC5)
- [ ] Produto cadastrado/alterado (SB1)
- [ ] Título a receber gerado (SE1)
- [ ] Movimento de estoque (SD3)
- [ ] Cliente cadastrado (SA1)

### Melhorias

- [ ] Dead Letter Queue (DLQ) para erros
- [ ] Retry automático com backoff exponencial
- [ ] Schema Registry (Avro/Protobuf)
- [ ] Autenticação SASL/SSL no Kafka
- [ ] Métricas com Prometheus
- [ ] Dashboard Grafana
- [ ] Testes unitários ADVPL
- [ ] CI/CD Pipeline

---

## 🤝 Contribuindo

Contribuições são bem-vindas! 

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/NovoEvento`)
3. Commit suas mudanças (`git commit -m 'Add: Novo evento de pedido'`)
4. Push para a branch (`git push origin feature/NovoEvento`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Seu Nome**

- LinkedIn: [[Seu LinkedIn](https://www.linkedin.com/in/fernando-v-10758522/)](#)
- GitHub: [@ftvernier](#)
- Email: fernando.vernier@hotmail.com

---

## ⭐ Mostre seu apoio

Se este projeto te ajudou, deixe uma ⭐!

---

## 📚 Referências

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [KafkaJS Documentation](https://kafka.js.org/)
- [Protheus TDN](https://tdn.totvs.com/)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
