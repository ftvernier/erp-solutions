---
name: sql-postgres-converter
description: "Detecta e converte sintaxe SQL Server/DBAccess embutida em código AdvPL/TLPP para sintaxe segura e portável em PostgreSQL. Cobre hints (NOLOCK) literais, TOP n (inclusive DISTINCT TOP e TOP em subquery/APPLY), funções T-SQL (ISNULL, CONVERT, GETDATE, DATEDIFF, HASHBYTES, LEN, PATINDEX, ISNUMERIC, IIF, JSON_VALUE, STRING_AGG WITHIN GROUP, STUFF+FOR XML PATH), OUTER/CROSS APPLY, concatenação com +, DML T-SQL (UPDATE...FROM, DELETE alias FROM, MERGE, SELECT INTO), DDL/objetos (CREATE TRIGGER, dbo., sys.*, EXEC procedure), roundtrip CONVERT(VARBINARY) em memo, nomes cross-database, riscos semânticos silenciosos (comparação com '' e espaços à direita, LIKE case-sensitive, CAST de char para inteiro) e a camada de detecção de banco via TcGetDb() (anti-padrão 'não-Oracle = MSSQL'). Verifica se ChangeQuery() é chamado antes de MPSysOpenQuery/TCQUERY/FWExecStatement. Use quando o usuário disser 'converter para postgres', 'preparar código para migração postgres', 'corrigir NOLOCK para postgres', 'ISNULL para COALESCE', 'sql server para postgres', 'migrar query para postgres', 'auditar queries para postgres'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Fernando Vernier
  category: Migração / Qualidade de Código
  version: '2.0.0'
---

# Conversor SQL Server → PostgreSQL para Protheus

## Visão Geral

O Protheus suporta MSSQL, Oracle e PostgreSQL através de abstrações do
próprio framework (`RetSqlName`, `RetSqlTab`, `RetSqlCond`, macros DBAccess,
`ChangeQuery()`). Essas abstrações resolvem parte da portabilidade, mas
`ChangeQuery()` só traduz tokens de macro (`%notDel%`, `%table:`, etc.) e o
`TOP n` da query principal. Qualquer sintaxe T-SQL escrita literalmente na
string SQL (hints de lock, funções proprietárias, operadores, catálogos
`sys.*`, DML/DDL proprietário) passa direto e quebra em tempo de execução
quando o banco ativo é trocado para PostgreSQL.

Há ainda uma segunda classe de problema, mais perigosa: **queries que rodam
sem erro no PostgreSQL mas devolvem resultado diferente** (comparação com
string vazia, `LIKE` sensível a maiúsculas, `CAST` de campo caractere).
Esta skill trata as duas classes.

Esta skill varre código AdvPL/TLPP com SQL embutido, separa o que já é
portável do que não é, classifica cada achado por severidade e sugere (ou
aplica, quando solicitado) a correção apropriada.

## Quando Usar

- Preparar código AdvPL/TLPP para migração de MSSQL para PostgreSQL.
- Revisar arquivos que montam SQL manualmente (`cQuery +=`, `cSql :=`,
  `cQry +=`, `cUpdate :=`, `cInsert +=`) ou usam `BeginSQL/EndSQL`.
- Converter qualquer padrão listado na tabela de referência encontrado em SQL embutido.
- Auditar se `ChangeQuery()` é realmente chamado antes de `MPSysOpenQuery()`,
  `TCQUERY`, `TCGenQry`+`DbUseArea`, `FWExecStatement():New()` ou `FWPreparedStatement():New()`.
- Auditar camadas de compatibilidade caseiras que ramificam por `TcGetDb()`.
- Corrigir referências a catálogos e objetos proprietários do SQL Server
  (`sys.databases`, `dbo.`, triggers T-SQL, `EXEC procedure`).

## Modo de Operação

