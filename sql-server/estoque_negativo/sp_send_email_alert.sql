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
