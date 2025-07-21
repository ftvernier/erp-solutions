-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: 02_create_indexes.sql
-- Descrição: Criação de índices para performance
-- =============================================

USE [SEU BANCO]
GO

-- Índice para consultas rápidas de produtos com alerta
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SB2010_ALERT_LOG_PRODUTO_NEGATIVO')
BEGIN
    CREATE INDEX [IX_SB2010_ALERT_LOG_PRODUTO_NEGATIVO] 
    ON [dbo].[SB2010_ALERT_LOG] ([B2_COD], [B2_QATU])
    WHERE [B2_QATU] < 0;
    
    PRINT '✅ Índice IX_SB2010_ALERT_LOG_PRODUTO_NEGATIVO criado!';
END
ELSE
    PRINT '⚠️ Índice IX_SB2010_ALERT_LOG_PRODUTO_NEGATIVO já existe.';
GO

-- Índice para consultas por data
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SB2010_ALERT_LOG_DATA')
BEGIN
    CREATE INDEX [IX_SB2010_ALERT_LOG_DATA] 
    ON [dbo].[SB2010_ALERT_LOG] ([ALERT_DATE] DESC)
    INCLUDE ([B2_COD], [B2_QATU], [ALERT_TYPE], [STATUS]);
    
    PRINT '✅ Índice IX_SB2010_ALERT_LOG_DATA criado!';
END
ELSE
    PRINT '⚠️ Índice IX_SB2010_ALERT_LOG_DATA já existe.';
GO

-- Índice para tipo de alerta e status
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SB2010_ALERT_LOG_TYPE_STATUS')
BEGIN
    CREATE INDEX [IX_SB2010_ALERT_LOG_TYPE_STATUS] 
    ON [dbo].[SB2010_ALERT_LOG] ([ALERT_TYPE], [STATUS])
    INCLUDE ([ALERT_DATE], [B2_COD]);
    
    PRINT '✅ Índice IX_SB2010_ALERT_LOG_TYPE_STATUS criado!';
END
ELSE
    PRINT '⚠️ Índice IX_SB2010_ALERT_LOG_TYPE_STATUS já existe.';
GO

-- Índice para configurações ativas
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ALERT_CONFIG_ACTIVE')
BEGIN
    CREATE INDEX [IX_ALERT_CONFIG_ACTIVE] 
    ON [dbo].[ALERT_CONFIG] ([IS_ACTIVE], [ALERT_TYPE])
    WHERE [IS_ACTIVE] = 1;
    
    PRINT '✅ Índice IX_ALERT_CONFIG_ACTIVE criado!';
END
ELSE
    PRINT '⚠️ Índice IX_ALERT_CONFIG_ACTIVE já existe.';
GO

-- Índice para log de erros por data
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SB2010_ERROR_LOG_DATE')
BEGIN
    CREATE INDEX [IX_SB2010_ERROR_LOG_DATE] 
    ON [dbo].[SB2010_ERROR_LOG] ([ERROR_DATE] DESC)
    INCLUDE ([ERROR_PROCEDURE], [USERNAME]);
    
    PRINT '✅ Índice IX_SB2010_ERROR_LOG_DATE criado!';
END
ELSE
    PRINT '⚠️ Índice IX_SB2010_ERROR_LOG_DATE já existe.';
GO

-- Índice composto para otimizar a consulta da trigger
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SB2010_ALERT_LOG_TRIGGER_OPTIMIZATION')
BEGIN
    CREATE INDEX [IX_SB2010_ALERT_LOG_TRIGGER_OPTIMIZATION] 
    ON [dbo].[SB2010_ALERT_LOG] ([B2_COD])
    WHERE [B2_QATU] < 0
    INCLUDE ([B2_QATU], [ALERT_DATE]);
    
    PRINT '✅ Índice IX_SB2010_ALERT_LOG_TRIGGER_OPTIMIZATION criado!';
END
ELSE
    PRINT '⚠️ Índice IX_SB2010_ALERT_LOG_TRIGGER_OPTIMIZATION já existe.';
GO

-- Estatísticas de performance
PRINT '';
PRINT '📊 ESTATÍSTICAS DE PERFORMANCE:';
PRINT '================================';

-- Tamanho das tabelas
SELECT 
    OBJECT_NAME(object_id) AS 'Tabela',
    SUM(row_count) AS 'Registros',
    FORMAT(SUM(used_page_count) * 8, 'N0') + ' KB' AS 'Tamanho'
FROM sys.dm_db_partition_stats 
WHERE object_id IN (
    OBJECT_ID('SB2010_ALERT_LOG'),
    OBJECT_ID('ALERT_CONFIG'),
    OBJECT_ID('SB2010_ERROR_LOG')
)
GROUP BY object_id;

-- Índices criados
SELECT 
    t.name AS 'Tabela',
    i.name AS 'Índice',
    i.type_desc AS 'Tipo'
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('SB2010_ALERT_LOG', 'ALERT_CONFIG', 'SB2010_ERROR_LOG')
AND i.name IS NOT NULL
ORDER BY t.name, i.name;

PRINT '';
PRINT '🎉 Índices criados com sucesso!';
PRINT '📋 Próximo passo: Execute as procedures em /procedures/';
