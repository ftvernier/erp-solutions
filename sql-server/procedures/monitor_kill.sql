-- =====================================================
-- SISTEMA DE MONITORAMENTO DE PERFORMANCE SQL SERVER
-- Detecta, registra e opcionalmente finaliza processos problemáticos
-- Autor: Fernando Vernier
-- GitHub: https://github.com/ftvernier/erp-solutions
-- =====================================================

-- =====================================================
-- 1. CRIAÇÃO DA TABELA DE LOG (EXECUTE APENAS UMA VEZ)
-- =====================================================
USE [master] -- ou substitua pelo seu database de monitoramento
GO

-- Verificar se a tabela já existe
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[PerformanceMonitorLog]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[PerformanceMonitorLog] (
        [LogId] BIGINT IDENTITY(1,1) PRIMARY KEY,
        [EventTime] DATETIME2 DEFAULT GETDATE(),
        [EventType] VARCHAR(50) NOT NULL, -- 'LONG_TRANSACTION', 'LONG_QUERY', 'BLOCKING'
        [SessionId] INT NOT NULL,
        [Duration_Minutes] DECIMAL(10,2) NULL,
        [Wait_Seconds] DECIMAL(10,2) NULL,
        [LoginName] VARCHAR(128) NULL,
        [HostName] VARCHAR(128) NULL,
        [ProgramName] VARCHAR(255) NULL,
        [ApplicationType] VARCHAR(50) NULL,
        [Command] VARCHAR(50) NULL,
        [Status] VARCHAR(50) NULL,
        [CPU_Seconds] DECIMAL(10,2) NULL,
        [Reads] BIGINT NULL,
        [Writes] BIGINT NULL,
        [SqlText] NVARCHAR(MAX) NULL,
        [ActionTaken] VARCHAR(100) NULL, -- 'ALERTED', 'AUTO_KILLED', 'PROTECTED_USER', 'BLOCKING_DETECTED'
        [ServerName] VARCHAR(128) DEFAULT @@SERVERNAME,
        [ErrorMessage] NVARCHAR(500) NULL,
        [BlockingSessionId] INT NULL,
        [WaitType] VARCHAR(50) NULL
    );

    -- Criar índices para performance
    CREATE INDEX IX_PerformanceMonitorLog_EventTime ON [dbo].[PerformanceMonitorLog] ([EventTime] DESC);
    CREATE INDEX IX_PerformanceMonitorLog_EventType ON [dbo].[PerformanceMonitorLog] ([EventType]);
    CREATE INDEX IX_PerformanceMonitorLog_SessionId ON [dbo].[PerformanceMonitorLog] ([SessionId]);
    
    PRINT '✅ Tabela PerformanceMonitorLog criada com sucesso!'
END
ELSE
BEGIN
    PRINT 'ℹ️ Tabela PerformanceMonitorLog já existe.'
END
GO

