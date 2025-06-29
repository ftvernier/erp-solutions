import React, { useState } from 'react';
import { Code2, Copy, Download, Activity, Database, Clock, AlertTriangle, Search, Target } from 'lucide-react';

const SQLDiagnosticGenerator = () => {
  const [selectedDiagnostics, setSelectedDiagnostics] = useState([]);
  const [generatedScript, setGeneratedScript] = useState('');
  const [activeCategory, setActiveCategory] = useState('performance');

  // Categorias de diagnóstico
  const diagnosticCategories = {
    performance: {
      name: 'Performance Geral',
      icon: <Activity className="w-5 h-5" />,
      color: 'blue',
      description: 'Análise geral de performance do banco'
    },
    blocking: {
      name: 'Bloqueios & Deadlocks',
      icon: <AlertTriangle className="w-5 h-5" />,
      color: 'red',
      description: 'Identificar bloqueios e deadlocks'
    },
    queries: {
      name: 'Queries Problemáticas',
      icon: <Search className="w-5 h-5" />,
      color: 'yellow',
      description: 'Queries lentas e com alta CPU'
    },
    maintenance: {
      name: 'Manutenção DB',
      icon: <Database className="w-5 h-5" />,
      color: 'green',
      description: 'Índices, fragmentação e estatísticas'
    },
    connections: {
      name: 'Conexões & Sessões',
      icon: <Target className="w-5 h-5" />,
      color: 'purple',
      description: 'Análise de conexões ativas'
    },
    protheus: {
      name: 'Procedures Manutenção',
      icon: <Clock className="w-5 h-5" />,
      color: 'indigo',
      description: 'Stored procedures para manutenção automática'
    }
  };

  // Scripts de diagnóstico
  const diagnosticScripts = {
    // Performance Geral
    'cpu_usage': {
      category: 'performance',
      name: 'CPU Usage por Query',
      description: 'Top queries que mais consomem CPU',
      script: `-- =====================================================
-- CPU USAGE - TOP QUERIES MAIS PESADAS
-- =====================================================
SELECT TOP 20
    qs.execution_count,
    qs.total_worker_time / 1000 as total_cpu_time_ms,
    qs.total_worker_time / qs.execution_count / 1000 as avg_cpu_time_ms,
    qs.total_elapsed_time / 1000 as total_elapsed_time_ms,
    qs.total_elapsed_time / qs.execution_count / 1000 as avg_elapsed_time_ms,
    qs.total_logical_reads,
    qs.total_logical_reads / qs.execution_count as avg_logical_reads,
    qs.creation_time,
    qs.last_execution_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset)/2) + 1) AS statement_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE qs.last_execution_time > DATEADD(HOUR, -2, GETDATE())
    AND st.text NOT LIKE '%sys.dm_%'  -- Excluir queries do sistema
ORDER BY qs.total_worker_time DESC;`
    },
    
    'wait_stats': {
      category: 'performance',
      name: 'Wait Statistics',
      description: 'Principais gargalos do sistema',
      script: `-- =====================================================
-- WAIT TYPES - PRINCIPAIS GARGALOS
-- =====================================================
SELECT TOP 20
    wait_type,
    wait_time_ms,
    waiting_tasks_count,
    signal_wait_time_ms,
    wait_time_ms - signal_wait_time_ms AS resource_wait_time_ms,
    CAST(100.0 * wait_time_ms / SUM(wait_time_ms) OVER() AS DECIMAL(5,2)) AS percent_total_waits,
    CAST(wait_time_ms / 1000.0 / 60 AS DECIMAL(10,2)) AS wait_time_minutes,
    CASE wait_type
        WHEN 'PAGEIOLATCH_SH' THEN 'Disk I/O - Shared page latch'
        WHEN 'PAGEIOLATCH_EX' THEN 'Disk I/O - Exclusive page latch'
        WHEN 'LCK_M_S' THEN 'Lock - Shared lock'
        WHEN 'LCK_M_X' THEN 'Lock - Exclusive lock'
        WHEN 'CXPACKET' THEN 'Parallelism - Waiting for parallel query'
        WHEN 'ASYNC_NETWORK_IO' THEN 'Network - Client not consuming data'
        ELSE 'Other'
    END as wait_description
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'CLR_SEMAPHORE', 'LAZYWRITER_SLEEP', 'RESOURCE_QUEUE', 'SLEEP_TASK',
    'SLEEP_SYSTEMTASK', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR', 'LOGMGR_QUEUE',
    'CHECKPOINT_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH', 'XE_TIMER_EVENT',
    'BROKER_TO_FLUSH', 'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT'
)
AND wait_time_ms > 0
ORDER BY wait_time_ms DESC;`
    },

    // Bloqueios
    'active_blocks': {
      category: 'blocking',
      name: 'Bloqueios Ativos',
      description: 'Sessões bloqueadas e bloqueadoras',
      script: `-- =====================================================
-- BLOQUEIOS ATIVOS - ANÁLISE COMPLETA
-- =====================================================
SELECT 
    s.session_id,
    s.login_name,
    s.host_name,
    s.program_name,
    s.status,
    s.cpu_time,
    s.memory_usage,
    s.total_elapsed_time,
    s.last_request_start_time,
    r.blocking_session_id,
    r.wait_type,
    r.wait_time,
    r.wait_resource,
    r.command,
    DB_NAME(r.database_id) as database_name,
    SUBSTRING(t.text, (r.statement_start_offset/2)+1,
        ((CASE r.statement_end_offset
            WHEN -1 THEN DATALENGTH(t.text)
            ELSE r.statement_end_offset
        END - r.statement_start_offset)/2) + 1) AS current_statement,
    t.text as full_sql_text,
    -- Informações da sessão bloqueadora
    bs.login_name as blocking_login,
    bs.host_name as blocking_host,
    bs.program_name as blocking_program
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
LEFT JOIN sys.dm_exec_sessions bs ON r.blocking_session_id = bs.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE s.is_user_process = 1
    AND (r.blocking_session_id > 0 OR r.session_id IN (
        SELECT blocking_session_id 
        FROM sys.dm_exec_requests 
        WHERE blocking_session_id > 0
    ))
ORDER BY r.total_elapsed_time DESC;`
    },

    'long_transactions': {
      category: 'blocking',
      name: 'Transações Longas',
      description: 'Transações abertas há muito tempo',
      script: `-- =====================================================
-- TRANSAÇÕES LONGAS - ANÁLISE DETALHADA
-- =====================================================
SELECT 
    s.session_id,
    s.login_name,
    s.host_name,
    s.program_name,
    at.transaction_id,
    at.transaction_begin_time,
    DATEDIFF(SECOND, at.transaction_begin_time, GETDATE()) as duration_seconds,
    DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) as duration_minutes,
    at.transaction_type,
    at.transaction_state,
    r.command,
    r.status,
    r.wait_type,
    r.wait_time,
    r.cpu_time,
    r.reads,
    r.writes,
    -- Query atual em execução
    CASE 
        WHEN r.sql_handle IS NOT NULL THEN st.text
        ELSE ec.most_recent_sql_handle_text
    END as current_sql,
    -- Última query executada na sessão
    ec.most_recent_sql_handle_text as last_executed_sql,
    -- Identificar se é transação do Protheus
    CASE 
        WHEN s.program_name LIKE '%Protheus%' THEN 'Protheus ERP'
        WHEN s.program_name LIKE '%dbaccess%' THEN 'DBAccess'
        WHEN s.program_name LIKE '%smartclient%' THEN 'SmartClient'
        WHEN s.program_name LIKE '%totvsappserver%' THEN 'AppServer'
        ELSE 'Other Application'
    END as application_type,
    -- Classificar duração
    CASE 
        WHEN DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) > 60 THEN 'CRÍTICO (>1h)'
        WHEN DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) > 30 THEN 'ALTO (>30min)'
        WHEN DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) > 10 THEN 'MÉDIO (>10min)'
        ELSE 'BAIXO (<10min)'
    END as duration_classification
FROM sys.dm_tran_active_transactions at
INNER JOIN sys.dm_tran_session_transactions st_session ON at.transaction_id = st_session.transaction_id
INNER JOIN sys.dm_exec_sessions s ON st_session.session_id = s.session_id
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) st
OUTER APPLY (
    SELECT TOP 1 st2.text as most_recent_sql_handle_text
    FROM sys.dm_exec_connections c
    CROSS APPLY sys.dm_exec_sql_text(c.most_recent_sql_handle) st2
    WHERE c.session_id = s.session_id
) ec
WHERE DATEDIFF(SECOND, at.transaction_begin_time, GETDATE()) > 30
    AND s.is_user_process = 1
ORDER BY at.transaction_begin_time;`
    },

    // Queries
    'slow_queries': {
      category: 'queries',
      name: 'Queries Lentas',
      description: 'Queries com maior tempo de execução',
      script: `-- =====================================================
-- QUERIES MAIS LENTAS - ANÁLISE DETALHADA
-- =====================================================
SELECT TOP 30
    qs.sql_handle,
    qs.execution_count,
    qs.total_elapsed_time / 1000 as total_elapsed_time_ms,
    qs.total_elapsed_time / qs.execution_count / 1000 as avg_elapsed_time_ms,
    qs.total_worker_time / 1000 as total_cpu_time_ms,
    qs.total_worker_time / qs.execution_count / 1000 as avg_cpu_time_ms,
    qs.total_logical_reads,
    qs.total_logical_reads / qs.execution_count as avg_logical_reads,
    qs.total_physical_reads,
    qs.total_physical_reads / qs.execution_count as avg_physical_reads,
    qs.creation_time,
    qs.last_execution_time,
    -- Verificar se é query do Protheus
    CASE 
        WHEN st.text LIKE '%RetSqlName%' THEN 'Protheus Query'
        WHEN st.text LIKE '%D_E_L_E_T_%' THEN 'Protheus Query'
        WHEN st.text LIKE '%xFilial%' THEN 'Protheus Query'
        ELSE 'Other'
    END as query_type,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset)/2) + 1) AS statement_text,
    st.text as full_sql_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE qs.last_execution_time > DATEADD(HOUR, -4, GETDATE())
    AND qs.total_elapsed_time / qs.execution_count > 1000000
ORDER BY qs.total_elapsed_time / qs.execution_count DESC;`
    },

    // Manutenção
    'index_fragmentation': {
      category: 'maintenance',
      name: 'Fragmentação de Índices',
      description: 'Índices que precisam de manutenção',
      script: `-- =====================================================
-- ANÁLISE DE FRAGMENTAÇÃO DE ÍNDICES
-- =====================================================
SELECT 
    DB_NAME(ps.database_id) as database_name,
    OBJECT_SCHEMA_NAME(ps.object_id, ps.database_id) as schema_name,
    OBJECT_NAME(ps.object_id, ps.database_id) as table_name,
    i.name as index_name,
    ps.index_type_desc,
    ps.avg_fragmentation_in_percent,
    ps.fragment_count,
    ps.page_count,
    ps.avg_page_space_used_in_percent,
    CASE 
        WHEN ps.avg_fragmentation_in_percent > 30 AND ps.page_count > 1000 THEN 'REBUILD REQUIRED'
        WHEN ps.avg_fragmentation_in_percent > 10 AND ps.page_count > 1000 THEN 'REORGANIZE REQUIRED'
        ELSE 'OK - No maintenance needed'
    END as recommendation
FROM sys.dm_db_index_physical_stats(NULL, NULL, NULL, NULL, 'LIMITED') ps
INNER JOIN sys.indexes i ON ps.object_id = i.object_id AND ps.index_id = i.index_id
WHERE ps.avg_fragmentation_in_percent > 10
    AND ps.page_count > 1000
    AND i.name IS NOT NULL
ORDER BY ps.avg_fragmentation_in_percent DESC;`
    },

    // Conexões
    'active_connections': {
      category: 'connections',
      name: 'Conexões Ativas',
      description: 'Sessões ativas e tempo de inatividade',
      script: `-- =====================================================
-- ANÁLISE DE CONEXÕES ATIVAS
-- =====================================================
SELECT 
    s.session_id,
    s.login_name,
    s.host_name,
    s.program_name,
    s.status,
    s.open_transaction_count,
    s.last_request_start_time,
    s.last_request_end_time,
    DATEDIFF(SECOND, s.last_request_end_time, GETDATE()) as seconds_since_last_request,
    DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) as minutes_since_last_request,
    c.connect_time,
    c.net_transport,
    c.client_net_address,
    c.client_tcp_port,
    s.cpu_time,
    s.memory_usage,
    s.reads,
    s.writes,
    s.logical_reads,
    -- Identificar conexões do Protheus
    CASE 
        WHEN s.program_name LIKE '%Protheus%' THEN 'Protheus ERP'
        WHEN s.program_name LIKE '%dbaccess%' THEN 'DBAccess'
        WHEN s.program_name LIKE '%smartclient%' THEN 'SmartClient'
        WHEN s.program_name LIKE '%totvsappserver%' THEN 'AppServer'
        ELSE 'Other'
    END as connection_type,
    -- Status da conexão
    CASE 
        WHEN DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) > 30 THEN 'IDLE_LONG'
        WHEN DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) > 10 THEN 'IDLE_MEDIUM'
        WHEN s.status = 'running' THEN 'ACTIVE'
        ELSE 'IDLE_SHORT'
    END as connection_status
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_connections c ON s.session_id = c.session_id
WHERE s.is_user_process = 1
    AND s.session_id > 50
ORDER BY s.last_request_start_time DESC;`
    },

    // Procedures de Manutenção
    'maintain_indexes_procedure': {
      category: 'protheus',
      name: 'Procedure Manutenção Índices',
      description: 'Stored procedure para manutenção automática de índices',
      script: `-- =====================================================
-- STORED PROCEDURE - MANUTENÇÃO AUTOMÁTICA DE ÍNDICES
-- =====================================================
USE [SEUBANCO]
GO
/****** Object:  StoredProcedure [dbo].[MaintainIndexes]    Script Date: 6/29/2025 11:57:30 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE OR ALTER PROCEDURE [dbo].[MaintainIndexes]
AS
BEGIN
    SET NOCOUNT ON;
    -- Declaração de variáveis
    DECLARE @SchemaName NVARCHAR(256);
    DECLARE @TableName NVARCHAR(256);
    DECLARE @IndexName NVARCHAR(256);
    DECLARE @IndexID INT;
    DECLARE @Fragmentation FLOAT;
    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @StartTime DATETIMEOFFSET;
    DECLARE @EndTime DATETIMEOFFSET;
    DECLARE @ElapsedTime NVARCHAR(50);
    DECLARE @TotalIndexes INT = 0;
    DECLARE @ProcessedIndexes INT = 0;
    
    PRINT '=====================================================';
    PRINT 'INICIANDO MANUTENÇÃO AUTOMÁTICA DE ÍNDICES';
    PRINT 'Data/Hora: ' + CONVERT(NVARCHAR, GETDATE(), 121);
    PRINT '=====================================================';
    
    -- Contar total de índices a serem processados
    SELECT @TotalIndexes = COUNT(*)
    FROM sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, 'SAMPLED') ips
        INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
        INNER JOIN sys.objects o ON o.object_id = i.object_id
    WHERE avg_fragmentation_in_percent > 5
        AND ips.page_count > 100
        AND i.type_desc NOT IN ('XML', 'SPATIAL', 'FULLTEXT')
        AND i.is_disabled = 0;
        
    PRINT 'Total de índices a serem processados: ' + CAST(@TotalIndexes AS NVARCHAR(10));
    PRINT '';
    
    -- Cursor para iterar sobre índices fragmentados
    DECLARE IndexCursor CURSOR FOR
    SELECT 
        SCHEMA_NAME(o.schema_id) AS SchemaName,
        OBJECT_NAME(ips.object_id) AS TableName,
        i.name AS IndexName,
        ips.index_id,
        ips.avg_fragmentation_in_percent
    FROM 
        sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, 'SAMPLED') ips
        INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
        INNER JOIN sys.objects o ON o.object_id = i.object_id
    WHERE 
        avg_fragmentation_in_percent > 5
        AND ips.page_count > 100
        AND i.type_desc NOT IN ('XML', 'SPATIAL', 'FULLTEXT')
        AND i.is_disabled = 0
    ORDER BY 
        avg_fragmentation_in_percent DESC;
        
    OPEN IndexCursor;
    FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @ProcessedIndexes = @ProcessedIndexes + 1;
        
        -- Captura o horário de início do servidor
        SET @StartTime = SYSDATETIMEOFFSET();
        
        BEGIN TRANSACTION;
        BEGIN TRY
            IF @Fragmentation >= 30
            BEGIN
                -- Rebuild Index para fragmentação >= 30%
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REBUILD WITH (ONLINE = OFF, MAXDOP = 1);';
                PRINT '[' + CAST(@ProcessedIndexes AS NVARCHAR(10)) + '/' + CAST(@TotalIndexes AS NVARCHAR(10)) + '] REBUILD - Fragmentation: ' + CAST(ROUND(@Fragmentation, 2) AS NVARCHAR(10)) + '%';
            END
            ELSE IF @Fragmentation >= 5 AND @Fragmentation < 30
            BEGIN
                -- Reorganize Index para fragmentação entre 5% e 30%
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REORGANIZE;';
                PRINT '[' + CAST(@ProcessedIndexes AS NVARCHAR(10)) + '/' + CAST(@TotalIndexes AS NVARCHAR(10)) + '] REORGANIZE - Fragmentation: ' + CAST(ROUND(@Fragmentation, 2) AS NVARCHAR(10)) + '%';
            END
            
            -- Executa o comando
            EXEC sp_executesql @SQL;
            
            -- Captura o horário de término do servidor
            SET @EndTime = SYSDATETIMEOFFSET();
            
            -- Calcula o tempo decorrido
            SET @ElapsedTime = CONVERT(NVARCHAR(50), DATEDIFF(SECOND, @StartTime, @EndTime)) + ' seconds';
            
            -- Imprime os resultados
            PRINT 'Table: [' + @SchemaName + '].[' + @TableName + '] | Index: [' + @IndexName + ']';
            PRINT 'Start: ' + CONVERT(NVARCHAR, @StartTime, 121) + ' | End: ' + CONVERT(NVARCHAR, @EndTime, 121) + ' | Duration: ' + @ElapsedTime;
            PRINT 'SUCCESS: ' + @SQL;
            PRINT '';
            
            -- Commit da transação
            COMMIT TRANSACTION;
            
        END TRY
        BEGIN CATCH
            ROLLBACK TRANSACTION;
            PRINT 'ERRO ao executar: ' + @SQL;
            PRINT 'Error Message: ' + ERROR_MESSAGE();
            PRINT '';
        END CATCH;
        
        FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;
    END;
    
    -- Encerramento do Cursor
    BEGIN TRY
        CLOSE IndexCursor;
        DEALLOCATE IndexCursor;
    END TRY
    BEGIN CATCH
        IF CURSOR_STATUS('global', 'IndexCursor') >= 0
        BEGIN
            CLOSE IndexCursor;
            DEALLOCATE IndexCursor;
        END
    END CATCH;
    
    PRINT '=====================================================';
    PRINT 'MANUTENÇÃO DE ÍNDICES CONCLUÍDA';
    PRINT 'Total processado: ' + CAST(@ProcessedIndexes AS NVARCHAR(10)) + ' índices';
    PRINT 'Data/Hora Fim: ' + CONVERT(NVARCHAR, GETDATE(), 121);
    PRINT '=====================================================';
    
END;
GO

-- =====================================================
-- COMO EXECUTAR A PROCEDURE:
-- =====================================================
-- EXEC dbo.MaintainIndexes;

-- =====================================================
-- AGENDAR NO SQL SERVER AGENT (EXEMPLO):
-- =====================================================
/*
1. Abra o SQL Server Management Studio
2. Conecte no SQL Server Agent
3. Clique com botão direito em "Jobs" → "New Job"
4. Nome: "Manutenção Automática de Índices - TOTVS"
5. Na aba "Steps":
   - Step name: "Executar MaintainIndexes"
   - Type: "Transact-SQL script (T-SQL)"
   - Database: TOTVS2310
   - Command: EXEC dbo.MaintainIndexes;
6. Na aba "Schedules":
   - Schedule: "Semanalmente aos domingos às 02:00"
   - Frequency: Weekly, Sundays
*/`
    },

    'update_statistics_procedure': {
      category: 'protheus',
      name: 'Procedure Atualizar Estatísticas',
      description: 'Stored procedure para atualização de estatísticas',
      script: `-- =====================================================
-- STORED PROCEDURE - ATUALIZAÇÃO DE ESTATÍSTICAS
-- =====================================================
USE [TOTVS2310]
GO
CREATE OR ALTER PROCEDURE [dbo].[UpdateStatistics]
    @SamplePercent INT = 20,  -- Percentual de amostragem (padrão 20%)
    @TablesFilter NVARCHAR(50) = NULL  -- Filtro de tabelas (opcional)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @SchemaName NVARCHAR(256);
    DECLARE @TableName NVARCHAR(256);
    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @StartTime DATETIMEOFFSET;
    DECLARE @EndTime DATETIMEOFFSET;
    DECLARE @ElapsedTime NVARCHAR(50);
    DECLARE @TotalTables INT = 0;
    DECLARE @ProcessedTables INT = 0;
    
    PRINT '=====================================================';
    PRINT 'INICIANDO ATUALIZAÇÃO DE ESTATÍSTICAS';
    PRINT 'Data/Hora: ' + CONVERT(NVARCHAR, GETDATE(), 121);
    PRINT 'Sample Percent: ' + CAST(@SamplePercent AS NVARCHAR(10)) + '%';
    IF @TablesFilter IS NOT NULL
        PRINT 'Filtro de Tabelas: ' + @TablesFilter;
    PRINT '=====================================================';
    
    -- Contar total de tabelas
    SELECT @TotalTables = COUNT(*)
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE (@TablesFilter IS NULL OR t.name LIKE '%' + @TablesFilter + '%')
        AND t.type = 'U'  -- User tables only
        AND t.is_ms_shipped = 0;  -- Exclude system tables
    
    PRINT 'Total de tabelas a serem processadas: ' + CAST(@TotalTables AS NVARCHAR(10));
    PRINT '';
    
    -- Cursor para iterar sobre todas as tabelas
    DECLARE StatsCursor CURSOR FOR
    SELECT 
        s.name AS SchemaName,
        t.name AS TableName
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE (@TablesFilter IS NULL OR t.name LIKE '%' + @TablesFilter + '%')
        AND t.type = 'U'
        AND t.is_ms_shipped = 0
    ORDER BY t.name;
    
    OPEN StatsCursor;
    FETCH NEXT FROM StatsCursor INTO @SchemaName, @TableName;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @ProcessedTables = @ProcessedTables + 1;
        SET @StartTime = SYSDATETIMEOFFSET();
        
        BEGIN TRY
            -- Construir comando UPDATE STATISTICS
            SET @SQL = 'UPDATE STATISTICS [' + @SchemaName + '].[' + @TableName + '] WITH SAMPLE ' + CAST(@SamplePercent AS NVARCHAR(10)) + ' PERCENT;';
            
            -- Executar o comando
            EXEC sp_executesql @SQL;
            
            SET @EndTime = SYSDATETIMEOFFSET();
            SET @ElapsedTime = CONVERT(NVARCHAR(50), DATEDIFF(MILLISECOND, @StartTime, @EndTime)) + ' ms';
            
            PRINT '[' + CAST(@ProcessedTables AS NVARCHAR(10)) + '/' + CAST(@TotalTables AS NVARCHAR(10)) + '] SUCCESS: [' + @SchemaName + '].[' + @TableName + '] - ' + @ElapsedTime;
            
        END TRY
        BEGIN CATCH
            PRINT '[' + CAST(@ProcessedTables AS NVARCHAR(10)) + '/' + CAST(@TotalTables AS NVARCHAR(10)) + '] ERROR: [' + @SchemaName + '].[' + @TableName + '] - ' + ERROR_MESSAGE();
        END CATCH;
        
        FETCH NEXT FROM StatsCursor INTO @SchemaName, @TableName;
    END;
    
    CLOSE StatsCursor;
    DEALLOCATE StatsCursor;
    
    PRINT '';
    PRINT '=====================================================';
    PRINT 'ATUALIZAÇÃO DE ESTATÍSTICAS CONCLUÍDA';
    PRINT 'Total processado: ' + CAST(@ProcessedTables AS NVARCHAR(10)) + ' tabelas';
    PRINT 'Data/Hora Fim: ' + CONVERT(NVARCHAR, GETDATE(), 121);
    PRINT '=====================================================';
    
END;
GO

-- =====================================================
-- EXEMPLOS DE USO:
-- =====================================================
-- Atualizar todas as tabelas com 20% de amostragem:
-- EXEC dbo.UpdateStatistics;

-- Atualizar apenas tabelas que começam com 'SA' com 30% de amostragem:
-- EXEC dbo.UpdateStatistics @SamplePercent = 30, @TablesFilter = 'SA';

-- Atualizar tabelas do Protheus (que terminam com números) com 15% de amostragem:
-- EXEC dbo.UpdateStatistics @SamplePercent = 15, @TablesFilter = '%[0-9][0-9][0-9]';`
    },

    // Queries específicas do Protheus (mantidas mas simplificadas)
    'protheus_queries': {
      category: 'queries',
      name: 'Queries do Protheus',
      description: 'Análise específica de queries ERP',
      script: `-- =====================================================
-- QUERIES ESPECÍFICAS DO PROTHEUS
-- =====================================================
SELECT 
    qs.execution_count,
    qs.total_elapsed_time / 1000 as total_elapsed_time_ms,
    qs.total_elapsed_time / qs.execution_count / 1000 as avg_elapsed_time_ms,
    qs.total_worker_time / qs.execution_count / 1000 as avg_cpu_time_ms,
    qs.total_logical_reads / qs.execution_count as avg_logical_reads,
    qs.creation_time,
    qs.last_execution_time,
    -- Categorizar por tipo de query Protheus
    CASE 
        WHEN st.text LIKE '%RetSqlName("SA1")%' THEN 'Clientes (SA1)'
        WHEN st.text LIKE '%RetSqlName("SA2")%' THEN 'Fornecedores (SA2)'
        WHEN st.text LIKE '%RetSqlName("SB1")%' THEN 'Produtos (SB1)'
        WHEN st.text LIKE '%RetSqlName("SC5")%' THEN 'Pedidos Venda (SC5)'
        WHEN st.text LIKE '%RetSqlName("SC6")%' THEN 'Itens Pedido (SC6)'
        WHEN st.text LIKE '%RetSqlName("SC7")%' THEN 'Pedidos Compra (SC7)'
        WHEN st.text LIKE '%RetSqlName("SD1")%' THEN 'Itens NF Entrada (SD1)'
        WHEN st.text LIKE '%RetSqlName("SD2")%' THEN 'Itens NF Saída (SD2)'
        WHEN st.text LIKE '%RetSqlName("SE1")%' THEN 'Contas Receber (SE1)'
        WHEN st.text LIKE '%RetSqlName("SE2")%' THEN 'Contas Pagar (SE2)'
        WHEN st.text LIKE '%RetSqlName("SF1")%' THEN 'NF Entrada (SF1)'
        WHEN st.text LIKE '%RetSqlName("SF2")%' THEN 'NF Saída (SF2)'
        WHEN st.text LIKE '%RetSqlName%' THEN 'Outras Tabelas Protheus'
        ELSE 'Query Não-Protheus'
    END as protheus_table_type,
    -- Verificar boas práticas
    CASE 
        WHEN st.text NOT LIKE '%D_E_L_E_T_ = '' ''%' THEN 'ERRO: Falta filtro D_E_L_E_T_'
        WHEN st.text NOT LIKE '%xFilial%' AND st.text NOT LIKE '%FWxFilial%' THEN 'AVISO: Falta filtro xFilial'
        WHEN st.text LIKE '%SELECT *%' THEN 'AVISO: Usando SELECT *'
        ELSE 'OK'
    END as best_practices_check,
    LEFT(REPLACE(REPLACE(st.text, CHAR(13), ' '), CHAR(10), ' '), 200) as query_preview
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE (st.text LIKE '%RetSqlName%' 
    OR st.text LIKE '%D_E_L_E_T_%' 
    OR st.text LIKE '%xFilial%'
    OR st.text LIKE '%FWxFilial%')
    AND qs.last_execution_time > DATEADD(HOUR, -2, GETDATE())
ORDER BY qs.total_elapsed_time / qs.execution_count DESC;`
    }
  };

  const toggleDiagnostic = (diagnosticId) => {
    setSelectedDiagnostics(prev => 
      prev.includes(diagnosticId) 
        ? prev.filter(id => id !== diagnosticId)
        : [...prev, diagnosticId]
    );
  };

  const generateScript = () => {
    if (selectedDiagnostics.length === 0) {
      alert('Selecione pelo menos um diagnóstico!');
      return;
    }

    let script = `-- =====================================================
-- SCRIPT DE DIAGNÓSTICO SQL SERVER - ERP PROTHEUS
-- Gerado em: ${new Date().toLocaleString('pt-BR')}
-- Diagnósticos selecionados: ${selectedDiagnostics.length}
-- =====================================================

`;

    selectedDiagnostics.forEach((diagnosticId, index) => {
      const diagnostic = diagnosticScripts[diagnosticId];
      script += diagnostic.script;
      
      if (index < selectedDiagnostics.length - 1) {
        script += '\n\n';
      }
    });

    script += `

-- =====================================================
-- FIM DO SCRIPT DE DIAGNÓSTICO
-- =====================================================
-- DICAS DE USO:
-- 1. Execute em ambiente de PRODUÇÃO com cuidado
-- 2. Horários recomendados: após horário comercial
-- 3. Monitore o impacto durante a execução
-- 4. Salve os resultados para análise histórica
-- =====================================================`;

    setGeneratedScript(script);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedScript);
    alert('Script copiado para a área de transferência!');
  };

  const downloadScript = () => {
    const element = document.createElement('a');
    const file = new Blob([generatedScript], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `diagnostico_sqlserver_${new Date().toISOString().slice(0,10)}.sql`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const selectAllInCategory = () => {
    const categoryDiagnostics = Object.keys(diagnosticScripts).filter(
      key => diagnosticScripts[key].category === activeCategory
    );
    setSelectedDiagnostics(prev => [...new Set([...prev, ...categoryDiagnostics])]);
  };

  const clearSelection = () => {
    setSelectedDiagnostics([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Database className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-800">Gerador de Diagnóstico SQL Server</h1>
          </div>
          <p className="text-gray-600 text-lg">
            🚀 Gere scripts personalizados para diagnosticar performance do ERP Protheus
          </p>
        </div>

        {/* Category Tabs */}
        <div className="bg-white rounded-lg shadow-lg mb-6 p-2">
          <div className="flex flex-wrap gap-2">
            {Object.entries(diagnosticCategories).map(([key, category]) => (
              <button
                key={key}
                onClick={() => setActiveCategory(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeCategory === key
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-blue-600 hover:bg-blue-50'
                }`}
              >
                {category.icon}
                {category.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Diagnostic Selection */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-800">
                  {diagnosticCategories[activeCategory].name}
                </h3>
                <p className="text-sm text-gray-600">
                  {diagnosticCategories[activeCategory].description}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={selectAllInCategory}
                  className="text-sm bg-blue-100 text-blue-600 px-3 py-1 rounded hover:bg-blue-200 transition-colors"
                >
                  Selecionar Todos
                </button>
                <button
                  onClick={clearSelection}
                  className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded hover:bg-gray-200 transition-colors"
                >
                  Limpar
                </button>
              </div>
            </div>

            <div className="grid gap-3">
              {Object.entries(diagnosticScripts)
                .filter(([_, diagnostic]) => diagnostic.category === activeCategory)
                .map(([key, diagnostic]) => (
                  <div
                    key={key}
                    onClick={() => toggleDiagnostic(key)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedDiagnostics.includes(key)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">{diagnostic.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{diagnostic.description}</p>
                      </div>
                      <div className={`w-5 h-5 rounded border-2 ml-3 ${
                        selectedDiagnostics.includes(key)
                          ? 'bg-blue-500 border-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedDiagnostics.includes(key) && (
                          <div className="w-full h-full flex items-center justify-center text-white text-xs">
                            ✓
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Summary and Generate */}
          <div className="space-y-6">
            {/* Selection Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Diagnósticos Selecionados ({selectedDiagnostics.length})
              </h3>
              
              {selectedDiagnostics.length === 0 ? (
                <p className="text-gray-500 text-sm">Nenhum diagnóstico selecionado</p>
              ) : (
                <div className="space-y-2">
                  {selectedDiagnostics.map(diagnosticId => {
                    const diagnostic = diagnosticScripts[diagnosticId];
                    return (
                      <div key={diagnosticId} className="flex items-center gap-2 text-sm">
                        <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                        <span className="text-gray-700">{diagnostic.name}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              <button
                onClick={generateScript}
                disabled={selectedDiagnostics.length === 0}
                className="w-full mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Code2 className="w-5 h-5 inline mr-2" />
                Gerar Script SQL
              </button>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Ações Rápidas</h3>
              
              <div className="space-y-3">
                <button
                  onClick={() => {
                    setSelectedDiagnostics(['cpu_usage', 'wait_stats', 'active_blocks']);
                    setActiveCategory('performance');
                  }}
                  className="w-full text-left p-3 rounded-lg border border-orange-200 hover:bg-orange-50 transition-colors"
                >
                  <div className="font-medium text-orange-800">🔥 Performance Crítica</div>
                  <div className="text-xs text-orange-600">CPU + Wait Stats + Bloqueios</div>
                </button>

                <button
                  onClick={() => {
                    setSelectedDiagnostics(['maintain_indexes_procedure', 'update_statistics_procedure']);
                    setActiveCategory('protheus');
                  }}
                  className="w-full text-left p-3 rounded-lg border border-blue-200 hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-blue-800">⚡ Procedures Manutenção</div>
                  <div className="text-xs text-blue-600">Índices + Estatísticas</div>
                </button>

                <button
                  onClick={() => {
                    setSelectedDiagnostics(['index_fragmentation', 'active_connections']);
                    setActiveCategory('maintenance');
                  }}
                  className="w-full text-left p-3 rounded-lg border border-green-200 hover:bg-green-50 transition-colors"
                >
                  <div className="font-medium text-green-800">🔧 Manutenção DB</div>
                  <div className="text-xs text-green-600">Índices + Conexões</div>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Generated Script */}
        {generatedScript && (
          <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Script Gerado</h3>
              <div className="flex gap-2">
                <button
                  onClick={copyToClipboard}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Copy className="w-4 h-4 inline mr-2" />
                  Copiar
                </button>
                <button
                  onClick={downloadScript}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Download className="w-4 h-4 inline mr-2" />
                  Download
                </button>
              </div>
            </div>
            
            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-96">
              <pre className="text-green-400 text-xs font-mono whitespace-pre-wrap">
                {generatedScript}
              </pre>
            </div>

            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-2">⚠️ Cuidados ao Executar:</h4>
              <ul className="text-yellow-700 text-sm space-y-1">
                <li>• Execute preferencialmente fora do horário comercial</li>
                <li>• Monitore o impacto no sistema durante a execução</li>
                <li>• Salve os resultados para análise histórica</li>
                <li>• Queries de diagnóstico podem consumir recursos</li>
                <li>• Teste primeiro em ambiente de homologação</li>
              </ul>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8 text-gray-600">
          <p>🚀 Scripts baseados em DMVs do SQL Server para ambiente Protheus</p>
          <p className="text-sm mt-1">Use com responsabilidade em ambiente de produção!</p>
        </div>
      </div>
    </div>
  );
};

export default SQLDiagnosticGenerator;
