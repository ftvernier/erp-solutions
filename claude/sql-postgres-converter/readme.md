# sql-postgres-converter

> Skill para Claude Code que detecta e converte sintaxe SQL Server embutida em código ADVPL/TLPP para sintaxe segura e portável em PostgreSQL.

---

## O problema que essa skill resolve

Protheus roda em MSSQL, Oracle e PostgreSQL através de abstrações do próprio framework — `RetSqlName()`, `RetSqlTab()`, `RetSqlCond()`, macros do DBAccess, `ChangeQuery()`. Isso engana: dá a impressão de que qualquer código já é portável. Não é.

`ChangeQuery()` só traduz **tokens de macro** (`%notDel%`, `%table:`, `%exp:`...) e o comando `TOP n`. Tudo que é escrito **literalmente** na string do SQL passa direto:

- Colocar `(NOLOCK)` cru na query, achando que `ChangeQuery()` vai resolver — e descobrir em produção que não resolve. A forma seguramente portável é a macro `%nolock%`, que a maioria dos projetos nunca usa
- Usar `TCQUERY`/`TCGenQry()` direto, sem passar a string por `ChangeQuery()` nenhuma vez — nem o `TOP N` é traduzido nesse caso
- Trocar `ISNULL` por `COALESCE` mas esquecer que `GETDATE()`, `DATEDIFF()` e `HASHBYTES()` não têm equivalente automático
- Confundir concatenação `+` dentro do SQL (que precisa virar `||`) com o `+=` do AdvPL usado só para montar a string
- Tentar resolver com find-and-replace um roundtrip `CONVERT(VARBINARY, CONVERT(VARCHAR, campoMemo))` — que existe para contornar truncamento de MEMO no MSSQL e não deveria ser removido sem entender por que está ali
- Achar que uma tabela `banco.dbo.tabela` de outro banco vai "simplesmente funcionar" em Postgres

Essa skill instrui o Claude Code a separar automaticamente o que já é portável do que não é, e a corrigir cada padrão do jeito certo — não com um find-and-replace genérico.

---

## O que está coberto

| Padrão | Risco | Correção |
|---|---|---|
| `(NOLOCK)` / `WITH (NOLOCK)` literal | Crítico — quebra a query inteira em Postgres | `WITH (%nolock%)` + garantir `ChangeQuery()` no caminho de execução |
| `TCQUERY`/`TCGenQry()` sem `ChangeQuery()` | Crítico — nenhuma tradução acontece | Inserir `ChangeQuery()` no ponto de execução |
| `ISNULL(a, b)` | Médio | `COALESCE(a, b)` |
| Concatenação `+` dentro do SQL | Médio | `\|\|` |
| `CONVERT(tipo, expr, estilo)` | Médio, caso a caso | `TO_CHAR`/`CAST` conforme o código de estilo |
| `GETDATE()` / `DATEDIFF(DAY, d1, d2)` | Médio | `CURRENT_DATE`/`NOW()` / subtração direta de datas |
| `HASHBYTES('MD5', x)` | Médio, requer extensão | `digest(x, 'md5')` com `pgcrypto` |
| `banco.dbo.tabela` | Arquitetural — sinalizado, não reescrito | `postgres_fdw`/`dblink` ou consolidação de schema |
| Roundtrip `CONVERT(VARBINARY,...)` para MEMO | Arquitetural — sinalizado, não reescrito | Decisão humana — Postgres `TEXT` não trunca |

O que a skill **não toca**, porque já é portável: `RetSqlName()`, `RetSqlTab()`, `RetSqlCond()`, `RetFullName()`, `RetSqlDel()` e as macros `%notDel%`, `%table:`, `%exp:`, `%xFilial:`, `%Order:`.

---

## Modo de operação

Por padrão a skill **detecta e sugere** — mostra o trecho original, o risco e a correção proposta, e só aplica no arquivo quando você confirmar. Ela não roda em lote sozinha sobre uma base inteira sem revisão.

---

## Estrutura

```
sql-postgres-converter/
  SKILL.md                       # Instruções para o Claude Code
  references/
    tabela-conversao.md          # Tabela completa de conversão + códigos de estilo do CONVERT
```

---

## Como instalar

1. Copie a pasta `sql-postgres-converter/` inteira para dentro do `.claude/skills/` do seu projeto:

```
seu-projeto/
  .claude/
    skills/
      sql-postgres-converter/
        SKILL.md
        references/
          tabela-conversao.md
```

2. Abra o projeto no Claude Code — a skill é detectada automaticamente.

3. Peça naturalmente, ou simplesmente selecione um trecho de SQL embutido e pergunte:
   - *"Essa query tem algum problema para rodar em PostgreSQL?"*
   - *"Converte esse SQL para sintaxe do Postgres"*
   - *"Preciso preparar esse relatório para a migração de MSSQL para Postgres"*
   - *"Por que esse (NOLOCK) não vai funcionar depois da migração?"*

---

## Requisitos

- [Claude Code](https://claude.ai/code)
- Protheus 12.1.x ou superior
- ADVPL / TLPP
- PostgreSQL como banco de destino da migração

---

## Autor

**Fernando Vernier** — Staff Software Engineer, DBA e Tech Lead
[GitHub](https://github.com/ftvernier/erp-solutions) · [LinkedIn](https://www.linkedin.com/in/fernando-v-10758522/)

---

## Licença

MIT
