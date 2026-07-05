---
name: sql-postgres-converter
description: "Detecta e converte sintaxe SQL Server/DBAccess embutida em código AdvPL/TLPP para sintaxe segura e portável em PostgreSQL. Substitui hints (NOLOCK) literais pela macro %nolock%, converte funções T-SQL literais (ISNULL, CONVERT, GETDATE, DATEDIFF, HASHBYTES), reescreve concatenação T-SQL (+) para o padrão ANSI (||), sinaliza nomes cross-database de três partes e roundtrips CONVERT(VARBINARY,...) como decisão arquitetural, e verifica se ChangeQuery() é chamado onde TOP N ou macros DBAccess são usados. Use quando o usuário disser 'converter para postgres', 'preparar código para migração postgres', 'corrigir NOLOCK para postgres', 'ISNULL para COALESCE', 'sql server para postgres', 'migrar query para postgres'."
license: MIT
metadata:
  domain: Protheus
  maintainer: Comunidade AdvPL/TLPP
  category: Migração / Qualidade de Código
  version: '1.0.0'
---

# Conversor SQL Server → PostgreSQL para Protheus

## Visão Geral

O Protheus suporta MSSQL, Oracle e PostgreSQL através de abstrações do
próprio framework (`RetSqlName`, `RetSqlTab`, `RetSqlCond`, macros DBAccess,
`ChangeQuery()`). Essas abstrações resolvem a maior parte da portabilidade —
mas `ChangeQuery()` só traduz tokens de macro (`%notDel%`, `%table:`, etc.)
e o comando `TOP n`. Qualquer sintaxe T-SQL escrita literalmente na string
SQL (hints de lock, funções, operadores) passa direto e quebra
silenciosamente quando o banco de dados ativo é trocado para PostgreSQL.

Esta skill varre código AdvPL/TLPP com SQL embutido, separa o que já é
portável do que não é, e aplica ou sugere a correção apropriada para cada
padrão encontrado.

## Quando Usar

- Preparar código AdvPL/TLPP para uma migração de MSSQL para PostgreSQL
- Revisar um arquivo que monta SQL manualmente (`cQuery +=`) quanto à
  portabilidade entre bancos
- Converter `(NOLOCK)`, `ISNULL`, `CONVERT`, `GETDATE`, `DATEDIFF`,
  `HASHBYTES` ou concatenação com `+` encontrados em SQL embutido
- Auditar se `ChangeQuery()` é realmente chamado antes de
  `MpSysOpenQuery`/`TCGenQry`/`TCQUERY`

## O que já é portável (nunca reescrever)

| Padrão | Por que já é seguro |
| --- | --- |
| `RetSqlName()`, `RetSqlTab()`, `RetFullName()` | Nativas do framework — resolvem o nome físico correto para o banco ativo |
| `RetSqlCond()`, `RetSqlDel()` | Nativas — geram a condição padrão de exclusão lógica/filial por banco ativo |
| `%notDel%`, `%table:`, `%exp:`, `%xFilial:`, `%Order:` | Macros DBAccess traduzidas automaticamente por `ChangeQuery()` dentro de `BeginSQL/EndSQL` |
| `Stuff()`, `Year()`/`Month()`/`Day()` sobre variáveis AdvPL | Funções nativas AdvPL homônimas de funções T-SQL — não são SQL, cuidado ao vasculhar o código |
| `TCSqlExec()` | Função framework de execução — não é o comando `EXEC`/`sp_` do T-SQL |

## Algoritmo de Detecção

Para cada arquivo `.prw`/`.tlpp`/`.prg` com SQL embutido:

1. Localizar os pontos de montagem de query: `cQuery :=`/`+=`, blocos
   `BeginSQL/EndSQL`, comando `TCQUERY ... NEW ALIAS`.
2. Para cada `RetSqlTab()`/`RetSqlName()`/`RetSqlCond()` — não fazer nada,
   já é portável.
3. Sinalizar `(NOLOCK)`/`WITH (NOLOCK)` literal → substituir por
   `WITH (%nolock%)` (seguro em MSSQL e PostgreSQL simultaneamente).
4. Verificar se a string passa por `ChangeQuery()` antes da execução. Se
   não passar, adicionar a chamada no ponto de execução
   (`MpSysOpenQuery(ChangeQuery(cQuery))`,
   `TCGenQry(,,ChangeQuery(cQuery))` ou `TCQUERY ChangeQuery(cQuery) NEW ALIAS`)
   — pré-requisito para a correção do item 3 funcionar.
5. Sinalizar e reescrever funções T-SQL literais:
   - `ISNULL(a, b)` → `COALESCE(a, b)`
   - `GETDATE()` → `CURRENT_DATE` (uso apenas de data) ou `NOW()` (uso de timestamp)
   - `DATEDIFF(DAY, d1, d2)` → `(d2 - d1)` (subtração de datas já retorna
     dias como inteiro em PostgreSQL)
   - `CONVERT(VARCHAR, expr, estilo)` → `TO_CHAR(expr, 'máscara')` conforme
     a tabela de estilos (ver `references/tabela-conversao.md`)
   - `HASHBYTES('MD5', x)` → `digest(x, 'md5')` (requer
     `CREATE EXTENSION pgcrypto`)
6. Sinalizar o operador `+` usado como concatenação *dentro do texto SQL*
   (ex.: `SELECT A+B AS C`) → reescrever como `A || B`. Não confundir com o
   `+=` do AdvPL usado para montar a string da query fora dos literais.
7. Verificar `SELECT TOP n` contra o resultado do passo 4 — se
   `ChangeQuery()` não estiver no caminho de execução, tratar como risco
   também (já resolvido automaticamente quando presente).
8. Sinalizar como **arquitetural — não reescrever automaticamente**:
   - Nomes cross-database de três/quatro partes (`banco.dbo.tabela`) — sem
     equivalente sintático em PostgreSQL; requer `postgres_fdw`/`dblink`
     ou consolidação de schema.
   - Roundtrip `CONVERT(VARBINARY(n), CONVERT(VARCHAR(n), campoMemo))` —
     existe no MSSQL para contornar truncamento de campos MEMO;
     PostgreSQL `TEXT` não trunca, então remover o roundtrip muda
     comportamento e exige decisão humana.
   - `CAST(... AS MONEY/BIT/DATETIME2)` — mapear caso a caso para
     `NUMERIC`/`BOOLEAN`/`TIMESTAMP`, validando precisão/arredondamento no
     código AdvPL ao redor.

## Anti-Padrões

| Anti-padrão | Por que é errado |
| --- | --- |
| Apagar `(NOLOCK)` em vez de trocar pela macro `%nolock%` | Quebra o comportamento de leitura sem lock enquanto o MSSQL ainda estiver ativo, durante a janela de migração |
| Reescrever chamadas a `RetSqlTab`/`RetSqlCond`/`RetSqlName` | Já são portáveis — mexer nelas é churn desnecessário |
| Reescrever automaticamente nomes cross-database de três partes | Exige decisão de infraestrutura, não é conversão de sintaxe |
| Tratar todo `CONVERT` da mesma forma | O comportamento depende do código de estilo e do tipo alvo; alguns casos são arquiteturais |
| Assumir que `TOP n` é sempre seguro só porque `ChangeQuery()` existe em algum lugar do arquivo | É preciso confirmar a chamada naquele caminho de execução específico |

## Referência

Ver [references/tabela-conversao.md](references/tabela-conversao.md) para
a tabela completa de padrão → equivalente PostgreSQL, incluindo todos os
códigos de estilo do `CONVERT` de data/hora do T-SQL.
