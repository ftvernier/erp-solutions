# Tabela de Conversão — SQL Server (T-SQL) → PostgreSQL / DBAccess (Protheus)

Documento de referência para suporte à skill de migração e conformidade de código AdvPL/TLPP.
Severidade: 🔴 bloqueante (erro no PostgreSQL) · 🟠 semântico (roda, resultado muda) · 🟣 arquitetural (decisão humana).

---

## 1. Funções de Texto, Strings e Espaços

| Padrão T-SQL (MSSQL) | Equivalente PostgreSQL / DBAccess | Observação & Impacto Protheus |
| :--- | :--- | :--- |
| 🔴 `a + b` (concatenação em SQL) | `a \|\| b` ou `CONCAT(a, b)` | No Postgres, `+` é aritmético. `CONCAT()` existe nos dois bancos e é a opção mais portável. Não alterar o `+` do AdvPL fora da query. Ocorre em `JOIN ... ON E1_PREFIXO+E1_NUM = E5_PREFIXO+E5_NUMERO`, `SELECT AE_CODCLI + AE_LOJCLI`, `', ' + col` em `FOR XML`, `C6_ITEM + RTRIM(C6_PRODUTO)` em `STRING_AGG`. |
| 🟠 `LEN(x)` | `LENGTH(RTRIM(x))` | `LEN` ignora espaços à direita; `LENGTH` conta todos. Como o Protheus preenche campos com espaços, `LENGTH(B1_COD) <= 6` nunca será verdadeiro sem `RTRIM`. |
| `DATALENGTH(x)` | `OCTET_LENGTH(x)` | Tamanho em bytes. |
| `SUBSTRING(x, pos, tam)` | `SUBSTRING(x, pos, tam)` | Aceito nativamente no PostgreSQL. `SUBSTR` também. |
| `LEFT(x, n)` / `RIGHT(x, n)` | `LEFT(x, n)` / `RIGHT(x, n)` | Idênticas. `RIGHT(x, LEN(y))` vira `RIGHT(x, LENGTH(RTRIM(y)))`. |
| 🔴 `CHARINDEX(busca, texto)` | `POSITION(busca IN texto)` ou `STRPOS(texto, busca)` | Ordem dos parâmetros inverte no `STRPOS`. |
| 🔴 `PATINDEX('%[0-9.-]%', x)` (classe de caracteres) | `SUBSTRING(x FROM '[0-9.-]+')` para extrair o primeiro trecho; `x ~ '[0-9.-]'` para testar presença | `PATINDEX` com colchetes é regex proprietária. Expressões como `LEFT(SUBSTRING(x, PATINDEX(...), 8000), PATINDEX('%[^...]%', ...) - 1)` reduzem-se a uma única `SUBSTRING(x FROM 'regex')`. |
| 🔴 `PATINDEX('%texto%', x)` (texto fixo) | `POSITION('texto' IN x)` | Sem classe de caracteres, equivale a `CHARINDEX`. |
| 🔴 `STUFF(str, ini, len, sub)` | `OVERLAY(str PLACING sub FROM ini FOR len)` | Não confundir com `Stuff()` do AdvPL. Quando usado em `STUFF((SELECT ... FOR XML PATH('')), 1, 1, '')`, ver seção 7. |
| 🔴 `REPLICATE(char, n)` | `REPEAT(char, n)` | Substituição direta. |
| 🔴 `SPACE(n)` | `REPEAT(' ', n)` | Só se estiver dentro do SQL; `Space()` do AdvPL é outra função. |
| 🔴 `STR(n)` / `STR(n, tam, dec)` | `CAST(n AS VARCHAR)` / `TO_CHAR(n, 'FM999990.00')` | Só se estiver dentro do SQL. |
| 🔴 `CHAR(13)`, `CHAR(10)`, `CHAR(9)` | `CHR(13)`, `CHR(10)`, `CHR(9)` | `CHAR` no PostgreSQL é tipo, não função. |
| 🔴 `NCHAR(n)` | `CHR(n)` | Idem. |
| 🔴 `FORMAT(valor, 'mascara')` | `TO_CHAR(valor, 'mascara')` | Máscaras diferem; ver seção 4. |
| `LTRIM(RTRIM(x))` | `TRIM(x)` | Simplificação permitida; `LTRIM(RTRIM())` também funciona. |
| `UPPER`, `LOWER`, `REPLACE`, `TRIM`, `RTRIM`, `LTRIM` | idênticos | Portáveis. |
| 🟠 Comparação de `VARCHAR` com espaços à direita | ver seção 9 | MSSQL ignora espaços à direita; PostgreSQL e Oracle não. |

