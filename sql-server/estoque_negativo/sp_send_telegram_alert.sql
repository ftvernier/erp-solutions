-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: sp_send_telegram_alert.sql
-- Descrição: Procedure para envio de alertas via Telegram
-- =============================================

USE [SEU BANCO]
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_send_telegram_alert]
    @B2_COD NVARCHAR(50),
    @B2_QATU FLOAT,
    @USERNAME NVARCHAR(100),
    @MACHINE_NAME NVARCHAR(100),
    @CLIENT_IP NVARCHAR(50),
    @BOT_TOKEN VARCHAR(200),
    @CHAT_ID VARCHAR(50),
    @LogID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartTime DATETIME = GETDATE();
    
    BEGIN TRY
        DECLARE @json NVARCHAR(MAX);
        DECLARE @Object INT;
        DECLARE @Result INT;
        DECLARE @ResponseText NVARCHAR(MAX);
        DECLARE @telegram_url NVARCHAR(500);
        DECLARE @product_name NVARCHAR(255) = '';
        DECLARE @message_text NVARCHAR(4000);
        
        -- Buscar nome do produto
        SELECT TOP 1 @product_name = B1_DESC 
        FROM SB1010 
        WHERE B1_COD = @B2_COD 
        AND D_E_L_E_T_ = '';
        
        -- Construir URL da API do Telegram
        SET @telegram_url = 'https://api.telegram.org/bot' + @BOT_TOKEN + '/sendMessage';
        
        -- Escape de caracteres especiais para Telegram (MarkdownV2)
        SET @B2_COD = REPLACE(REPLACE(REPLACE(@B2_COD, '_', '\_'), '*', '\*'), '[', '\[');
        SET @USERNAME = REPLACE(REPLACE(REPLACE(@USERNAME, '_', '\_'), '*', '\*'), '[', '\[');
        SET @MACHINE_NAME = REPLACE(REPLACE(REPLACE(@MACHINE_NAME, '_', '\_'), '*', '\*'), '[', '\[');
        SET @product_name = REPLACE(REPLACE(REPLACE(@product_name, '_', '\_'), '*', '\*'), '[', '\[');
        
        -- Montar mensagem formatada
        SET @message_text = '🚨 *ALERTA DE ESTOQUE NEGATIVO*' + CHAR(10) + CHAR(10) +
                           '📦 *Produto:* `' + @B2_COD + '`' + CHAR(10) +
                           '📝 *Descrição:* ' + ISNULL(@product_name, 'Não localizada') + CHAR(10) +
                           '📊 *Quantidade:* `' + CAST(@B2_QATU AS NVARCHAR) + '`' + CHAR(10) +
                           '👤 *Usuário:* ' + @USERNAME + CHAR(10) +
                           '💻 *Máquina:* ' + @MACHINE_NAME + CHAR(10) +
                           '🌐 *IP:* `' + @CLIENT_IP + '`' + CHAR(10) +
                           '🕐 *Data/Hora:* ' + FORMAT(GETDATE(), 'dd/MM/yyyy HH:mm:ss') + CHAR(10) + CHAR(10) +
                           '⚠️ *Ação necessária:* Verificar movimentações e regularizar estoque';
        
        -- Escape final para JSON
        SET @message_text = REPLACE(REPLACE(@message_text, '\', '\\'), '"', '\"');
        
        -- JSON para API do Telegram
        SET @json = '{
            "chat_id": "' + @CHAT_ID + '",
            "text": "' + @message_text + '",
            "parse_mode": "MarkdownV2",
            "disable_notification": false
        }';

        PRINT '📱 Enviando para Telegram...';
        
        -- Criar objeto HTTP
        EXEC sp_OACreate 'MSXML2.ServerXMLHTTP.6.0', @Object OUT;
        
        IF @Object IS NULL
        BEGIN
            RAISERROR('Não foi possível criar objeto HTTP', 16, 1);
            RETURN;
        END

        -- Configurar requisição
        EXEC sp_OAMethod @Object, 'open', NULL, 'POST', @telegram_url, 'false';
        EXEC sp_OAMethod @Object, 'setRequestHeader', NULL, 'Content-Type', 'application/json';
        EXEC sp_OAMethod @Object, 'setRequestHeader', NULL, 'User-Agent', 'TOTVS-Protheus-Alert/1.0';
        
        -- Timeout de 30 segundos
        EXEC sp_OASetProperty @Object, 'timeout', 30000;
        
        -- Enviar requisição
        EXEC sp_OAMethod @Object, 'send', NULL, @json;
        
        -- Verificar status da resposta
        EXEC sp_OAGetProperty @Object, 'status', @Result OUT;
        EXEC sp_OAGetProperty @Object, 'responseText', @ResponseText OUT;
        
        -- Limpeza do objeto
        EXEC sp_OADestroy @Object;
        
        IF @Result = 200
        BEGIN
            PRINT '✅ Alerta enviado com sucesso para Telegram!';
            
            -- Atualizar log como sucesso
            IF @LogID IS NOT NULL
            BEGIN
                UPDATE SB2010_ALERT_LOG 
                SET STATUS = 'SUCCESS',
                    RESPONSE_TIME_MS = DATEDIFF(ms, @StartTime, GETDATE())
                WHERE ID = @LogID;
            END
        END
        ELSE
        BEGIN
            DECLARE @ErrorMsg NVARCHAR(500) = 'HTTP Status: ' + CAST(@Result AS NVARCHAR) + ' - ' + ISNULL(@ResponseText, 'Sem resposta');
            PRINT '❌ Erro no envio - ' + @ErrorMsg;
            
            -- Atualizar log como erro
            IF @LogID IS NOT NULL
            BEGIN
                UPDATE SB2010_ALERT_LOG 
                SET STATUS = 'ERROR',
                    ERROR_MESSAGE = @ErrorMsg,
                    RESPONSE_TIME_MS = DATEDIFF(ms, @StartTime, GETDATE())
                WHERE ID = @LogID;
            END
        END

    END TRY
    BEGIN CATCH
        -- Limpeza do objeto em caso de erro
        IF @Object IS NOT NULL
            EXEC sp_OADestroy @Object;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        PRINT '❌ Erro na procedure Telegram: ' + @ErrorMessage;
        
        -- Atualizar log como erro
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

PRINT '✅ Procedure sp_send_telegram_alert criada com sucesso!';
