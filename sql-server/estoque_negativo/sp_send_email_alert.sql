-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: sp_send_email_alert.sql
-- Descrição: Procedure para envio de alertas via email
-- =============================================

USE [SEU BANCO]
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_send_email_alert]
    @B2_COD NVARCHAR(50),
    @B2_QATU FLOAT,
    @USERNAME NVARCHAR(100),
    @MACHINE_NAME NVARCHAR(100),
    @CLIENT_IP NVARCHAR(50),
    @EMAIL_TO NVARCHAR(255),
    @EMAIL_PROFILE VARCHAR(100) = 'AlertasEstoque',
    @LogID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartTime DATETIME = GETDATE();
    
    BEGIN TRY
        DECLARE @subject NVARCHAR(255);
        DECLARE @body NVARCHAR(MAX);
        DECLARE @product_name NVARCHAR(255) = '';
        
        -- Buscar nome do produto
        SELECT TOP 1 @product_name = B1_DESC 
        FROM SB1010 
        WHERE B1_COD = @B2_COD 
        AND D_E_L_E_T_ = '';
        
        -- Montar assunto do email
        SET @subject = '🚨 ALERTA: Estoque Negativo - Produto ' + @B2_COD;
        
        -- Montar corpo do email em HTML
        SET @body = '
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; }
                .content { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 10px 0; }
                .info-table { width: 100%; border-collapse: collapse; }
                .info-table td { padding: 8px; border-bottom: 1px solid #ddd; }
                .label { font-weight: bold; color: #495057; }
                .footer { color: #6c757d; font-size: 12px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 ALERTA DE ESTOQUE NEGATIVO</h2>
            </div>
            
            <div class="content">
                <p>O sistema detectou que o produto abaixo ficou com estoque negativo:</p>
                
                <table class="info-table">
                    <tr>
                        <td class="label">Código do Produto:</td>
                        <td><strong>' + @B2_COD + '</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Descrição:</td>
                        <td>' + ISNULL(@product_name, 'Não localizada') + '</td>
                    </tr>
                    <tr>
                        <td class="label">Quantidade Atual:</td>
                        <td><span style="color: #dc3545; font-weight: bold;">' + CAST(@B2_QATU AS NVARCHAR) + '</span></td>
                    </tr>
                    <tr>
                        <td class="label">Data/Hora:</td>
                        <td>' + FORMAT(GETDATE(), 'dd/MM/yyyy HH:mm:ss') + '</td>
                    </tr>
                    <tr>
                        <td class="label">Usuário:</td>
                        <td>' + @USERNAME + '</td>
                    </tr>
                    <tr>
                        <td class="label">Máquina:</td>
                        <td>' + @MACHINE_NAME + '</td>
                    </tr>
                    <tr>
                        <td class="label">IP:</td>
                        <td>' + @CLIENT_IP + '</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px;">
                    <strong>Ação Recomendada:</strong><br>
                    Verifique imediatamente as movimentações deste produto e tome as ações necessárias para regularizar o estoque.
                </p>
            </div>
            
            <div class="footer">
                <p>Este é um alerta automático do sistema ERP Protheus.<br>
                Para dúvidas, entre em contato com a equipe de TI.</p>
            </div>
        </body>
        </html>';

        PRINT '📧 Enviando email para: ' + @EMAIL_TO;
        
        -- Enviar email usando Database Mail
        EXEC msdb.dbo.sp_send_dbmail
            @profile_name = @EMAIL_PROFILE,
            @recipients = @EMAIL_TO,
            @subject = @subject,
            @body = @body,
            @body_format = 'HTML',
            @importance = 'High';
        
        -- Atualizar log como sucesso
        IF @LogID IS NOT NULL
        BEGIN
            UPDATE SB2010_ALERT_LOG 
            SET STATUS = 'SUCCESS',
                RESPONSE_TIME_MS = DATEDIFF(ms, @StartTime, GETDATE())
            WHERE ID = @LogID;
        END
        
        PRINT '✅ Email enviado com sucesso!';
        
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        
        PRINT '❌ Erro ao enviar email: ' + @ErrorMessage;
        
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

PRINT '✅ Procedure sp_send_email_alert criada com sucesso!';
