# 🚀 Dashboard ERP Protheus 2.0

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

**Dashboard moderno e completo para gerenciamento de serviços ERP Protheus no Linux**

[🎯 Features](#-features) • [🚀 Quick Start](#-quick-start) • [📖 Documentação](#-documentação) • [🎨 Screenshots](#-screenshots) • [🤝 Contribuindo](#-contribuindo)

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Features](#-features)
- [Tecnologias](#-tecnologias)
- [Screenshots](#-screenshots)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [API REST](#-api-rest)
- [Arquitetura](#-arquitetura)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🎯 Sobre o Projeto

O **Dashboard ERP Protheus 2.0** é uma solução web completa desenvolvida para simplificar o gerenciamento de serviços ERP Protheus em ambientes Linux (OpenSUSE). 

Criado para resolver a necessidade de uma interface amigável que permitisse à equipe técnica gerenciar múltiplos serviços systemd sem a necessidade de acesso SSH ou conhecimento profundo de linha de comando.

### 💡 Motivação

Em ambientes corporativos com dezenas de serviços Protheus rodando simultaneamente, o gerenciamento via terminal pode ser:
- ⏰ **Demorado**: Múltiplos comandos SSH para verificar status
- 🔍 **Complexo**: Necessário conhecimento de systemctl, journalctl, etc
- 🚫 **Limitado**: Sem visibilidade de métricas e histórico
- 👥 **Restritivo**: Nem todos da equipe têm experiência com Linux

### ✨ Solução

Dashboard web intuitivo que oferece:
- 📊 Visão consolidada de todos os serviços
- 🎯 Controle centralizado com poucos cliques
- 📈 Monitoramento em tempo real
- 📝 Auditoria completa de ações
- 🔐 Controle de permissões por nível

---

## ✨ Features

### 🎨 Interface & UX

- ✅ **Design Moderno**: Interface responsiva com Bootstrap 5
- 🌓 **Tema Claro/Escuro**: Alternância suave entre temas
- 📱 **Mobile-First**: Totalmente responsivo para tablets e celulares
- 🎯 **Organização Inteligente**: 32 serviços organizados em 7 grupos funcionais
- 🔍 **Busca em Tempo Real**: Filtro instantâneo de serviços
- ⏱️ **Timer Configurável**: Auto-refresh com countdown visual (5s até 1min)

### 📊 Monitoramento

- 💻 **Métricas de CPU**: Percentual de uso por serviço
- 💾 **Uso de Memória**: RAM em MB e percentual
- 🧵 **Threads Ativas**: Quantidade de threads por processo
- ⏰ **Uptime Real**: Tempo de atividade calculado automaticamente
- 📈 **Dashboard Cards**: Visão geral com estatísticas consolidadas
- 🎨 **Indicadores Coloridos**: Verde/Amarelo/Vermelho baseado em thresholds

### 🔧 Gerenciamento

- ▶️ **Iniciar Serviços**: Start individual ou em lote
- ⏹️ **Parar Serviços**: Stop individual ou em lote
- 🔄 **Reiniciar**: Restart individual ou em lote
- ⚡ **Kill Forçado**: Encerramento forçado de processos travados
- 📝 **Logs Integrados**: Visualização direta do journalctl
- 🎯 **Ações em Grupo**: Gerenciar múltiplos serviços simultaneamente

### 📝 Auditoria & Histórico

- 🗄️ **Banco de Dados SQLite**: Persistência de histórico e métricas
- 👤 **Rastreamento de Usuário**: Quem executou cada ação
- 🌐 **IP e User-Agent**: Identificação completa de origem
- ⏰ **Timestamp Preciso**: Data/hora de cada operação
- 📊 **Estatísticas de Uso**: Análise de ações e tendências
- 💾 **Exportação CSV**: Relatórios exportáveis

### 🔐 Segurança

- 🔒 **Autenticação HTTP Basic**: Proteção de acesso
- 👥 **Dois Níveis**: Administrador e Visualizador
- 🛡️ **Permissões Granulares**: Controle por ação
- 📋 **Auditoria Completa**: Todas as ações registradas
- 🔑 **Senhas Configuráveis**: Via variáveis de ambiente
- 🚫 **Validação de Inputs**: Proteção contra injeções

### 🔌 API REST

- 🌐 **10+ Endpoints**: API completa documentada
- 📊 **Status em JSON**: Dados estruturados
- 🔧 **Ações Remotas**: Controle via API
- 📈 **Métricas Históricas**: Dados de performance
- 📝 **Logs Programáticos**: Acesso aos logs via API
- 🔐 **Autenticação**: Mesmas credenciais do dashboard

---

## 🛠️ Tecnologias

### Backend

- **Python 3.10+**: Linguagem principal
- **Flask 3.0**: Framework web
- **SQLite3**: Banco de dados embutido
- **systemd**: Integração com serviços Linux
- **python-dotenv**: Gerenciamento de variáveis de ambiente

### Frontend

- **Bootstrap 5.3**: Framework CSS
- **Bootstrap Icons 1.11**: Ícones
- **JavaScript ES6+**: Interatividade
- **Chart.js 4.4** *(futuro)*: Gráficos de métricas

### Infraestrutura

- **Linux (OpenSUSE Leap 15.6)**: Sistema operacional
- **systemd**: Gerenciador de serviços
- **journalctl**: Sistema de logs
- **sudo**: Execução privilegiada

---

## 🎨 Screenshots

### Dashboard Principal
```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard ERP Protheus 2.0              🌓  👤 squad-erp   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │   32    │  │    28   │  │    4    │  │  87.5%  │       │
│  │ Total   │  │  Ativos │  │ Parados │  │ Uptime  │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  🔍 [Buscar serviços...        ] ⏸️ [10s▼] 🔄 ⏱️ 8s      │
│                                                             │
│  ┌─ WebApp & REST ────────────── 5/5 ativos 100% ────────┐ │
│  │ Serviço              Status  CPU   RAM    Ações       │ │
│  │ broker_rest          🟢Ativo  15%  512MB  ▶️⏹🔄⚡     │ │
│  │ broker_webapp        🟢Ativo  22%  1.2GB  ▶️⏹🔄⚡     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Slaves (Processamento) ──── 8/10 ativos 80% ─────────┐ │
│  │ slave_01             🟢Ativo  45%  2.1GB  ▶️⏹🔄⚡     │ │
│  │ slave_02             🔴Parado   0%    0MB  ▶️⏹🔄       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Página de Logs
```
┌─────────────────────────────────────────────────────────────┐
│  📄 Visualização de Logs                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Serviço: [appserver_slave_01  ▼]  Linhas: [100 ▼] 🔍     │
│                                                             │
│  ┌─ Logs de appserver_slave_01 ──────────────────────────┐ │
│  │ Feb 07 14:30:15 server appserver[12345]: Starting...  │ │
│  │ Feb 07 14:30:16 server appserver[12345]: Connected    │ │
│  │ Feb 07 14:30:17 server appserver[12345]: Ready        │ │
│  │ ...                                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Pré-requisitos

### Sistema Operacional
- Linux (testado em OpenSUSE Leap 15.6)
- systemd habilitado
- sudo configurado

### Software
```bash
Python 3.10 ou superior
pip3
systemd
journalctl
```

### Permissões
- Usuário com acesso sudo
- Permissões para executar systemctl
- Acesso aos logs do journalctl

---

## 🚀 Instalação

### Instalação Automatizada (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/dashboard-erp-protheus-v2.git
cd dashboard-erp-protheus-v2

# 2. Execute o instalador
chmod +x install.sh
./install.sh

# 3. Configure as senhas
nano dashboard.env
# Altere USER_SQUAD_ERP_PASS e USER_VIEWER_ERP_PASS

# 4. Inicie o dashboard
./start.sh
```

### Instalação Manual

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/dashboard-erp-protheus-v2.git
cd dashboard-erp-protheus-v2

# 2. Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis
cp dashboard.env.example dashboard.env
nano dashboard.env

# 5. Configure sudoers
sudo visudo
# Adicione as linhas conforme documentação

# 6. Inicialize banco
python3 -c "from models import Database; Database()"

# 7. Inicie aplicação
python3 app.py
```

### Docker (Em Breve)

```bash
docker pull seu-usuario/dashboard-erp-protheus:latest
docker run -p 8050:8050 dashboard-erp-protheus
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (`dashboard.env`)

```env
# Flask
SECRET_KEY=sua-chave-secreta-forte-aqui
DEBUG=False
HOST=0.0.0.0
PORT=8050

# Banco de Dados
DATABASE_PATH=dashboard.db

# Limites
MAX_LOG_LINES=100
ACTION_TIMEOUT=30
HISTORY_RETENTION_DAYS=90

# Auto-refresh
DEFAULT_REFRESH_INTERVAL=10000
MIN_REFRESH_INTERVAL=5000

# Métricas
ENABLE_PERFORMANCE_METRICS=True
METRICS_COLLECTION_INTERVAL=30

# Usuários (ALTERE AS SENHAS!)
USER_SQUAD_ERP_PASS=sua-senha-admin-forte
USER_VIEWER_ERP_PASS=sua-senha-viewer-forte

# Emails
ADMIN_EMAIL=admin@empresa.com
VIEWER_EMAIL=viewer@empresa.com
```

### Grupos de Serviços (`config.py`)

```python
GRUPOS = {
    "WebApp & REST": {
        "icon": "bi-globe",
        "color": "#4f46e5",
        "servicos": [
            "appserver_broker_rest",
            "appserver_broker_webapp",
            # Adicione seus serviços aqui
        ]
    },
    # Adicione mais grupos conforme necessário
}
```

### Configuração Sudoers

```bash
sudo visudo
```

Adicione ao final:
```bash
# Dashboard ERP Protheus
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/systemctl start *.service
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop *.service
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart *.service
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active *.service
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/systemctl show *.service
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u *.service *
seu-usuario ALL=(ALL) NOPASSWD: /usr/bin/kill -9 *
```

---

## 📖 Uso

### Acesso Web

```
URL: http://seu-servidor:8050

Credenciais Padrão:
├─ Administrador
│  └─ Usuário: squad-erp
│     Senha: (configurada no dashboard.env)
│
└─ Visualizador
   └─ Usuário: viewer-erp
      Senha: (configurada no dashboard.env)
```

### Funcionalidades por Perfil

#### 👨‍💼 Administrador (`squad-erp`)
- ✅ Visualizar status de todos os serviços
- ✅ Iniciar/Parar/Reiniciar serviços
- ✅ Kill forçado de processos
- ✅ Visualizar logs
- ✅ Acessar histórico completo
- ✅ Exportar relatórios
- ✅ Executar ações em lote

#### 👁️ Visualizador (`viewer-erp`)
- ✅ Visualizar status de todos os serviços
- ✅ Visualizar métricas e uptime
- ✅ Visualizar logs
- ✅ Acessar histórico
- ✅ Exportar relatórios
- ❌ Não pode executar ações

### Timer de Auto-Refresh

```
Intervalos disponíveis:
├─ 5 segundos   → Ambiente de testes
├─ 10 segundos  → Produção (padrão)
├─ 15 segundos  → Médio
├─ 20 segundos  → Lento
├─ 30 segundos  → Muito lento
└─ 1 minuto     → Economia de recursos

Controles:
⏸️ Pausar/Retomar
⏱️ Countdown visual
🎨 Cores: Verde (>5s) → Azul (3-5s) → Amarelo (≤3s)
```

---

## 🔌 API REST

### Autenticação

Todas as requisições requerem HTTP Basic Auth:

```bash
curl -u squad-erp:senha http://localhost:8050/api/status
```

### Endpoints Principais

#### Status de Serviços

```bash
# Todos os serviços
GET /api/status

# Serviço específico
GET /api/status/{servico}

# Resposta
{
  "success": true,
  "servico": {
    "servico": "appserver_slave_01",
    "ativo": true,
    "pid": "12345",
    "uptime": "2d 5h 30m",
    "cpu_percent": 15.3,
    "memoria_mb": 512.5,
    "threads": 25
  }
}
```

#### Executar Ações

```bash
POST /api/acao
Content-Type: application/json

{
  "servico": "appserver_slave_01",
  "acao": "restart"
}

# Ações disponíveis: start, stop, restart, kill
# Ações globais: iniciar_todos, parar_todos
```

#### Logs

```bash
GET /api/logs/{servico}?linhas=100

# Resposta
{
  "success": true,
  "servico": "appserver_slave_01",
  "logs": ["linha 1", "linha 2", ...],
  "total_linhas": 100
}
```

#### Métricas Históricas

```bash
GET /api/metricas/{servico}?limite=100

# Resposta
{
  "success": true,
  "metricas": [...],
  "media_24h": {
    "cpu_avg": 25.5,
    "memory_avg": 1024.0
  }
}
```

#### Histórico de Ações

```bash
GET /api/historico?limite=100&servico=slave_01&usuario=admin

# Resposta
{
  "success": true,
  "historico": [
    {
      "timestamp": "2024-02-07 14:30:15",
      "usuario": "squad-erp",
      "servico": "appserver_slave_01",
      "acao": "restart",
      "status": "sucesso"
    }
  ]
}
```

#### Alertas

```bash
# Listar alertas ativos
GET /api/alertas?ativos=true

# Resolver alerta
POST /api/alertas/{id}/resolver
```

### Exemplos de Uso

#### Python

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('squad-erp', 'sua-senha')

# Obter status
response = requests.get('http://localhost:8050/api/status', auth=auth)
data = response.json()

# Reiniciar serviço
payload = {'servico': 'appserver_slave_01', 'acao': 'restart'}
response = requests.post('http://localhost:8050/api/acao', json=payload, auth=auth)
```

#### cURL

```bash
# Status
curl -u squad-erp:senha http://localhost:8050/api/status

# Reiniciar
curl -u squad-erp:senha \
  -H "Content-Type: application/json" \
  -d '{"servico":"appserver_slave_01","acao":"restart"}' \
  http://localhost:8050/api/acao

# Logs
curl -u squad-erp:senha \
  "http://localhost:8050/api/logs/appserver_slave_01?linhas=50"
```

---

## 🏗️ Arquitetura

### Estrutura do Projeto

```
dashboard-erp-v2/
├── 📄 app.py                 # Aplicação Flask principal
├── ⚙️  config.py              # Configurações centralizadas
├── 🔐 auth.py                # Sistema de autenticação
├── 🔧 services.py            # Gerenciamento de serviços
├── 🗄️  models.py              # Modelos de banco de dados
├── 📋 requirements.txt       # Dependências Python
├── 🔧 dashboard.env          # Variáveis de ambiente
├── 📁 templates/             # Templates HTML
│   ├── base.html            # Template base
│   ├── dashboard.html       # Dashboard principal
│   ├── history.html         # Página de histórico
│   ├── logs.html            # Visualização de logs
│   └── error.html           # Página de erro
├── 📁 static/               # Arquivos estáticos
│   ├── css/
│   │   └── dashboard.css   # Estilos customizados
│   └── js/
│       └── dashboard.js    # JavaScript do frontend
├── 🗄️  dashboard.db          # Banco SQLite (gerado)
├── 📖 README.md             # Este arquivo
├── 📝 CHANGELOG.md          # Histórico de versões
└── 🚀 install.sh            # Script de instalação
```

### Fluxo de Dados

```
┌─────────────┐
│  Navegador  │
└──────┬──────┘
       │ HTTP Request (Basic Auth)
       ▼
┌─────────────────────────────────┐
│  Flask App (app.py)             │
│  ├─ Autenticação (auth.py)      │
│  ├─ Rotas e Controllers         │
│  └─ Templates (Jinja2)          │
└──────┬──────────────────────────┘
       │
       ├──► 🔧 ServiceManager (services.py)
       │    ├─ systemctl commands
       │    ├─ journalctl logs
       │    └─ Process metrics (ps)
       │         │
       │         ▼
       │    ┌─────────────────┐
       │    │  systemd        │
       │    │  (Linux)        │
       │    └─────────────────┘
       │
       └──► 🗄️  Database (models.py)
            ├─ historico_acoes
            ├─ metricas_servicos
            └─ alertas
                 │
                 ▼
            ┌─────────────────┐
            │  SQLite3        │
            └─────────────────┘
```

### Banco de Dados (SQLite)

#### Tabela: `historico_acoes`
```sql
CREATE TABLE historico_acoes (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario TEXT NOT NULL,
    nome_completo TEXT,
    servico TEXT,
    acao TEXT NOT NULL,
    status TEXT DEFAULT 'sucesso',
    mensagem TEXT,
    ip_address TEXT,
    user_agent TEXT
);
```

#### Tabela: `metricas_servicos`
```sql
CREATE TABLE metricas_servicos (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    servico TEXT NOT NULL,
    cpu_percent REAL,
    memory_mb REAL,
    memory_percent REAL,
    threads INTEGER,
    status TEXT,
    uptime_seconds INTEGER
);
```

#### Tabela: `alertas`
```sql
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    servico TEXT NOT NULL,
    tipo_alerta TEXT NOT NULL,
    severidade TEXT DEFAULT 'warning',
    mensagem TEXT,
    resolvido BOOLEAN DEFAULT 0,
    resolvido_em DATETIME,
    resolvido_por TEXT
);
```

---

## 🗺️ Roadmap

### 🚧 Em Desenvolvimento

- [ ] Gráficos interativos com Chart.js
- [ ] Dashboard customizável (drag-and-drop)
- [ ] Webhooks para Slack/Microsoft Teams
- [ ] Notificações por email
- [ ] PWA (Progressive Web App)

### 💡 Sugestões

Tem alguma ideia? [Abra uma issue](https://github.com/ftvernier/erp-solutions/issues/new) com a tag `enhancement`!

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Este projeto segue as práticas de código aberto.

### Como Contribuir

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. **Push** para a branch (`git push origin feature/MinhaFeature`)
5. Abra um **Pull Request**

### Diretrizes

- ✅ Siga o estilo de código existente
- ✅ Adicione testes quando aplicável
- ✅ Atualize a documentação
- ✅ Descreva claramente as mudanças no PR
- ✅ Um recurso por PR

### Reportar Bugs

Encontrou um bug? [Abra uma issue](https://github.com/seu-usuario/dashboard-erp-protheus-v2/issues/new) com:

- 🐛 Descrição clara do problema
- 📋 Passos para reproduzir
- 💻 Ambiente (OS, Python version, etc)
- 📸 Screenshots se aplicável

### Código de Conduta

Este projeto adere ao [Contributor Covenant](https://www.contributor-covenant.org/). Ao participar, você concorda em manter um ambiente respeitoso e acolhedor.

---

## 📊 Estatísticas do Projeto

```
📁 Arquivos Python:       15
📄 Linhas de Código:      ~3.800
🧪 Testes:                Em desenvolvimento
📚 Documentação:          Completa
⭐ GitHub Stars:          -
🍴 Forks:                 -
📈 Commits:               100+
👥 Contribuidores:        1 (seja o próximo!)
```

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

```
MIT License

Copyright (c) 2024 Fernando Vernier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 👨‍💻 Autor

<div align="center">

### **Fernando Vernier**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/seu-linkedin)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/seu-usuario)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:fernando@solfacil.com.br)

**DBA & Tech Lead** | **ERP Protheus Specialist** | **Open Source Contributor**

🏢 Solfácil | 📍 Brasil

</div>

---

## 🙏 Agradecimentos

- 🏢 **Solfácil** - Pelo ambiente e suporte ao desenvolvimento
- 👥 **Squad ERP** - Pelo feedback e testes constantes
- 🌟 **Comunidade TOTVS** - Pelas referências e boas práticas
- 💡 **OpenSUSE Community** - Pela excelente documentação
- 🐍 **Python Community** - Pelas bibliotecas incríveis

---

## 📚 Recursos Adicionais

### Documentação
- 📖 [Guia de Início Rápido](QUICKSTART.md)
- 📝 [Changelog Completo](CHANGELOG.md)
- 🔧 [Guia de Troubleshooting](docs/TROUBLESHOOTING.md)
- 🎨 [Guia de Contribuição](CONTRIBUTING.md)

### Links Úteis
- [TOTVS Protheus Docs](https://tdn.totvs.com/)
- [systemd Documentation](https://www.freedesktop.org/wiki/Software/systemd/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.3/)

---

## 💬 FAQ

<details>
<summary><b>Funciona em outras distribuições Linux?</b></summary>

Sim! Testado em OpenSUSE, mas deve funcionar em qualquer distro com systemd (Ubuntu, Debian, CentOS, etc). Apenas ajuste os comandos de instalação de pacotes.

</details>

<details>
<summary><b>Posso usar com outros ERPs além do Protheus?</b></summary>

Sim! O dashboard gerencia qualquer serviço systemd. Basta ajustar a lista de serviços em `config.py`.

</details>

<details>
<summary><b>Como adiciono novos serviços?</b></summary>

Edite o arquivo `config.py` e adicione seus serviços nos grupos apropriados. Não precisa reiniciar, apenas recarregue a página.

</details>

<details>
<summary><b>Suporta múltiplos servidores?</b></summary>

Atualmente não, mas está no roadmap para v2.2. Por enquanto, você pode rodar uma instância por servidor.

</details>

<details>
<summary><b>Os dados são salvos permanentemente?</b></summary>

Sim! Histórico e métricas são salvos no SQLite. Configure `HISTORY_RETENTION_DAYS` para controlar por quanto tempo manter.

</details>

<details>
<summary><b>É seguro para produção?</b></summary>

Sim! Usa autenticação, auditoria completa, e validação de inputs. Recomendamos usar HTTPS com proxy reverso (nginx/Apache) em produção.

</details>

---

<div align="center">

### ⭐ Se este projeto foi útil, considere dar uma estrela!

### 🐛 Encontrou um bug? [Reporte aqui](https://github.com/seu-usuario/dashboard-erp-protheus-v2/issues)

### 💡 Tem uma sugestão? [Compartilhe conosco](https://github.com/seu-usuario/dashboard-erp-protheus-v2/discussions)

---

**Desenvolvido com ❤️ por [Fernando Vernier]([https://linkedin.com/in/seu-linkedin](https://www.linkedin.com/in/fernando-v-10758522/))**

**© 2024 Dashboard ERP Protheus 2.0 - Todos os direitos reservados**

</div>