-- =====================================================
-- 2. STORED PROCEDURE DE MONITORAMENTO
-- =====================================================
CREATE OR ALTER PROCEDURE [dbo].[sp_MonitorPerformanceDB]
    @TransactionThresholdMinutes INT = 10,
    @QueryThresholdMinutes INT = 10,
    @AutoKillThresholdMinutes INT = 60,
    @EnableTransactionAlerts BIT = 1,
    @EnableBlockingAlerts BIT = 1,
    @EnableLongQueryAlerts BIT = 1,
    @EnableAutoKill BIT = 0,
    @ExcludeSystemOperations BIT = 1,
    @Debug BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ServerName VARCHAR(128) = @@SERVERNAME
    DECLARE @CurrentTime DATETIME2 = GETDATE()
    DECLARE @AlertCount INT = 0
    
    -- Lista de usuários protegidos (ERP e sistemas críticos)
    DECLARE @ProtectedUsersList VARCHAR(500) = 'protheus,smartview,totvstss,sa,system'
    
    IF @Debug = 1
        PRINT 'Iniciando monitoramento: ' + @ServerName + ' as ' + CONVERT(VARCHAR, @CurrentTime, 120)
    
    -- =====================================================
    -- 1. VERIFICAR TRANSAÇÕES LONGAS
    -- =====================================================
    IF @EnableTransactionAlerts = 1
    BEGIN
        IF @Debug = 1 PRINT 'Verificando transacoes longas...'
        
        DECLARE transaction_cursor CURSOR FOR
        SELECT 
            s.session_id,
            s.login_name,
            s.host_name,
            s.program_name,
            DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) as duration_minutes,
            CASE 
                WHEN s.program_name LIKE '%Protheus%' THEN 'Protheus ERP'
                WHEN s.program_name LIKE '%dbaccess%' THEN 'DBAccess'
                WHEN s.program_name LIKE '%smartclient%' THEN 'SmartClient'
                WHEN s.program_name LIKE '%totvsappserver%' THEN 'AppServer'
                ELSE 'Other Application'
            END as application_type,
            ISNULL(SUBSTRING(REPLACE(REPLACE(REPLACE(st.text, CHAR(10), ' '), CHAR(13), ' '), CHAR(9), ' '), 1, 400), 'N/A') as sql_snippet
        FROM sys.dm_tran_active_transactions at
        INNER JOIN sys.dm_tran_session_transactions st_session ON at.transaction_id = st_session.transaction_id
        INNER JOIN sys.dm_exec_sessions s ON st_session.session_id = s.session_id
        LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
        OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) > @TransactionThresholdMinutes
            AND s.is_user_process = 1
            -- Filtrar operações de sistema/CDC
            AND s.login_name NOT LIKE 'NT SERVICE%'
            AND s.login_name NOT LIKE 'NT AUTHORITY%'
            AND ISNULL(s.program_name, '') NOT LIKE '%SQLAgent%'
        ORDER BY duration_minutes DESC

        DECLARE @SessionId INT, @LoginName VARCHAR(128), @HostName VARCHAR(128), @ProgramName VARCHAR(255)
        DECLARE @DurationMinutes INT, @ApplicationType VARCHAR(50), @SqlSnippet NVARCHAR(400)

        OPEN transaction_cursor
        FETCH NEXT FROM transaction_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @DurationMinutes, @ApplicationType, @SqlSnippet

        WHILE @@FETCH_STATUS = 0
        BEGIN
            DECLARE @ShouldKill BIT = 0
            DECLARE @ActionTaken VARCHAR(100) = 'ALERTED'
            DECLARE @IsProtectedUser BIT = 0
            DECLARE @ErrorMsg NVARCHAR(500) = NULL
            
            -- Verificar se é usuário protegido
            IF CHARINDEX(LOWER(@LoginName), @ProtectedUsersList) > 0
            BEGIN
                SET @IsProtectedUser = 1
                SET @ActionTaken = 'PROTECTED_USER'
            END
            
            -- Auto-kill se habilitado e não for usuário protegido
            IF @EnableAutoKill = 1 AND @DurationMinutes >= @AutoKillThresholdMinutes AND @IsProtectedUser = 0
            BEGIN
                DECLARE @KillCommand NVARCHAR(50) = 'KILL ' + CAST(@SessionId AS NVARCHAR(10))
                
                BEGIN TRY
                    EXEC sp_executesql @KillCommand
                    SET @ShouldKill = 1
                    SET @ActionTaken = 'AUTO_KILLED'
                    
                    IF @Debug = 1
                        PRINT 'Auto-kill executado na session: ' + CAST(@SessionId AS VARCHAR)
                END TRY
                BEGIN CATCH
                    SET @ErrorMsg = ERROR_MESSAGE()
                    SET @ActionTaken = 'KILL_FAILED'
                    
                    IF @Debug = 1
                        PRINT 'Erro no auto-kill session ' + CAST(@SessionId AS VARCHAR) + ': ' + @ErrorMsg
                END CATCH
            END

            -- Registrar no log
            INSERT INTO [dbo].[PerformanceMonitorLog] (
                [EventType], [SessionId], [Duration_Minutes], [LoginName], [HostName], 
                [ProgramName], [ApplicationType], [SqlText], [ActionTaken], [ErrorMessage]
            )
            VALUES (
                'LONG_TRANSACTION', @SessionId, @DurationMinutes, @LoginName, @HostName,
                @ProgramName, @ApplicationType, @SqlSnippet, @ActionTaken, @ErrorMsg
            )

            SET @AlertCount = @AlertCount + 1

            FETCH NEXT FROM transaction_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @DurationMinutes, @ApplicationType, @SqlSnippet
        END

        CLOSE transaction_cursor
        DEALLOCATE transaction_cursor
    END

    -- =====================================================
    -- 2. VERIFICAR BLOQUEIOS ATIVOS
    -- =====================================================
    IF @EnableBlockingAlerts = 1
    BEGIN
        IF @Debug = 1 PRINT 'Verificando bloqueios ativos...'
        
        DECLARE blocking_cursor CURSOR FOR
        SELECT 
            s.session_id,
            s.login_name,
            s.host_name,
            s.program_name,
            r.blocking_session_id,
            r.wait_type,
            CAST(r.wait_time / 1000.0 AS DECIMAL(10,2)) as wait_seconds,
            bs.login_name as blocking_login,
            bs.host_name as blocking_host,
            ISNULL(SUBSTRING(REPLACE(REPLACE(REPLACE(st.text, CHAR(10), ' '), CHAR(13), ' '), CHAR(9), ' '), 1, 400), 'N/A') as sql_snippet
        FROM sys.dm_exec_sessions s
        LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
        LEFT JOIN sys.dm_exec_sessions bs ON r.blocking_session_id = bs.session_id
        OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE s.is_user_process = 1
            AND r.blocking_session_id > 0
        ORDER BY r.wait_time DESC

        DECLARE @BlockingId INT, @WaitType VARCHAR(50), @WaitSeconds DECIMAL(10,2)
        DECLARE @BlockingLogin VARCHAR(128), @BlockingHost VARCHAR(128)

        OPEN blocking_cursor
        FETCH NEXT FROM blocking_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @BlockingId, @WaitType, @WaitSeconds, @BlockingLogin, @BlockingHost, @SqlSnippet

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Registrar bloqueio no log
            INSERT INTO [dbo].[PerformanceMonitorLog] (
                [EventType], [SessionId], [Wait_Seconds], [LoginName], [HostName], [ProgramName],
                [SqlText], [ActionTaken], [BlockingSessionId], [WaitType]
            )
            VALUES (
                'BLOCKING', @SessionId, @WaitSeconds, @LoginName, @HostName, @ProgramName,
                @SqlSnippet, 'BLOCKING_DETECTED', @BlockingId, @WaitType
            )

            SET @AlertCount = @AlertCount + 1

            IF @Debug = 1
                PRINT 'Bloqueio detectado - Session: ' + CAST(@SessionId AS VARCHAR) + ' bloqueada por: ' + CAST(@BlockingId AS VARCHAR)

            FETCH NEXT FROM blocking_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @BlockingId, @WaitType, @WaitSeconds, @BlockingLogin, @BlockingHost, @SqlSnippet
        END

        CLOSE blocking_cursor
        DEALLOCATE blocking_cursor
    END

    -- =====================================================
    -- 3. VERIFICAR QUERIES LONGAS
    -- =====================================================
    IF @EnableLongQueryAlerts = 1
    BEGIN
        IF @Debug = 1 PRINT 'Verificando queries longas...'
        
        DECLARE long_query_cursor CURSOR FOR
        SELECT 
            s.session_id,
            s.login_name,
            s.host_name,
            s.program_name,
            r.command,
            r.status,
            CAST(r.total_elapsed_time / 1000.0 / 60 AS DECIMAL(10,2)) as elapsed_minutes,
            CAST(r.cpu_time / 1000.0 AS DECIMAL(10,2)) as cpu_seconds,
            r.reads,
            r.writes,
            ISNULL(SUBSTRING(REPLACE(REPLACE(REPLACE(st.text, CHAR(10), ' '), CHAR(13), ' '), CHAR(9), ' '), 1, 400), 'N/A') as sql_snippet,
            CASE 
                WHEN s.program_name LIKE '%Protheus%' THEN 'Protheus ERP'
                WHEN s.program_name LIKE '%dbaccess%' THEN 'DBAccess'
                WHEN s.program_name LIKE '%smartclient%' THEN 'SmartClient'
                WHEN s.program_name LIKE '%totvsappserver%' THEN 'AppServer'
                ELSE 'Other Application'
            END as application_type
        FROM sys.dm_exec_sessions s
        INNER JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
        OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
        WHERE s.is_user_process = 1
            AND r.total_elapsed_time > (@QueryThresholdMinutes * 60 * 1000)
            -- Filtrar operações de sistema/CDC
            AND s.login_name NOT LIKE 'NT SERVICE%'
            AND s.login_name NOT LIKE 'NT AUTHORITY%'
            AND ISNULL(s.program_name, '') NOT LIKE '%SQLAgent%'
        ORDER BY r.total_elapsed_time DESC

        DECLARE @Command VARCHAR(50), @Status VARCHAR(50), @ElapsedMinutes DECIMAL(10,2)
        DECLARE @CpuSeconds DECIMAL(10,2), @Reads BIGINT, @Writes BIGINT

        OPEN long_query_cursor
        FETCH NEXT FROM long_query_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @Command, @Status, @ElapsedMinutes, @CpuSeconds, @Reads, @Writes, @SqlSnippet, @ApplicationType

        WHILE @@FETCH_STATUS = 0
        BEGIN
            DECLARE @ShouldKillQuery BIT = 0
            DECLARE @ActionTakenQuery VARCHAR(100) = 'ALERTED'
            DECLARE @IsProtectedUserQuery BIT = 0
            DECLARE @ErrorMsgQuery NVARCHAR(500) = NULL
            
            -- Verificar se é usuário protegido
            IF CHARINDEX(LOWER(@LoginName), @ProtectedUsersList) > 0
            BEGIN
                SET @IsProtectedUserQuery = 1
                SET @ActionTakenQuery = 'PROTECTED_USER'
            END
            
            -- Auto-kill se habilitado e não for usuário protegido
            IF @EnableAutoKill = 1 AND @ElapsedMinutes >= @AutoKillThresholdMinutes AND @IsProtectedUserQuery = 0
            BEGIN
                DECLARE @KillCommandQuery NVARCHAR(50) = 'KILL ' + CAST(@SessionId AS NVARCHAR(10))
                
                BEGIN TRY
                    EXEC sp_executesql @KillCommandQuery
                    SET @ShouldKillQuery = 1
                    SET @ActionTakenQuery = 'AUTO_KILLED'
                    
                    IF @Debug = 1
                        PRINT 'Auto-kill query executado na session: ' + CAST(@SessionId AS VARCHAR)
                END TRY
                BEGIN CATCH
                    SET @ErrorMsgQuery = ERROR_MESSAGE()
                    SET @ActionTakenQuery = 'KILL_FAILED'
                    
                    IF @Debug = 1
                        PRINT 'Erro no auto-kill query session ' + CAST(@SessionId AS VARCHAR) + ': ' + @ErrorMsgQuery
                END CATCH
            END

            -- Registrar no log
            INSERT INTO [dbo].[PerformanceMonitorLog] (
                [EventType], [SessionId], [Duration_Minutes], [LoginName], [HostName], [ProgramName], 
                [ApplicationType], [Command], [Status], [CPU_Seconds], [Reads], [Writes], 
                [SqlText], [ActionTaken], [ErrorMessage]
            )
            VALUES (
                'LONG_QUERY', @SessionId, @ElapsedMinutes, @LoginName, @HostName, @ProgramName,
                @ApplicationType, @Command, @Status, @CpuSeconds, @Reads, @Writes,
                @SqlSnippet, @ActionTakenQuery, @ErrorMsgQuery
            )

            SET @AlertCount = @AlertCount + 1

            FETCH NEXT FROM long_query_cursor INTO @SessionId, @LoginName, @HostName, @ProgramName, @Command, @Status, @ElapsedMinutes, @CpuSeconds, @Reads, @Writes, @SqlSnippet, @ApplicationType
        END

        CLOSE long_query_cursor
        DEALLOCATE long_query_cursor
    END

    -- =====================================================
    -- RESUMO FINAL
    -- =====================================================
    DECLARE @SuccessCount INT, @ErrorCount INT, @KilledCount INT, @ProtectedCount INT
    
    SELECT @SuccessCount = COUNT(*) FROM [dbo].[PerformanceMonitorLog] 
    WHERE EventTime >= DATEADD(MINUTE, -1, @CurrentTime) AND ActionTaken = 'ALERTED'
    
    SELECT @KilledCount = COUNT(*) FROM [dbo].[PerformanceMonitorLog] 
    WHERE EventTime >= DATEADD(MINUTE, -1, @CurrentTime) AND ActionTaken = 'AUTO_KILLED'
    
    SELECT @ProtectedCount = COUNT(*) FROM [dbo].[PerformanceMonitorLog] 
    WHERE EventTime >= DATEADD(MINUTE, -1, @CurrentTime) AND ActionTaken = 'PROTECTED_USER'
    
    SELECT @ErrorCount = COUNT(*) FROM [dbo].[PerformanceMonitorLog] 
    WHERE EventTime >= DATEADD(MINUTE, -1, @CurrentTime) AND ActionTaken LIKE '%FAILED%'
    
    PRINT '============ RESUMO MONITORAMENTO ============'
    PRINT 'Total de eventos detectados: ' + CAST(@AlertCount AS VARCHAR)
    PRINT 'Processos finalizados automaticamente: ' + CAST(@KilledCount AS VARCHAR)
    PRINT 'Usuarios protegidos (nao finalizados): ' + CAST(@ProtectedCount AS VARCHAR)
    PRINT 'Falhas na finalizacao: ' + CAST(@ErrorCount AS VARCHAR)
    PRINT 'Servidor: ' + @ServerName
    PRINT 'Timestamp: ' + CONVERT(VARCHAR, @CurrentTime, 120)
    
    IF @Debug = 1
    BEGIN
        PRINT ''
        PRINT 'Detalhes dos eventos (ultimos 10):'
        SELECT TOP 10 
            EventTime,
            EventType,
            SessionId,
            ISNULL(Duration_Minutes, Wait_Seconds) as Duration_Wait,
            LoginName,
            ApplicationType,
            ActionTaken,
            CASE WHEN LEN(SqlText) > 100 THEN LEFT(SqlText, 100) + '...' ELSE SqlText END as SqlPreview
        FROM [dbo].[PerformanceMonitorLog]
        WHERE EventTime >= DATEADD(HOUR, -1, @CurrentTime)
        ORDER BY EventTime DESC
    END
    
    RETURN @AlertCount
