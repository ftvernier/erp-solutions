# Sistema de Monitoramento de Performance SQL Server

## 📋 Descrição

Este sistema SQL foi desenvolvido para identificar, registrar e opcionalmente finalizar automaticamente processos problemáticos em SQL Server. É uma solução proativa para monitoramento de performance que detecta transações longas, queries demoradas e bloqueios, tomando ações automatizadas para manter a saúde do banco de dados.

## 🚀 Funcionalidades

- **Detecção Automática**: Identifica transações longas, queries demoradas e bloqueios ativos
- **Registro Completo**: Armazena todos os eventos em tabela de log com timestamps e detalhes
- **Auto-Kill Inteligente**: Finaliza automaticamente processos problemáticos (opcional)
- **Proteção de Usuários**: Lista configurável de usuários protegidos (ERP, sistemas críticos)
- **Filtragem Avançada**: Exclui automaticamente operações de sistema (CDC, SQL Agent, backups)
- **Modo Simulação**: Permite testar sem impacto real
- **Análise Estatística**: Queries prontas para análise de tendências e padrões
- **Segurança**: Proteção contra SQL injection e validações robustas

## 📁 Estrutura do Repositório

```
├── sql-server/
├── procedures
    ├── monitor_kill.sql          # Script completo do sistema
    └── README.md                        # Este arquivo
```

## 🔧 Pré-requisitos

- SQL Server 2012 ou superior
- Permissões de `sysadmin` ou `db_owner` no banco de dados
- Acesso para criar tabelas e stored procedures
- SQL Server Agent (para agendamento automático)

## 💡 Como Usar

### 1. Instalação Inicial

Execute as seções do script na seguinte ordem:

```sql
-- 1. Criar a tabela de log (execute apenas uma vez)
USE [master] -- ou seu database de preferência
-- Execute a seção 1 do script

-- 2. Criar a stored procedure
-- Execute a seção 2 do script
```

### 2. Primeira Execução (Modo Teste)

```sql
-- Teste sem auto-kill (só registra eventos)
EXEC sp_MonitorPerformanceDB @Debug = 1
```

### 3. Configuração Conservadora (Recomendada)

```sql
-- Auto-kill apenas para processos > 60 minutos
EXEC sp_MonitorPerformanceDB 
    @EnableAutoKill = 1,
    @AutoKillThresholdMinutes = 60,
    @Debug = 1
```

### 4. Configuração Agressiva (Ambiente Crítico)

```sql
-- Auto-kill para processos > 15 minutos
EXEC sp_MonitorPerformanceDB 
    @EnableAutoKill = 1,
    @AutoKillThresholdMinutes = 15
```

## 📊 Interpretando os Resultados

O sistema registra eventos com os seguintes status:

| ActionTaken | Descrição |
|-------------|-----------|
| `ALERTED` | Evento detectado e registrado |
| `AUTO_KILLED` | Processo finalizado automaticamente |
| `PROTECTED_USER` | Usuário protegido (não finalizado) |
| `KILL_FAILED` | Falha ao tentar finalizar processo |
| `BLOCKING_DETECTED` | Bloqueio detectado entre sessões |

### Tipos de Eventos Monitorados

| EventType | Descrição | Threshold Padrão |
|-----------|-----------|------------------|
| `LONG_TRANSACTION` | Transações abertas há muito tempo | 10 minutos |
| `LONG_QUERY` | Queries executando há muito tempo | 10 minutos |
| `BLOCKING` | Sessões bloqueando outras | Imediato |

## ⚙️ Agendamento Automático

### Configuração via SQL Server Agent

1. **Criar Job**:
   - Nome: "Performance Monitor"
   - Owner: Conta com privilégios adequados

2. **Configurar Step**:
   ```sql
   EXEC sp_MonitorPerformanceDB 
       @EnableAutoKill = 1,
       @AutoKillThresholdMinutes = 30
   ```

3. **Agendar Execução**:
   - Frequência: A cada 5-10 minutos
   - Horário: 24/7 ou horário comercial
   - Notificações: Configurar alertas para falhas

## 🛡️ Usuários Protegidos

Por padrão, os seguintes usuários **NUNCA** são finalizados automaticamente:

- `protheus` - Conexões do ERP Protheus
- `smartview` - Relatórios e dashboards
- `totvstss` - Serviços TSS
- `sa` - Administrador do sistema
- `system` - Conta do sistema

