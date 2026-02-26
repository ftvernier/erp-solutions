# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.1.0] - 2024-02-26

### 🔥 Adicionado
- **Streaming de Logs em Tempo Real** via Server-Sent Events (SSE)
- **Download de Log Completo** sem limite de linhas
- **Controles de Streaming**: Pausar, continuar, parar e limpar
- **Auto-scroll Configurável** para visualização de logs
- **Colorização Automática** de logs (error/warning/info/debug)
- **Modo Terminal** com fundo preto e fonte monoespaçada
- **Copiar Logs** para clipboard com um clique
- **Contador em Tempo Real** de linhas recebidas
- **Status Visual** de conexão (conectado/pausado/erro)
- **Reconexão Automática** em caso de falha (5s)

### 📝 Endpoints Novos
- `GET /api/logs/<servico>/stream` - Streaming em tempo real
- `GET /api/logs/<servico>/download` - Download completo do log

### 🔧 Melhorado
- Interface de logs completamente redesenhada
- Limite de linhas no modo estático aumentado para 1.000
- Performance otimizada para streaming de alto volume
- UX melhorada com controles intuitivos

### 🐛 Corrigido
- Error handlers agora passam `permissoes` corretamente
- Templates não geram mais erro quando `permissoes` não está definido

---

## [2.0.0] - 2024-02-07

### 🎉 Lançamento Inicial
- Dashboard web completo para gerenciamento de serviços Protheus
- Monitoramento em tempo real (CPU, RAM, threads, uptime)
- Timer configurável com countdown visual
- Sistema de permissões (Admin/Viewer)
- Histórico permanente com auditoria (SQLite)
- API REST completa (10+ endpoints)
- Logs integrados via journalctl
- Tema claro/escuro
- Mobile-ready (Bootstrap 5.3)
- Controle de 32+ serviços em 7 grupos funcionais

### 📊 Features Principais
- Start/Stop/Restart serviços com 1 clique
- Kill forçado para processos travados
- Ações em lote (iniciar/parar todos)
- Exportação CSV (histórico e métricas)
- Sistema de alertas automáticos
- Estatísticas consolidadas

---

## Formato

Este changelog segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

### Tipos de Mudanças
- **Adicionado** para novas funcionalidades
- **Modificado** para mudanças em funcionalidades existentes
- **Descontinuado** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correção de bugs
- **Segurança** para vulnerabilidades