---

## 2. Nulos, Lógica e Controle de Fluxo

| Padrão T-SQL (MSSQL) | Equivalente PostgreSQL / DBAccess | Observação & Impacto Protheus |
| :--- | :--- | :--- |
| 🔴 `ISNULL(a, b)` | `COALESCE(a, b)` | ANSI, suportado em todos os bancos Protheus. Inclui `ISNULL((SELECT TOP 1 ...), '')`: além do `ISNULL`, tratar o `TOP` (seção 6). |
| `NULLIF(a, b)` | `NULLIF(a, b)` | Idêntico. |
| `COALESCE(a, b)` | `COALESCE(a, b)` | Idêntico. |
| 🔴 `IIF(cond, a, b)` | `CASE WHEN cond THEN a ELSE b END` | Proprietário. Ex.: `SUM(IIF(C9_BLCRED = '', 1, 0))` → `SUM(CASE WHEN C9_BLCRED = ' ' THEN 1 ELSE 0 END)` (note também o `' '`, seção 9). |
| 🔴 `CHOOSE(idx, a, b, c)` | `CASE idx WHEN 1 THEN a WHEN 2 THEN b ... END` | Proprietário. |
| 🟠 `ISNUMERIC(x) = 1` | `x ~ '^[0-9]+$'` (inteiro) ou `x ~ '^-?[0-9]+(\.[0-9]+)?$'` (decimal) | `ISNUMERIC` aceita `e`, `.`, `$`, gerando falso-positivo antes de `CAST`. Aplicar `RTRIM` antes: `RTRIM(x) ~ '^[0-9]+$'`. |
| 🟠 `CAST(campo_char AS INTEGER)` protegido por `ISNUMERIC` no `WHERE` | `MAX(CASE WHEN RTRIM(campo) ~ '^[0-9]+$' THEN CAST(campo AS INTEGER) END)` | O PostgreSQL não garante que o filtro seja avaliado antes da expressão do `SELECT`; proteger a conversão com `CASE`. |
| 🟠 `CAST('' AS INT)` / `CAST('   ' AS INT)` | `CAST(NULLIF(RTRIM(x), '') AS INT)` | MSSQL devolve 0; PostgreSQL falha. |
| 🟣 `TRY_CAST(x AS tipo)` / `TRY_CONVERT` | *(Decisão Arquitetural)* | Sem equivalente. Validar com regex + `CAST`, ou função PL/pgSQL com bloco `EXCEPTION`. |
| 🟠 `CASE WHEN c THEN 'X' ELSE 0 END` (tipos mistos) | Uniformizar: `THEN 'X' ELSE '0'` | MSSQL converte implicitamente; PostgreSQL rejeita. Vale também para `UNION`. |
| 🟠 `campo_char = 1` (número sem aspas) | `campo_char = '1'` | Conversão implícita só existe no MSSQL. |

---

## 3. Data e Hora

> **Atenção Protheus:** campos tipo Data (`D`) do SX3 são gravados como texto `YYYYMMDD` (8 posições). Só use `TO_DATE` quando houver aritmética de datas; comparações `>=`/`<=` com literal `'YYYYMMDD'` já funcionam como string.