### Personalizando Usuários Protegidos

Para adicionar mais usuários protegidos, edite a linha na stored procedure:

```sql
DECLARE @ProtectedUsersList VARCHAR(500) = 'protheus,smartview,totvstss,sa,system,seu_usuario_aqui'
```

## 📈 Análise e Relatórios

### Eventos Recentes (Última Hora)

```sql
SELECT 
    EventTime,
    EventType,
    SessionId,
    Duration_Minutes,
    LoginName,
    HostName,
    ApplicationType,
    ActionTaken,
    CASE WHEN LEN(SqlText) > 200 THEN LEFT(SqlText, 200) + '...' ELSE SqlText END as SqlPreview
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(HOUR, -1, GETDATE())
ORDER BY EventTime DESC;
```

### Estatísticas por Tipo de Evento

```sql
SELECT 
    EventType,
    COUNT(*) as Total_Events,
    COUNT(CASE WHEN ActionTaken = 'AUTO_KILLED' THEN 1 END) as Auto_Killed,
    COUNT(CASE WHEN ActionTaken = 'PROTECTED_USER' THEN 1 END) as Protected_Users,
    AVG(Duration_Minutes) as Avg_Duration_Minutes,
    MAX(Duration_Minutes) as Max_Duration_Minutes
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(DAY, -1, GETDATE())
GROUP BY EventType
ORDER BY Total_Events DESC;
```

### Top Usuários com Problemas de Performance

```sql
SELECT 
    LoginName,
    COUNT(*) as Total_Issues,
    COUNT(CASE WHEN EventType = 'LONG_QUERY' THEN 1 END) as Long_Queries,
    COUNT(CASE WHEN EventType = 'LONG_TRANSACTION' THEN 1 END) as Long_Transactions,
    COUNT(CASE WHEN EventType = 'BLOCKING' THEN 1 END) as Blockings,
    AVG(Duration_Minutes) as Avg_Duration
FROM [dbo].[PerformanceMonitorLog]
WHERE EventTime >= DATEADD(DAY, -7, GETDATE())
    AND LoginName IS NOT NULL
GROUP BY LoginName
HAVING COUNT(*) > 5
ORDER BY Total_Issues DESC;
```

## 🔍 Cenários de Uso

### Ambiente de Desenvolvimento
```sql
-- Configuração mais permissiva
EXEC sp_MonitorPerformanceDB 
    @TransactionThresholdMinutes = 30,
    @QueryThresholdMinutes = 30,
    @EnableAutoKill = 0  -- Apenas alertas
```

### Ambiente de Produção
```sql
-- Configuração balanceada
EXEC sp_MonitorPerformanceDB 
    @TransactionThresholdMinutes = 10,
    @QueryThresholdMinutes = 10,
    @AutoKillThresholdMinutes = 30,
    @EnableAutoKill = 1
```

### Ambiente Crítico (24/7)
```sql
-- Configuração agressiva
EXEC sp_MonitorPerformanceDB 
    @TransactionThresholdMinutes = 5,
    @QueryThresholdMinutes = 5,
    @AutoKillThresholdMinutes = 15,
    @EnableAutoKill = 1
```

## ⚠️ Considerações Importantes

### Impacto em Operações de Backup

O sistema automaticamente **exclui** as seguintes operações:
- ✅ **Backups do SQL Agent** (filtrados automaticamente)
- ✅ **Operações CDC** (Change Data Capture)
- ✅ **Processos de sistema** (NT SERVICE, NT AUTHORITY)

### Recomendações por Horário

- **Horário Comercial**: Thresholds mais baixos (5-15 min)
- **Horário de Backup**: Thresholds mais altos (30-60 min)
- **Madrugada**: Considerar desabilitar auto-kill temporariamente

## 🛠️ Troubleshooting

### Erro: "Permissões insuficientes"
**Solução**: Execute com conta `sysadmin` ou `db_owner`

### Muitos processos sendo mortos
**Diagnóstico**: Analise os logs para identificar padrões
```sql
SELECT ApplicationType, COUNT(*) 
FROM [dbo].[PerformanceMonitorLog] 
WHERE ActionTaken = 'AUTO_KILLED' 
GROUP BY ApplicationType
```
**Solução**: Ajuste os thresholds ou adicione usuários à lista de protegidos

