/* ==========================================================================
   Protheus e o banco de dados - scripts de diagnostico (SQL Server)
   Fernando Vernier - github.com/ftvernier/erp-solutions

   Scripts de leitura, salvo indicacao em contrario no proprio bloco.
   Rode primeiro em homologacao. Troque nomes de tabela/banco pelos do seu ambiente.
   ========================================================================== */

-- ==========================================================================
-- [S01] Estrutura fisica de uma tabela do Protheus
SELECT c.name AS coluna, t.name AS tipo, c.max_length AS tamanho,
       c.is_nullable AS aceita_nulo, dc.definition AS valor_padrao
FROM sys.columns c
JOIN sys.types t ON t.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
WHERE c.object_id = OBJECT_ID('dbo.SE1010')
ORDER BY c.column_id;
GO

-- ==========================================================================
-- [S02] Indices de uma tabela e suas colunas, na ordem da chave
SELECT i.name AS indice, i.type_desc AS tipo, i.is_unique AS unico,
       STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS colunas
FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE i.object_id = OBJECT_ID('dbo.SE1010')
  AND ic.is_included_column = 0
GROUP BY i.name, i.type_desc, i.is_unique
ORDER BY i.name;
GO

-- ==========================================================================
-- [S03] Criacao idempotente de indice de cobertura (ALTERA o banco: use janela)
IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE object_id = OBJECT_ID('dbo.SE1010')
                 AND name = 'IXC_SE1010_VENCREA')
BEGIN
    CREATE NONCLUSTERED INDEX IXC_SE1010_VENCREA
        ON dbo.SE1010 (E1_FILIAL, E1_VENCREA)
        INCLUDE (E1_CLIENTE, E1_LOJA, E1_PREFIXO, E1_NUM, E1_PARCELA,
                 E1_TIPO, E1_SALDO, D_E_L_E_T_)
        WITH (ONLINE = ON);   -- somente na edicao Enterprise; remova na Standard
END
GO

-- ==========================================================================
-- [S04] Indices que o otimizador sentiu falta (sugestoes, nao ordens)
SELECT TOP (20)
       OBJECT_NAME(d.object_id, d.database_id) AS tabela,
       d.equality_columns   AS colunas_igualdade,
       d.inequality_columns AS colunas_faixa,
       d.included_columns   AS colunas_incluidas,
       s.user_seeks         AS vezes_que_ajudaria,
       s.avg_user_impact    AS melhora_estimada_pct,
       CAST(s.user_seeks * s.avg_total_user_cost * s.avg_user_impact / 100.0
            AS BIGINT)      AS pontuacao
FROM sys.dm_db_missing_index_details d
JOIN sys.dm_db_missing_index_groups g       ON g.index_handle = d.index_handle
JOIN sys.dm_db_missing_index_group_stats s  ON s.group_handle = g.index_group_handle
WHERE d.database_id = DB_ID()
ORDER BY pontuacao DESC;
GO

-- ==========================================================================
-- [S05] Uso real dos indices: muito gravados e pouco lidos
SELECT OBJECT_NAME(i.object_id) AS tabela, i.name AS indice,
       ISNULL(u.user_seeks, 0) + ISNULL(u.user_scans, 0)
         + ISNULL(u.user_lookups, 0) AS leituras,
       ISNULL(u.user_updates, 0)     AS gravacoes
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats u
       ON u.object_id = i.object_id AND u.index_id = i.index_id
      AND u.database_id = DB_ID()
WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
  AND i.index_id > 1
ORDER BY gravacoes DESC, leituras ASC;
GO

-- ==========================================================================
-- [S06] Sessoes bloqueadas e por quem
SELECT r.session_id            AS sessao_bloqueada,
       r.blocking_session_id   AS bloqueada_por,
       r.wait_type             AS tipo_espera,
       r.wait_time / 1000      AS espera_s,
       DB_NAME(r.database_id)  AS banco,
       SUBSTRING(t.text, r.statement_start_offset / 2 + 1, 400) AS comando
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.blocking_session_id <> 0
ORDER BY r.wait_time DESC;
GO

-- ==========================================================================
-- [S07] Bloqueadores de topo: quem segura a fila
SELECT s.session_id, s.status, s.open_transaction_count AS transacoes_abertas,
       s.last_request_end_time AS fim_do_ultimo_comando,
       s.host_name, s.program_name,
       t.text AS ultimo_comando
FROM sys.dm_exec_sessions s
JOIN sys.dm_exec_connections c ON c.session_id = s.session_id
CROSS APPLY sys.dm_exec_sql_text(c.most_recent_sql_handle) t
WHERE s.session_id IN (SELECT blocking_session_id FROM sys.dm_exec_requests
                       WHERE blocking_session_id <> 0)
  AND s.session_id NOT IN (SELECT session_id FROM sys.dm_exec_requests
                           WHERE blocking_session_id <> 0);
