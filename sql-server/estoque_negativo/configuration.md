# 🔧 Guia de Configuração - Sistema de Alertas de Estoque

Este guia te ajudará a configurar todos os canais de alerta disponíveis no sistema.

## 📧 1. Configuração de Email (Database Mail)

### Pré-requisitos
- SQL Server com Database Mail habilitado
- Servidor SMTP configurado

### Passo a Passo

#### 1.1 Habilitar Database Mail
```sql
-- Habilitar Database Mail XPs
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'Database Mail XPs', 1;
RECONFIGURE;
```

#### 1.2 Criar Conta de Email
```sql
-- Criar conta de email
EXEC msdb.dbo.sysmail_add_account_sp
    @account_name = 'ContaAlertas',
    @description = 'Conta para alertas de estoque',
    @email_address = 'alertas@suaempresa.com',
    @display_name = 'Sistema de Alertas ERP',
    @mailserver_name = 'smtp.suaempresa.com',
    @port = 587,
    @enable_ssl = 1,
    @username = 'alertas@suaempresa.com',
    @password = 'sua_senha_aqui';
```

#### 1.3 Criar Perfil
```sql
-- Criar perfil
EXEC msdb.dbo.sysmail_add_profile_sp
    @profile_name = 'AlertasEstoque',
    @description = 'Perfil para alertas de estoque negativo';

-- Associar conta ao perfil
EXEC msdb.dbo.sysmail_add_profileaccount_sp
    @profile_name = 'AlertasEstoque',
    @account_name = 'ContaAlertas',
    @sequence_number = 1;
```

#### 1.4 Configurar no Sistema
```sql
-- Ativar alertas por email
UPDATE ALERT_CONFIG 
SET IS_ACTIVE = 1,
    EMAIL_TO = 'equipe.estoque@suaempresa.com',
    EMAIL_PROFILE = 'AlertasEstoque'
WHERE ALERT_TYPE = 'EMAIL';
```

#### 1.5 Testar Configuração
```sql
-- Teste de email
EXEC msdb.dbo.sp_send_dbmail
    @profile_name = 'AlertasEstoque',
    @recipients = 'teste@suaempresa.com',
    @subject = 'Teste de Configuração',
    @body = 'Se você recebeu este email, a configuração está funcionando!';
```

---

## 👥 2. Configuração Microsoft Teams

### Pré-requisitos
- Acesso administrativo ao Microsoft Teams
- Permissão para criar conectores

### Passo a Passo

#### 2.1 Criar Webhook no Teams
1. Abra o Microsoft Teams
2. Vá para o canal onde deseja receber alertas
3. Clique nos três pontos (...) ao lado do nome do canal
4. Selecione "Conectores"
5. Procure por "Webhook de Entrada" e clique em "Configurar"
6. Dê um nome: "Alertas de Estoque ERP"
7. Opcionalmente, adicione uma imagem
8. Clique em "Criar"
9. **Copie a URL do webhook gerada**

#### 2.2 Configurar no Sistema
```sql
-- Ativar alertas por Teams
UPDATE ALERT_CONFIG 
SET IS_ACTIVE = 1,
    WEBHOOK_URL = 'https://outlook.office.com/webhook/SEU_WEBHOOK_AQUI'
WHERE ALERT_TYPE = 'TEAMS';
```

#### 2.3 Testar Configuração
```sql
-- Teste manual
EXEC sp_send_teams_alert 
    @B2_COD = 'TESTE001',
    @B2_QATU = -5,
    @USERNAME = 'Administrador',
    @MACHINE_NAME = 'Servidor',
    @CLIENT_IP = '192.168.1.100',
    @WEBHOOK_URL = 'SUA_URL_WEBHOOK',
    @LogID = NULL;
```

---

## 📱 3. Configuração Telegram

### Pré-requisitos
- Conta no Telegram
- Acesso para criar bots

### Passo a Passo