Por padrão, esta skill **detecta e sugere**: apresenta cada ocorrência
encontrada com arquivo:linha, o trecho original, a severidade, o risco e a
correção proposta, e só aplica a mudança no arquivo quando o usuário
confirmar (análise primeiro, edição depois). Quando o usuário colar ou
selecionar um trecho com SQL embutido, aplicar a análise diretamente e
mostrar antes/depois, sem esperar pedido explícito.

Ao editar arquivos `.prw`/`.tlpp`/`.prx`, respeitar a codificação CP-1252
(ver skill `utf8-to-cp1252-conversion`): converter para CP-1252 **por último**,
depois de todas as edições.

## Classificação de Severidade

| Nível | Significado | Exemplos |
| --- | --- | --- |
| 🔴 **BLOQUEANTE** | Erro de sintaxe ou de execução no PostgreSQL | `(NOLOCK)`, `ISNULL`, `CONVERT`, `GETDATE`, `TOP` em subquery, `OUTER APPLY`, `JSON_VALUE`, `STRING_AGG ... WITHIN GROUP`, `FOR XML PATH`, `DELETE alias FROM`, `EXEC`, `dbo.`, `sys.*`, `+` entre strings |
| 🟠 **SEMÂNTICO** | Executa sem erro, mas o resultado muda | `campo = ''`, literal sem padding, `LIKE` sem `UPPER`, `CAST(campo_char AS INTEGER)`, `ISNUMERIC`, ordenação por collation, `LEN` com espaços à direita |
| 🟣 **ARQUITETURAL** | Não é conversão de texto; exige decisão humana | Nome cross-database (`banco.dbo.tabela`), trigger T-SQL, tabela criada por `SELECT INTO`, procedure externa, roundtrip `CONVERT(VARBINARY)` em memo, camada `TcGetDb()` caseira |
| 🟢 **PORTÁVEL** | Já funciona nos dois bancos; nunca reescrever | Ver seção abaixo |

## O que já é portável (nunca reescrever)

| Padrão | Por que já é seguro |
| --- | --- |
| `RetSqlName()`, `RetSqlTab()`, `RetFullName()` | Nativas do framework, resolvem o nome físico correto para o banco ativo |
| `RetSqlCond()`, `RetSqlDel()`, `ValToSql()`, `FormatIn()` | Nativas, geram condição/literal no formato do banco ativo |
| `%notDel%`, `%table:`, `%exp:`, `%xFilial:`, `%Order:`, `%NoLock%` | Macros DBAccess traduzidas automaticamente dentro de `BeginSQL/EndSQL` |
| `FWExecStatement`/`FWPreparedStatement` com `?` | Bind portável, desde que a string base passe por `ChangeQuery()` antes de `New()` |
| `COALESCE`, `NULLIF`, `CASE WHEN`, `CONCAT()`, `TRIM`, `RTRIM`, `LTRIM`, `UPPER`, `LOWER`, `REPLACE`, `SUBSTRING(x, pos, tam)`, `LEFT`, `RIGHT`, `ROW_NUMBER() OVER`, `EXISTS`, `UNION`, `!=`, `<>`, `%` (módulo) | Sintaxe idêntica ou compatível nos dois bancos |
| `OFFSET n ROWS FETCH NEXT n ROWS ONLY`, `FETCH FIRST n ROWS ONLY` | Sintaxe ANSI aceita por MSSQL 2012+, PostgreSQL, Oracle 12c+ e DB2 (MSSQL exige `ORDER BY`) |
| `Stuff()`, `Len()`, `Str()`, `Space()`, `Replicate()`, `Round()`, `IIf()`, `IsNumeric()` sobre variáveis AdvPL | Funções nativas AdvPL homônimas de funções T-SQL; não são SQL, ignorar fora do literal |
| Literais de data Protheus `'YYYYMMDD'` | Padrão nativo gravado como string de 8 caracteres; não converter para `DATE` a menos que haja aritmética de datas |

## Algoritmo de Detecção

Para cada arquivo `.prw`/`.tlpp`/`.prg`/`.prx` com SQL embutido:

