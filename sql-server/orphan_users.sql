USE [SEU_BANCO_AQUI]; -- Substitua pelo nome da sua base
GO

SET NOCOUNT ON;

-- Configurações
DECLARE @ModoSimulacao BIT = 0; -- 1 para simular, 0 para executar
DECLARE @SenhaDefault NVARCHAR(50) = 'TempPassword@123';

-- Limpeza preventiva de tabelas temporárias
IF OBJECT_ID('tempdb..#Orfaos') IS NOT NULL DROP TABLE #Orfaos;
IF OBJECT_ID('tempdb..#LogAcoes') IS NOT NULL DROP TABLE #LogAcoes;

CREATE TABLE #LogAcoes (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    UserName SYSNAME,
    Status VARCHAR(50),
    Mensagem NVARCHAR(500),
    DataHora DATETIME2 DEFAULT SYSDATETIME(),
    Comando NVARCHAR(MAX) NULL
);

-- Mapeia órfãos diretamente via Views de Catálogo (substitui sp_change_users_login)
-- Um usuário SQL ('S') é órfão se seu SID não existir em sys.server_principals
SELECT 
    dp.name AS UserName,
    dp.sid AS UserSID,
    ROW_NUMBER() OVER (ORDER BY dp.name) AS RowNum
INTO #Orfaos
FROM sys.database_principals dp
LEFT JOIN sys.server_principals sp ON dp.sid = sp.sid
WHERE dp.type = 'S' 
  AND dp.authentication_type = 1 -- Instância de BD / SQL Auth
  AND sp.sid IS NULL
  AND dp.name NOT IN ('guest', 'INFORMATION_SCHEMA', 'sys');

DECLARE @TotalOrfaos INT = @@ROWCOUNT;

INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
VALUES ('SISTEMA', 'INFO', CONCAT('Encontrados ', @TotalOrfaos, ' usuários órfãos.'));

IF @TotalOrfaos = 0
BEGIN
    PRINT 'Nenhum usuário órfão encontrado.';
    GOTO FinalScript;
END

-- Variáveis de iteração
DECLARE @CurrentRow INT = 1;
DECLARE @UserName SYSNAME;
DECLARE @sql NVARCHAR(MAX);
DECLARE @msg NVARCHAR(500);

WHILE @CurrentRow <= @TotalOrfaos
BEGIN
    SELECT @UserName = UserName 
    FROM #Orfaos 
    WHERE RowNum = @CurrentRow;

    PRINT '------------------------------------------------------------';
    PRINT 'Processando usuário: ' + @UserName;

    -- Caso 1: O login já existe no servidor com o mesmo nome (apenas o SID difere)
    IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @UserName AND type = 'S')
    BEGIN
        SET @sql = N'ALTER USER ' + QUOTENAME(@UserName) + N' WITH LOGIN = ' + QUOTENAME(@UserName) + N';';

        IF @ModoSimulacao = 1
        BEGIN
            INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
            VALUES (@UserName, 'SIMULAÇÃO', 'Comando de reassociação simulado', @sql);
            PRINT 'SIMULAÇÃO: ' + @sql;
        END
        ELSE
        BEGIN
            BEGIN TRY
                EXEC sys.sp_executesql @sql;
                INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
                VALUES (@UserName, 'SUCESSO', 'Usuário reassociado com sucesso', @sql);
                PRINT 'SUCESSO: ' + @UserName + ' reassociado.';
            END TRY
            BEGIN CATCH
                SET @msg = ERROR_MESSAGE();
                INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
                VALUES (@UserName, 'ERRO', CONCAT('Falha ao reassociar: ', @msg), @sql);
                PRINT 'ERRO: ' + @msg;
            END CATCH
        END
    END
    -- Caso 2: O login nem existe no servidor (requer criação)
    ELSE
    BEGIN
        SET @sql = N'CREATE LOGIN ' + QUOTENAME(@UserName) + N' WITH PASSWORD = ' + QUOTENAME(@SenhaDefault, '''') + N', CHECK_POLICY = OFF;';
        
        INSERT INTO #LogAcoes (UserName, Status, Mensagem, Comando) 
        VALUES (@UserName, 'LOGIN_AUSENTE', 'Login não existe na instância (execute manualmente no master)', @sql);
        
        PRINT 'LOGIN AUSENTE: Criar via master -> ' + @sql;
    END

    SET @CurrentRow += 1;
END

FinalScript:

-- Resumo consolidado
PRINT '';
PRINT '==================== RESUMO FINAL ====================';
PRINT 'Total de órfãos identificados: ' + CAST(@TotalOrfaos AS VARCHAR(10));
PRINT 'Reassociados com sucesso: ' + CAST((SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'SUCESSO') AS VARCHAR(10));
PRINT 'Erros encontrados: ' + CAST((SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'ERRO') AS VARCHAR(10));
PRINT 'Logins não existentes na instância: ' + CAST((SELECT COUNT(*) FROM #LogAcoes WHERE Status = 'LOGIN_AUSENTE') AS VARCHAR(10));

IF @ModoSimulacao = 1
    PRINT 'ATENÇÃO: MODO SIMULAÇÃO ESTAVA ATIVO - Nenhuma alteração foi persistida.';

-- Grid detalhado
SELECT 
    UserName AS [Usuário],
    Status,
    Mensagem,
    DataHora AS [Data/Hora],
    Comando
FROM #LogAcoes
ORDER BY 
    CASE Status 
        WHEN 'ERRO' THEN 1
        WHEN 'LOGIN_AUSENTE' THEN 2
        WHEN 'SUCESSO' THEN 3
        WHEN 'SIMULAÇÃO' THEN 4
        ELSE 5 
    END,
    UserName;

-- Limpeza
DROP TABLE IF EXISTS #Orfaos;
DROP TABLE IF EXISTS #LogAcoes;
GO
