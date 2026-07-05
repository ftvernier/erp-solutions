# Tabela de Conversão — SQL Server → PostgreSQL (Protheus)

## Funções e operadores

| Padrão T-SQL | Equivalente PostgreSQL | Observação |
| --- | --- | --- |
| `(NOLOCK)` / `WITH (NOLOCK)` literal | `WITH (%nolock%)` (macro DBAccess) | Requer que a string passe por `ChangeQuery()` |
| `ISNULL(a, b)` | `COALESCE(a, b)` | Substituição direta |
| `a + b` (concatenação, dentro do SQL) | `a \|\| b` | Não confundir com `+=` do AdvPL |
| `GETDATE()` | `CURRENT_DATE` / `NOW()` | Escolher conforme o campo ser data ou timestamp |
| `DATEDIFF(DAY, d1, d2)` | `(d2 - d1)` | Subtração de datas já retorna dias |
| `HASHBYTES('MD5', x)` | `digest(x, 'md5')` | Requer `CREATE EXTENSION pgcrypto`; retorna `bytea` |
| `CAST(x AS BIT)` | `CAST(x AS BOOLEAN)` | Verificar uso de `0`/`1` vs `TRUE`/`FALSE` no AdvPL |
| `CAST(x AS MONEY)` | `CAST(x AS NUMERIC(18,2))` | Ajustar escala conforme o campo |
| `CAST(x AS DATETIME2)` | `CAST(x AS TIMESTAMP)` | — |
| `banco.dbo.tabela` | *(sem equivalente direto)* | Requer `postgres_fdw`/`dblink` ou consolidação de schema — decisão arquitetural |
| `CONVERT(VARBINARY(n), CONVERT(VARCHAR(n), campoMemo))` | *(remover roundtrip)* | PostgreSQL `TEXT` não trunca — decisão arquitetural, validar efeitos colaterais antes de remover |

## Códigos de estilo do CONVERT (data/hora)

| Estilo | Formato MSSQL | Máscara `TO_CHAR` equivalente |
| --- | --- | --- |
| 101 | mm/dd/yyyy | `MM/DD/YYYY` |
| 103 | dd/mm/yyyy | `DD/MM/YYYY` |
| 108 | hh:mi:ss | `HH24:MI:SS` |
| 112 | yyyymmdd | `YYYYMMDD` |
| 120 | yyyy-mm-dd hh:mi:ss | `YYYY-MM-DD HH24:MI:SS` |
| 121 | yyyy-mm-dd hh:mi:ss.mmm | `YYYY-MM-DD HH24:MI:SS.MS` |
| 126 | yyyy-mm-ddThh:mi:ss.mmm (ISO 8601) | `YYYY-MM-DD"T"HH24:MI:SS.MS` |
