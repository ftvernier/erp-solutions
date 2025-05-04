# 📊 Dashboard de Monitoramento do ERP Protheus

Este projeto é um **painel web interativo em Flask** para monitorar, iniciar/parar e administrar os serviços do ERP Protheus de forma centralizada. Ideal para equipes de TI que buscam **mais visibilidade e controle em tempo real**, com permissões de acesso diferenciadas e integração com arquivos `.INI`, `.LOG` e scripts de limpeza.

---

## ✅ Funcionalidades

- 🔍 **Visualização do status de todos os serviços do Protheus**
- ▶️⏹️ **Botões para iniciar, parar, reiniciar e forçar encerramento**
- 📝 **Editor online de arquivos `.INI`**
- 📄 **Visualizador somente leitura dos arquivos `.LOG`**
- 🧹 **Execução e edição de scripts de limpeza via interface**
- 🔐 **Controle de acesso com login por `Basic Auth` (admin e visualização)**

---

## 🚀 Instalação

1. Crie o ambiente virtual:
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Configure variáveis de ambiente
Crie o arquivo .env no mesmo diretório do dashboard.py com o seguinte conteúdo:

SECRET_KEY=sua_chave_secreta_segura
Use um gerador como passwordwolf.com para criar uma chave segura

4. Execute localmente (modo dev)
source venv/bin/activate
python dashboard.py

🛠️ Implantação com systemd (Linux)

/etc/systemd/system/dashboard-erp.service
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

Ative e inicie:

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable dashboard-erp.service
sudo systemctl start dashboard-erp.service

🔒 Acesso

USUARIOS = {
    "squad-erp": {
        "senha": "senha_segura",
        "permissoes": "admin"
    },
    "viewer-erp": {
        "senha": "outra_senha_segura",
        "permissoes": "visualizacao"
    }
}

💡 Telas do sistema
Página inicial com status dos serviços

Modal com resultado do script de limpeza

Edição de arquivos .INI

Visualização de arquivos .LOG (somente leitura)

Painel adaptado para diferentes níveis de acesso

👨‍💻 Autor
Fernando Vernier
Staff Software Engineer - Especialista em ERP Protheus
https://www.linkedin.com/in/fernando-v-10758522/

📢 Licença
Distribuído sob licença MIT. Sinta-se à vontade para usar e adaptar conforme a sua realidade.
