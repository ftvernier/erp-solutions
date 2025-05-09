USE [TOTVS2310]
GO
/****** Object:  StoredProcedure [dbo].[MaintainIndexes]    Script Date: 5/9/2025 7:23:19 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[MaintainIndexes]
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
        -- Captura o horário de início do servidor
        SET @StartTime = SYSDATETIMEOFFSET();

        BEGIN TRANSACTION;
        BEGIN TRY
            IF @Fragmentation >= 30
            BEGIN
                -- Rebuild Index
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REBUILD;';
            END
            ELSE IF @Fragmentation >= 5 AND @Fragmentation < 30
            BEGIN
                -- Reorganize Index
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REORGANIZE;';
            END

            -- Executa o comando
            EXEC sp_executesql @SQL;

            -- Captura o horário de término do servidor
            SET @EndTime = SYSDATETIMEOFFSET();

            -- Calcula o tempo decorrido
            SET @ElapsedTime = CONVERT(NVARCHAR(50), DATEDIFF(SECOND, @StartTime, @EndTime)) + ' seconds';

            -- Imprime os resultados
            PRINT 'Executed: ' + @SQL + ' | Start Time: ' + CONVERT(NVARCHAR, @StartTime, 121) +
                  ' | End Time: ' + CONVERT(NVARCHAR, @EndTime, 121) +
                  ' | Elapsed Time: ' + @ElapsedTime;

            -- Commit da transação
            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            ROLLBACK TRANSACTION;
            PRINT 'Erro ao executar: ' + @SQL;
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
END;
