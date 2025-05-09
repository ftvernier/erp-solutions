# 🛠️ SQL Server Index Maintenance Procedure - `MaintainIndexes`

Esta procedure foi criada com o objetivo de **automatizar a manutenção de índices fragmentados**  garantindo melhor desempenho nas consultas e estabilidade da aplicação ERP.

## 📌 O que ela faz?

A procedure `[dbo].[MaintainIndexes]` percorre todos os índices das tabelas no banco e aplica as ações conforme o nível de fragmentação:

- **Reorganização (`REORGANIZE`)**: Quando a fragmentação está entre 5% e 30%.
- **Reconstrução (`REBUILD`)**: Quando a fragmentação é igual ou superior a 30%.

## ⚙️ Requisitos para manutenção

- Fragmentação acima de **5%**.
- Índices com mais de **100 páginas**.
- Índices **não desabilitados**.
- Exclui índices do tipo `XML`, `SPATIAL`, e `FULLTEXT`.

## 🧠 Lógica por trás

- Usa `sys.dm_db_index_physical_stats` com modo `SAMPLED` para identificar fragmentações.
- Utiliza `CURSOR` para iterar sobre os índices elegíveis.
- Cada ação é envolta por uma **transação segura**, com `TRY/CATCH` para garantir rollback em caso de erro.
- O tempo de execução de cada comando é **calculado e exibido** com precisão de segundos.

## 🧾 Exemplo de saída no SQL Server

Executed: ALTER INDEX [IDX_MYTABLE] ON [dbo].[MYTABLE] REBUILD; | Start Time: 2025-05-09 07:22:01.123 | End Time: 2025-05-09 07:22:08.456 | Elapsed Time: 7 seconds


## 🛡️ Boas práticas aplicadas

- Evita manutenção desnecessária em índices com baixa fragmentação.
- Proteção contra falhas com `ROLLBACK` seguro.
- Totalmente compatível com ambientes produtivos do SQL Server em uso com o ERP TOTVS Protheus.

## 💡 Dica para agendamento

Para manter a performance do banco, recomendamos agendar a execução da procedure semanalmente fora do horário de pico, utilizando o SQL Server Agent:

```sql
EXEC dbo.MaintainIndexes;

👨‍💻 Autor: Fernando Vernier
📅 Data de criação: 09/05/2025