| Padrão T-SQL (MSSQL) | Equivalente PostgreSQL / DBAccess | Observação & Impacto Protheus |
| :--- | :--- | :--- |
| 🔴 `GETDATE()` | `CURRENT_TIMESTAMP` ou `NOW()` | Se o objetivo for só a data, `CURRENT_DATE`. Para comparar com campo Protheus: `TO_CHAR(CURRENT_DATE, 'YYYYMMDD')`. |
| 🔴 `GETUTCDATE()` | `CURRENT_TIMESTAMP AT TIME ZONE 'UTC'` | |
| 🔴 `SYSDATETIME()` | `CLOCK_TIMESTAMP()` | |
| 🔴 `DATEDIFF(DAY, campo_char8, GETDATE())` | `(CURRENT_DATE - TO_DATE(campo_char8, 'YYYYMMDD'))` | Subtração de `DATE` no Postgres devolve dias (`INTEGER`). Se `campo_char8` puder estar em branco, envolver com `NULLIF(RTRIM(campo), '')`. |
| 🔴 `DATEDIFF(DAY, d1, d2)` (colunas `DATETIME`) | `(CAST(d2 AS DATE) - CAST(d1 AS DATE))` | |
| 🔴 `DATEDIFF(MONTH, d1, d2)` | `(EXTRACT(YEAR FROM age(d2, d1)) * 12 + EXTRACT(MONTH FROM age(d2, d1)))` | |
| 🔴 `DATEADD(DAY, n, d)` | `(CAST(d AS DATE) + n)` | `DATE + INTEGER` soma dias. |
| 🔴 `DATEADD(MONTH, n, d)` | `(CAST(d AS TIMESTAMP) + (n \|\| ' month')::INTERVAL)` | |
| 🔴 `DATEPART(YEAR, d)` / `YEAR(d)` | `EXTRACT(YEAR FROM d)` | Idem `MONTH`, `DAY`. |
| 🔴 `CONVERT(CHAR(8), coluna_datetime, 112)` | `TO_CHAR(coluna_datetime, 'YYYYMMDD')` | Padrão para trazer `DATETIME` de tabela externa no formato Protheus. |
| Conversão de campo Protheus `YYYYMMDD` para data | `TO_DATE(campo, 'YYYYMMDD')` | Só quando há aritmética. |

---

## 4. Estilos do CONVERT (Data / Hora / Formatação)

| Estilo MSSQL | Formato Original | Máscara `TO_CHAR` no PostgreSQL | Exemplo T-SQL → PostgreSQL |
| :---: | :--- | :--- | :--- |
| **101** | `mm/dd/yyyy` | `MM/DD/YYYY` | `TO_CHAR(d, 'MM/DD/YYYY')` |
| **102** | `yyyy.mm.dd` | `YYYY.MM.DD` | `TO_CHAR(d, 'YYYY.MM.DD')` |
| **103** | `dd/mm/yyyy` | `DD/MM/YYYY` | `TO_CHAR(d, 'DD/MM/YYYY')` |
| **104** | `dd.mm.yyyy` | `DD.MM.YYYY` | `TO_CHAR(d, 'DD.MM.YYYY')` |
| **105** | `dd-mm-yyyy` | `DD-MM-YYYY` | `TO_CHAR(d, 'DD-MM-YYYY')` |
| **108** | `hh:mi:ss` | `HH24:MI:SS` | `TO_CHAR(d, 'HH24:MI:SS')` |
| **110** | `mm-dd-yyyy` | `MM-DD-YYYY` | `TO_CHAR(d, 'MM-DD-YYYY')` |
| **111** | `yyyy/mm/dd` | `YYYY/MM/DD` | `TO_CHAR(d, 'YYYY/MM/DD')` |
| **112** | `yyyymmdd` | `YYYYMMDD` | `TO_CHAR(d, 'YYYYMMDD')` *(Padrão Protheus)* |
| **120** | `yyyy-mm-dd hh:mi:ss` | `YYYY-MM-DD HH24:MI:SS` | `TO_CHAR(d, 'YYYY-MM-DD HH24:MI:SS')` |
| **121** | `yyyy-mm-dd hh:mi:ss.mmm` | `YYYY-MM-DD HH24:MI:SS.MS` | `TO_CHAR(d, 'YYYY-MM-DD HH24:MI:SS.MS')` |
| **126** | `yyyy-mm-ddThh:mi:ss.mmm` | `YYYY-MM-DD"T"HH24:MI:SS.MS` | `TO_CHAR(d, 'YYYY-MM-DD"T"HH24:MI:SS.MS')` |
| **2** (binário → hex sem `0x`) | `CONVERT(VARCHAR(32), HASHBYTES('MD5', x), 2)` | `UPPER(MD5(x))` | `MD5()` nativo do PostgreSQL devolve hex minúsculo; estilo 2 do MSSQL é maiúsculo. |

---

## 5. Mapeamento de Tipos de Dados em `CAST`/`CONVERT`