#### 3.1 Criar Bot no Telegram
1. Abra o Telegram e procure por `@BotFather`
2. Inicie uma conversa e digite: `/newbot`
3. Escolha um nome para o bot: `Alertas ERP Estoque`
4. Escolha um username: `alertas_erp_estoque_bot`
5. **Copie o token fornecido** (formato: `123456789:ABCdef...`)

#### 3.2 Obter Chat ID
```bash
# Método 1: Adicione o bot a um grupo e digite qualquer mensagem
# Depois acesse: https://api.telegram.org/bot[SEU_TOKEN]/getUpdates

# Método 2: Para chat privado, envie uma mensagem para o bot e use a URL acima
```

#### 3.3 Configurar no Sistema
```sql
-- Configurar bot token e chat ID
UPDATE ALERT_CONFIG 
SET IS_ACTIVE = 1,
    BOT_TOKEN = '123456789:ABCdef_seu_token_aqui',
    CHAT_ID = '-1001234567890'  -- ID do grupo (negativo) ou ID do usuário (positivo)
WHERE ALERT_TYPE = 'TELEGRAM';
```

#### 3.4 Testar Configuração
```sql
-- Teste manual
EXEC sp_send_telegram_alert 
    @B2_COD = 'TESTE001',
    @B2_QATU = -3,
    @USERNAME = 'Administrador',
    @MACHINE_NAME = 'Servidor',
    @CLIENT_IP = '192.168.1.100',
    @BOT_TOKEN = 'SEU_TOKEN',
    @CHAT_ID = 'SEU_CHAT_ID',
    @LogID = NULL;
```

---

## 💬 4. Configuração Slack

### Pré-requisitos
- Workspace do Slack
- Permissões para criar apps

### Passo a Passo