GO

-- ==========================================================================
-- [S08] Deadlocks recentes registrados pela sessao system_health
SELECT x.ev.value('@timestamp', 'datetime2') AS quando_utc,
       x.ev.query('.')                       AS detalhe_xml
FROM (SELECT CAST(st.target_data AS XML) AS dados
      FROM sys.dm_xe_session_targets st
      JOIN sys.dm_xe_sessions s ON s.address = st.event_session_address
      WHERE s.name = 'system_health' AND st.target_name = 'ring_buffer') d
CROSS APPLY d.dados.nodes('RingBufferTarget/event[@name="xml_deadlock_report"]')
            AS x(ev)
ORDER BY quando_utc DESC;
GO

-- ==========================================================================
-- [S09] Requisicoes em execucao, das mais longas para as mais curtas
SELECT r.session_id, r.status,
       r.total_elapsed_time / 1000 AS duracao_s,
       r.cpu_time                  AS cpu_ms,
       r.logical_reads             AS leituras,
       r.wait_type                 AS esperando_por,
       r.blocking_session_id       AS bloqueada_por,
       SUBSTRING(t.text, r.statement_start_offset / 2 + 1,
                 (CASE r.statement_end_offset
                      WHEN -1 THEN DATALENGTH(t.text)
                      ELSE r.statement_end_offset
                  END - r.statement_start_offset) / 2 + 1) AS comando
FROM sys.dm_exec_requests r
JOIN sys.dm_exec_sessions s ON s.session_id = r.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE s.is_user_process = 1
  AND r.session_id <> @@SPID
ORDER BY r.total_elapsed_time DESC;
GO

-- ==========================================================================
-- [S10] Comandos que mais consumiram leituras desde que entraram no cache
SELECT TOP (20)
       qs.execution_count                              AS execucoes,
       qs.total_logical_reads                          AS leituras_total,
       qs.total_logical_reads / qs.execution_count     AS leituras_media,
       qs.total_elapsed_time / 1000000                 AS duracao_total_s,
       qs.total_elapsed_time / qs.execution_count / 1000 AS duracao_media_ms,
       qs.last_execution_time                          AS ultima_execucao,
       SUBSTRING(t.text, qs.statement_start_offset / 2 + 1, 600) AS comando
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) t
ORDER BY qs.total_logical_reads DESC;
GO

-- ==========================================================================
-- [S11] Query Store: comandos mais caros das ultimas 24 horas
SELECT TOP (20)
       q.query_id,
       SUM(rs.count_executions)                               AS execucoes,
       SUM(rs.avg_duration * rs.count_executions) / 1000000.0 AS duracao_total_s,
       SUM(rs.avg_logical_io_reads * rs.count_executions)     AS leituras_total,
       COUNT(DISTINCT p.plan_id)                              AS planos_diferentes,
       MAX(CAST(qt.query_sql_text AS NVARCHAR(600)))          AS comando
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON qt.query_text_id = q.query_text_id
JOIN sys.query_store_plan p        ON p.query_id = q.query_id
JOIN sys.query_store_runtime_stats rs ON rs.plan_id = p.plan_id
JOIN sys.query_store_runtime_stats_interval i
     ON i.runtime_stats_interval_id = rs.runtime_stats_interval_id
WHERE i.start_time >= DATEADD(HOUR, -24, SYSDATETIMEOFFSET())
GROUP BY q.query_id
ORDER BY duracao_total_s DESC;
GO

-- ==========================================================================
-- [S12] Principais esperas acumuladas desde o ultimo reinicio
SELECT TOP (12)
       wait_type                 AS tipo_espera,
       wait_time_ms / 1000       AS espera_total_s,
       waiting_tasks_count       AS ocorrencias,
       CAST(100.0 * wait_time_ms / SUM(wait_time_ms) OVER () AS DECIMAL(5, 2))
                                 AS pct