END
GO

-- =====================================================
-- 3. QUERIES ÚTEIS PARA ANÁLISE DOS LOGS
-- =====================================================

-- Visualizar eventos recentes (última hora)
/*
SELECT 
    EventTime,
    EventType,
    SessionId,
    Duration_Minutes,
    LoginName,
    HostName,
    ApplicationType,
    ActionTaken,
    CASE WHEN LEN(SqlText) > 200 THEN LEFT(SqlText, 200) + '...' ELSE SqlText END as SqlPreview
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(HOUR, -1, GETDATE())
ORDER BY EventTime DESC;
*/

-- Estatísticas por tipo de evento (últimas 24 horas)
/*
SELECT 
    EventType,
    COUNT(*) as Total_Events,
    COUNT(CASE WHEN ActionTaken = 'AUTO_KILLED' THEN 1 END) as Auto_Killed,
    COUNT(CASE WHEN ActionTaken = 'PROTECTED_USER' THEN 1 END) as Protected_Users,
    AVG(Duration_Minutes) as Avg_Duration_Minutes,
    MAX(Duration_Minutes) as Max_Duration_Minutes
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(DAY, -1, GETDATE())
GROUP BY EventType
ORDER BY Total_Events DESC;
*/

-- Top usuários com mais problemas de performance (última semana)
/*
SELECT 
    LoginName,
    COUNT(*) as Total_Issues,
    COUNT(CASE WHEN EventType = 'LONG_QUERY' THEN 1 END) as Long_Queries,
    COUNT(CASE WHEN EventType = 'LONG_TRANSACTION' THEN 1 END) as Long_Transactions,
    COUNT(CASE WHEN EventType = 'BLOCKING' THEN 1 END) as Blockings,
    AVG(Duration_Minutes) as Avg_Duration
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(DAY, -7, GETDATE())
    AND LoginName IS NOT NULL
GROUP BY LoginName
HAVING COUNT(*) > 5
ORDER BY Total_Issues DESC;
*/