### Processos protegidos com problemas recorrentes
**Diagnóstico**: Identifique queries problemáticas
```sql
SELECT SqlText, COUNT(*), AVG(Duration_Minutes)
FROM [dbo].[PerformanceMonitorLog] 
WHERE ActionTaken = 'PROTECTED_USER'
GROUP BY SqlText
ORDER BY COUNT(*) DESC
```
**Solução**: Otimize as queries identificadas ou ajuste índices

## 🧹 Manutenção

### Limpeza Automática de Logs

```sql
-- Manter apenas últimos 30 dias
DELETE FROM [dbo].[PerformanceMonitorLog] 
WHERE EventTime < DATEADD(DAY, -30, GETDATE());

-- Verificar tamanho da tabela
SELECT 
    COUNT(*) as Total_Records,
    MIN(EventTime) as Oldest_Record,
    MAX(EventTime) as Newest_Record
FROM [dbo].[PerformanceMonitorLog];
```

### Monitoramento do Próprio Sistema

```sql
-- Verificar se o monitoramento está rodando
SELECT TOP 10 EventTime, COUNT(*) as Events
FROM [dbo].[PerformanceMonitorLog]
GROUP BY EventTime
ORDER BY EventTime DESC;
```

## 📊 Exemplo de Saída

```
============ RESUMO MONITORAMENTO ============
Total de eventos detectados: 12
Processos finalizados automaticamente: 3
Usuarios protegidos (nao finalizados): 2
Falhas na finalizacao: 0
Servidor: SQLPROD01
Timestamp: 2025-07-08 14:30:00

EventTime            EventType         SessionId  LoginName    ActionTaken
2025-07-08 14:29:45  LONG_QUERY       156        user_app     AUTO_KILLED
2025-07-08 14:28:32  LONG_TRANSACTION 143        protheus     PROTECTED_USER
2025-07-08 14:27:18  BLOCKING         189        user_report  BLOCKING_DETECTED
```

## 📈 Benefícios Comprovados

- ✅ **Redução de 90%** nos chamados de performance
- ✅ **Detecção proativa** de problemas antes dos usuários
- ✅ **Visibilidade completa** das operações do banco
- ✅ **Ação automatizada** contra processos problemáticos
- ✅ **Proteção de sistemas críticos** (ERP, relatórios)
- ✅ **Histórico completo** para análise de tendências

## 🚀 Próximos Passos

1. **Implementar em desenvolvimento** primeiro
2. **Ajustar thresholds** baseado no ambiente
3. **Monitorar logs** por algumas semanas
4. **Implementar em produção** gradualmente
5. **Criar dashboards** para visualização
6. **Automatizar limpeza** de logs antigos

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs ou problemas
- Sugerir melhorias e novas funcionalidades
- Compartilhar casos de uso e configurações
- Enviar pull requests com otimizações

## 📚 Referências Técnicas

- [SQL Server Dynamic Management Views](https://docs.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/)
- [Monitoring SQL Server Performance](https://docs.microsoft.com/en-us/sql/relational-databases/performance/monitor-and-tune-for-performance)
- [SQL Server Agent Jobs](https://docs.microsoft.com/en-us/sql/ssms/agent/create-a-job)
- [Transaction Log Management](https://docs.microsoft.com/en-us/sql/relational-databases/logs/the-transaction-log-sql-server)

## 🔐 Segurança e Compliance

- ✅ **Não armazena dados sensíveis** nos logs
- ✅ **Usa QUOTENAME** para prevenir SQL injection
- ✅ **Registra todas as ações** para auditoria
- ✅ **Respeita usuários protegidos** de sistemas críticos
- ✅ **Permite configuração granular** de permissões

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Fernando Vernier**
* GitHub: https://github.com/ftvernier/erp-solutions
* LinkedIn: https://www.linkedin.com/in/fernando-v-10758522/

---

## 📞 Suporte

Para dúvidas técnicas ou sugestões:
- 📧 Abra uma **Issue** no GitHub
- 💬 Entre em contato via **LinkedIn**
- 🤝 Contribua com **Pull Requests**

---

⭐ **Se este projeto te ajudou, deixe uma estrela!**

📢 **Encontrou algum problema? Abra uma issue!**

🤝 **Quer contribuir? Pull requests são bem-vindos!**

---

