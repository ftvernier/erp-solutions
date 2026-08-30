ALTER PROCEDURE [dbo].[MaintainIndexes]
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @SchemaName NVARCHAR(256);
    DECLARE @TableName NVARCHAR(256);
    DECLARE @IndexName NVARCHAR(256);
    DECLARE @IndexID INT;
    DECLARE @Fragmentation FLOAT;
    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @StartTime DATETIMEOFFSET;
    DECLARE @EndTime DATETIMEOFFSET;
    DECLARE @ElapsedTime NVARCHAR(50);
    DECLARE @LogMessage NVARCHAR(4000);

    -- Cursor para mapear os índices que precisam de manutenção
    -- Utilizando o modo 'LIMITED' para máxima performance
    DECLARE IndexCursor CURSOR LOCAL FAST_FORWARD FOR
    SELECT 
        SCHEMA_NAME(o.schema_id) AS SchemaName,
        OBJECT_NAME(ips.object_id) AS TableName,
        i.name AS IndexName,
        ips.index_id,
        ips.avg_fragmentation_in_percent
    FROM 
        sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
        INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
        INNER JOIN sys.objects o ON o.object_id = i.object_id
    WHERE 
        avg_fragmentation_in_percent > 5
        AND ips.page_count > 1000 -- Melhoria: Aumentado de 100 para 1000 páginas (8MB)
        AND i.type_desc NOT IN ('XML', 'SPATIAL', 'FULLTEXT')
        AND i.is_disabled = 0
        -- EXCLUSÃO DAS TABELAS SYS_ DO PROTHEUS (Dicionário de dados estático)
        AND OBJECT_NAME(ips.object_id) NOT LIKE 'SYS[_]%'
    ORDER BY 
        avg_fragmentation_in_percent DESC;

    OPEN IndexCursor;
    FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @StartTime = SYSDATETIMEOFFSET();

        BEGIN TRY
            -- Fragmentação Alta (>= 30%): REBUILD
            -- Melhoria: Adicionado MAXDOP (Ajuste o número conforme a arquitetura do seu servidor, 2 ou 4 é recomendado)
            IF @Fragmentation >= 30
            BEGIN
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REBUILD WITH (SORT_IN_TEMPDB = ON, MAXDOP = 4);';
                EXEC sp_executesql @SQL;
            END
            
            -- Fragmentação Leve/Moderada (5% a 29.9%): REORGANIZE
            ELSE IF @Fragmentation >= 5 AND @Fragmentation < 30
            BEGIN
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REORGANIZE;';
                EXEC sp_executesql @SQL;
                
                -- Atualização de estatísticas do índice após o REORGANIZE
                SET @SQL = 'UPDATE STATISTICS [' + @SchemaName + '].[' + @TableName + '] [' + @IndexName + '];';
                EXEC sp_executesql @SQL;
            END

            SET @EndTime = SYSDATETIMEOFFSET();
            SET @ElapsedTime = CONVERT(NVARCHAR(50), DATEDIFF(SECOND, @StartTime, @EndTime)) + ' seconds';

            -- Melhoria: RAISERROR WITH NOWAIT envia o log imediatamente no SQL Agent
            SET @LogMessage = 'Executed: ' + @SQL + ' | Elapsed Time: ' + @ElapsedTime;
            RAISERROR(@LogMessage, 0, 1) WITH NOWAIT;

        END TRY
        BEGIN CATCH
            SET @LogMessage = 'Erro no índice ' + @IndexName + ' (Tabela ' + @TableName + '): ' + ERROR_MESSAGE();
            RAISERROR(@LogMessage, 0, 1) WITH NOWAIT;
        END CATCH;

        FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;
    END;

    -- Fechamento seguro do Cursor (FAST_FORWARD remove a necessidade de validações complexas no fechamento)
    IF CURSOR_STATUS('local', 'IndexCursor') >= 0
    BEGIN
        CLOSE IndexCursor;
        DEALLOCATE IndexCursor;
    END
END;
