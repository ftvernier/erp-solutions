# 🚀 Dashboard ERP Protheus - Monitoramento Avançado

## 📊 Visão Geral

Dashboard moderno e responsivo para monitoramento e controle de serviços do ERP Protheus TOTVS em ambiente de produção. Desenvolvido com Flask e interface web moderna, oferece controle completo dos serviços do sistema com feedback visual em tempo real.

![Dashboard ERP](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-purple.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

## ✨ Principais Funcionalidades

### 🎯 **Controle de Serviços**
- **Monitoramento em tempo real** de todos os serviços do ERP
- **Ações individuais**: Iniciar, Parar, Reiniciar e Kill (força encerramento)
- **Ações em lote**: Controle global de todos os serviços simultaneamente
- **Status visual** com badges coloridos (Ativo/Inativo/Processando)

### 🔄 **Feedback Visual Avançado**
- **Notificações Toast** elegantes para cada ação executada
- **Overlay de progresso** com spinner durante execuções
- **Estados visuais** específicos para cada serviço durante processamento
- **Prevenção de múltiplas ações** simultâneas com bloqueio de interface

### 🔍 **Busca e Filtros**
- **Filtro em tempo real** para localizar serviços específicos
- **Persistência de filtros** entre sessões (localStorage)
- **Contador dinâmico** de serviços visíveis
- **Interface limpa** com botão de limpeza de filtro

### 📱 **Interface Moderna**
- **Design responsivo** compatível com desktop, tablet e mobile
- **Tema moderno** com gradientes e efeitos visuais
- **Auto-refresh configurável** (10s, 20s, 30s, 1min)
- **Controles intuitivos** com ícones Bootstrap

### 🔐 **Segurança e Permissões**
- **Autenticação HTTP Basic** integrada
- **Dois níveis de acesso**: Administrador e Visualização
- **Proteção contra ações não autorizadas**
- **Logs detalhados** de todas as operações

## 🏗️ Arquitetura Técnica

### **Backend (Python + Flask)**
```python
• Flask 2.0+ como framework web
• Subprocess para controle de serviços systemd
• python-dotenv para variáveis de ambiente
• Decorators para autenticação e autorização
• API REST para atualizações assíncronas
```

### **Frontend (HTML5 + CSS3 + JavaScript)**
```javascript
• Bootstrap 5.3.2 para responsividade
• JavaScript vanilla para interatividade
• CSS Grid e Flexbox para layouts
• Animations e transitions suaves
• LocalStorage para persistência de estado
```

### **Serviços Monitorados**
- AppServers (Broker, Portal, Compilar, Slaves)
- Workflow Servers (Faturamento, Compras, Financeiro)
- Web Services REST
- TSS (Tax Service Server)
- Smart View Agent

## 🛠️ Instalação e Configuração

### **1. Pré-requisitos**
```bash
# Sistema operacional: Linux (Ubuntu/CentOS/RHEL)
# Python 3.10+
# Sudo/Root access para controle de serviços
# Serviços systemd configurados
```

### **2. Instalação**
```bash
# Clone o repositório
git clone https://github.com/ftvernier/erp-solutions.git
cd erp-solutions/erp-protheus-ops

# Criar ambiente virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install flask python-dotenv
```

### **3. Configuração**
```bash
# Criar arquivo de ambiente
cp dashboard.env.example dashboard.env

# Editar variáveis de ambiente
nano dashboard.env
```

**Arquivo dashboard.env:**
```env
SECRET_KEY=sua_chave_secreta_super_segura
USER_SQUAD_ERP_PASS=senha_admin_segura
USER_VIEWER_ERP_PASS=senha_viewer_segura
```

### **4. Configurar como Serviço Systemd**
```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/dashboard-erp.service
```

**Conteúdo do arquivo:**
```ini
[Unit]
Description=Dashboard ERP Protheus
After=network.target

[Service]
Type=simple
User=seu_usuario
Group=seu_grupo
WorkingDirectory=/caminho/para/dashboard
ExecStart=/caminho/para/venv/bin/python dashboard.py
Restart=always
RestartSec=3
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

**Ativar serviço:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard-erp.service
sudo systemctl start dashboard-erp.service
sudo systemctl status dashboard-erp.service
```

## 🚦 Uso do Sistema

### **Acesso ao Dashboard**
```
URL: http://seu-servidor:8050
Usuários:
  - squad-erp (Administrador completo)
  - viewer-erp (Somente visualização)
```

### **Funcionalidades por Perfil**

**👨‍💼 Administrador (squad-erp):**
- Visualizar status de todos os serviços
- Executar todas as ações (start/stop/restart/kill)
- Controle global (iniciar/parar todos)
- Configurar auto-refresh
- Acesso a logs e estatísticas

**👁️ Visualizador (viewer-erp):**
- Visualizar status de todos os serviços
- Filtrar e buscar serviços
- Acompanhar estatísticas em tempo real
- Sem permissões de controle

## 📈 Monitoramento e Estatísticas

### **Dashboard Principal**
- **Serviços Ativos**: Contador em tempo real
- **Serviços Parados**: Identificação imediata de problemas
- **Total de Serviços**: Visão geral do ambiente
- **Uptime**: Percentual de disponibilidade

### **Status Individual**
- **Tempo real**: Atualização automática de status
- **PID do processo**: Para troubleshooting avançado
- **Histórico de ações**: Logs detalhados no backend

## 🔧 Personalização

### **Adicionar Novos Serviços**
```python
# No arquivo dashboard.py, editar a lista SERVICOS
SERVICOS = [
    "seu_novo_servico",
    # ... outros serviços
]
```

### **Customizar Interface**
```css
/* Modificar variáveis CSS no HTML_TEMPLATE */
:root {
    --primary-color: #sua-cor;
    --success-color: #sua-cor;
    /* ... outras variáveis */
}
```

## 📱 Responsividade

O dashboard é **100% responsivo** e funciona perfeitamente em:
- **Desktop**: Interface completa com todas as funcionalidades
- **Tablet**: Layout adaptado com navegação otimizada
- **Mobile**: Interface compacta com controles touch-friendly

## 🔒 Segurança

### **Medidas Implementadas**
- Autenticação HTTP Basic obrigatória
- Controle de permissões por usuário
- Validação de entrada em todas as ações
- Logs de auditoria completos
- Proteção contra CSRF básica

### **Recomendações Adicionais**
- Use HTTPS em produção
- Configure firewall adequadamente
- Monitore logs regularmente
- Mantenha senhas seguras e atualizadas

## 🚨 Troubleshooting

### **Problemas Comuns**

**Serviço não inicia:**
```bash
# Verificar logs
sudo journalctl -u dashboard-erp.service -f

# Verificar permissões
ls -la /caminho/para/dashboard.py

# Testar manualmente
cd /caminho/para/dashboard && python dashboard.py
```

**Erro de importação Flask:**
```bash
# Instalar dependências
pip install flask python-dotenv

# Ou globalmente
sudo pip3 install flask python-dotenv
```

**Problemas de permissão com systemctl:**
```bash
# Verificar se usuário tem acesso sudo
sudo visudo

# Adicionar linha (substitua 'usuario'):
usuario ALL=(ALL) NOPASSWD: /bin/systemctl
```

## 📋 Logs e Monitoramento

### **Logs do Sistema**
```bash
# Logs do serviço dashboard
sudo journalctl -u dashboard-erp.service

# Logs em tempo real
sudo journalctl -u dashboard-erp.service -f

# Logs dos últimos N registros
sudo journalctl -u dashboard-erp.service -n 50
```

### **Logs da Aplicação**
Todos os logs são enviados para stdout/stderr e capturados pelo systemd.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Fernando Vernier**
- GitHub: [@ftvernier]([https://github.com/ftvernier](https://github.com/ftvernier/erp-solutions))
- LinkedIn: [Fernando Vernier]([https://linkedin.com/in/fernando-vernier](https://www.linkedin.com/in/fernando-v-10758522/))

## 🙏 Agradecimentos

- Comunidade TOTVS/Protheus
- Contribuidores do projeto
- Equipe de infraestrutura

---

**⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub!**