1. **Localizar os pontos de montagem de query**: `cQuery :=`/`+=`, `cSql`,
   `cQry`, `cUpdate`, `cInsert`, `cDelete`, `cValues`, `cWhere`, blocos
   `BeginSQL/EndSQL`, comando `TCQUERY ... NEW ALIAS`, templates caseiros
   (`getSqlFormat`, `StrTran` com `${...}` ou `%s`). Considerar apenas texto
   dentro de literais de string; ignorar código AdvPL fora deles.
2. **Ignorar chamadas nativas** do framework (`RetSqlTab`, `RetSqlName`,
   `RetSqlCond`, `ValToSql`, `FormatIn`, `SqlOrder`).
3. **Hints de lock** 🔴: `(NOLOCK)`/`WITH (NOLOCK)` literal → substituir por
   `%NoLock%` em `BeginSQL`. Em strings montadas à mão, `%NoLock%` só é resolvido
   se a string passar por `ChangeQuery()`; se isso não for garantido no
   ambiente, usar um helper único `Static Function NoLock()` que devolve
   `"(NOLOCK)"` apenas quando `Upper(TcGetDb()) == "MSSQL"` e `""` caso
   contrário. Nunca apagar o hint sem substituto enquanto houver convivência com MSSQL.
4. **Ponto de execução** 🔴: verificar se a string passa por `ChangeQuery()`
   antes de `MPSysOpenQuery()`, `TCQUERY`, `TCGenQry`+`DbUseArea`,
   `TCSqlExec()`, `FWExecStatement():New()` e `FWPreparedStatement():New()`.
   Se não passar, propor adicionar a chamada no ponto de execução (padrão:
   `cQuery := ChangeQuery(cQuery)` imediatamente antes).
5. **Funções e sintaxe T-SQL literais** 🔴 (ver tabela completa na referência):
   - `ISNULL(a, b)` → `COALESCE(a, b)`
   - `GETDATE()` → `CURRENT_TIMESTAMP` (ou `CURRENT_DATE`)
   - `DATEDIFF(DAY, campo_char8, GETDATE())` → `(CURRENT_DATE - TO_DATE(campo_char8, 'YYYYMMDD'))`
   - `CONVERT(VARCHAR, expr, estilo)` / `CONVERT(CHAR(8), datetime, 112)` → `TO_CHAR(expr, 'máscara')`
   - `CONVERT(VARCHAR(MAX), coluna)` → `CAST(coluna AS TEXT)`
   - `LEN(x)` → `LENGTH(RTRIM(x))` (o `RTRIM` é obrigatório para preservar o comportamento do `LEN`)
   - `PATINDEX('%[classe]%', expr)` → `SUBSTRING(expr FROM '[classe]+')` quando o objetivo é extrair o primeiro trecho; `POSITION` quando o padrão é texto fixo
   - `HASHBYTES('MD5', x)` + `CONVERT(VARCHAR(32), ..., 2)` → `UPPER(MD5(x))` (nativo, sem `pgcrypto`); SHA exige `pgcrypto`/`digest()`
   - `ISNUMERIC(x) = 1` → `x ~ '^[0-9]+$'`
   - `IIF(cond, a, b)` → `CASE WHEN cond THEN a ELSE b END`
   - `JSON_VALUE(CAST(col AS VARCHAR(MAX)), '$.chave')` → `(CAST(col AS TEXT)::jsonb ->> 'chave')`
   - `STRING_AGG(x, sep) WITHIN GROUP (ORDER BY y)` → `STRING_AGG(x, sep ORDER BY y)`
   - `STUFF((SELECT ',' + col ... FOR XML PATH('')), 1, 1, '')` → `(SELECT STRING_AGG(col, ',' ORDER BY col) ...)`
   - `CHAR(13)`/`CHAR(10)` dentro do SQL → `CHR(13)`/`CHR(10)`
   - `OUTER APPLY (SELECT TOP 1 ... ORDER BY ...) X` → `LEFT JOIN LATERAL (SELECT ... ORDER BY ... LIMIT 1) X ON TRUE`
   - `CROSS APPLY (...)` → `CROSS JOIN LATERAL (...)`
