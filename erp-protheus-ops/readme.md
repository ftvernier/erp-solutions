# 📊 Dashboard de Monitoramento do ERP Protheus
Este projeto é um **painel web interativo em Flask** para monitorar, iniciar/parar e administrar os serviços do ERP Protheus de forma centralizada. Ideal para equipes de TI que buscam **mais visibilidade e controle em tempo real**, com permissões de acesso diferenciadas e integração com arquivos `.INI`, `.LOG` e scripts de limpeza.

**✨ Agora com suporte completo para Linux e Windows Server!**

---

## ✅ Funcionalidades
- 🔍 **Visualização do status de todos os serviços do Protheus**
- ▶️⏹️ **Botões para iniciar, parar, reiniciar e forçar encerramento**
- 📝 **Editor online de arquivos `.INI`**
- 📄 **Visualizador somente leitura dos arquivos `.LOG`**
- 🧹 **Execução e edição de scripts de limpeza via interface**
- 🔐 **Controle de acesso com login por `Basic Auth` (admin e visualização)**
- 🐧🪟 **Compatível com Linux (systemd) e Windows Server (Windows Services)**

---

## 🚀 Instalação

### 📋 Dependências

Crie um arquivo `requirements.txt`:

**Para Linux:**
```
Flask==2.3.3
python-dotenv==1.0.0
```

**Para Windows:**
```
Flask==2.3.3
python-dotenv==1.0.0
psutil==5.9.6
pywin32==306
```

### 1. Crie o ambiente virtual:

**Linux:**
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure variáveis de ambiente

Crie o arquivo `dashboard.env` no mesmo diretório do script:

```env
SECRET_KEY=chave_muito_secreta_aqui
ADMIN_PASSWORD=senha_admin_segura
VIEWER_PASSWORD=senha_viewer_segura
```

Use um gerador como https://passwordwolf.com para criar uma chave segura.

### 3. Configuração específica por plataforma

#### 🐧 Linux
```python
# Caminhos Linux
CAMINHO_INIS = '/totvs/p12prd/bin'
CAMINHO_LIMPEZA = '/totvs/scripts/limpa_upddistr.sh'

# Serviços systemd
SERVICOS = [
    "appserver_broker", "appserver_portal_01",
    "appserver_slave_01", "appserver_slave_02",
    # ... seus serviços
]
```

#### 🪟 Windows Server
```python
# Caminhos Windows
CAMINHO_INIS = r'C:\TOTVS\P12PRD\bin'
CAMINHO_LIMPEZA = r'C:\TOTVS\scripts\limpa_upddistr.bat'

# Serviços Windows
SERVICOS = [
    "TOTVS_AppServer_Broker", "TOTVS_AppServer_Portal_01",
    "TOTVS_AppServer_Slave_01", "TOTVS_AppServer_Slave_02",
    # ... seus serviços
]
```

Para descobrir os nomes dos serviços Windows:
```cmd
sc query | findstr "TOTVS"
```

### 4. Execute localmente (modo dev)

**Linux:**
```bash
source venv/bin/activate
python dashboard.py
```

**Windows:**
```cmd
venv\Scripts\activate
python dashboard_windows.py
```

---

## 🛠️ Implantação em Produção

### 🐧 Linux com systemd

Crie o arquivo de serviço:
```ini
# /etc/systemd/system/dashboard-erp.service
[Unit]
Description=Dashboard de Monitoramento ERP Protheus
After=network.target

[Service]
ExecStart=/totvs/scripts/venv/bin/python /totvs/scripts/dashboard.py
WorkingDirectory=/totvs/scripts
Environment="PYTHONUNBUFFERED=1"
Restart=always
User=totvs
Group=totvs

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard-erp.service
sudo systemctl start dashboard-erp.service
```

### 🪟 Windows Server como Serviço

#### Opção 1: NSSM (Recomendado)
1. **Baixe o NSSM**: https://nssm.cc/download
2. **Instale o serviço**:
   ```cmd
   nssm install "Dashboard_ERP_Protheus" "C:\Python\python.exe" "C:\caminho\para\dashboard_windows.py"
   nssm set "Dashboard_ERP_Protheus" AppDirectory "C:\caminho\para\seu\script"
   nssm start "Dashboard_ERP_Protheus"
   ```

#### Opção 2: Executar manualmente
```cmd
cd C:\caminho\para\seu\script
venv\Scripts\activate
python dashboard_windows.py
```

---

## 🧹 Scripts de Limpeza