| Tipo T-SQL | Tipo Alvo PostgreSQL | Cuidados na Migração |
| :--- | :--- | :--- |
| 🔴 `VARCHAR(MAX)` / `CONVERT(VARCHAR(MAX), col)` | `TEXT` / `CAST(col AS TEXT)` | `MAX` não existe no PostgreSQL. |
| 🔴 `NVARCHAR(n)` / `N'texto'` | `VARCHAR(n)` / `'texto'` | PostgreSQL é UTF-8 nativo; remover o prefixo `N`. |
| `CAST(x AS INTEGER)` / `BIGINT` | idem | Ver seção 2 para campo caractere. |
| 🔴 `CAST(x AS BIT)` | `CAST(x AS BOOLEAN)` ou `SMALLINT` | Validar como o AdvPL lê o retorno. |
| 🔴 `TINYINT` | `SMALLINT` | |
| 🔴 `DATETIME` / `DATETIME2` | `TIMESTAMP` | |
| 🔴 `MONEY` | `NUMERIC(18,2)` | Evitar o tipo `money` do PostgreSQL. |
| 🔴 `UNIQUEIDENTIFIER` | `UUID` | |
| 🟣 `VARBINARY(MAX)` / `VARBINARY(n)` | `BYTEA` | Ver seção 8 para o caso memo. |
| 🟠 `ROUND(expr_double, n)` | `ROUND(CAST(expr AS NUMERIC), n)` | PostgreSQL só tem `ROUND(numeric, int)`. Colunas Protheus normalmente já são `NUMERIC`; o risco é em expressões com literal `1.0` ou funções que devolvem `double`. |

---

## 6. Locks, `TOP` e Sintaxe DBAccess

| Padrão Encontrado | Ação Recomendada | Justificativa |
| :--- | :--- | :--- |
| 🔴 `(NOLOCK)` / `WITH (NOLOCK)` | `%NoLock%` em `BeginSQL`; em string manual, `%NoLock%` + `ChangeQuery()` ou helper `NoLock()` que devolve `"(NOLOCK)"` só quando `TcGetDb() == "MSSQL"` | O PostgreSQL usa MVCC e não bloqueia leitura; o hint gera erro de sintaxe. |
| 🔴 `WITH (READPAST\|UPDLOCK\|ROWLOCK\|INDEX(...))`, `OPTION (RECOMPILE\|MAXDOP)` | Remover | Sem equivalente; `UPDLOCK` → `SELECT ... FOR UPDATE`. |
| 🔴 `SELECT TOP n ...` (query principal) | Garantir `ChangeQuery()` | Converte `TOP n` para `LIMIT n` no PostgreSQL e `ROWNUM` no Oracle. |
| 🔴 `SELECT DISTINCT TOP n ...` | `SELECT DISTINCT ... FETCH FIRST n ROWS ONLY` | `ChangeQuery()` pode não reconhecer `DISTINCT TOP`. |
| 🔴 `EXISTS (SELECT TOP 1 ...)` / `NOT EXISTS (...)` | Remover o `TOP 1` | `EXISTS` já é booleano. |
| 🔴 `TOP 1` em subquery escalar (`ISNULL((SELECT TOP 1 ...), '')`), derivada (`JOIN (SELECT TOP 1 ...)`) ou em `APPLY` | `... ORDER BY x FETCH FIRST 1 ROWS ONLY` (portável) ou `LIMIT 1` (só PG) ou `MIN()`/`MAX()` | `ChangeQuery()` não alcança subqueries. Sem `ORDER BY`, `TOP 1` já era indeterminado; aproveitar para definir. |
| `OFFSET n ROWS FETCH NEXT m ROWS ONLY` | manter | ANSI; PostgreSQL, MSSQL 2012+, Oracle 12c+. MSSQL exige `ORDER BY`. |
| 🔴 `LIMIT n` literal em código que também roda no MSSQL | `FETCH FIRST n ROWS ONLY` ou ramificar por `TcGetDb()` | `LIMIT` não existe no MSSQL. |
| 🔴 `FROM ${TABLE}` / `${NOLOCK}` / `%s` (templates caseiros) | Auditar o que cada placeholder injeta por banco | Templates costumam injetar `(NoLock)`/`Top 1` quando o banco não é Oracle. |

---

## 7. Agregação, Junções e JSON