-- =====================================================
-- 4. INSTRUÇÕES DE USO
-- =====================================================
/*
CONFIGURAÇÃO INICIAL:
1. Execute a seção de criação da tabela (seção 1) apenas uma vez
2. A stored procedure (seção 2) pode ser executada quantas vezes necessário

EXECUÇÃO MANUAL:
-- Modo de teste (só registra, não mata processos)
EXEC sp_MonitorPerformanceDB @Debug = 1

-- Modo conservador (mata processos > 60 minutos)
EXEC sp_MonitorPerformanceDB 
    @EnableAutoKill = 1,
    @AutoKillThresholdMinutes = 60,
    @Debug = 1

-- Modo agressivo (mata processos > 15 minutos)
EXEC sp_MonitorPerformanceDB 
    @EnableAutoKill = 1,
    @AutoKillThresholdMinutes = 15

AGENDAMENTO VIA SQL AGENT JOB:
1. Crie um novo Job no SQL Server Agent
2. Adicione um step com o comando: EXEC sp_MonitorPerformanceDB @EnableAutoKill = 1, @AutoKillThresholdMinutes = 30
3. Agende para executar a cada 5-10 minutos
4. Configure alertas de falha se necessário

PARÂMETROS PRINCIPAIS:
- @TransactionThresholdMinutes: Threshold para alertar sobre transações longas (padrão: 10)
- @QueryThresholdMinutes: Threshold para alertar sobre queries longas (padrão: 10)
- @AutoKillThresholdMinutes: Threshold para auto-kill de processos (padrão: 60)
- @EnableAutoKill: Habilita finalizaçäo automática de processos (padrão: 0 - DESABILITADO)
- @EnableTransactionAlerts: Habilita monitoramento de transações longas (padrão: 1)
- @EnableBlockingAlerts: Habilita monitoramento de bloqueios (padrão: 1)
- @EnableLongQueryAlerts: Habilita monitoramento de queries longas (padrão: 1)
- @Debug: Exibe informações detalhadas durante execução (padrão: 0)

USUÁRIOS PROTEGIDOS (NUNCA SÃO FINALIZADOS):
- protheus, smartview, totvstss, sa, system

ANÁLISE DOS LOGS:
Use as queries comentadas na seção 3 para analisar:
- Eventos recentes
- Estatísticas por tipo
- Usuários com mais problemas
- Tendências de performance

MANUTENÇÃO:
-- Limpeza de logs antigos (manter apenas últimos 30 dias)
DELETE FROM [dbo].[PerformanceMonitorLog] 
WHERE EventTime < DATEADD(DAY, -30, GETDATE());

IMPORTANTE:
- Sempre teste primeiro com @EnableAutoKill = 0
- Monitore os logs regularmente
- Ajuste os thresholds conforme necessário
- Faça backup antes de implementar em produção
*/
