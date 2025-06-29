# 🔍 Gerador de Diagnóstico SQL Server - ERP Protheus

![GitHub last commit](https://img.shields.io/github/last-commit/ftvernier/sql-diagnostic-generator)
![GitHub repo size](https://img.shields.io/github/repo-size/ftvernier/sql-diagnostic-generator)
![License](https://img.shields.io/badge/license-MIT-blue)

> 🚀 **Ferramenta web para gerar scripts personalizados de diagnóstico SQL Server específicos para ambiente ERP Protheus**

Uma solução completa que permite aos DBAs e desenvolvedores gerar rapidamente scripts de diagnóstico customizados para identificar problemas de performance, bloqueios, queries lentas e realizar manutenções automáticas no SQL Server.

## 📋 Sobre o Projeto

Este gerador foi desenvolvido especificamente para ambientes **ERP Protheus + SQL Server**, oferecendo:

- **6 categorias** de diagnóstico organizadas
- **10+ scripts especializados** baseados em DMVs do SQL Server
- **Stored procedures** para manutenção automática
- **Interface intuitiva** para seleção e customização
- **Scripts prontos** para produção

## 🎯 Principais Funcionalidades

### 📊 Categorias de Diagnóstico

| Categoria | Descrição | Scripts Incluídos |
|-----------|-----------|-------------------|
| **Performance Geral** | Análise de CPU e wait statistics | CPU Usage, Wait Types |
| **Bloqueios & Deadlocks** | Identificação de locks e transações | Bloqueios Ativos, Transações Longas |
| **Queries Problemáticas** | Análise de queries lentas | Queries Lentas, Alto I/O |
| **Manutenção DB** | Índices e fragmentação | Fragmentação, Índices Sugeridos |
| **Conexões & Sessões** | Monitoramento de conexões | Conexões Ativas, Sessões Idle |
| **Procedures Manutenção** | Automação de manutenção | MaintainIndexes, UpdateStatistics |

### 🛠️ Scripts Especializados

#### 🔥 Performance Crítica
- **CPU Usage por Query** - Top queries que mais consomem CPU
- **Wait Statistics** - Principais gargalos do sistema com descrições
- **Queries Lentas** - Análise detalhada de queries com tempo > 1 segundo

#### 🚨 Bloqueios e Problemas
- **Bloqueios Ativos** - Sessões bloqueadas e bloqueadoras em tempo real
- **Transações Longas** - Análise completa de transações abertas há muito tempo
- **Histórico de Deadlocks** - Deadlocks das últimas 24 horas via Extended Events

#### 🔧 Manutenção Automática
- **MaintainIndexes** - Stored procedure para manutenção automática de índices
- **UpdateStatistics** - Procedure para atualização de estatísticas configurável

#### 📈 Específico para Protheus
- **Queries do Protheus** - Análise de queries ERP com validação de boas práticas
- **Verificação D_E_L_E_T_** - Identifica queries sem filtro de deleção
- **Validação xFilial** - Verifica uso correto de filtros de filial

## 🚀 Como Usar

### 1. Acessar a Ferramenta
```bash
# Clone o repositório
git clone https://github.com/ftvernier/sql-diagnostic-generator.git

# Ou acesse diretamente via web
# https://seu-dominio.com/sql-diagnostic-generator
```

### 2. Seleção de Diagnósticos
1. **Escolha a categoria** na aba superior
2. **Selecione os scripts** desejados clicando nos cards
3. **Use ações rápidas** para cenários comuns:
   - 🔥 **Performance Crítica**: CPU + Wait Stats + Bloqueios
   - ⚡ **Procedures Manutenção**: Índices + Estatísticas
   - 🔧 **Manutenção DB**: Fragmentação + Conexões

### 3. Geração e Execução
1. Clique em **"Gerar Script SQL"**
2. **Copie** ou faça **download** do script gerado
3. Execute no **SQL Server Management Studio**
4. Analise os resultados

## 📝 Exemplos de Uso

### Cenário 1: Sistema Lento
```sql
-- Script gerado para performance crítica
-- Inclui: CPU Usage + Wait Statistics + Bloqueios Ativos
```

### Cenário 2: Manutenção Semanal
```sql
-- Executar procedures de manutenção
EXEC dbo.MaintainIndexes;
EXEC dbo.UpdateStatistics @SamplePercent = 20;
```

### Cenário 3: Análise de Queries Protheus
```sql
-- Verificar boas práticas em queries ERP
-- Identifica: falta de D_E_L_E_T_, xFilial, SELECT *
```

## ⚙️ Configuração das Stored Procedures

### MaintainIndexes
```sql
-- Cria a procedure de manutenção automática
-- Características:
-- ✅ Fragmentação > 30% = REBUILD
-- ✅ Fragmentação 5-30% = REORGANIZE  
-- ✅ Log detalhado com timing
-- ✅ Tratamento de erros robusto
-- ✅ Contador de progresso

EXEC dbo.MaintainIndexes;
```

### UpdateStatistics
```sql
-- Atualização de estatísticas configurável
-- Parâmetros disponíveis:
-- @SamplePercent: Percentual de amostragem (padrão 20%)
-- @TablesFilter: Filtro de tabelas (opcional)

-- Exemplos:
EXEC dbo.UpdateStatistics;                                    -- Todas as tabelas, 20%
EXEC dbo.UpdateStatistics @SamplePercent = 30;               -- Todas as tabelas, 30%
EXEC dbo.UpdateStatistics @TablesFilter = 'SA';              -- Apenas tabelas SA*, 20%
```

## 📅 Agendamento no SQL Server Agent

### Job de Manutenção Semanal
```sql
-- Configuração recomendada:
-- Nome: "Manutenção Automática - TOTVS"
-- Frequência: Domingos às 02:00
-- Comando: EXEC dbo.MaintainIndexes;
-- Notification: Email em caso de falha
```

### Job de Estatísticas
```sql
-- Configuração recomendada:
-- Nome: "Atualização Estatísticas - TOTVS"  
-- Frequência: Diário às 01:00
-- Comando: EXEC dbo.UpdateStatistics @SamplePercent = 15;
```

## 🎯 Melhores Práticas

### ⚠️ Cuidados na Execução
- **Horário**: Execute preferencialmente fora do horário comercial
- **Monitoramento**: Acompanhe o impacto no sistema durante execução
- **Backup**: Sempre tenha backup antes de manutenções
- **Teste**: Valide em ambiente de homologação primeiro

### 📊 Interpretação de Resultados

#### Wait Statistics
| Wait Type | Significado | Ação Recomendada |
|-----------|-------------|------------------|
| `PAGEIOLATCH_*` | I/O de disco lento | Verificar subsistema de disco |
| `LCK_M_*` | Contenção de locks | Analisar transações longas |
| `CXPACKET` | Paralelismo excessivo | Ajustar MAXDOP |
| `ASYNC_NETWORK_IO` | Cliente lento | Verificar rede/aplicação |

#### Fragmentação de Índices
| Fragmentação | Ação | Comando |
|--------------|------|---------|
| 5% - 30% | REORGANIZE | `ALTER INDEX ... REORGANIZE` |
| > 30% | REBUILD | `ALTER INDEX ... REBUILD` |
| < 5% | Nenhuma | Índice OK |

## 🔧 Customizações

### Adicionar Novos Scripts
```javascript
// Estrutura para novos diagnósticos
'novo_script': {
  category: 'performance',
  name: 'Nome do Script',
  description: 'Descrição detalhada',
  script: `-- Seu SQL aqui`
}
```

### Modificar Procedures
```sql
-- Exemplo: Alterar limite de fragmentação
-- Na procedure MaintainIndexes, linha XX:
WHERE avg_fragmentation_in_percent > 10  -- Era 5, agora 10
```

## 📈 Monitoramento Contínuo

### Dashboard Recomendado
1. **Performance**: CPU médio, Wait times, Queries lentas
2. **Bloqueios**: Número de deadlocks, Transações longas
3. **Manutenção**: Fragmentação média, Última atualização de stats
4. **Protheus**: Queries sem boas práticas, Tempo médio ERP

### Alertas Sugeridos
- Wait time > 30% do total
- Transações abertas > 10 minutos  
- Fragmentação média > 25%
- Deadlocks > 5 por hora

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Para contribuir:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um **Pull Request**

### 💡 Ideias para Contribuição
- Novos scripts de diagnóstico
- Suporte a outros SGBDs (Oracle, PostgreSQL)
- Dashboard em tempo real
- Exportação para Excel/PDF
- Integração com ferramentas de monitoramento

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- **Comunidade ERP Protheus** - Feedback e casos de uso
- **Microsoft SQL Server Team** - DMVs e documentação  
- **TOTVS** - Plataforma ERP que inspirou a solução

## 📞 Suporte e Contato

### 🐛 Reportar Bugs
Encontrou um problema? [Abra uma issue](https://github.com/ftvernier/sql-diagnostic-generator/issues)

### 💬 Discussões
Participe das discussões na [área de Discussions](https://github.com/ftvernier/sql-diagnostic-generator/discussions)

### 📧 Contato Direto
- **LinkedIn**: [Fernando Vernier]([https://linkedin.com/in/seu-perfil](https://www.linkedin.com/in/fernando-v-10758522/))
- **Email**: fernando.vernier@hotmail.com
---

<div align="center">

**🚀 Desenvolvido com ❤️ para a comunidade ERP Protheus**

[![GitHub](https://img.shields.io/badge/GitHub-ftvernier-black?style=flat-square&logo=github)](https://github.com/ftvernier)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Conectar-blue?style=flat-square&logo=linkedin)]([https://linkedin.com/in/seu-perfil](https://www.linkedin.com/in/fernando-v-10758522/))

</div>

---

<sub>📅 Última atualização: Junho 2025 | 🔄 Atualizado regularmente com novos scripts e melhorias</sub>