| Padrão T-SQL (MSSQL) | Equivalente PostgreSQL | Observação |
| :--- | :--- | :--- |
| 🔴 `STRING_AGG(x, ',') WITHIN GROUP (ORDER BY y)` | `STRING_AGG(x, ',' ORDER BY y)` | O `ORDER BY` vai dentro dos parênteses. `CAST(... AS VARCHAR(MAX))` interno vira `CAST(... AS TEXT)` ou é removido. |
| 🔴 `STUFF((SELECT ',' + RTRIM(col) FROM ... FOR XML PATH('')), 1, 1, '')` | `(SELECT STRING_AGG(RTRIM(col), ',' ORDER BY col) FROM ...)` | `FOR XML` não existe. Com `SELECT DISTINCT ',' + col`, usar `STRING_AGG(DISTINCT RTRIM(col), ',')`. `CONVERT(VARCHAR, STUFF(...))` externo é removido. |
| 🔴 `OUTER APPLY (SELECT TOP 1 ... ORDER BY ...) X` | `LEFT JOIN LATERAL (SELECT ... ORDER BY ... LIMIT 1) X ON TRUE` | Colunas da tabela externa continuam visíveis dentro do `LATERAL`. O `TOP 1` vira `LIMIT 1` dentro da subquery. |
| 🔴 `CROSS APPLY (...) X` | `CROSS JOIN LATERAL (...) X` | |
| `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` | idêntico | Portável; boa alternativa ao `TOP 1` em subquery. |
| 🔴 `JSON_VALUE(CAST(col AS VARCHAR(MAX)), '$.id')` | `(CAST(col AS TEXT)::jsonb ->> 'id')` | Caminhos aninhados: `col::jsonb #>> '{a,b}'`. Se `col` puder conter JSON inválido, o cast falha; validar na origem. |
| 🔴 `ISJSON(x)` | `(x::jsonb IS NOT NULL)` dentro de função com `EXCEPTION`, ou validação na aplicação | Sem equivalente direto. |
| 🔴 `PIVOT` / `UNPIVOT` | `FILTER (WHERE ...)` em agregações condicionais / `UNION ALL` | Sem equivalente direto. |
| `GROUP BY` / `HAVING` / `UNION` / `EXISTS` | idênticos | Portáveis. |

---

## 8. DML, DDL, Objetos e Decisões Arquiteturais

