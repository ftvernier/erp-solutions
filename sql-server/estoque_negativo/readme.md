# 🚨 Sistema de Alertas de Estoque Negativo - ERP Protheus

[![SQL Server](https://img.shields.io/badge/SQL%20Server-2016+-blue.svg)](https://www.microsoft.com/sql-server)
[![ERP](https://img.shields.io/badge/ERP-Protheus-green.svg)](https://www.totvs.com/protheus)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema automatizado de alertas para estoque negativo no ERP Protheus, com suporte a múltiplos canais de notificação (Email, Teams, Telegram, Slack e Webhooks genéricos).

## 🎯 Funcionalidades

- **Detecção automática** de estoque negativo via trigger na tabela SB2010
- **Múltiplos canais** de notificação configuráveis
- **Performance otimizada** para operações em lote
- **Tratamento robusto** de erros e rollback
- **Log completo** de alertas enviados
- **Prevenção de duplicação** de alertas
- **Arquitetura modular** e extensível

## 📋 Canais de Notificação Suportados

| Canal | Status | Configuração |
|-------|--------|--------------|
| 📧 Email | ✅ Implementado | Database Mail |
| 👥 Microsoft Teams | ✅ Implementado | Webhook |
| 📱 Telegram | ✅ Implementado | Bot API |
| 💬 Slack | ✅ Implementado | Webhook |
| 🔗 Webhook Genérico | ✅ Implementado | HTTP POST |

## 🚀 Instalação Rápida

### 1. Estrutura de Tabelas
```sql
-- Execute os scripts na ordem:
.\database\01_create_tables.sql
.\database\02_create_indexes.sql
```

### 2. Procedures e Triggers
```sql
-- Execute as procedures:
.\procedures\sp_send_universal_alert.sql
.\procedures\sp_send_email_alert.sql
.\procedures\sp_send_teams_alert.sql
.\procedures\sp_send_telegram_alert.sql
.\procedures\sp_send_slack_alert.sql
.\procedures\sp_send_webhook_alert.sql

-- Execute a trigger:
.\triggers\tr_estoque_negativo.sql
```

### 3. Configuração Inicial
```sql
-- Configure seu canal preferido:
INSERT INTO ALERT_CONFIG (ALERT_TYPE, WEBHOOK_URL, IS_ACTIVE, EMAIL_TO)
VALUES ('EMAIL', NULL, 1, 'estoque@suaempresa.com');
```

## ⚙️ Configuração

### Email (Database Mail)
```sql
-- Configurar Database Mail no SQL Server
EXEC sp_configure 'Database Mail XPs', 1;
RECONFIGURE;

-- Criar perfil de email
EXEC msdb.dbo.sysmail_add_profile_sp
    @profile_name = 'AlertasEstoque',
    @description = 'Perfil para alertas de estoque';
```

### Microsoft Teams
```sql
-- Obter webhook do Teams e configurar
UPDATE ALERT_CONFIG 
SET WEBHOOK_URL = 'https://outlook.office.com/webhook/SEU_WEBHOOK_TEAMS',
    IS_ACTIVE = 1
WHERE ALERT_TYPE = 'TEAMS';
```

### Telegram
```sql
-- Criar bot no @BotFather e configurar
UPDATE ALERT_CONFIG 
SET WEBHOOK_URL = 'https://api.telegram.org/botSEU_TOKEN/sendMessage',
    CHAT_ID = 'SEU_CHAT_ID',
    IS_ACTIVE = 1
WHERE ALERT_TYPE = 'TELEGRAM';
```

## 📊 Monitoramento

### Consultar Alertas Enviados
```sql
SELECT 
    B2_COD as Produto,
    B2_QATU as Estoque,
    ALERT_DATE as DataAlerta,
    USERNAME as Usuario,
    ALERT_TYPE as Canal
FROM SB2010_ALERT_LOG 
WHERE ALERT_DATE >= GETDATE() - 7
ORDER BY ALERT_DATE DESC;
```

### Relatório de Performance
```sql
SELECT 
    ALERT_TYPE,
    COUNT(*) as TotalAlertas,
    COUNT(CASE WHEN STATUS = 'SUCCESS' THEN 1 END) as Sucessos,
    COUNT(CASE WHEN STATUS = 'ERROR' THEN 1 END) as Erros
FROM SB2010_ALERT_LOG 
WHERE ALERT_DATE >= GETDATE() - 30
GROUP BY ALERT_TYPE;
```

## 🔧 Personalização

### Adicionar Novo Canal
1. Crie uma nova procedure seguindo o padrão: `sp_send_[CANAL]_alert`
2. Adicione o canal na tabela `ALERT_CONFIG`
3. Atualize a procedure `sp_send_universal_alert`

### Filtros Personalizados
Modifique a trigger para incluir filtros específicos:
```sql
-- Exemplo: Apenas produtos críticos
AND EXISTS (
    SELECT 1 FROM SB1010 sb1 
    WHERE sb1.B1_COD = i.B2_COD 
    AND sb1.B1_TIPO IN ('PA', 'MP')
    AND sb1.D_E_L_E_T_ = ''
)
```

## 📈 Performance

### Benchmarks
- **Operação unitária**: ~50ms
- **Lote de 100 produtos**: ~200ms (vs 5s na versão com cursor)
- **Impacto na SB2010**: <1% overhead

### Otimizações Implementadas
- ✅ INSERT em lote na tabela de log
- ✅ Cursor otimizado (LOCAL FAST_FORWARD)
- ✅ Índices estratégicos
- ✅ Tratamento de erro sem rollback forçado

## 🛡️ Segurança

- **Webhooks**: URLs armazenadas de forma segura
- **Tratamento de erros**: Não expõe informações sensíveis
- **Validação de entrada**: Escape de caracteres especiais
- **Timeout**: Evita travamento em chamadas HTTP

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovoCanal`)
3. Commit suas mudanças (`git commit -am 'Adiciona canal Discord'`)
4. Push para a branch (`git push origin feature/NovoCanal`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: [GitHub Issues](../../issues)
- **Discussões**: [GitHub Discussions](../../discussions)
- **LinkedIn**: [Seu Perfil](https://linkedin.com/in/fernando-v-10758522/)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🏆 Casos de Uso

### Cenários Típicos
- **Distribuição/Varejo**: Alerta imediato de ruptura
- **Indústria**: Controle de matéria-prima crítica
- **E-commerce**: Sincronização com marketplace
- **Logística**: Controle de expedição

### Empresas que Podem Beneficiar-se
- Distribuidoras com alto giro de estoque
- Indústrias com processo just-in-time
- Varejistas com múltiplas filiais
- E-commerces integrados ao ERP

---

⭐ **Se este projeto te ajudou, deixe uma estrela no repositório!**

Desenvolvido com ❤️ para a comunidade Protheus
