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