6. **Concatenação** 🔴: operador `+` entre colunas/literais *dentro da string
   SQL* (ex.: `E1_PREFIXO+E1_NUM`, `', ' + SC6.C6_TES`, `C6_ITEM + RTRIM(C6_PRODUTO)`)
   → reescrever como `a || b` ou `CONCAT(a, b)`. `CONCAT()` é a opção mais
   portável entre MSSQL e PostgreSQL. **Atenção:** não alterar o `+` do AdvPL
   que concatena pedaços da string fora do literal SQL.
7. **`TOP n`** 🔴:
   - `SELECT TOP n` na query principal: garantir `ChangeQuery()`.
   - `SELECT DISTINCT TOP n`: `ChangeQuery()` pode não tratar; reescrever como `SELECT DISTINCT ... LIMIT n` ou `FETCH FIRST n ROWS ONLY` (portável).
   - `EXISTS (SELECT TOP 1 ...)` / `NOT EXISTS (SELECT TOP 1 ...)`: **remover o `TOP 1`**; o `EXISTS` já avalia presença.
   - `ISNULL((SELECT TOP 1 col ... ), '')` e subqueries escalares, derivadas ou em `APPLY`: `ChangeQuery()` não alcança; reescrever com `ORDER BY ... FETCH FIRST 1 ROWS ONLY` (portável, exige `ORDER BY` no MSSQL), `LIMIT 1` (só PG), ou `MIN()`/`MAX()`/`ROW_NUMBER()` quando semanticamente equivalente.
   - Injeção condicional de `"Top 1"` por código AdvPL (`If(!lOracle, "Top 1", "")`): ver item 11.
8. **Riscos semânticos silenciosos** 🟠 (a query roda, mas o resultado muda):
   - **Comparação com string vazia**: `D_E_L_E_T_ = ''`, `campo <> ''`, `IN ('')`. No MSSQL `'' = ' '` é verdadeiro (espaços à direita são ignorados no `VARCHAR`); no PostgreSQL e no Oracle não. O Protheus grava campos caractere preenchidos com espaços até o tamanho do SX3. Corrigir para `= ' '` (um espaço) em `D_E_L_E_T_`, e preferencialmente `%notDel%`/`RetSqlCond()`. Para outros campos: `campo = ' '` com padding correto ou `RTRIM(campo) = ''`.
   - **Literal sem padding** vindo de `AllTrim()`/`RTrim()` embutido: `"' AND A1_COD = '" + AllTrim(cCod) + "'"`. Funciona no MSSQL, falha silenciosamente no PostgreSQL. Corrigir com `PadR(cCod, TamSX3("A1_COD")[1])`, `ValToSql()` ou `RTRIM(A1_COD) = 'valor'` (perde índice; usar só quando necessário).
   - **`LIKE` e igualdade sensíveis a maiúsculas**: a collation padrão do SQL Server é case-insensitive; no PostgreSQL `LIKE` e `=` são case-sensitive. Se o dado ou o filtro podem variar de caixa (descrições, históricos, e-mails), envolver os dois lados com `UPPER()`. Não alterar filtros sobre códigos/chaves já normalizados.
   - **`CAST(campo_char AS INTEGER)`** com filtro `ISNUMERIC`: o PostgreSQL pode avaliar o `CAST` antes do filtro e falhar em valor não numérico. Proteger com `CASE WHEN campo ~ '^[0-9]+$' THEN CAST(campo AS INTEGER) END`.
   - **`CAST('' AS INT)`**: retorna 0 no MSSQL, erro no PostgreSQL. Usar `NULLIF(RTRIM(campo), '')` antes do `CAST`.
   - **`ORDER BY` com texto**: a ordem de maiúsculas/minúsculas/acentos depende da collation (`C` vs `pt_BR`). Sinalizar quando a ordenação alimenta lógica de quebra no AdvPL.
   - **Tipos mistos em `CASE`/`UNION`** (`THEN 'X' ELSE 0`): o MSSQL converte implicitamente; o PostgreSQL rejeita. Uniformizar os tipos.
   - **Campo caractere comparado com número** (`C5_STATUS = 1`): o MSSQL converte implicitamente; o PostgreSQL falha. Usar literal com aspas.
   - **`ROUND(expr, n)`** quando `expr` é `DOUBLE PRECISION`: o PostgreSQL só aceita `ROUND(numeric, int)`. Usar `ROUND(CAST(expr AS NUMERIC), n)`.