| Padrão Encontrado | Ação Recomendada | Justificativa |
| :--- | :--- | :--- |
| 🔴 `UPDATE t SET c = u.c FROM t JOIN u ON ...` (alvo repetido no `FROM`) | `UPDATE t SET c = u.c FROM u WHERE t.k = u.k` | No PostgreSQL o alvo não é repetido no `FROM`. `UPDATE t SET ... FROM (SELECT ...) UPD WHERE ...` já é aceito. |
| 🔴 `DELETE alias FROM tabela alias WHERE ...` | `DELETE FROM tabela alias WHERE ...` | Sintaxe `DELETE alias FROM` é T-SQL. Com junção: `DELETE FROM t USING u WHERE ...`. |
| 🔴 `MERGE INTO t USING s ON ... WHEN MATCHED THEN UPDATE ...` | PostgreSQL 15+: `MERGE` (sem `;` obrigatório, sem `OUTPUT`); abaixo: `UPDATE ... FROM` + `INSERT ... ON CONFLICT` | Validar a versão do servidor. |
| 🟣 `SELECT ... INTO nova_tabela FROM ...` | `CREATE TABLE nova AS SELECT ...` (PostgreSQL aceita `SELECT INTO`, mas a tabela fica fora do dicionário) | Preferir `FWTemporaryTable`. Tabela sem `R_E_C_N_O_` não é gerenciável pelo DBAccess. |
| 🟣 `INSERT INTO tabela_protheus (...) VALUES (...)` via `TCSqlExec` | Preferir `RecLock`/`MsExecAuto`; se inevitável, não informar `R_E_C_N_O_` manualmente | No PostgreSQL o `R_E_C_N_O_` vem de sequência gerenciada pelo DBAccess. |
| 🟣 `SET campo_memo = CONVERT(VARBINARY(MAX), 'texto')` | Confirmar tipo físico em `information_schema.columns`; `TEXT` → gravar string direta; `BYTEA` → `CAST('texto' AS BYTEA)` | Preferir `MSMM()`/`RecLock`. |
| 🟣 `CONVERT(VARCHAR(n), CONVERT(VARBINARY(n), campo_memo))` (leitura) | Selecionar o campo direto ou `CAST(campo AS TEXT)`; se `BYTEA`, `CONVERT_FROM(campo, 'WIN1252')` | Roundtrip usado para driblar truncamento do MSSQL; não existe no PostgreSQL. `SUBSTRING(memo, 4001, 4000)` em fatias vira `SUBSTRING(CAST(memo AS TEXT), 4001, 4000)`. |
| 🔴 `CREATE VIEW dbo.NOME AS ...` / `FROM dbo.TABELA` | Remover `dbo.` | Schema padrão do PostgreSQL é `public`. Nomes de objeto ficam em minúsculas quando não citados. |
| 🔴 `DROP TABLE X` / `DROP VIEW X` sem `IF EXISTS` | `DROP TABLE IF EXISTS X` | Evita erro na primeira execução; aceito nos dois bancos. |
| 🟣 `banco.dbo.tabela` (cross-database) | `postgres_fdw` (`IMPORT FOREIGN SCHEMA`), `dblink`, ou consolidar em schema do mesmo banco (`schema.tabela`) | PostgreSQL não consulta outro banco na mesma conexão. |
| 🟣 `EXEC banco.dbo.procedure;` / `TCSPExec()` | Recriar em PL/pgSQL; `CALL procedure()` (PG 11+) ou `SELECT funcao()` | Procedures T-SQL não migram automaticamente. |
| 🟣 `CREATE TRIGGER trg ON tabela FOR UPDATE AS BEGIN INSERT ... FROM DELETED END` | `CREATE FUNCTION fn() RETURNS TRIGGER ... OLD.* ... $$ LANGUAGE plpgsql;` + `CREATE TRIGGER trg AFTER UPDATE ON tabela FOR EACH ROW EXECUTE FUNCTION fn()` | `DELETED`/`INSERTED` viram `OLD`/`NEW`; trigger de conjunto vira trigger por linha. |
| 🔴 `sys.databases` | `pg_database` (coluna `datname`) | |
| 🔴 `sys.tables` / `sys.columns` | `information_schema.tables` / `information_schema.columns` | |
| 🟠 `INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'SE201H'` | `WHERE UPPER(table_name) = 'SE201H'` | Nomes em minúsculas no catálogo do PostgreSQL. |
| 🔴 `@@IDENTITY` / `SCOPE_IDENTITY()` | `RETURNING R_E_C_N_O_` | Tabelas Protheus não usam `IDENTITY`. |
| 🔴 `DECLARE @v`, `SET @v`, `#temp`, `GO`, `SET NOCOUNT` | Sem equivalente em query única | Reescrever em AdvPL ou PL/pgSQL. |
| 🔴 `NEWID()` | `gen_random_uuid()` | PG 13+ nativo. |
| 🔴 `[coluna]` (colchetes) | `"coluna"` ou sem delimitador | Só se estiver dentro do SQL; `[]` do AdvPL é índice de array. |

---

## 9. Riscos Semânticos Silenciosos (roda no PostgreSQL, resultado muda)

