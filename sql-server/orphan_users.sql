USE [SEU_BANCO_AQUI]; -- Substitua pelo nome da sua base
GO

-- Configurações
DECLARE @ModoSimulacao BIT = 0 -- 1 para simular, 0 para executar
DECLARE @SenhaDefault NVARCHAR(50) = 'TempPassword@123'

-- Limpeza de tabelas temporárias
IF OBJECT_ID('tempdb..#Orfaos') IS NOT NULL DROP TABLE #Orfaos
IF OBJECT_ID('tempdb..#LogAcoes') IS NOT NULL DROP TABLE #LogAcoes

-- Criação das tabelas temporárias
CREATE TABLE #Orfaos (
    ID INT IDENTITY(1,1),
    UserName SYSNAME,
    UserSID VARBINARY(85),
    Processado BIT DEFAULT 0
)

CREATE TABLE #LogAcoes (
    ID INT IDENTITY(1,1),
    UserName SYSNAME,
    Status VARCHAR(50),
    Mensagem NVARCHAR(500),
    DataHora DATETIME2 DEFAULT GETDATE(),
    Comando NVARCHAR(MAX) NULL
)

-- Verificação de permissões
IF IS_SRVROLEMEMBER('sysadmin') = 0 AND IS_MEMBER('db_owner') = 0
BEGIN
    INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
    VALUES ('SISTEMA', 'AVISO', 'Usuário pode não ter permissões suficientes')
END

-- Preenche a tabela com os usuários órfãos
BEGIN TRY
    INSERT INTO #Orfaos (UserName, UserSID)
    EXEC sp_change_users_login 'Report'
    
    INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
    VALUES ('SISTEMA', 'INFO', 'Encontrados ' + CAST(@@ROWCOUNT AS VARCHAR(10)) + ' usuários órfãos')
END TRY
BEGIN CATCH
    INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
    VALUES ('SISTEMA', 'ERRO', 'Erro ao buscar usuários órfãos: ' + ERROR_MESSAGE())
    GOTO FinalScript
END CATCH

-- Variáveis de trabalho
DECLARE @UserName SYSNAME
DECLARE @sql NVARCHAR(MAX)
DECLARE @msg NVARCHAR(500)

-- Processamento dos usuários órfãos (sem cursor)
WHILE EXISTS (SELECT 1 FROM #Orfaos WHERE Processado = 0)
BEGIN
    -- Seleciona próximo usuário não processado
    SELECT TOP(1) @UserName = UserName 
    FROM #Orfaos 
    WHERE Processado = 0
    ORDER BY ID
    
    PRINT '------------------------------------------------------------'
    PRINT 'Verificando usuário órfão: ' + @UserName
    
    -- Verifica se o usuário ainda existe no banco
    IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = @UserName AND type = 'S')
    BEGIN
        INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
        VALUES (@UserName, 'IGNORADO', 'Usuário não existe mais no banco de dados')
        PRINT 'Usuário não encontrado no banco. Ignorando.'
    END
    -- Verifica se o login existe no servidor
    ELSE IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @UserName)
    BEGIN
        -- Login existe, tenta reassociar
        SET @sql = 'ALTER USER ' + QUOTENAME(@UserName) + ' WITH LOGIN = ' + QUOTENAME(@UserName)
        
        BEGIN TRY
            IF @ModoSimulacao = 0
            BEGIN
                EXEC (@sql)
                INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
                VALUES (@UserName, 'SUCESSO', 'Usuário reassociado com sucesso', @sql)
                PRINT 'Usuário reassociado com sucesso: ' + @UserName
            END
            ELSE
            BEGIN
                INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
                VALUES (@UserName, 'SIMULAÇÃO', 'Comando que seria executado', @sql)
                PRINT 'SIMULAÇÃO - Comando: ' + @sql
            END
        END TRY
        BEGIN CATCH
            SET @msg = ERROR_MESSAGE()
            INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
            VALUES (@UserName, 'ERRO', 'Erro ao reassociar: ' + @msg, @sql)
            PRINT 'Erro ao reassociar: ' + @msg
        END CATCH
    END
    ELSE
    BEGIN
        -- Login não existe, sugere criação
        SET @sql = 'CREATE LOGIN ' + QUOTENAME(@UserName) + ' WITH PASSWORD = ' + QUOTENAME(@SenhaDefault, '''')
        INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
        VALUES (@UserName, 'LOGIN_AUSENTE', 'Login não encontrado no servidor', @sql)
        
        PRINT 'Login não encontrado no servidor.'
        PRINT 'Para criar o login, use: ' + @sql
    END
    
    -- Marca como processado
    UPDATE #Orfaos SET Processado = 1 WHERE UserName = @UserName
END

FinalScript:

-- Estatísticas finais
DECLARE @TotalOrfaos INT = (SELECT COUNT(*) FROM #Orfaos)
DECLARE @Reassociados INT = (SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'SUCESSO')
DECLARE @Erros INT = (SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'ERRO')
DECLARE @LoginsAusentes INT = (SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'LOGIN_AUSENTE')

PRINT '==================== RESUMO FINAL ===================='
PRINT 'Total de usuários órfãos encontrados: ' + CAST(@TotalOrfaos AS VARCHAR(10))
PRINT 'Usuários reassociados com sucesso: ' + CAST(@Reassociados AS VARCHAR(10))
PRINT 'Erros durante reassociação: ' + CAST(@Erros AS VARCHAR(10))
PRINT 'Logins ausentes (requerem criação): ' + CAST(@LoginsAusentes AS VARCHAR(10))

IF @ModoSimulacao = 1
    PRINT 'MODO SIMULAÇÃO ATIVO - Nenhuma alteração foi realizada'

PRINT ''
PRINT 'Detalhamento das ações:'

-- Mostra log detalhado
SELECT 
    UserName AS 'Usuário',
    Status,
    Mensagem,
    DataHora AS 'Data/Hora',
    Comando
FROM #LogAcoes
ORDER BY 
    CASE Status 
        WHEN 'SUCESSO' THEN 1
        WHEN 'SIMULAÇÃO' THEN 2
        WHEN 'LOGIN_AUSENTE' THEN 3
        WHEN 'ERRO' THEN 4
        ELSE 5
    END,
    UserName

-- Limpeza
DROP TABLE #Orfaos
DROP TABLE #LogAcoes

PRINT '==================== SCRIPT FINALIZADO ===================='