9. **DML proprietário via `TCSqlExec`** 🔴 (ver referência, seção 8):
   - `UPDATE t SET ... FROM t JOIN u ON ...` (alvo repetido no `FROM`) → `UPDATE t SET ... FROM u WHERE ...`.
   - `DELETE alias FROM tabela alias WHERE ...` → `DELETE FROM tabela alias WHERE ...` (sem `USING`) ou `DELETE FROM t USING u WHERE ...` quando há junção.
   - `MERGE INTO ... WHEN MATCHED` → PostgreSQL 15+ suporta `MERGE`; abaixo disso, `UPDATE ... FROM` + `INSERT ... ON CONFLICT`.
   - `SELECT ... INTO nova_tabela` → sinalizar 🟣: cria tabela fora do dicionário e sem `R_E_C_N_O_`; preferir `FWTemporaryTable`.
   - `INSERT`/`UPDATE` direto em tabela Protheus: verificar `R_E_C_N_O_` (no PostgreSQL é sequência gerenciada pelo DBAccess). Preferir `RecLock`/`MsExecAuto`.
   - `CONVERT(VARBINARY(MAX), 'texto')` para gravar campo memo → 🟣 confirmar o tipo físico da coluna no PostgreSQL (`information_schema.columns`); se for `TEXT`, gravar a string direta; se for `BYTEA`, usar `CAST(... AS BYTEA)`. Preferir `MSMM()`/`RecLock`.
10. **Catálogos, objetos e DDL** 🔴/🟣:
    - `sys.databases` → `pg_database`; `sys.tables`/`sys.columns` → `information_schema.tables`/`.columns`.
    - `INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'SE201H'`: no PostgreSQL os nomes ficam em minúsculas; comparar com `UPPER(table_name) = 'SE201H'`.
    - Prefixo `dbo.` (`CREATE VIEW dbo.X`, `FROM dbo.X`) → remover; o schema padrão do PostgreSQL é `public`.
    - Nome cross-database de três partes (`banco.dbo.tabela`, `inncash.dbo.`) → 🟣 `postgres_fdw`/`dblink` ou consolidação de schema.
    - `EXEC banco.dbo.procedure;` → 🟣 recriar em PL/pgSQL e chamar com `CALL procedure()`.
    - `CREATE TRIGGER ... FOR UPDATE AS BEGIN INSERT ... FROM DELETED` → 🟣 no PostgreSQL trigger exige função PL/pgSQL separada; `DELETED`/`INSERTED` viram `OLD`/`NEW`.
    - `DROP TABLE`/`DROP VIEW` sem `IF EXISTS` → adicionar `IF EXISTS` (ambos os bancos aceitam nas versões atuais).
