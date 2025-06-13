# Monitor de URL Protheus

Sistema de monitoramento automatizado para verificar a disponibilidade e performance de URLs do sistema Protheus, com alertas por e-mail.

## 📋 Descrição

Este projeto oferece scripts de monitoramento para Windows (PowerShell) e Linux (Bash) que:
- Verificam a disponibilidade da URL a cada 60 segundos
- Medem o tempo de resposta das requisições
- Enviam alertas por e-mail em caso de indisponibilidade ou lentidão
- Mantêm logs detalhados de todas as verificações

## 🚀 Funcionalidades

- ✅ Monitoramento contínuo 24/7
- ⏱️ Detecção de lentidão (tempo de resposta configurável)
- 📧 Alertas por e-mail automáticos
- 📝 Logs detalhados com timestamp
- 🔄 Verificação a cada 5 segundos
- ❌ Detecção de erros HTTP

## 💻 Versão Windows (PowerShell)

### Pré-requisitos

- Windows PowerShell 5.0 ou superior
- Permissões para executar scripts PowerShell
- Acesso SMTP para envio de e-mails

### Instalação

1. **Clone o repositório ou baixe o script**
   ```powershell
   git clone [url-do-repositorio]
   cd monitor_url
   ```

2. **Configure as variáveis no script `script.ps1`**
   ```powershell
   $URL = "https://seuprotheus.com.br/webapp"
   $EmailFrom = "seu-email@empresa.com"
   $EmailTo = "destinatario@empresa.com"
   $SmtpServer = "smtp.office365.com"
   $SmtpPort = 587
   $SmtpUser = "seu-email@empresa.com"
   $SmtpPassword = "sua-senha-aqui"
   ```

3. **Habilite a execução de scripts (se necessário)**
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Execução

```powershell
# Execute o script
.\script.ps1

# Ou execute como administrador para melhor performance
Start-Process PowerShell -Verb RunAs -ArgumentList "-File C:\caminho\para\script.ps1"
```

### Configuração de E-mail para Provedores Comuns

**Office 365:**
```powershell
$SmtpServer = "smtp.office365.com"
$SmtpPort = 587
```

**Gmail:**
```powershell
$SmtpServer = "smtp.gmail.com"
$SmtpPort = 587
# Use uma senha de aplicativo, não a senha normal
```

## 🐧 Versão Linux (Bash)

### Pré-requisitos

- Sistema Linux com Bash
- Utilitários: `curl`, `bc`, `mail` ou `sendmail`
- MTA (Mail Transfer Agent) configurado

### Instalação

1. **Clone o repositório ou baixe o script**
   ```bash
   git clone [url-do-repositorio]
   cd monitor_url
   ```

2. **Instale as dependências**
   
   **Debian/Ubuntu:**
   ```bash
   sudo apt-get update
   sudo apt-get install curl bc mailutils postfix
   ```
   
   **RedHat/CentOS:**
   ```bash
   sudo yum install curl bc mailx postfix
   ```

3. **Configure as variáveis no script `script.sh`**
   ```bash
   URL="https://seuprotheus.com.br/webapp"
   EMAIL_TO="destinatario@empresa.com"
   EMAIL_FROM="monitor@empresa.com"
   ```

4. **Dê permissão de execução**
   ```bash
   chmod +x script.sh
   ```

### Execução

```bash
# Execute o script
./script.sh

# Execute em background
nohup ./script.sh &

# Execute como serviço (recomendado)
sudo cp script.sh /usr/local/bin/monitor-protheus
sudo chmod +x /usr/local/bin/monitor-protheus
```

### Configuração para Gmail/Office365 (usando ssmtp)

1. **Instale o ssmtp**
   ```bash
   sudo apt-get install ssmtp
   ```

2. **Configure `/etc/ssmtp/ssmtp.conf`**
   ```
   root=seu-email@gmail.com
   mailhub=smtp.gmail.com:587
   AuthUser=seu-email@gmail.com
   AuthPass=senha-de-aplicativo
   UseSTARTTLS=YES
   ```

3. **Descomente o método ssmtp no script**

## 🔧 Configurações Avançadas

### Ajustar Tempo Limite de Resposta

**Windows:**
```powershell
$TEMPO_LIMITE = 10  # segundos
```

**Linux:**
```bash
TEMPO_LIMITE=5  # segundos
```

### Alterar Intervalo de Verificação

**Windows:**
```powershell
Start-Sleep -Seconds 5  # Altere o valor
```

**Linux:**
```bash
sleep 5  # Altere o valor
```

### Localização dos Logs

- **Windows:** `C:\Logs\monitor_webapp.log`
- **Linux:** `/var/log/monitor_webapp.log`

## 🚨 Tipos de Alertas

### 1. Alerta de Lentidão
Enviado quando o tempo de resposta excede o limite configurado:
- Assunto: ⚠️ Alerta: Lentidão detectada na URL do Protheus
- Informações: URL, tempo de resposta, horário

### 2. Alerta de Indisponibilidade
Enviado quando a URL retorna código HTTP diferente de 200:
- Assunto: 🚨 CRÍTICO: Indisponibilidade na URL de Produção do Protheus
- Informações: URL, código HTTP, horário

## 📊 Formato dos Logs

```
2024-01-15 10:30:45 ✅ Serviço OK (HTTP 200, Tempo: 1.23s)
2024-01-15 10:31:45 ⚠️ LENTIDÃO - Tempo de resposta: 12.45s
2024-01-15 10:32:45 ❌ ERRO - Código HTTP: 503
```

## 🛠️ Troubleshooting

### Windows

**Erro de autenticação SMTP:**
- Verifique se está usando senha de aplicativo (Gmail)
- Confirme se SMTP está habilitado (Office 365)
- Teste as credenciais manualmente

**Script não executa:**
```powershell
Get-ExecutionPolicy
Set-ExecutionPolicy RemoteSigned
```

### Linux

**E-mails não são enviados:**
```bash
# Teste o envio manual
echo "Teste" | mail -s "Teste Monitor" seu-email@empresa.com

# Verifique logs do mail
sudo tail -f /var/log/mail.log
```

**Permissão negada:**
```bash
chmod +x script.sh
sudo chown $USER:$USER /var/log/monitor_webapp.log
```

## ✉️ Suporte

Para dúvidas ou problemas, entre em contato com a equipe de infraestrutura.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Fernando Vernier**
* GitHub: https://github.com/ftvernier/erp-solutions
* LinkedIn: https://www.linkedin.com/in/fernando-v-10758522/

## 🙏 Agradecimentos

* Comunidade Protheus pela troca de experiências
* Equipe de desenvolvimento que colaborou nos testes

⭐ **Se este projeto te ajudou, deixe uma estrela!**

