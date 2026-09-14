-- =============================================================================
-- Script: Reassociação de Usuários Órfãos (Orphaned Users) - SQL Server 2022
-- Objetivo: Identificar e corrigir usuários órfãos (comuns após RESTORE de banco
--           entre instâncias diferentes), reassociando-os aos logins do servidor
--           ou sinalizando a necessidade de criação manual do login.
-- Versão: 2.0 (revisada)
-- =============================================================================

USE [SEU_BANCO_AQUI]; -- Substitua pelo nome da sua base
GO

SET NOCOUNT ON;
SET XACT_ABORT ON; -- garante rollback automático em erros graves dentro de transação

-- =============================================================================
-- CONFIGURAÇÕES
-- =============================================================================
DECLARE @ModoSimulacao BIT = 1; -- 1 = simula (RECOMENDADO rodar assim primeiro), 0 = executa de fato
DECLARE @SenhaDefault  NVARCHAR(50) = 'TempPassword@123'; -- Troque por uma senha forte antes de usar
DECLARE @ForcarTrocaSenha BIT = 1; -- 1 = exige troca no primeiro login (recomendado)

-- Validação simples de força mínima da senha, mesmo com CHECK_POLICY controlado
IF LEN(@SenhaDefault) < 8
BEGIN
    RAISERROR('A senha padrão definida é muito curta (mínimo 8 caracteres). Ajuste @SenhaDefault antes de continuar.', 16, 1);
    RETURN;
END

-- =============================================================================
-- LIMPEZA PREVENTIVA DE TABELAS TEMPORÁRIAS
-- =============================================================================
IF OBJECT_ID('tempdb..#Orfaos') IS NOT NULL DROP TABLE #Orfaos;
IF OBJECT_ID('tempdb..#LogAcoes') IS NOT NULL DROP TABLE #LogAcoes;
IF OBJECT_ID('tempdb..#BackupOriginal') IS NOT NULL DROP TABLE #BackupOriginal;

CREATE TABLE #LogAcoes (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    UserName SYSNAME,
    Status VARCHAR(50),
    Mensagem NVARCHAR(500),
    DataHora DATETIME2 DEFAULT SYSDATETIME(),
    SID_Antigo VARBINARY(85) NULL,
    SID_Novo VARBINARY(85) NULL,
    Comando NVARCHAR(MAX) NULL
);

-- =============================================================================
-- MAPEAMENTO DE ÓRFÃOS
-- =============================================================================
SELECT 
    dp.name AS UserName,
    dp.sid AS UserSID,
    dp.type_desc,
    ROW_NUMBER() OVER (ORDER BY dp.name) AS RowNum
INTO #Orfaos
FROM sys.database_principals dp
LEFT JOIN sys.server_principals sp ON dp.sid = sp.sid
WHERE dp.type = 'S' 
  AND dp.authentication_type = 1        -- autenticação via SQL Server
  AND sp.sid IS NULL                     -- não existe login correspondente no servidor
  AND dp.sid IS NOT NULL
  AND dp.sid NOT IN (0x00)               -- exclui SID compartilhado/nulo
  AND dp.name NOT IN ('guest', 'INFORMATION_SCHEMA', 'sys');

DECLARE @TotalOrfaos INT = @@ROWCOUNT;

-- Backup do estado original, para referência/rollback manual se necessário
SELECT 
    o.UserName,
    o.UserSID AS SID_Original,
    o.type_desc
INTO #BackupOriginal
FROM #Orfaos o;

INSERT INTO #LogAcoes (UserName, Status, Mensagem) 
VALUES ('SISTEMA', 'INFO', CONCAT('Encontrados ', @TotalOrfaos, ' usuários órfãos. Modo simulação: ', 
        CASE WHEN @ModoSimulacao = 1 THEN 'SIM' ELSE 'NÃO' END));

IF @TotalOrfaos = 0
BEGIN
    PRINT 'Nenhum usuário órfão encontrado.';
    GOTO FinalScript;
END

-- =============================================================================
-- PROCESSAMENTO
-- =============================================================================
DECLARE @CurrentRow INT = 1;
DECLARE @UserName SYSNAME;
DECLARE @SidAntigo VARBINARY(85);
DECLARE @SidNovo VARBINARY(85);
DECLARE @sql NVARCHAR(MAX);
DECLARE @sqlLog NVARCHAR(MAX); -- versão sanitizada do comando, para log
DECLARE @msg NVARCHAR(500);
DECLARE @LoginDesabilitado BIT;