11. **Camada de detecção de banco** 🟣: localizar `TcGetDb()`, wrappers
    (`U_InndbOracle()`, `lOracle`, `cSGBD`, `__cDBType`) e templates que
    injetam `"Top 1"`, `"(NoLock)"`, `rownum`, nomes de catálogo ou operador
    de concatenação conforme o banco. Anti-padrão a sinalizar: **"não-Oracle =
    MSSQL"** (`If(!lOracle, "Top 1", "")`, `cSGBD $ "MSSQL7" ... Else "+"`,
    `Otherwise cSelect := " TOP 1 "`). Toda ramificação precisa de um ramo
    explícito `"POSTGRES"` ou, melhor, ser substituída pela macro/`ChangeQuery()`
    equivalente. Modelo de ramificação correto:

    ```advpl
    cSGBD := AllTrim(Upper(TcGetDb()))
    Do Case
        Case cSGBD == "ORACLE"   ; cLimit := " AND ROWNUM = 1 "
        Case cSGBD == "POSTGRES" ; cLimit := " LIMIT 1 "
        Case cSGBD == "MSSQL"    ; cTop   := " TOP 1 "
        Otherwise                ; cTop   := " TOP 1 "   // documentar por que
    EndCase
    ```
12. **`BeginSQL/EndSQL`**: mesmo com macros, o corpo pode conter funções
    T-SQL literais (`CONVERT`, `ISNULL`, `LEN`) e `(NOLOCK)`; aplicar os
    itens 5 a 8 também dentro do bloco.
13. **Produzir o relatório** no formato abaixo antes de qualquer edição.

## Formato do Relatório

Para cada arquivo, uma tabela:

| # | Linha | Severidade | Padrão | Trecho original | Correção proposta |
| --- | --- | --- | --- | --- | --- |

Seguida de um resumo consolidado por severidade e de uma lista dos itens
🟣 ARQUITETURAL que exigem decisão do usuário. A ordem de execução
recomendada é: 🔴 de maior volume e menor risco primeiro (`(NOLOCK)`,
`ChangeQuery()` ausente, `ISNULL`), depois 🔴 pontuais (`CONVERT`,
`STRING_AGG`, `APPLY`, DML), depois 🟠 semânticos (exigem entendimento do
dado), e por último os 🟣.

## Anti-Padrões

| Anti-padrão | Por que é errado |
| --- | --- |
| Apagar `(NOLOCK)` em vez de trocar por `%NoLock%`/helper | Quebra a leitura sem lock no MSSQL durante o período de convivência |
| Reescrever `RetSqlTab`/`RetSqlCond`/`RetSqlName`/`ValToSql` | Já são portáveis; gera retrabalho |
| Confundir `+` do AdvPL com `+` do SQL | Quebra a montagem da string no fonte |
| Manter `SELECT TOP 1` dentro de `EXISTS (...)` | Falso erro de sintaxe no DBAccess para PostgreSQL |
| Confiar em `ChangeQuery()` para `TOP` em subquery, `DISTINCT TOP` ou `APPLY` | `ChangeQuery()` só trata o `TOP` da query principal |
| Converter `'YYYYMMDD'` para `TO_DATE()` indiscriminadamente | O Protheus armazena datas em strings de 8 posições; só converter quando há aritmética |
| Trocar `campo = ''` por `RTRIM(campo) = ''` em massa | Perde uso de índice; preferir `= ' '` ou `%notDel%`/`RetSqlCond()` |
| Envolver todo `LIKE` com `UPPER()` sem analisar o dado | Perde índice e mascara filtros sobre chaves já normalizadas |
| Adicionar ramo `"POSTGRES"` copiando o ramo MSSQL | Reintroduz `TOP`/`(NOLOCK)`/`+` no PostgreSQL |
| Usar `LIMIT n` literal como única forma | Só funciona no PostgreSQL/MySQL; em convivência preferir `FETCH FIRST n ROWS ONLY` |
| Aplicar correções em lote sem mostrar o diff | O modo padrão é sugerir e aguardar aprovação explícita |
| Editar `.prw`/`.tlpp` e não reconverter para CP-1252 | Corrompe acentos no compilador (ver skill `utf8-to-cp1252-conversion`) |

## Referência

Ver [references/tabela-conversao.md](references/tabela-conversao.md) para a
tabela completa de padrões e mapeamentos MSSQL → PostgreSQL, incluindo
agregação/junções avançadas, DML/DDL e riscos semânticos.
