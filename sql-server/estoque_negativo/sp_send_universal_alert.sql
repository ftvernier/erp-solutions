-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: sp_send_universal_alert.sql
-- Descrição: Procedure principal que gerencia todos os canais
-- =============================================

USE [SEU BANCO]
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_send_universal_alert]
    @B2_COD NVARCHAR(50),
    @B2_QATU FLOAT,
    @USERNAME NVARCHAR(100),
    @MACHINE_NAME NVARCHAR(100) = 'Sistema',
    @CLIENT_IP NVARCHAR(50) = 'N/A'
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartTime DATETIME = GETDATE();
    DECLARE @LogID INT;
    
    BEGIN TRY
        PRINT '🚀 Iniciando envio de alerta universal...';
        PRINT '📦 Produto: ' + @B2_COD + ' | Estoque: ' + CAST(@B2_QATU AS NVARCHAR);
        
        -- Cursor para processar todos os canais ativos
        DECLARE @ALERT_TYPE VARCHAR(20);
        DECLARE @WEBHOOK_URL NVARCHAR(500);
        DECLARE @EMAIL_TO NVARCHAR(255);
        DECLARE @EMAIL_PROFILE VARCHAR(100);
        DECLARE @CHAT_ID VARCHAR(50);
        DECLARE @BOT_TOKEN VARCHAR(200);
        
        DECLARE alert_channels_cursor CURSOR LOCAL FAST_FORWARD FOR
        SELECT 
            ALERT_TYPE, 
            WEBHOOK_URL, 
            EMAIL_TO, 
            EMAIL_PROFILE,
            CHAT_ID,
            BOT_TOKEN
        FROM ALERT_CONFIG 
        WHERE IS_ACTIVE = 1
        ORDER BY 
            CASE ALERT_TYPE 
                WHEN 'EMAIL' THEN 1 
                WHEN 'TEAMS' THEN 2 
                WHEN 'SLACK' THEN 3 
                WHEN 'TELEGRAM' THEN 4 
                ELSE 5 
            END;
        
        OPEN alert_channels_cursor;
        FETCH NEXT FROM alert_channels_cursor INTO 
            @ALERT_TYPE, @WEBHOOK_URL, @EMAIL_TO, @EMAIL_PROFILE, @CHAT_ID, @BOT_TOKEN;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Inserir log inicial
            INSERT INTO SB2010_ALERT_LOG 
            (B2_COD, B2_QATU, ALERT_DATE, USERNAME, MACHINE_NAME, CLIENT_IP, ALERT_TYPE, STATUS)
            VALUES 
            (@B2_COD, @B2_QATU, GETDATE(), @USERNAME, @MACHINE_NAME, @CLIENT_IP, @ALERT_TYPE, 'SENDING');
            
            SET @LogID = SCOPE_IDENTITY();
            
            PRINT '📤 Enviando via ' + @ALERT_TYPE + '...';
            
            -- Chamar procedure específica baseada no tipo
            IF @ALERT_TYPE = 'EMAIL'
            BEGIN
                EXEC [dbo].[sp_send_email_alert] 
                    @B2_COD, @B2_QATU, @USERNAME, @MACHINE_NAME, @CLIENT_IP, @EMAIL_TO, @EMAIL_PROFILE, @LogID;
            END
            ELSE IF @ALERT_TYPE = 'TEAMS'
            BEGIN
                EXEC [dbo].[sp_send_teams_alert] 
                    @B2_COD, @B2_QATU, @USERNAME, @MACHINE_NAME, @CLIENT_IP, @WEBHOOK_URL, @LogID;
            END
            ELSE IF @ALERT_TYPE = 'SLACK'
            BEGIN
                EXEC [dbo].[sp_send_slack_alert] 
                    @B2_COD, @B2_QATU, @USERNAME, @MACHINE_NAME, @CLIENT_IP, @WEBHOOK_URL, @LogID;
            END
            ELSE IF @ALERT_TYPE = 'TELEGRAM'
            BEGIN
                EXEC [dbo].[sp_send_telegram_alert] 
                    @B2_COD, @B2_QATU, @USERNAME, @MACHINE_NAME, @CLIENT_IP, @BOT_TOKEN, @CHAT_ID, @LogID;
            END
            ELSE IF @ALERT_TYPE = 'WEBHOOK'
            BEGIN
                EXEC [dbo].[sp_send_webhook_alert] 
                    @B2_COD, @B2_QATU, @USERNAME, @MACHINE_NAME, @CLIENT_IP, @WEBHOOK_URL, @LogID;
            END
            ELSE
            BEGIN
                -- Tipo não suportado
                UPDATE SB2010_ALERT_LOG 
                SET STATUS = 'ERROR', 
                    ERROR_MESSAGE = 'Tipo de alerta não suportado: ' + @ALERT_TYPE,
                    RESPONSE_TIME_MS = DATEDIFF(ms, @StartTime, GETDATE())
                WHERE ID = @LogID;
                
                PRINT '❌ Tipo não suportado: ' + @ALERT_TYPE;
            END
            
            FETCH NEXT FROM alert_channels_cursor INTO 
                @ALERT_TYPE, @WEBHOOK_URL, @EMAIL_TO, @EMAIL_PROFILE, @CHAT_ID, @BOT_TOKEN;
        END;
        
        CLOSE alert_channels_cursor;
        DEALLOCATE alert_channels_cursor;
        
        PRINT '✅ Processo de alerta universal concluído!';
        
    END TRY
    BEGIN CATCH
        -- Limpeza do cursor em caso de erro
        IF CURSOR_STATUS('local', 'alert_channels_cursor') >= 0
        BEGIN
            CLOSE alert_channels_cursor;
            DEALLOCATE alert_channels_cursor;
        END
        
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorProcedure NVARCHAR(128) = ERROR_PROCEDURE();
        DECLARE @ErrorLine INT = ERROR_LINE();
        
        PRINT '❌ Erro na procedure universal: ' + @ErrorMessage;
        
        -- Log do erro
        BEGIN TRY
            INSERT INTO SB2010_ERROR_LOG 
            (ERROR_DATE, ERROR_MESSAGE, ERROR_PROCEDURE, ERROR_LINE, USERNAME, ADDITIONAL_INFO)
            VALUES 
            (GETDATE(), @ErrorMessage, @ErrorProcedure, @ErrorLine, @USERNAME, 
             'Produto: ' + @B2_COD + ' | Estoque: ' + CAST(@B2_QATU AS NVARCHAR));
        END TRY
        BEGIN CATCH
            PRINT '❌ Falha ao gravar log de erro: ' + ERROR_MESSAGE();
        END CATCH
        
        -- Atualizar log se existir
        IF @LogID IS NOT NULL
        BEGIN
            UPDATE SB2010_ALERT_LOG 
            SET STATUS = 'ERROR', 
                ERROR_MESSAGE = @ErrorMessage,
                RESPONSE_TIME_MS = DATEDIFF(ms, @StartTime, GETDATE())
            WHERE ID = @LogID;
        END
    END CATCH
END;
GO

PRINT '✅ Procedure sp_send_universal_alert criada com sucesso!';