#### 4.1 Criar Webhook do Slack
1. Vá para https://api.slack.com/apps
2. Clique em "Create New App"
3. Escolha "From scratch"
4. Nome: "Alertas ERP Estoque"
5. Selecione seu workspace
6. No menu lateral, clique em "Incoming Webhooks"
7. Ative "Activate Incoming Webhooks"
8. Clique em "Add New Webhook to Workspace"
9. Escolha o canal (#estoque, por exemplo)
10. **Copie a URL do webhook**

#### 4.2 Configurar no Sistema
```sql
-- Ativar alertas por Slack
UPDATE ALERT_CONFIG 
SET IS_ACTIVE = 1,
    WEBHOOK_URL = 'https://hooks.slack.com/services/SEU/WEBHOOK/AQUI'
WHERE ALERT_TYPE = 'SLACK';
```

---

## 🔗 5. Webhook Genérico

### Para Discord, Zapier, ou APIs Customizadas

```sql
-- Configurar webhook genérico
UPDATE ALERT_CONFIG 
SET IS_ACTIVE = 1,
    WEBHOOK_URL = 'https://seu-endpoint.com/webhook'
WHERE ALERT_TYPE = 'WEBHOOK';
```

---

## ⚙️ 6. Configurações Avançadas

### 6.1 Múltiplos Canais Simultâneos
```sql
-- Ativar email e Teams ao mesmo tempo
UPDATE ALERT_CONFIG SET IS_ACTIVE = 1 WHERE ALERT_TYPE IN ('EMAIL', 'TEAMS');
```

### 6.2 Filtros Personalizados
Modifique a trigger para incluir filtros específicos:

```sql
-- Exemplo: Apenas produtos de determinados tipos
AND EXISTS (
    SELECT 1 FROM SB1010 sb1 
    WHERE sb1.B1_COD = i.B2_COD 
    AND sb1.B1_TIPO IN ('PA', 'MP', 'PI')  -- Produto Acabado, Matéria Prima, Produto Intermediário
    AND sb1.D_E_L_E_T_ = ''
)

-- Exemplo: Apenas determinadas filiais
AND i.B2_FILIAL IN ('01', '02', '03')

-- Exemplo: Apenas produtos críticos (com classificação específica)
AND EXISTS (
    SELECT 1 FROM SB1010 sb1 
    WHERE sb1.B1_COD = i.B2_COD 
    AND sb1.B1_CURVA = 'A'  -- Curva ABC = A
    AND sb1.D_E_L_E_T_ = ''
)
```

### 6.3 Horário de Funcionamento
```sql
-- Adicionar na trigger para só alertar em horário comercial
IF DATEPART(HOUR, GETDATE()) BETWEEN 7 AND 18 
AND DATEPART(WEEKDAY, GETDATE()) BETWEEN 2 AND 6  -- Seg-Sex
BEGIN
    -- Lógica de alerta aqui
END
```

### 6.4 Configuração de Timeout
```sql
-- Ajustar timeout para redes lentas
UPDATE ALERT_CONFIG 
SET TIMEOUT_SECONDS = 60  -- 60 segundos
WHERE ALERT_TYPE = 'TEAMS';
```

---

## 📊 7. Monitoramento e Relatórios

### 7.1 Consultar Alertas Recentes
```sql
SELECT 
    B2_COD as Produto,
    B2_QATU as Estoque,
    ALERT_TYPE as Canal,
    STATUS as Status,
    ALERT_DATE as DataHora,
    ERROR_MESSAGE as Erro
FROM SB2010_ALERT_LOG 
WHERE ALERT_DATE >= GETDATE() - 1  -- Últimas 24 horas
ORDER BY ALERT_DATE DESC;
```

### 7.2 Relatório de Performance por Canal
```sql
SELECT 
    ALERT_TYPE as Canal,
    COUNT(*) as TotalAlertas,
    COUNT(CASE WHEN STATUS = 'SUCCESS' THEN 1 END) as Sucessos,
    COUNT(CASE WHEN STATUS = 'ERROR' THEN 1 END) as Erros,
    AVG(RESPONSE_TIME_MS) as TempoMedioMs
FROM SB2010_ALERT_LOG 
WHERE ALERT_DATE >= GETDATE() - 30  -- Últimos 30 dias
GROUP BY ALERT_TYPE
ORDER BY TotalAlertas DESC;
```

### 7.3 Top Produtos com Estoque Negativo
```sql
SELECT 
    B2_COD as Produto,
    COUNT(*) as QtdAlertas,
    MIN(B2_QATU) as MenorEstoque,
    MAX(ALERT_DATE) as UltimoAlerta
FROM SB2010_ALERT_LOG 
WHERE ALERT_DATE >= GETDATE() - 30
AND B2_QATU < 0
GROUP BY B2_COD
ORDER BY QtdAlertas DESC;
```

---

## 🚨 8. Solução de Problemas

### 8.1 Email não está sendo enviado
```sql
-- Verificar status do Database Mail
SELECT * FROM msdb.dbo.sysmail_event_log 
WHERE event_type = 'error' 
ORDER BY log_date DESC;

-- Verificar fila de emails
SELECT * FROM msdb.dbo.sysmail_mailitems 
ORDER BY send_request_date DESC;
```

### 8.2 Webhook retornando erro
```sql
-- Verificar logs de erro
SELECT * FROM SB2010_ALERT_LOG 
WHERE STATUS = 'ERROR' 
AND ALERT_TYPE IN ('TEAMS', 'SLACK', 'TELEGRAM')
ORDER BY ALERT_DATE DESC;
```

### 8.3 Trigger não está disparando
```sql
-- Verificar se a trigger está ativa
SELECT 
    name,
    is_disabled,
    create_date,
    modify_date
FROM sys.triggers 
WHERE name = 'tr_estoque_negativo';

-- Testar manualmente
UPDATE SB2010 SET B2_QATU = -1 WHERE B2_COD = 'PRODUTO_TESTE';
```

---

⚡ **Dica Pro**: Comece sempre com o canal EMAIL ativo para validar o funcionamento, depois adicione os outros canais gradualmente.