| Padrão | Correção | Justificativa |
| :--- | :--- | :--- |
| 🟠 `D_E_L_E_T_ = ''` / `<> ''` / `IN ('')` | `D_E_L_E_T_ = ' '` (um espaço); melhor: `%notDel%` ou `RetSqlCond()` | MSSQL: `'' = ' '` é verdadeiro (ignora espaços à direita no `VARCHAR`). PostgreSQL e Oracle: falso. O Protheus grava `' '` no registro ativo. `<> '*'` é a forma que já funciona nos três bancos. |
| 🟠 `campo = ''` para qualquer campo caractere | `campo = ' '` com padding do SX3, ou `RTRIM(campo) = ''` | Mesmo motivo. `RTRIM` no lado da coluna impede uso de índice. |
| 🟠 `"' AND A1_COD = '" + AllTrim(cCod) + "'"` (literal sem padding) | `PadR(cCod, TamSX3("A1_COD")[1])`, `ValToSql(cCod)` com valor já preenchido, ou `RTRIM(A1_COD) = '...'` | O valor gravado tem espaços até o tamanho do campo; o literal sem padding não casa no PostgreSQL. `LIKE 'valor%'` é uma alternativa que usa índice. |
| 🟠 `campo LIKE '%texto%'` / `campo = 'Texto'` em dado de caixa variável | `UPPER(campo) LIKE '%TEXTO%'` | Collation padrão do MSSQL é case-insensitive; PostgreSQL é case-sensitive. Não aplicar em chaves/códigos já normalizados. `ILIKE` só existe no PostgreSQL. |
| 🟠 `ORDER BY campo_texto` alimentando quebra no AdvPL | Sinalizar; testar com a collation do banco destino (`C`, `pt_BR.UTF-8`) | Ordem de acentos e caixa pode mudar. Preferir ordenar por campos código/data. |
| 🟠 `LEN(campo) > 0` para testar preenchido | `LENGTH(RTRIM(campo)) > 0` ou `campo <> ' '` | `LENGTH` conta espaços de padding. |
| 🟠 Aritmética `int / int` | `CAST(a AS NUMERIC) / b` quando se espera decimal | Ambos truncam em divisão inteira; o risco é literal `1` no MSSQL que no Protheus costuma vir de coluna `FLOAT`/`NUMERIC`. |
| 🟠 `SUM(campo) = 0` vs `NULL` | `COALESCE(SUM(campo), 0)` | Idêntico nos dois; listado para lembrar que não muda. |
| 🟠 Datas `'YYYYMMDD'` comparadas com `''` | `= ' '` com 8 espaços ou `%notDel%`-style | Campo data em branco é gravado como 8 espaços. |

---

## 10. Camada de Detecção de Banco (`TcGetDb()`)

`TcGetDb()` devolve, entre outros, `"MSSQL"`, `"ORACLE"`, `"POSTGRES"`, `"DB2"`, `"MYSQL"`, `"INFORMIX"`.

| Padrão encontrado | Problema | Correção |
| :--- | :--- | :--- |
| 🟣 `If(!U_InndbOracle(), "Top 1", "")` / `If(lOracle, "", "(NoLock)")` | "Não-Oracle = MSSQL": injeta `TOP`/`(NOLOCK)` no PostgreSQL | Adicionar ramo `POSTGRES` (`LIMIT 1`, `""`), ou trocar por `ChangeQuery()`/`%NoLock%` e eliminar a ramificação |
| 🟣 `cOperador := IIf(cSGBD $ "MSSQL7", "+", "\|\|")` | Correto para PostgreSQL por acaso | Manter, mas preferir `CONCAT()` e eliminar a variável |
| 🟣 `Do Case ... Otherwise cSelect := " TOP 1 "` | `POSTGRES` cai no `Otherwise` | Adicionar `Case cSGBD == "POSTGRES"` com `LIMIT 1` no final da query, ou usar `FETCH FIRST 1 ROWS ONLY` para todos |
| 🟣 `lSqlOracle := (TcGetDb() $ "MSSQL\|ORACLE\|DB2")` | Nome enganoso e lista incompleta | Renomear e incluir `POSTGRES` explicitamente onde fizer sentido |
| 🟣 `If "MSSQL" $ TcGetDb()` para nome real de tabela temporária (`FwTemporaryTable:GetRealName()`) | Comportamento específico do MSSQL | Testar no PostgreSQL; `GetRealName()` já devolve o nome correto por banco |
| 🟣 Wrappers `U_InndbMsSql()`, `U_InndbOracle()`, `U_InndbPostgres()` | Só o wrapper existe; o uso ignora Postgres | Auditar cada ponto de uso; nunca copiar o ramo MSSQL para o ramo Postgres |

Modelo recomendado quando a ramificação for inevitável:

```advpl
Static Function SqlTop1(cSGBD)
    Local cRet := ""
    If cSGBD == "ORACLE"
        cRet := ""          // usar "AND ROWNUM = 1" no WHERE
    ElseIf cSGBD == "POSTGRES"
        cRet := ""          // usar "LIMIT 1" no final
    Else
        cRet := " TOP 1 "
    EndIf
Return cRet
```

Preferir sempre a forma portável (`ChangeQuery()` + `TOP` na query principal, ou `FETCH FIRST 1 ROWS ONLY`) à ramificação.
