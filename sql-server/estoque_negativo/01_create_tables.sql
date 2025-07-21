-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: 01_create_tables.sql
-- Descrição: Criação das tabelas principais
-- =============================================

USE [SEU BANCO]
GO

-- Tabela de configuração de alertas
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ALERT_CONFIG]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[ALERT_CONFIG](
        [ID] [int] IDENTITY(1,1) NOT NULL,
        [ALERT_TYPE] [varchar](20) NOT NULL,
        [WEBHOOK_URL] [nvarchar](500) NULL,
        [IS_ACTIVE] [bit] NOT NULL DEFAULT(0),
        [EMAIL_TO] [nvarchar](255) NULL,
        [EMAIL_PROFILE] [varchar](100) NULL DEFAULT('AlertasEstoque'),
        [CHAT_ID] [varchar](50) NULL,
        [BOT_TOKEN] [varchar](200) NULL,
        [TIMEOUT_SECONDS] [int] NULL DEFAULT(30),
        [CREATED_DATE] [datetime] NOT NULL DEFAULT(GETDATE()),
        [UPDATED_DATE] [datetime] NULL,
        CONSTRAINT [PK_ALERT_CONFIG] PRIMARY KEY CLUSTERED ([ID] ASC)
    )
    
    PRINT '✅ Tabela ALERT_CONFIG criada com sucesso!';
END
ELSE
    PRINT '⚠️ Tabela ALERT_CONFIG já existe.';
GO

-- Tabela de log de alertas enviados
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SB2010_ALERT_LOG]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[SB2010_ALERT_LOG](
        [ID] [int] IDENTITY(1,1) NOT NULL,
        [B2_COD] [nvarchar](50) NOT NULL,
        [B2_QATU] [float] NOT NULL,
        [ALERT_DATE] [datetime] NOT NULL,
        [USERNAME] [nvarchar](100) NULL,
        [MACHINE_NAME] [nvarchar](100) NULL,
        [CLIENT_IP] [nvarchar](50) NULL,
        [ALERT_TYPE] [varchar](20) NULL DEFAULT('EMAIL'),
        [STATUS] [varchar](10) NULL DEFAULT('PENDING'),
        [ERROR_MESSAGE] [nvarchar](500) NULL,
        [RESPONSE_TIME_MS] [int] NULL,
        [CREATED_DATE] [datetime] NOT NULL DEFAULT(GETDATE()),
        CONSTRAINT [PK_SB2010_ALERT_LOG] PRIMARY KEY CLUSTERED ([ID] ASC)
    )
    
    PRINT '✅ Tabela SB2010_ALERT_LOG criada com sucesso!';
END
ELSE
    PRINT '⚠️ Tabela SB2010_ALERT_LOG já existe.';
GO

-- Tabela de log de erros (opcional)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SB2010_ERROR_LOG]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[SB2010_ERROR_LOG](
        [ID] [int] IDENTITY(1,1) NOT NULL,
        [ERROR_DATE] [datetime] NOT NULL DEFAULT(GETDATE()),
        [ERROR_MESSAGE] [nvarchar](4000) NULL,
        [ERROR_PROCEDURE] [nvarchar](128) NULL,
        [ERROR_LINE] [int] NULL,
        [USERNAME] [nvarchar](100) NULL,
        [ADDITIONAL_INFO] [nvarchar](max) NULL,
        CONSTRAINT [PK_SB2010_ERROR_LOG] PRIMARY KEY CLUSTERED ([ID] ASC)
    )
    
    PRINT '✅ Tabela SB2010_ERROR_LOG criada com sucesso!';
END
ELSE
    PRINT '⚠️ Tabela SB2010_ERROR_LOG já existe.';
GO

-- Inserção de configurações padrão
IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE ALERT_TYPE = 'EMAIL')
BEGIN
    INSERT INTO [dbo].[ALERT_CONFIG] 
    ([ALERT_TYPE], [IS_ACTIVE], [EMAIL_TO], [EMAIL_PROFILE])
    VALUES 
    ('EMAIL', 1, 'estoque@suaempresa.com', 'AlertasEstoque');
    
    PRINT '✅ Configuração padrão EMAIL inserida!';
END

IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE ALERT_TYPE = 'TEAMS')
BEGIN
    INSERT INTO [dbo].[ALERT_CONFIG] 
    ([ALERT_TYPE], [IS_ACTIVE], [WEBHOOK_URL])
    VALUES 
    ('TEAMS', 0, 'https://outlook.office.com/webhook/SEU_WEBHOOK_TEAMS');
    
    PRINT '✅ Configuração padrão TEAMS inserida!';
END

IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE ALERT_TYPE = 'TELEGRAM')
BEGIN
    INSERT INTO [dbo].[ALERT_CONFIG] 
    ([ALERT_TYPE], [IS_ACTIVE], [WEBHOOK_URL], [CHAT_ID])
    VALUES 
    ('TELEGRAM', 0, 'https://api.telegram.org/bot', '-1001234567890');
    
    PRINT '✅ Configuração padrão TELEGRAM inserida!';
END

IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE ALERT_TYPE = 'SLACK')
BEGIN
    INSERT INTO [dbo].[ALERT_CONFIG] 
    ([ALERT_TYPE], [IS_ACTIVE], [WEBHOOK_URL])
    VALUES 
    ('SLACK', 0, 'https://hooks.slack.com/triggers/');
    
    PRINT '✅ Configuração padrão SLACK inserida!';
END

IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE ALERT_TYPE = 'WEBHOOK')
BEGIN
    INSERT INTO [dbo].[ALERT_CONFIG] 
    ([ALERT_TYPE], [IS_ACTIVE], [WEBHOOK_URL])
    VALUES 
    ('WEBHOOK', 0, 'https://seu-endpoint.com/webhook');
    
    PRINT '✅ Configuração padrão WEBHOOK inserida!';
END

PRINT '🎉 Estrutura de tabelas criada com sucesso!'
PRINT '📋 Próximo passo: Execute 02_create_indexes.sql';