### 🐧 Linux (.sh)
```bash
#!/bin/bash
echo "Iniciando limpeza do UPDDISTR..."

# Para cada serviço
sudo systemctl stop appserver_broker
sudo systemctl stop appserver_portal_01
# ... pare todos os serviços necessários

echo "Aguardando serviços pararem..."
sleep 10

# Limpeza de arquivos temporários
rm -f /totvs/p12prd/UPDDISTR/*.tmp
rm -f /totvs/p12prd/UPDDISTR/*.lock

echo "Reiniciando serviços..."
sudo systemctl start appserver_broker
sudo systemctl start appserver_portal_01
# ... inicie todos os serviços necessários

echo "Limpeza concluída!"
```

### 🪟 Windows (.bat)
```batch
@echo off
echo Iniciando limpeza do UPDDISTR...

REM Para cada serviço TOTVS
sc stop "TOTVS_AppServer_Broker"
sc stop "TOTVS_AppServer_Portal_01"
REM ... pare todos os serviços necessários

echo Aguardando serviços pararem...
timeout /t 10

REM Limpeza de arquivos temporários
del /q "C:\TOTVS\P12PRD\UPDDISTR\*.tmp"
del /q "C:\TOTVS\P12PRD\UPDDISTR\*.lock"

echo Reiniciando serviços...
sc start "TOTVS_AppServer_Broker"
sc start "TOTVS_AppServer_Portal_01"
REM ... inicie todos os serviços necessários

echo Limpeza concluída!
pause
```

---

## 🔒 Controle de Acesso

As permissões são definidas diretamente no código:

```python
USUARIOS = {
    "squad-erp": {
        "senha": os.getenv("ADMIN_PASSWORD"),
        "permissoes": "admin"
    },
    "viewer-erp": {
        "senha": os.getenv("VIEWER_PASSWORD"),
        "permissoes": "visualizacao"
    }
}
```

### Níveis de Acesso:
- **Admin**: Pode iniciar/parar serviços, editar INIs, executar scripts
- **Visualização**: Apenas visualizar status dos serviços

---

## 📱 Interface do Sistema

### 💡 Principais Telas:
- 📊 **Página inicial**: Status em tempo real de todos os serviços
- 🔧 **Modal de limpeza**: Resultado da execução dos scripts
- ✏️ **Editor de INI**: Edição online dos arquivos de configuração
- 📋 **Visualizador de LOG**: Leitura dos arquivos de log (somente leitura)
- 🎛️ **Painel adaptado**: Interface responsiva para diferentes níveis de acesso

### ⚡ Recursos Avançados:
- 🔄 **Auto-refresh**: Atualização automática configurável (10/20/30s)
- 🎯 **Ações em lote**: Iniciar/parar todos os serviços de uma vez
- 🛡️ **Kill process**: Forçar encerramento de processos travados
- 📱 **Design responsivo**: Interface adaptada para desktop e mobile

---

## 🌐 Acesso

Após iniciar o dashboard, acesse:
- **URL**: `http://localhost:8050`
- **Login**: Use as credenciais configuradas no `dashboard.env`

---

## 🔧 Permissões Necessárias

### 🐧 Linux:
- Controlar serviços systemd (`sudo` ou grupo `systemd-journal`)
- Ler/escrever nos diretórios do TOTVS
- Executar scripts shell

### 🪟 Windows:
- Controlar serviços Windows (usuário com privilégios administrativos)
- Ler/escrever nos diretórios do TOTVS
- Executar scripts batch

---

## 📁 Estrutura do Projeto

```
dashboard-erp-protheus/
├── dashboard_protheus_ops.py                  # Versão Linux
├── dashboard_protheus_ops_windows.py          # Versão Windows
├── requirements_linux.txt                     # Dependências Python
├── requirements_windows.txt                   # Dependências Python
└── README.md
```

---

## 🚨 Troubleshooting

### Problemas Comuns:

**🔴 Erro de permissão nos serviços:**
- Linux: Adicione o usuário ao grupo `sudo` ou configure `sudoers`
- Windows: Execute como administrador

**🔴 Serviços não aparecem:**
- Verifique se os nomes estão corretos na lista `SERVICOS`
- Linux: `systemctl list-units | grep appserver`
- Windows: `sc query | findstr "TOTVS"`

**🔴 Erro de encoding nos arquivos:**
- Versão Windows trata automaticamente UTF-8 e Latin-1

---

## 👨‍💻 Autor

**Fernando Vernier**  
Staff Software Engineer - Especialista em ERP Protheus  
🔗 https://www.linkedin.com/in/fernando-v-10758522/

---

## 📢 Licença

Distribuído sob licença **MIT**.  
Sinta-se à vontade para usar, adaptar e contribuir com melhorias para sua realidade.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- 🐛 Reportar bugs
- 💡 Sugerir novas funcionalidades  
- 🔧 Enviar pull requests
- 📖 Melhorar a documentação

**⭐ Se este projeto te ajudou, considere dar uma estrela!**
