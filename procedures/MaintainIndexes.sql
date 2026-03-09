USE [SEU_BANCO]
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

    DECLARE @SchemaName NVARCHAR(256);
    DECLARE @TableName NVARCHAR(256);
    DECLARE @IndexName NVARCHAR(256);
    DECLARE @IndexID INT;
    DECLARE @Fragmentation FLOAT;
    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @StartTime DATETIMEOFFSET;
    DECLARE @EndTime DATETIMEOFFSET;
    DECLARE @ElapsedTime NVARCHAR(50);

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
        --EXCLUSÃO DAS TABELAS SYS_ DO PROTHEUS
        AND OBJECT_NAME(ips.object_id) NOT LIKE 'SYS[_]%'
    ORDER BY 
        avg_fragmentation_in_percent DESC;

    OPEN IndexCursor;
    FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @StartTime = SYSDATETIMEOFFSET();

        BEGIN TRANSACTION;
        BEGIN TRY
            IF @Fragmentation >= 30
            BEGIN
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REBUILD;';
            END
            ELSE IF @Fragmentation >= 5 AND @Fragmentation < 30
            BEGIN
                SET @SQL = 'ALTER INDEX [' + @IndexName + '] ON [' + @SchemaName + '].[' + @TableName + '] REORGANIZE;';
            END

            EXEC sp_executesql @SQL;

            SET @EndTime = SYSDATETIMEOFFSET();
            SET @ElapsedTime = CONVERT(NVARCHAR(50), DATEDIFF(SECOND, @StartTime, @EndTime)) + ' seconds';

            PRINT 'Executed: ' + @SQL + ' | Start Time: ' + CONVERT(NVARCHAR, @StartTime, 121) +
                  ' | End Time: ' + CONVERT(NVARCHAR, @EndTime, 121) +
                  ' | Elapsed Time: ' + @ElapsedTime;

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            ROLLBACK TRANSACTION;
            PRINT 'Erro ao executar: ' + @SQL;
        END CATCH;

        FETCH NEXT FROM IndexCursor INTO @SchemaName, @TableName, @IndexName, @IndexID, @Fragmentation;
    END;

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