FROM sys.dm_os_wait_stats
WHERE waiting_tasks_count > 0
  AND wait_type NOT IN (
      'SLEEP_TASK', 'LAZYWRITER_SLEEP', 'SQLTRACE_BUFFER_FLUSH', 'WAITFOR',
      'LOGMGR_QUEUE', 'CHECKPOINT_QUEUE', 'REQUEST_FOR_DEADLOCK_SEARCH',
      'XE_TIMER_EVENT', 'XE_DISPATCHER_WAIT', 'BROKER_TO_FLUSH',
      'BROKER_TASK_STOP', 'BROKER_EVENTHANDLER', 'CLR_AUTO_EVENT',
      'CLR_MANUAL_EVENT', 'DISPATCHER_QUEUE_SEMAPHORE', 'DIRTY_PAGE_POLL',
      'FT_IFTS_SCHEDULER_IDLE_WAIT', 'SP_SERVER_DIAGNOSTICS_SLEEP',
      'HADR_FILESTREAM_IOMGR_IOCOMPLETION', 'SOS_WORK_DISPATCHER',
      'QDS_PERSIST_TASK_MAIN_LOOP_SLEEP',
      'QDS_CLEANUP_STALE_QUERIES_TASK_MAIN_LOOP_SLEEP')
ORDER BY wait_time_ms DESC;
GO

-- ==========================================================================
-- [S13] Estatisticas com mais modificacoes pendentes
SELECT TOP (30)
       OBJECT_NAME(s.object_id)  AS tabela,
       s.name                    AS estatistica,
       sp.last_updated           AS ultima_atualizacao,
       sp.rows                   AS linhas,
       sp.rows_sampled           AS linhas_amostradas,
       sp.modification_counter   AS modificacoes_pendentes
FROM sys.stats s
CROSS APPLY sys.dm_db_stats_properties(s.object_id, s.stats_id) sp
WHERE OBJECTPROPERTY(s.object_id, 'IsUserTable') = 1
  AND sp.modification_counter > 0
ORDER BY sp.modification_counter DESC;
GO

-- ==========================================================================
-- [S14] Configuracoes de instancia e de banco relevantes para o Protheus
SELECT name AS configuracao, value_in_use AS valor
FROM sys.configurations
WHERE name IN ('max server memory (MB)', 'max degree of parallelism',
               'cost threshold for parallelism',
               'optimize for ad hoc workloads', 'backup compression default');

SELECT name AS banco, compatibility_level, is_read_committed_snapshot_on,
       is_auto_update_stats_on, is_auto_create_stats_on,
       is_query_store_on, page_verify_option_desc
FROM sys.databases
WHERE name = DB_NAME();
GO

-- ==========================================================================
-- [S15] Arquivos da tempdb: quantidade, tamanho e crescimento
SELECT name, type_desc AS tipo, size * 8 / 1024 AS tamanho_mb,
       CASE WHEN is_percent_growth = 1 THEN CAST(growth AS VARCHAR(10)) + ' %'
            ELSE CAST(growth * 8 / 1024 AS VARCHAR(10)) + ' MB' END AS crescimento,
       CASE max_size WHEN -1 THEN 'ilimitado'
            ELSE CAST(CAST(max_size AS BIGINT) * 8 / 1024 AS VARCHAR(20)) + ' MB'
       END AS tamanho_maximo,
       physical_name AS arquivo
FROM tempdb.sys.database_files;
GO

-- ==========================================================================
-- [S16] As 30 maiores tabelas: linhas, dados e indices
SELECT TOP (30)
       t.name AS tabela,
       SUM(CASE WHEN p.index_id IN (0, 1) THEN p.row_count ELSE 0 END) AS linhas,
       SUM(p.reserved_page_count) * 8 / 1024                           AS total_mb,
       SUM(CASE WHEN p.index_id IN (0, 1)
                THEN p.reserved_page_count ELSE 0 END) * 8 / 1024      AS dados_mb,
       SUM(CASE WHEN p.index_id > 1
                THEN p.reserved_page_count ELSE 0 END) * 8 / 1024      AS indices_mb
FROM sys.dm_db_partition_stats p
JOIN sys.tables t ON t.object_id = p.object_id
GROUP BY t.name
ORDER BY total_mb DESC;
GO

-- ==========================================================================
-- [S17] Proporcao de registros logicamente excluidos (le a tabela inteira)
SELECT COUNT(*) AS linhas_total,
       SUM(CASE WHEN D_E_L_E_T_ = '*' THEN 1 ELSE 0 END) AS linhas_excluidas,
       CAST(100.0 * SUM(CASE WHEN D_E_L_E_T_ = '*' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))      AS pct_excluidas
FROM dbo.SC6010;
GO

-- ==========================================================================
-- [S18] Expurgo em lotes (ALTERA dados: backup, janela e aprovacao antes)
DECLARE @linhas INT = 1;

WHILE @linhas > 0
BEGIN
    DELETE TOP (5000)
    FROM dbo.ZZL010
    WHERE ZZL_DATA < '20240101';

    SET @linhas = @@ROWCOUNT;

    WAITFOR DELAY '00:00:01';   -- da espaco para as outras sessoes
END
GO
