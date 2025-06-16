# Script de Associação de Usuários Órfãos - SQL Server

## 📋 Descrição

Este script SQL foi desenvolvido para identificar e reassociar usuários órfãos em bancos de dados SQL Server. Usuários órfãos são contas de usuário no banco de dados que perderam a associação com seus logins correspondentes no servidor, geralmente após operações de restore, backup/restore entre servidores diferentes, ou outras operações de manutenção.

## 🚀 Funcionalidades

- **Identificação Automática**: Localiza todos os usuários órfãos no banco de dados
- **Reassociação Inteligente**: Tenta reassociar automaticamente usuários com logins existentes
- **Modo Simulação**: Permite testar o script antes da execução real
- **Log Detalhado**: Registra todas as ações executadas com timestamp
- **Tratamento de Erros**: Captura e reporta erros de forma organizada
- **Estatísticas**: Fornece resumo quantitativo das operações
- **Segurança**: Usa QUOTENAME para prevenir SQL injection

## 📁 Estrutura do Repositório

```
├── sql-serlver
├── orphan_users.sql                 # Versão original do script
└── README.md                        # Este arquivo
```

## 🔧 Pré-requisitos

- SQL Server 2012 ou superior
- Permissões de `sysadmin` ou `db_owner` no banco de dados
- Acesso ao servidor SQL Server com privilégios adequados

## 💡 Como Usar

### 1. Configuração Inicial

Edite as seguintes variáveis no início do script:

```sql
USE [SEU_BANCO_AQUI]; -- Substitua pelo nome do seu banco

-- Configurações
DECLARE @ModoSimulacao BIT = 1 -- 1 para simular, 0 para executar
DECLARE @SenhaDefault NVARCHAR(50) = 'SuaSenhaSegura@123'
```

### 2. Primeira Execução (Modo Simulação)

```sql
-- Mantenha @ModoSimulacao = 1 para testar
DECLARE @ModoSimulacao BIT = 1
```

Execute o script para ver quais ações seriam realizadas sem fazer alterações reais.

### 3. Execução Real

Após verificar os resultados da simulação:

```sql
-- Altere para @ModoSimulacao = 0 para executar
DECLARE @ModoSimulacao BIT = 0
```

Execute o script para realizar as associações.

## 📊 Interpretando os Resultados

O script gera um relatório detalhado com os seguintes status:

| Status | Descrição |
|--------|-----------|
| `SUCESSO` | Usuário reassociado com sucesso ao login |
| `SIMULAÇÃO` | Comando que seria executado (modo simulação) |
| `LOGIN_AUSENTE` | Login não existe no servidor (requer criação manual) |
| `ERRO` | Erro durante a reassociação |
| `IGNORADO` | Usuário não existe mais no banco |

## ⚠️ Cenários Comuns

### Usuário Reassociado com Sucesso
```
Status: SUCESSO
Mensagem: Usuário reassociado com sucesso
Comando: ALTER USER [usuario] WITH LOGIN = [usuario]
```

### Login Não Encontrado
```
Status: LOGIN_AUSENTE  
Mensagem: Login não encontrado no servidor
Comando: CREATE LOGIN [usuario] WITH PASSWORD = 'SenhaSegura@123'
```

Para estes casos, você precisará:
1. Criar o login manualmente usando o comando sugerido
2. Executar o script novamente para reassociar

## 🛡️ Boas Práticas de Segurança

1. **Sempre teste primeiro**: Use o modo simulação antes da execução real
2. **Backup**: Faça backup do banco antes de executar alterações
3. **Senhas seguras**: Use senhas complexas para novos logins
4. **Monitoramento**: Revise os logs gerados pelo script
5. **Permissões**: Execute apenas com as permissões mínimas necessárias

## 🔍 Troubleshooting

### Erro: "Usuário não tem permissões suficientes"
**Solução**: Execute o script com uma conta que tenha privilégios `sysadmin` ou `db_owner`.

### Erro: "ALTER USER failed"
**Possíveis causas**:
- Login já está associado a outro usuário
- Login foi desabilitado
- Restrições de política de segurança

**Solução**: Verifique o status do login e resolva conflitos manualmente.

### Muitos usuários com status "LOGIN_AUSENTE"
**Causa comum**: Restore de backup de outro servidor onde os logins não existem.

**Solução**: 
1. Use os comandos CREATE LOGIN sugeridos pelo script
2. Ou sincronize os logins entre os servidores

## 📈 Exemplo de Saída

```
==================== RESUMO FINAL ====================
Total de usuários órfãos encontrados: 5
Usuários reassociados com sucesso: 3
Erros durante reassociação: 0
Logins ausentes (requerem criação): 2

Usuário          Status           Mensagem
user_app         SUCESSO          Usuário reassociado com sucesso
user_report      SUCESSO          Usuário reassociado com sucesso  
user_service     SUCESSO          Usuário reassociado com sucesso
user_temp        LOGIN_AUSENTE    Login não encontrado no servidor
user_legacy      LOGIN_AUSENTE    Login não encontrado no servidor
```

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir melhorias
- Enviar pull requests
- Compartilhar casos de uso

## 📚 Referências

- [Microsoft Docs - sp_change_users_login](https://docs.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-change-users-login-transact-sql)
- [Troubleshooting Orphaned Users](https://docs.microsoft.com/en-us/sql/sql-server/failover-clusters/troubleshoot-orphaned-users-sql-server)
- [SQL Server Security Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/security/security-center-for-sql-server-database-engine-and-azure-sql-database)

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Fernando Vernier**
* GitHub: https://github.com/ftvernier/erp-solutions
* LinkedIn: https://www.linkedin.com/in/fernando-v-10758522/

## 🙏 Agradecimentos

* Comunidade Protheus pela troca de experiências
* Equipe de desenvolvimento que colaborou nos testes

---

⭐ **Se este projeto te ajudou, deixe uma estrela!**

📢 **Encontrou algum problema? Abra uma issue!**

🤝 **Quer contribuir? Pull requests são bem-vindos!**