WHILE @CurrentRow <= @TotalOrfaos
BEGIN
    SELECT @UserName = UserName, @SidAntigo = UserSID
    FROM #Orfaos 
    WHERE RowNum = @CurrentRow;

    PRINT '------------------------------------------------------------';
    PRINT 'Processando usuário: ' + @UserName;

    -- Caso 1: já existe um login no servidor com o mesmo nome (apenas o SID difere)
    IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @UserName AND type = 'S')
    BEGIN
        SELECT @LoginDesabilitado = is_disabled, @SidNovo = sid
        FROM sys.server_principals 
        WHERE name = @UserName AND type = 'S';

        IF @LoginDesabilitado = 1
            PRINT 'AVISO: login existe no servidor, porém está DESABILITADO.';

        SET @sql = N'ALTER USER ' + QUOTENAME(@UserName) + N' WITH LOGIN = ' + QUOTENAME(@UserName) + N';';

        IF @ModoSimulacao = 1
        BEGIN
            INSERT INTO #LogAcoes (UserName, Status, Mensagem, SID_Antigo, SID_Novo, Comando) 
            VALUES (@UserName, 'SIMULAÇÃO', 
                    CASE WHEN @LoginDesabilitado = 1 THEN 'Reassociação simulada (login desabilitado no servidor)' 
                         ELSE 'Comando de reassociação simulado' END, 
                    @SidAntigo, @SidNovo, @sql);
            PRINT 'SIMULAÇÃO: ' + @sql;
        END
        ELSE
        BEGIN
            BEGIN TRY
                BEGIN TRANSACTION;
                EXEC sys.sp_executesql @sql;
                COMMIT TRANSACTION;

                INSERT INTO #LogAcoes (UserName, Status, Mensagem, SID_Antigo, SID_Novo, Comando) 
                VALUES (@UserName, 'SUCESSO', 'Usuário reassociado com sucesso', @sidAntigo, @SidNovo, @sql);
                PRINT 'SUCESSO: ' + @UserName + ' reassociado.';
            END TRY
            BEGIN CATCH
                IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
                SET @msg = ERROR_MESSAGE();
                INSERT INTO #LogAcoes (UserName, Status, Mensagem, SID_Antigo, SID_Novo, Comando) 
                VALUES (@UserName, 'ERRO', CONCAT('Falha ao reassociar: ', @msg), @sidAntigo, @SidNovo, @sql);
                PRINT 'ERRO: ' + @msg;
            END CATCH
        END
    END
    -- Caso 2: o login não existe no servidor (requer criação manual)
    ELSE
    BEGIN
        SET @sql = N'CREATE LOGIN ' + QUOTENAME(@UserName) + N' WITH PASSWORD = ' + QUOTENAME(@SenhaDefault, '''') 
                 + CASE WHEN @ForcarTrocaSenha = 1 
                        THEN N' MUST_CHANGE, CHECK_POLICY = ON, CHECK_EXPIRATION = ON;' 
                        ELSE N', CHECK_POLICY = OFF;' END;

        -- Nunca gravar a senha em texto plano no log
        SET @sqlLog = REPLACE(@sql, @SenhaDefault, '********');

        INSERT INTO #LogAcoes (UserName, Status, Mensagem, SID_Antigo, Comando) 
        VALUES (@UserName, 'LOGIN_AUSENTE', 'Login não existe na instância (execute manualmente no master)', 
                @SidAntigo, @sqlLog);
        
        PRINT 'LOGIN AUSENTE: Criar via master -> ' + @sqlLog;
    END

    SET @CurrentRow += 1;
END

FinalScript:

-- =============================================================================
-- RESUMO CONSOLIDADO
-- =============================================================================
DECLARE @Reassociados INT;
DECLARE @Erros INT;
DECLARE @LoginsAusentes INT;

SELECT 
    @Reassociados   = COUNT(CASE WHEN Status = 'SUCESSO' THEN 1 END),
    @Erros          = COUNT(CASE WHEN Status = 'ERRO' THEN 1 END),
    @LoginsAusentes = COUNT(CASE WHEN Status = 'LOGIN_AUSENTE' THEN 1 END)
FROM #LogAcoes;

PRINT '';
PRINT '==================== RESUMO FINAL ====================';
PRINT 'Total de órfãos identificados: ' + CAST(ISNULL(@TotalOrfaos, 0) AS VARCHAR(10));
PRINT 'Reassociados com sucesso: ' + CAST(@Reassociados AS VARCHAR(10));
PRINT 'Erros encontrados: ' + CAST(@Erros AS VARCHAR(10));
PRINT 'Logins não existentes na instância: ' + CAST(@LoginsAusentes AS VARCHAR(10));

IF @ModoSimulacao = 1
    PRINT 'ATENÇÃO: MODO SIMULAÇÃO ESTAVA ATIVO - Nenhuma alteração foi persistida.';

-- Grid detalhado (inclui SID antigo/novo para auditoria)
SELECT 
    UserName AS [Usuário],
    Status,
    Mensagem,
    SID_Antigo,
    SID_Novo,
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

-- Grid de backup do estado original (útil para conferência/rollback manual)
SELECT * FROM #BackupOriginal ORDER BY UserName;

-- =============================================================================
-- LIMPEZA
-- =============================================================================
DROP TABLE IF EXISTS #Orfaos;
DROP TABLE IF EXISTS #LogAcoes;
DROP TABLE IF EXISTS #BackupOriginal;
GO
