-- =============================================
-- Sistema de Alertas de Estoque Negativo
-- Arquivo: tr_estoque_negativo.sql
-- Descrição: Trigger principal otimizada com performance em lote
-- =============================================

USE [SEU BANCO]
GO

CREATE OR ALTER TRIGGER [dbo].[tr_estoque_negativo]
ON [dbo].[SB2010]
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        PRINT '🚀 Trigger de estoque negativo acionada!';

        DECLARE @USERNAME NVARCHAR(100) = SUSER_SNAME();
        DECLARE @UPDATE_TIMESTAMP DATETIME = GETDATE();
        DECLARE @AFFECTED_COUNT INT = 0;

        -- Verificar se há configurações ativas
        IF NOT EXISTS (SELECT 1 FROM ALERT_CONFIG WHERE IS_ACTIVE = 1)
        BEGIN
            PRINT '⚠️ Nenhuma configuração de alerta ativa encontrada.';
            RETURN;
        END

        -- Tabela temporária para produtos afetados (Performance em Lote)
        DECLARE @affectedProducts TABLE (
            B2_COD NVARCHAR(50), 
            B2_QATU FLOAT
        );

        -- Identifica produtos negativos sem alerta em uma única operação
        INSERT INTO @affectedProducts (B2_COD, B2_QATU)
        SELECT i.B2_COD, i.B2_QATU
        FROM inserted i
        WHERE i.B2_QATU < 0  -- Agora está negativo
        AND i.D_E_L_E_T_ = ''  -- Registro não deletado
        AND NOT EXISTS ( -- Verifica se já existe um alerta enviado para esse produto
            SELECT 1
            FROM SB2010_ALERT_LOG al
            WHERE al.B2_COD = i.B2_COD
            AND al.B2_QATU < 0
            AND al.ALERT_DATE >= DATEADD(HOUR, -1, GETDATE()) -- Evita spam (alertas na última hora)
        );

        SELECT @AFFECTED_COUNT = COUNT(*) FROM @affectedProducts;

        -- Verifica se há produtos para processar
        IF @AFFECTED_COUNT > 0
        BEGIN
            PRINT '📦 Produtos com estoque negativo detectados: ' + CAST(@AFFECTED_COUNT AS NVARCHAR);

            -- Processa alertas para cada produto usando procedure universal
            DECLARE @B2_COD NVARCHAR(50);
            DECLARE @B2_QATU FLOAT;

            DECLARE alert_cursor CURSOR LOCAL FAST_FORWARD FOR 
            SELECT B2_COD, B2_QATU FROM @affectedProducts;

            OPEN alert_cursor;
            FETCH NEXT FROM alert_cursor INTO @B2_COD, @B2_QATU;

            WHILE @@FETCH_STATUS = 0
            BEGIN
                PRINT '📤 Processando alerta - Produto: ' + @B2_COD + ' | Estoque: ' + CAST(@B2_QATU AS NVARCHAR);
                
                -- Chama a procedure universal que gerencia todos os canais
                EXEC [dbo].[sp_send_universal_alert] 
                    @B2_COD = @B2_COD,
                    @B2_QATU = @B2_QATU,
                    @USERNAME = @USERNAME,
                    @MACHINE_NAME = 'Sistema-Trigger',
                    @CLIENT_IP = 'Internal';

                FETCH NEXT FROM alert_cursor INTO @B2_COD, @B2_QATU;
            END;

            CLOSE alert_cursor;
            DEALLOCATE alert_cursor;

            PRINT '✅ Processo de alertas concluído! Total processado: ' + CAST(@AFFECTED_COUNT AS NVARCHAR);
        END
        ELSE
        BEGIN
            PRINT '✅ Nenhum produto ficou negativo ou alertas já foram enviados recentemente.';
        END

    END TRY
    BEGIN CATCH
        -- Tratamento de Rollback
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        DECLARE @ErrorProcedure NVARCHAR(128) = ERROR_PROCEDURE();
        DECLARE @ErrorLine INT = ERROR_LINE();

        -- Log do erro para análise posterior
        PRINT '❌ ERRO na trigger tr_estoque_negativo:';
        PRINT '📝 Mensagem: ' + @ErrorMessage;
        PRINT '🔧 Procedure: ' + ISNULL(@ErrorProcedure, 'tr_estoque_negativo');
        PRINT '📍 Linha: ' + CAST(@ErrorLine AS NVARCHAR);
        
        -- Gravar erro em tabela de log (opcional)
        BEGIN TRY
            INSERT INTO SB2010_ERROR_LOG (ERROR_DATE, ERROR_MESSAGE, ERROR_PROCEDURE, ERROR_LINE, USERNAME, ADDITIONAL_INFO)
            VALUES (
                GETDATE(), 
                @ErrorMessage, 
                ISNULL(@ErrorProcedure, 'tr_estoque_negativo'), 
                @ErrorLine, 
                @USERNAME,
                'Trigger de estoque negativo - Total produtos afetados: ' + CAST(@AFFECTED_COUNT AS NVARCHAR)
            );
            
            PRINT '📋 Erro registrado no log para análise.';
        END TRY
        BEGIN CATCH
            -- Se até o log de erro falhar, só imprime
            PRINT '❌ Falha ao gravar log de erro: ' + ERROR_MESSAGE();
        END CATCH

        -- IMPORTANTE: Não fazer ROLLBACK aqui!
        -- Deixa a transação principal decidir o que fazer
        -- A trigger de alerta não deve interferir na operação principal do ERP
        
        -- Se quiser forçar rollback em casos críticos, descomente:
        -- IF @ErrorSeverity > 16
        --     THROW @ErrorSeverity, @ErrorMessage, @ErrorState;
        
    END CATCH
END;
GO

PRINT '✅ Trigger tr_estoque_negativo criada com sucesso!';
PRINT '🎯 Trigger otimizada para performance em lote e tratamento robusto de erros.';
PRINT '';
PRINT '📋 PRÓXIMOS PASSOS:';
PRINT '1. Configure os canais de alerta na tabela ALERT_CONFIG';
PRINT '2. Teste com um produto específico';
PRINT '3. Configure Database Mail se usando email';
PRINT '4. Monitore os logs em SB2010_ALERT_LOG';
