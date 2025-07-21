-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: sp_send_teams_alert.sql
-- Descrição: Procedure para envio de alertas via Microsoft Teams
-- =============================================

USE [SEU BANCO]
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_send_teams_alert]
    @B2_COD NVARCHAR(50),
    @B2_QATU FLOAT,
    @USERNAME NVARCHAR(100),
    @MACHINE_NAME NVARCHAR(100),
    @CLIENT_IP NVARCHAR(50),
    @WEBHOOK_URL NVARCHAR(500),
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
        DECLARE @product_name NVARCHAR(255) = '';
        
        -- Buscar nome do produto
        SELECT TOP 1 @product_name = B1_DESC 
        FROM SB1010 
        WHERE B1_COD = @B2_COD 
        AND D_E_L_E_T_ = '';
        
        -- Escape de caracteres especiais para JSON
        SET @B2_COD = REPLACE(REPLACE(@B2_COD, '\', '\\'), '"', '\"');
        SET @USERNAME = REPLACE(REPLACE(@USERNAME, '\', '\\'), '"', '\"');
        SET @MACHINE_NAME = REPLACE(REPLACE(@MACHINE_NAME, '\', '\\'), '"', '\"');
        SET @product_name = REPLACE(REPLACE(@product_name, '\', '\\'), '"', '\"');
        
        -- JSON no formato Microsoft Teams Adaptive Card
        SET @json = '{
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "dc3545",
            "summary": "Alerta de Estoque Negativo",
            "sections": [{
                "activityTitle": "🚨 **ALERTA DE ESTOQUE NEGATIVO**",
                "activitySubtitle": "Sistema ERP Protheus",
                "activityImage": "https://img.icons8.com/color/96/000000/error.png",
                "facts": [{
                    "name": "Produto:",
                    "value": "' + @B2_COD + '"
                }, {
                    "name": "Descrição:",
                    "value": "' + ISNULL(@product_name, 'Não localizada') + '"
                }, {
                    "name": "Quantidade:",
                    "value": "' + CAST(@B2_QATU AS NVARCHAR) + '"
                }, {
                    "name": "Usuário:",
                    "value": "' + @USERNAME + '"
                }, {
                    "name": "Data/Hora:",
                    "value": "' + FORMAT(GETDATE(), 'dd/MM/yyyy HH:mm:ss') + '"
                }, {
                    "name": "Máquina:",
                    "value": "' + @MACHINE_NAME + '"
                }, {
                    "name": "IP:",
                    "value": "' + @CLIENT_IP + '"
                }],
                "markdown": true
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "Verificar no Sistema",
                "targets": [{
                    "os": "default",
                    "uri": "http://seu-protheus.com/consulta-estoque"
                }]
            }]
        }';

        PRINT '📤 Enviando para Microsoft Teams...';
        
        -- Criar objeto HTTP
        EXEC sp_OACreate 'MSXML2.ServerXMLHTTP.6.0', @Object OUT;
        
        IF @Object IS NULL
        BEGIN
            RAISERROR('Não foi possível criar objeto HTTP', 16, 1);
            RETURN;
        END

        -- Configurar requisição
        EXEC sp_OAMethod @Object, 'open', NULL, 'POST', @WEBHOOK_URL, 'false';
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
            PRINT '✅ Alerta enviado com sucesso para Microsoft Teams!';
            
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
        PRINT '❌ Erro na procedure Teams: ' + @ErrorMessage;
        
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

PRINT '✅ Procedure sp_send_teams_alert criada com sucesso!';
